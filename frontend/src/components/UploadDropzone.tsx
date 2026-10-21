import { useCallback, useRef, useState } from "react";
import { UploadCloud, ImageIcon } from "lucide-react";

const ACCEPTED = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".xtf", ".jsf"];

export default function UploadDropzone({
  onFileSelected,
  compact = false,
}: {
  onFileSelected: (file: File) => void;
  compact?: boolean;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndEmit = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      if (!ACCEPTED.includes(ext)) return;
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      validateAndEmit(e.dataTransfer.files?.[0]);
    },
    [validateAndEmit]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`group cursor-pointer rounded-xl border-2 border-dashed transition-colors flex flex-col items-center justify-center text-center ${
        compact ? "p-6" : "p-12"
      } ${
        isDragging
          ? "border-signal-cyan bg-signal-cyan/5"
          : "border-abyss-600 hover:border-signal-cyan/50 bg-abyss-900/50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        className="hidden"
        onChange={(e) => validateAndEmit(e.target.files?.[0])}
      />
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-signal-cyan/10 border border-signal-cyan/20 mb-3 group-hover:scale-105 transition-transform">
        {compact ? (
          <ImageIcon className="h-5 w-5 text-signal-cyan" strokeWidth={2} />
        ) : (
          <UploadCloud className="h-6 w-6 text-signal-cyan" strokeWidth={2} />
        )}
      </div>
      <p className="text-sm font-medium text-slate-200">
        {isDragging ? "Drop file to upload" : "+ Upload Sonar Data"}
      </p>
      <p className="text-xs text-slate-500 mt-1">Drag & drop, or click to browse</p>
      <p className="text-[11px] text-slate-600 mt-2 font-mono">PNG · JPG · TIFF · XTF · JSF</p>
    </div>
  );
}
