let map;

export async function initMap() {
  map = L.map('map', {
    center: [59.33, 18.07],   // Stockholm — recentred on first data load
    zoom: 12,
    zoomControl: false,
    preferCanvas: true,       // Canvas renderer — much faster for many paths
  });

  let tileUrl = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png';
  try {
    const cfg = await fetch('/api/config').then(r => r.json());
    if (cfg.stadia_api_key) tileUrl += `?api_key=${cfg.stadia_api_key}`;
  } catch (_) { /* fall through without key */ }

  L.tileLayer(tileUrl, {
    attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openstreetmap.org">OSM</a>',
    maxZoom: 20,
  }).addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  return map;
}

export function getMap() { return map; }

export function fitBoundsToPoints(allPoints) {
  if (!allPoints.length) return;
  const bounds = L.latLngBounds(allPoints.map(p => [p.lat, p.lon]));
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }
}
