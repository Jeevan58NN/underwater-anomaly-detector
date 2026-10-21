import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { PageHeader } from "../components/PageHeader";
import { useAppData } from "../hooks/AppDataContext";
import type { Severity } from "../types";

const SEVERITY_COLOR: Record<Severity, string> = {
  High: "#f97066",
  Medium: "#f5b942",
  Low: "#4ade80",
};

// Helper component to handle dynamic map centering updates
function RecenterMap({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center);
  }, [center, map]);
  return null;
}

export default function MapView() {
  const { detections } = useAppData();

  // Validate coordinates: must be in WGS84 ranges and not null
  const validDetections = detections.filter(
    (d) =>
      d.latitude !== null &&
      d.longitude !== null &&
      d.latitude >= -90.0 &&
      d.latitude <= 90.0 &&
      d.longitude >= -180.0 &&
      d.longitude <= 180.0
  );

  // Center on first detection, or default to open ocean if none exist
  const center: [number, number] =
    validDetections.length > 0
      ? [validDetections[0].latitude as number, validDetections[0].longitude as number]
      : [20.0, -150.0];

  return (
    <div>
      <PageHeader title="Detection Map" subtitle="Geospatial view of anomaly locations" />

      <div className="mb-4 rounded-lg border border-sonar-amber/30 bg-sonar-amber/10 px-4 py-2.5 text-xs font-mono text-sonar-amber">
        ⚠ Note: Only geotagged or estimated locations are plotted. Ungeotagged images will not appear here.
      </div>

      <div className="rounded-xl border border-abyss-700/60 overflow-hidden" style={{ height: "560px" }}>
        <MapContainer center={center} zoom={4} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <RecenterMap center={center} />
          {validDetections.map((d) => (
            <CircleMarker
              key={d.id}
              center={[d.latitude as number, d.longitude as number]}
              radius={10}
              pathOptions={{
                color: SEVERITY_COLOR[d.severity],
                fillColor: SEVERITY_COLOR[d.severity],
                fillOpacity: 0.55,
                weight: 2,
              }}
            >
              <Popup>
                <div className="font-mono text-xs space-y-1">
                  <p className="font-display text-sm font-semibold mb-1 text-slate-100">{d.class_name}</p>
                  <p>Confidence: {Math.round(d.confidence * 100)}%</p>
                  <p>Latitude: {(d.latitude as number).toFixed(6)}</p>
                  <p>Longitude: {(d.longitude as number).toFixed(6)}</p>
                  <p>Severity: {d.severity}</p>
                  <p className="pt-1 text-slate-500">Detection ID: {d.id}</p>
                  <p className="pt-1 text-slate-500">
                    Status: {d.location_status === "estimated" ? "Estimated Location" : d.location_status}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div className="flex items-center gap-5 mt-4 text-xs font-mono text-slate-400">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-sonar-coral" /> High Risk
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-sonar-amber" /> Medium Risk
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-sonar-green" /> Low Risk
        </span>
      </div>
    </div>
  );
}
