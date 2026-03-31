import { getMap } from './map.js';

let particles = [];
let animFrameId = null;
let enabled = true;
const MAX_PARTICLES_PER_SEGMENT = 5;

// Speed (normalised t/ms) per movement type
const PARTICLE_SPEED = {
  stationary: 0,
  walking:    0.000012,
  running:    0.000025,
  cycling:    0.000045,
  driving:    0.0001,
  unknown:    0.000012,
};

// Emoji per movement type
const MOVEMENT_EMOJI = {
  stationary: '🏠',
  walking:    '🚶',
  running:    '🏃',
  cycling:    '🚴',
  driving:    '🚗',
  unknown:    '❓',
};

function makeIcon(movType, color) {
  const emoji = MOVEMENT_EMOJI[movType] || MOVEMENT_EMOJI.unknown;
  return L.divIcon({
    html: `<span style="font-size:13px;line-height:1;display:block;filter:drop-shadow(0 0 3px ${color}) drop-shadow(0 0 1px ${color});">${emoji}</span>`,
    className: '',
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function interpolateLatLng(latlngs, t) {
  if (latlngs.length < 2) return latlngs[0];
  const total = latlngs.length - 1;
  const pos = t * total;
  const i = Math.min(Math.floor(pos), total - 1);
  const frac = pos - i;
  const a = latlngs[i], b = latlngs[i + 1];
  return [
    a[0] + (b[0] - a[0]) * frac,
    a[1] + (b[1] - a[1]) * frac,
  ];
}

export function startAnimation(segments) {
  stopAnimation();
  if (!enabled || !segments.length) return;

  const map = getMap();

  segments.forEach(seg => {
    // Skip segments with no real geographic spread (GPS noise / truly stationary)
    const lats = seg.latlngs.map(p => p[0]);
    const lons = seg.latlngs.map(p => p[1]);
    const latSpanKm = (Math.max(...lats) - Math.min(...lats)) * 111;
    const lonSpanKm = (Math.max(...lons) - Math.min(...lons)) * 65;
    if (latSpanKm < 0.5 && lonSpanKm < 0.5) return;

    const spd = seg.movType === 'stationary'
      ? PARTICLE_SPEED.unknown
      : (PARTICLE_SPEED[seg.movType] || PARTICLE_SPEED.unknown);
    const color = seg.deviceColor || '#ffffff';
    const icon = makeIcon(seg.movType, color);
    const n = Math.min(MAX_PARTICLES_PER_SEGMENT, Math.max(1, Math.floor(seg.latlngs.length / 8)));

    for (let i = 0; i < n; i++) {
      const startT = i / n;
      const marker = L.marker(interpolateLatLng(seg.latlngs, startT), {
        icon,
        pane: 'markerPane',
        keyboard: false,
        interactive: false,
      }).addTo(map);

      particles.push({ marker, seg, t: startT, speed: spd });
    }
  });

  let last = performance.now();

  function tick(now) {
    const dt = now - last;
    last = now;

    particles.forEach(p => {
      p.t += p.speed * dt;
      if (p.t >= 1) p.t -= 1;
      p.marker.setLatLng(interpolateLatLng(p.seg.latlngs, p.t));
    });

    animFrameId = requestAnimationFrame(tick);
  }

  animFrameId = requestAnimationFrame(tick);
}

export function stopAnimation() {
  if (animFrameId) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }
  particles.forEach(p => p.marker.remove());
  particles = [];
}

export function setAnimationEnabled(val) {
  enabled = val;
  if (!val) stopAnimation();
}
