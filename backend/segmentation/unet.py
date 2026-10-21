from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# U-NET ARCHITECTURE
# ============================================================

class DoubleConv(nn.Module):
    """
    Two consecutive:
        Conv2D -> BatchNorm -> ReLU
    blocks.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
    ) -> None:
        super().__init__()

        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        return self.block(x)


class UNet(nn.Module):
    def __init__(
        self,
        in_channels=3,
        out_channels=1,
        base_channels=32,
    ):
        super().__init__()

        self.enc1 = DoubleConv(
            in_channels,
            base_channels
        )

        self.enc2 = DoubleConv(
            base_channels,
            base_channels * 2
        )

        self.enc3 = DoubleConv(
            base_channels * 2,
            base_channels * 4
        )

        self.enc4 = DoubleConv(
            base_channels * 4,
            base_channels * 8
        )

        self.bottleneck = DoubleConv(
            base_channels * 8,
            base_channels * 16
        )

        self.pool = nn.MaxPool2d(2, 2)

        self.up4 = nn.ConvTranspose2d(
            base_channels * 16,
            base_channels * 8,
            kernel_size=2,
            stride=2
        )

        self.dec4 = DoubleConv(
            base_channels * 16,
            base_channels * 8
        )

        self.up3 = nn.ConvTranspose2d(
            base_channels * 8,
            base_channels * 4,
            kernel_size=2,
            stride=2
        )

        self.dec3 = DoubleConv(
            base_channels * 8,
            base_channels * 4
        )

        self.up2 = nn.ConvTranspose2d(
            base_channels * 4,
            base_channels * 2,
            kernel_size=2,
            stride=2
        )

        self.dec2 = DoubleConv(
            base_channels * 4,
            base_channels * 2
        )

        self.up1 = nn.ConvTranspose2d(
            base_channels * 2,
            base_channels,
            kernel_size=2,
            stride=2
        )

        self.dec1 = DoubleConv(
            base_channels * 2,
            base_channels
        )

        self.final = nn.Conv2d(
            base_channels,
            out_channels,
            kernel_size=1
        )

    def forward(self, x):

        e1 = self.enc1(x)
        p1 = self.pool(e1)

        e2 = self.enc2(p1)
        p2 = self.pool(e2)

        e3 = self.enc3(p2)
        p3 = self.pool(e3)

        e4 = self.enc4(p3)
        p4 = self.pool(e4)

        b = self.bottleneck(p4)

        d4 = self.up4(b)
        d4 = torch.cat(
            [d4, e4],
            dim=1
        )
        d4 = self.dec4(d4)

        d3 = self.up3(d4)
        d3 = torch.cat(
            [d3, e3],
            dim=1
        )
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat(
            [d2, e2],
            dim=1
        )
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat(
            [d1, e1],
            dim=1
        )
        d1 = self.dec1(d1)

        return self.final(d1)
# ============================================================
# U-NET SEGMENTATION ENGINE
# ============================================================

class UNetSegmentation:
    """
    Production-style wrapper around the trained U-Net.

    Training characteristics taken from the supplied notebook:

        RGB input
        512 x 512
        normalization:
            image * 0.5 + 0.5 was used to undo
            normalization during visualization,
            meaning dataset normalization was:
            (image - 0.5) / 0.5

        binary output
        sigmoid + threshold 0.5
    """

    IMAGE_SIZE = (512, 512)

    def __init__(
        self,
        checkpoint_path: str,
        device: str | None = None,
        threshold: float = 0.5,
    ) -> None:

        self.checkpoint_path = Path(
            checkpoint_path
        )

        if not self.checkpoint_path.is_file():
            raise FileNotFoundError(
                "U-Net checkpoint not found: "
                f"{self.checkpoint_path}"
            )

        # ----------------------------------------------------
        # Device
        # ----------------------------------------------------

        if device is None:

            self.device = torch.device(
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        else:

            self.device = torch.device(
                device
            )

        # ----------------------------------------------------
        # Model
        # ----------------------------------------------------

        self.model = UNet(
            in_channels=3,
            out_channels=1,
            base_channels=32,
        ).to(self.device)

        # ----------------------------------------------------
        # Load checkpoint
        # ----------------------------------------------------

        checkpoint = torch.load(
            self.checkpoint_path,
            map_location=self.device,
        )

        # The supplied notebook stores:
        #
        # checkpoint["model_state_dict"]
        #

        if isinstance(
            checkpoint,
            dict
        ) and "model_state_dict" in checkpoint:

            state_dict = (
                checkpoint[
                    "model_state_dict"
                ]
            )

        else:

            # Support a plain state_dict as a
            # defensive fallback.
            state_dict = checkpoint

        self.model.load_state_dict(
            state_dict
        )

        self.model.eval()

        self.threshold = float(
            threshold
        )

        self.model_loaded = True

        print(
            "[AquaScan] U-Net loaded successfully:"
            f" {self.checkpoint_path}"
        )

        print(
            f"[AquaScan] Device: {self.device}"
        )

    # ========================================================
    # PREPROCESS
    # ========================================================

    def _preprocess(
        self,
        image: Image.Image,
    ) -> tuple[torch.Tensor, tuple[int, int]]:

        # ----------------------------------------------------
        # Original dimensions
        # ----------------------------------------------------

        original_width = image.width
        original_height = image.height

        # ----------------------------------------------------
        # RGB
        # ----------------------------------------------------

        image = image.convert(
            "RGB"
        )

        # ----------------------------------------------------
        # Resize to training size
        # ----------------------------------------------------

        image = image.resize(
            self.IMAGE_SIZE,
            Image.Resampling.BILINEAR,
        )

        # ----------------------------------------------------
        # NumPy
        # ----------------------------------------------------

        array = np.asarray(
            image,
            dtype=np.float32,
        )

        # ----------------------------------------------------
        # Scale 0-255 → 0-1
        # ----------------------------------------------------

        array /= 255.0

        # ----------------------------------------------------
        # Dataset normalization
        #
        # The notebook visualization uses:
        #
        # image = image * 0.5 + 0.5
        #
        # to undo normalization.
        #
        # Therefore:
        #
        # normalized = (image - 0.5) / 0.5
        # ----------------------------------------------------

        array = (
            array - 0.5
        ) / 0.5

        # ----------------------------------------------------
        # HWC → CHW
        # ----------------------------------------------------

        array = np.transpose(
            array,
            (2, 0, 1),
        )

        tensor = torch.from_numpy(
            array
        ).float()

        # ----------------------------------------------------
        # Add batch dimension
        # ----------------------------------------------------

        tensor = tensor.unsqueeze(
            0
        ).to(
            self.device
        )

        return (
            tensor,
            (
                original_width,
                original_height,
            ),
        )

    # ========================================================
    # INFERENCE
    # ========================================================

    @torch.no_grad()
    def predict_mask(
        self,
        image_path: str,
    ) -> dict[str, Any]:

        path = Path(
            image_path
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Segmentation image not found: {path}"
            )

        # ----------------------------------------------------
        # Load image
        # ----------------------------------------------------

        image = Image.open(
            path
        ).convert("RGB")

        # ----------------------------------------------------
        # Preprocess
        # ----------------------------------------------------

        tensor, original_size = (
            self._preprocess(image)
        )

        # ----------------------------------------------------
        # Model inference
        # ----------------------------------------------------

        logits = self.model(
            tensor
        )

        # ----------------------------------------------------
        # Sigmoid
        # ----------------------------------------------------

        probabilities = torch.sigmoid(
            logits
        )

        # ----------------------------------------------------
        # Threshold
        # ----------------------------------------------------

        mask = (
            probabilities
            >= self.threshold
        ).float()

        # ----------------------------------------------------
        # CPU
        # ----------------------------------------------------

        probability_map = (
            probabilities[0, 0]
            .detach()
            .cpu()
            .numpy()
        )

        mask_array = (
            mask[0, 0]
            .detach()
            .cpu()
            .numpy()
        )

        # ----------------------------------------------------
        # Convert binary mask to uint8
        #
        # 0   = background
        # 255 = segmented object
        # ----------------------------------------------------

        mask_uint8 = (
            mask_array * 255
        ).astype(
            np.uint8
        )

        # ----------------------------------------------------
        # Resize mask back to original
        # image dimensions
        # ----------------------------------------------------

        mask_image = Image.fromarray(
            mask_uint8,
            mode="L",
        )

        mask_image = mask_image.resize(
            original_size,
            Image.Resampling.NEAREST,
        )

        final_mask = np.asarray(
            mask_image,
            dtype=np.uint8,
        )

        # ----------------------------------------------------
        # Probability map back to
        # original dimensions
        # ----------------------------------------------------

        probability_image = Image.fromarray(
            (
                probability_map * 255
            ).clip(
                0,
                255,
            ).astype(
                np.uint8
            ),
            mode="L",
        )

        probability_image = (
            probability_image.resize(
                original_size,
                Image.Resampling.BILINEAR,
            )
        )

        final_probability = (
            np.asarray(
                probability_image,
                dtype=np.uint8,
            )
        )

        # ----------------------------------------------------
        # Calculate coverage
        # ----------------------------------------------------

        total_pixels = (
            final_mask.shape[0]
            * final_mask.shape[1]
        )

        segmented_pixels = int(
            np.count_nonzero(
                final_mask
            )
        )

        coverage_pct = (
            (
                segmented_pixels
                / total_pixels
            )
            * 100.0
            if total_pixels > 0
            else 0.0
        )

        return {
            "mask": final_mask,
            "probability_map": final_probability,
            "width": original_size[0],
            "height": original_size[1],
            "coverage_pct": round(
                coverage_pct,
                2,
            ),
            "threshold": self.threshold,
        }

    # ========================================================
    # SAVE MASK
    # ========================================================

    def save_mask(
        self,
        mask: np.ndarray,
        output_path: str,
    ) -> str:

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        image = Image.fromarray(
            mask.astype(np.uint8),
            mode="L",
        )

        image.save(
            output
        )

        return str(
            output
        )

    # ========================================================
    # SAVE OVERLAY
    # ========================================================

    def save_overlay(
        self,
        image_path: str,
        mask: np.ndarray,
        output_path: str,
        alpha: float = 0.45,
    ) -> str:
        """
        Create a simple visual overlay for the frontend.

        The original sonar image remains visible and
        segmented pixels are highlighted.
        """

        image = Image.open(
            image_path
        ).convert("RGB")

        original = np.asarray(
            image,
            dtype=np.uint8,
        )

        if (
            original.shape[:2]
            != mask.shape[:2]
        ):

            mask_image = Image.fromarray(
                mask,
                mode="L",
            )

            mask_image = (
                mask_image.resize(
                    (
                        original.shape[1],
                        original.shape[0],
                    ),
                    Image.Resampling.NEAREST,
                )
            )

            mask = np.asarray(
                mask_image,
                dtype=np.uint8,
            )

        # ----------------------------------------------------
        # Create overlay image.
        #
        # Use a red highlight for the segmentation mask.
        # ----------------------------------------------------

        overlay = original.copy()

        segmented = mask > 0

        if np.any(segmented):

            highlight = np.zeros_like(
                overlay
            )

            highlight[:, :, 0] = 255

            blended = (
                (
                    (
                        1.0 - alpha
                    )
                    * overlay
                )
                + (
                    alpha
                    * highlight
                )
            ).astype(
                np.uint8
            )

            overlay[segmented] = (
                blended[segmented]
            )

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        Image.fromarray(
            overlay
        ).save(
            output
        )

        return str(
            output
        )

    # ========================================================
    # COMPLETE SEGMENTATION
    # ========================================================

    def segment(
        self,
        image_path: str,
        output_dir: str,
    ) -> dict[str, Any]:

        output_root = Path(
            output_dir
        )

        output_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = self.predict_mask(
            image_path
        )

        image_stem = Path(
            image_path
        ).stem

        mask_path = (
            output_root
            / f"{image_stem}_mask.png"
        )

        overlay_path = (
            output_root
            / f"{image_stem}_segmented.png"
        )

        self.save_mask(
            result["mask"],
            str(mask_path),
        )

        self.save_overlay(
            image_path,
            result["mask"],
            str(overlay_path),
        )

        return {
            "mask_path": str(
                mask_path
            ),
            "overlay_path": str(
                overlay_path
            ),
            "width": result[
                "width"
            ],
            "height": result[
                "height"
            ],
            "coverage_pct": result[
                "coverage_pct"
            ],
            "threshold": result[
                "threshold"
            ],
        }