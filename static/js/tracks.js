import { COLORS } from './colors.js';
import { getMap } from './map.js';
import { catmullRomSmooth } from './spline.js';

let trackLayers = [];   // L.LayerGroup per segment pair
let trackGroup = null;
let tracksVisible = true;

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
      const smoothed = catmullRomSmooth(latlngs);

      const opts = { lineCap: 'round', lineJoin: 'round', smoothFactor: 1 };

      // Diffuse outer glow
      const outer = L.polyline(smoothed, { ...opts, color: deviceColor, weight: 12, opacity: tracksVisible ? 0.02 : 0 });
      outer._origOpacity = 0.02;
      // Mid halo
      const mid   = L.polyline(smoothed, { ...opts, color: deviceColor, weight: 4,  opacity: tracksVisible ? 0.07 : 0 });
      mid._origOpacity = 0.07;
      // Bright core
      const inner = L.polyline(smoothed, { ...opts, color: deviceColor, weight: 1.5, opacity: tracksVisible ? 0.28 : 0 });
      inner._origOpacity = 0.28;

      const group = L.layerGroup([outer, mid, inner]).addTo(trackGroup);
      trackLayers.push(group);

      allSegments.push({ points: seg.points, movType, col, latlngs: smoothed, deviceColor });
    });
  });

  return allSegments;
}

export function setTracksVisible(visible) {
  tracksVisible = visible;
  if (!trackGroup) return;
  trackGroup.eachLayer(segGroup => {
    segGroup.eachLayer(layer => {
      layer.setStyle({ opacity: visible ? (layer._origOpacity ?? 1) : 0 });
    });
  });
}
