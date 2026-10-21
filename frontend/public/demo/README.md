# Demo Images

Demo Mode in this prototype does not require static image files — it
generates a placeholder sonar-style image on the fly (see
`src/services/demoData.ts::generatePlaceholderSonarImage`) and pairs it
with deterministic mock detections.

If you'd like to use real sample side-scan sonar images instead, drop
1–3 PNG/JPG files in this folder and reference them from
`src/services/demoData.ts`.
