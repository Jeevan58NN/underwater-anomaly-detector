import type { Detection } from "../types";

const BAND_STYLE: Record<string, { border: string; text: string; bg: string }> = {
  High: { border: "border-sonar-green", text: "text-sonar-green", bg: "bg-sonar-green/15" },
  Medium: { border: "border-sonar-amber", text: "text-sonar-amber", bg: "bg-sonar-amber/15" },
  Low: { border: "border-sonar-coral border-dashed", text: "text-sonar-coral", bg: "bg-sonar-coral/15" },
};

export default function BoundingBoxOverlay({
  detections,
  imageWidth,
  imageHeight,
  activeId,
  onSelect,
}: {
  detections: Detection[];
  imageWidth: number;
  imageHeight: number;
  activeId?: string | null;
  onSelect?: (id: string) => void;
}) {
  return (
    <div className="absolute inset-0">
      {detections.map((d) => {
        const style = BAND_STYLE[d.confidence_band];
        const left = (d.bbox.x / imageWidth) * 100;
        const top = (d.bbox.y / imageHeight) * 100;
        const width = (d.bbox.width / imageWidth) * 100;
        const height = (d.bbox.height / imageHeight) * 100;
        const isActive = activeId === d.id;

        return (
          <button
            key={d.id}
            onClick={() => onSelect?.(d.id)}
            className={`absolute border-2 rounded-sm transition-all duration-200 ${style.border} ${
              isActive ? "ring-2 ring-white/70 z-10" : ""
            }`}
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: `${width}%`,
              height: `${height}%`,
            }}
            title={`${d.class_name} — ${Math.round(d.confidence * 100)}%`}
          >
            <span
              className={`absolute -top-6 left-0 whitespace-nowrap rounded px-1.5 py-0.5 text-[11px] font-mono font-medium ${style.bg} ${style.text}`}
            >
              {d.class_name} · {Math.round(d.confidence * 100)}%
            </span>
          </button>
        );
      })}
    </div>
  );
}
