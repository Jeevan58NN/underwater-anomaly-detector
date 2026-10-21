import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Radar, Layers, MapPin } from "lucide-react";

import { PageHeader } from "../components/PageHeader";
import UploadDropzone from "../components/UploadDropzone";
import AnalyzingLoader from "../components/AnalyzingLoader";
import BoundingBoxOverlay from "../components/BoundingBoxOverlay";
import ConfidenceBar from "../components/ConfidenceBar";
import { SeverityBadge, PrototypeBadge } from "../components/Badges";
import ToastStack from "../components/ToastStack";

import { useToast } from "../hooks/useToast";
import { useAppData } from "../hooks/AppDataContext";

import {
  analyzeFile,
  segmentFile,
  getAssetUrl,
} from "../services/api";

import { generatePlaceholderSonarImage } from "../services/demoData";

import type { Detection } from "../types";

export default function SonarAnalysis() {
  const location =
    useLocation() as {
      state?: {
        pendingFile?: File;
      };
    };

  const {
    currentAnalysis,
    setCurrentAnalysis,
    addDetections,
    isDemo,
  } = useAppData();

  const {
    toasts,
    pushToast,
    dismissToast,
  } = useToast();

  const [previewUrl, setPreviewUrl] =
    useState<string | null>(null);

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [activeDetectionId, setActiveDetectionId] =
    useState<string | null>(null);

  const [pendingFile, setPendingFile] =
    useState<File | null>(null);

  const [processingMode] =
    useState<"simulation" | "real">(
      "real"
    );

  const [overlayUrl, setOverlayUrl] = useState<string | null>(null);
  const [maskUrl, setMaskUrl] = useState<string | null>(null);
  const [coverage, setCoverage] = useState<number>(0);
  const [activeView, setActiveView] = useState<'detection' | 'segmentation' | null>(null);

  // ------------------------------------------------------------
  // INITIAL LOAD
  // ------------------------------------------------------------

  useEffect(() => {
    if (location.state?.pendingFile) {
      handleFile(
        location.state.pendingFile
      );
      return;
    }

    if (isDemo && currentAnalysis) {
      setPreviewUrl(
        generatePlaceholderSonarImage(
          currentAnalysis.image_width,
          currentAnalysis.image_height
        )
      );
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ------------------------------------------------------------
  // FILE SELECTION
  // ------------------------------------------------------------

  function handleFile(file: File) {
    setPendingFile(file);

    setCurrentAnalysis(null);

    setActiveDetectionId(null);
    setOverlayUrl(null);
    setMaskUrl(null);
    setCoverage(0);
    setActiveView(null);

    /*
     * Use a browser-local blob URL while the user
     * is previewing the selected file.
     */
    const url = URL.createObjectURL(file);

    setPreviewUrl(url);
  }

  // ------------------------------------------------------------
  // CLEANUP BLOB URL
  // ------------------------------------------------------------

  useEffect(() => {
    return () => {
      if (
        previewUrl &&
        previewUrl.startsWith("blob:")
      ) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // ------------------------------------------------------------
  // RUN ANALYSIS
  // ------------------------------------------------------------

  async function runAnalysis() {
    if (!pendingFile) {
      pushToast(
        "error",
        "No file selected. Please upload a sonar image or log first."
      );
      return;
    }

    setIsAnalyzing(true);
    setActiveView(null);

    try {
      /*
       * Send the selected file and the chosen mode
       * to the FastAPI backend.
       */
      const result = await analyzeFile(
        pendingFile,
        processingMode
      );

      /*
       * Store the complete backend analysis result.
       */
      setCurrentAnalysis(result);
      setActiveView('detection');

      /*
       * Add the real detections to the global data store.
       */
      addDetections(
        result.detections
      );

      /*
       * IMPORTANT:
       *
       * The backend returns a relative asset URL such as:
       *
       * /previews/SCAN-123/SCAN-123_preview.png
       *
       * getAssetUrl() converts that into:
       *
       * http://localhost:8000/previews/...
       *
       * This prevents the old 404 problem.
       */
      if (result.preview_image_url) {
        const backendPreviewUrl =
          getAssetUrl(
            result.preview_image_url
          );

        setPreviewUrl(
          backendPreviewUrl
        );
      }

      /*
       * Reset active selection so the first
       * detection can become active naturally.
       */
      setActiveDetectionId(null);

      if (
        result.detections.length === 0
      ) {
        pushToast(
          "info",
          "Analysis complete — no anomalies detected."
        );
      } else {
        pushToast(
          "success",
          `${result.detections.length} anomalies detected.`
        );
      }
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Analysis failed.";

      pushToast(
        "error",
        message
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  // ------------------------------------------------------------
  // SEGMENTATION
  // ------------------------------------------------------------

  async function runSegmentation() {
    if (!pendingFile) {
      pushToast("error", "Please select an image first.");
      return;
    }

    setIsAnalyzing(true);
    setActiveView(null);

    try {
      const result = await segmentFile(pendingFile);
      setOverlayUrl(getAssetUrl(result.overlay_url));
      setMaskUrl(getAssetUrl(result.mask_url));
      setCoverage(result.coverage_pct);
      setActiveView('segmentation');
      pushToast("success", "Segmentation completed successfully.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Segmentation failed.";
      pushToast("error", message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  // ------------------------------------------------------------
  // DETECTIONS
  // ------------------------------------------------------------

  const detections: Detection[] =
    currentAnalysis?.detections ?? [];

  const activeDetection =
    detections.find(
      (d) =>
        d.id === activeDetectionId
    ) ?? detections[0];

  // ------------------------------------------------------------
  // STATUS
  // ------------------------------------------------------------

  const statusLabel = "AI Analysis Complete";

  // ------------------------------------------------------------
  // RENDER
  // ------------------------------------------------------------

  return (
    <div>
      <PageHeader
        title="Sonar Analysis"
        subtitle="Upload a Side-Scan Sonar image and run a prototype anomaly scan"
      />

      {/* ======================================================
          UPLOAD
         ====================================================== */}

      {!previewUrl && (
        <UploadDropzone
          onFileSelected={handleFile}
        />
      )}

      {/* ======================================================
          SELECTED FILE / ANALYSIS CONTROLS
         ====================================================== */}

      {previewUrl &&
        !currentAnalysis &&
        !isAnalyzing && (
          <div className="space-y-4">
            <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-3">
              <img
                src={previewUrl}
                alt="Sonar preview"
                className="w-full rounded-lg max-h-[480px] object-contain bg-abyss-950"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3">

              <button
                onClick={
                  runAnalysis
                }
                className="inline-flex items-center gap-2 rounded-lg bg-signal-cyan px-5 py-2.5 text-sm font-semibold text-abyss-950 hover:bg-signal-teal transition-colors shadow-glow"
              >
                <Radar className="h-4 w-4" />

                Analyze Data (Detection)
              </button>

              <button
                onClick={
                  runSegmentation
                }
                className="inline-flex items-center gap-2 rounded-lg bg-signal-cyan px-5 py-2.5 text-sm font-semibold text-abyss-950 hover:bg-signal-teal transition-colors shadow-glow"
              >
                <Layers className="h-4 w-4" />

                Run Segmentation
              </button>

              <button
                onClick={() => {
                  setPreviewUrl(
                    null
                  );

                  setPendingFile(
                    null
                  );

                  setCurrentAnalysis(
                    null
                  );

                  setActiveDetectionId(
                    null
                  );

                  setOverlayUrl(null);
                  setMaskUrl(null);
                  setCoverage(0);
                  setActiveView(null);
                }}
                className="text-sm text-slate-500 hover:text-slate-300"
              >
                Choose a different file
              </button>
            </div>
          </div>
        )}

      {/* ======================================================
          ANALYZING
         ====================================================== */}

      {isAnalyzing && (
        <AnalyzingLoader />
      )}

      {/* ======================================================
          ANALYSIS RESULT
         ====================================================== */}

      {!isAnalyzing && activeView === 'detection' && currentAnalysis && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* ==================================================
                LEFT: IMAGE
               ================================================== */}

            <div className="lg:col-span-3 space-y-4">
              <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-3">
                <div className="relative rounded-lg overflow-hidden bg-abyss-950">
                  {previewUrl && (
                    <img
                      src={previewUrl}
                      alt="Sonar analysis"
                      className="w-full block"
                    />
                  )}

                  {previewUrl && (
                    <BoundingBoxOverlay
                      detections={
                        detections
                      }
                      imageWidth={
                        currentAnalysis.image_width
                      }
                      imageHeight={
                        currentAnalysis.image_height
                      }
                      activeId={
                        activeDetection?.id
                      }
                      onSelect={
                        setActiveDetectionId
                      }
                    />
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <PrototypeBadge
                  label={`Detection Status: ${statusLabel}`}
                />

                <p className="text-xs text-slate-600 font-mono">
                  {
                    currentAnalysis.analysis_id
                  }
                </p>
              </div>
            </div>

            {/* ==================================================
                RIGHT: RESULTS
               ================================================== */}

            <div className="lg:col-span-2 space-y-4">
              <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-5">
                <p className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                  <Layers className="h-4 w-4 text-signal-cyan" />

                  Detection Results
                </p>

                {detections.length ===
                0 ? (
                  <p className="text-sm text-slate-500">
                    No anomalies detected
                    in this image.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {detections.map(
                      (d) => (
                        <button
                          key={d.id}
                          onClick={() =>
                            setActiveDetectionId(
                              d.id
                            )
                          }
                          className={`w-full text-left rounded-lg border p-3.5 transition-colors ${
                            activeDetection?.id ===
                            d.id
                              ? "border-signal-cyan/50 bg-signal-cyan/5"
                              : "border-abyss-700/60 hover:border-abyss-600"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-sm font-semibold text-slate-100">
                              {
                                d.class_name
                              }
                            </p>

                            <SeverityBadge
                              severity={
                                d.severity
                              }
                            />
                          </div>

                          <ConfidenceBar
                            confidence={
                              d.confidence
                            }
                            band={
                              d.confidence_band
                            }
                          />

                          <div className="flex items-center gap-1.5 mt-2 text-[11px] text-slate-600 font-mono">
                            <MapPin className="h-3 w-3" />

                             {d.latitude !==
                              null &&
                            d.longitude !==
                              null
                              ? `${d.latitude.toFixed(
                                  4
                                )}, ${d.longitude.toFixed(
                                  4
                                )} (${d.location_status === "estimated" ? "Estimated Location" : d.location_status})`
                              : "Location unavailable"}
                          </div>
                        </button>
                      )
                    )}
                  </div>
                )}
              </div>

              {/* ==================================================
                  SEAFLOOR ASSESSMENT
                 ================================================== */}

              {activeDetection && (
                <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-5">
                  <p className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                    <Radar className="h-4 w-4 text-signal-cyan" /> Anomaly Details
                  </p>
                  <div className="space-y-2 text-xs font-mono text-slate-400 mb-4">
                    <div className="flex justify-between border-b border-abyss-800/40 pb-1.5">
                      <span>Class Name:</span>
                      <span className="text-slate-100 font-semibold">{activeDetection.class_name}</span>
                    </div>
                    <div className="flex justify-between border-b border-abyss-800/40 pb-1.5">
                      <span>Priority:</span>
                      <span className="text-slate-100">{activeDetection.priority || activeDetection.severity}</span>
                    </div>
                    <div className="flex justify-between border-b border-abyss-800/40 pb-1.5">
                      <span>Model Confidence:</span>
                      <span className="text-slate-100">{Math.round((activeDetection.model_confidence ?? activeDetection.confidence) * 100)}%</span>
                    </div>
                    {activeDetection.system_score !== undefined && activeDetection.system_score !== null && (
                      <div className="flex justify-between border-b border-abyss-800/40 pb-1.5">
                        <span>System Score:</span>
                        <span className="text-slate-100">{Math.round(activeDetection.system_score * 100)}%</span>
                      </div>
                    )}
                    <div className="flex justify-between border-b border-abyss-800/40 pb-1.5">
                      <span>Location:</span>
                      <span className="text-slate-100 font-semibold">
                        {activeDetection.latitude !== null && activeDetection.longitude !== null
                          ? `${activeDetection.latitude.toFixed(6)}, ${activeDetection.longitude.toFixed(6)}`
                          : "Location unavailable"}
                      </span>
                    </div>
                    {activeDetection.latitude !== null && activeDetection.longitude !== null && (
                      <div className="flex justify-between">
                        <span>Location Status:</span>
                        <span className="text-slate-100 uppercase text-[10px]">
                          {activeDetection.location_status === "estimated" ? "Estimated Location" : activeDetection.location_status}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeDetection && (
                <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-5">
                  <p className="text-sm font-medium text-slate-300 mb-3">
                    Seafloor Assessment
                  </p>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">
                        Artificial Anomaly
                      </span>

                      <span className="text-sonar-coral font-mono">
                        {
                          activeDetection
                            .seafloor_assessment
                            .artificial_pct
                        }
                        %
                      </span>
                    </div>

                    <div className="h-1.5 rounded-full bg-abyss-700 overflow-hidden">
                      <div
                        className="h-full bg-sonar-coral"
                        style={{
                          width: `${activeDetection.seafloor_assessment.artificial_pct}%`,
                        }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-sm mt-2">
                      <span className="text-slate-400">
                        Natural Seafloor
                      </span>

                      <span className="text-sonar-green font-mono">
                        {
                          activeDetection
                            .seafloor_assessment
                            .natural_pct
                        }
                        %
                      </span>
                    </div>

                    <div className="h-1.5 rounded-full bg-abyss-700 overflow-hidden">
                      <div
                        className="h-full bg-sonar-green"
                        style={{
                          width: `${activeDetection.seafloor_assessment.natural_pct}%`,
                        }}
                      />
                    </div>
                  </div>

                  <p className="text-[11px] text-sonar-amber font-mono mt-3">
                    Prototype Estimate
                  </p>
                </div>
              )}

              {/* ==================================================
                  CLASS INFORMATION
                 ================================================== */}

              <p className="text-[11px] text-slate-600 leading-relaxed">
                Model classes are supplied by the trained YOLO11 detector.
                Expected checkpoint classes include: Shipwreck, Aeroplane, Rock, Fish, Unknown.
              </p>
            </div>
          </div>
        )}

      {!isAnalyzing && activeView === 'segmentation' && overlayUrl && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-4">
              <p className="text-sm font-medium text-slate-300 mb-3">
                Segmented Result
              </p>
              <img
                src={overlayUrl}
                alt="U-Net segmentation"
                className="w-full rounded-lg bg-abyss-950"
              />
            </div>
            {maskUrl && (
              <div className="rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-4">
                <p className="text-sm font-medium text-slate-300 mb-3">
                  Binary Mask
                </p>
                <img
                  src={maskUrl}
                  alt="Segmentation mask"
                  className="w-full rounded-lg bg-abyss-950"
                />
              </div>
            )}
            <div className="lg:col-span-2 rounded-xl border border-abyss-700/60 bg-abyss-900/70 p-5">
              <p className="text-sm text-slate-400">
                Segmented Area
              </p>
              <p className="text-2xl font-semibold text-slate-100 mt-1">
                {coverage}%
              </p>
            </div>
          </div>
      )}

      <ToastStack
        toasts={toasts}
        onDismiss={dismissToast}
      />
    </div>
  );
}