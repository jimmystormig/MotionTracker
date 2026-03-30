import { getMap } from './map.js';

let heatLayers = [];

export function renderHeatmap(data, deviceColorMap, selectedIds) {
  clearHeatmap();
  const map = getMap();

  Object.entries(data.devices).forEach(([devId, device]) => {
    if (selectedIds?.size && !selectedIds.has(devId)) return;
    const hex = deviceColorMap?.get(devId) || '#00f5ff';
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    const pts = [];
    device.segments.forEach(seg =>
      seg.points.forEach(p => pts.push([p.lat, p.lon, 0.5]))
    );
    if (!pts.length) return;

    const layer = L.heatLayer(pts, {
      radius: 22,
      blur: 18,
      maxZoom: 17,
      gradient: {
        0.0: `rgba(${r},${g},${b},0)`,
        0.3: `rgba(${r},${g},${b},0.08)`,
        0.6: `rgba(${r},${g},${b},0.18)`,
        1.0: `rgba(${r},${g},${b},0.30)`,
      },
    }).addTo(map);
    heatLayers.push(layer);
  });
}

export function setHeatmapVisible(visible) {
  const map = getMap();
  heatLayers.forEach(layer => {
    if (visible) { if (!map.hasLayer(layer)) layer.addTo(map); }
    else layer.remove();
  });
}

export function clearHeatmap() {
  heatLayers.forEach(l => l.remove());
  heatLayers = [];
}
