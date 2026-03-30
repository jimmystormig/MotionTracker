import { COLORS } from './colors.js';
import { getMap } from './map.js';

let trackLayers = [];   // L.LayerGroup per segment pair
let trackGroup = null;

export function clearTracks() {
  trackLayers.forEach(g => g.remove());
  trackLayers = [];
}

export function renderTracks(data, visibleTypes, deviceColorMap, selectedIds) {
  const map = getMap();
  if (!trackGroup) {
    trackGroup = L.layerGroup().addTo(map);
  }
  clearTracks();

  const allSegments = [];   // returned for animation use

  Object.entries(data.devices).forEach(([devId, device]) => {
    if (selectedIds?.size && !selectedIds.has(devId)) return;
    const deviceColor = deviceColorMap?.get(devId) || '#aaaaaa';
    device.segments.forEach(seg => {
      if (!seg.points.length) return;
      // Use dominant movement type for segment color (first point may be unclassified)
      const typeCounts = {};
      seg.points.forEach(p => { typeCounts[p.movement_type] = (typeCounts[p.movement_type] || 0) + 1; });
      const movType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0][0];
      if (!visibleTypes.has(movType)) return;

      const latlngs = seg.points.map(p => [p.lat, p.lon]);
      if (latlngs.length < 2) return;
      const col = COLORS[movType] || COLORS.unknown;

      const opts = { lineCap: 'round', lineJoin: 'round', smoothFactor: 2 };

      // Diffuse outer glow
      const outer = L.polyline(latlngs, { ...opts, color: deviceColor, weight: 12, opacity: 0.02 });
      // Mid halo
      const mid   = L.polyline(latlngs, { ...opts, color: deviceColor, weight: 4,  opacity: 0.07 });
      // Bright core
      const inner = L.polyline(latlngs, { ...opts, color: deviceColor, weight: 1.5, opacity: 0.28 });

      const group = L.layerGroup([outer, mid, inner]).addTo(trackGroup);
      trackLayers.push(group);

      allSegments.push({ points: seg.points, movType, col, latlngs, deviceColor });
    });
  });

  return allSegments;
}

export function setTracksVisible(visible) {
  const map = getMap();
  if (!trackGroup) return;
  if (visible) {
    if (!map.hasLayer(trackGroup)) trackGroup.addTo(map);
  } else {
    trackGroup.remove();
  }
}
