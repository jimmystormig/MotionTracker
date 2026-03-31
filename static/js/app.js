import { initMap, fitBoundsToPoints } from './map.js';
import { renderTracks, clearTracks, setTracksVisible } from './tracks.js';
import { renderHeatmap, setHeatmapVisible, clearHeatmap } from './heatmap.js';
import { startAnimation, stopAnimation, setAnimationEnabled } from './animation.js';
import {
  initControls,
  getDateRange,
  getVisibleMovementTypes,
  getLayerState,
  populateDeviceList,
  getSelectedDeviceIds,
  updateStats,
} from './controls.js';
import { deviceColor } from './colors.js';

// ── State ─────────────────────────────────────────────────
let allDevices = [];
let deviceColorMap = new Map();   // deviceId (string) → hex color
let lastData = null;
let isLoading = false;
let hasFitBounds = false;
let _debounceTimer = null;

// ── Filter callbacks (declared before initControls call) ──
function onDateChange() {
  clearTimeout(_debounceTimer);
  _debounceTimer = setTimeout(loadTracks, 250);
}
function onRenderChange() {
  clearTimeout(_debounceTimer);
  _debounceTimer = setTimeout(applyRender, 50);
}

// ── Init ──────────────────────────────────────────────────
initControls(onDateChange, onRenderChange);

initMap().then(() => {
  loadDevices();
  loadStats();
  loadTracks();
});

// ── Load devices from API ─────────────────────────────────
async function loadDevices() {
  try {
    const res = await fetch('/api/devices');
    allDevices = await res.json();
    allDevices.forEach((dev, idx) => deviceColorMap.set(String(dev.id), deviceColor(idx)));
    populateDeviceList(allDevices);
  } catch (e) {
    console.error('Failed to load devices', e);
  }
}

// ── Load summary stats ────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();
    updateStats(lastData, stats);
  } catch (e) {
    console.error('Failed to load stats', e);
  }
}

// ── Load + render tracks ──────────────────────────────────
async function loadTracks() {
  if (isLoading) return;
  isLoading = true;
  setLoading(true);

  try {
    const { start, end } = getDateRange();
    const params = new URLSearchParams({ start, end });

    const res = await fetch(`/api/locations?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    lastData = await res.json();

    applyRender();
    updateStats(lastData, null);

    // Fit map to all points only on first load
    if (!hasFitBounds) {
      const allPoints = [];
      Object.values(lastData.devices).forEach(d =>
        d.segments.forEach(s => allPoints.push(...s.points))
      );
      if (allPoints.length) { fitBoundsToPoints(allPoints); hasFitBounds = true; }
    }

    loadStats();
  } catch (e) {
    console.error('Failed to load tracks', e);
  } finally {
    isLoading = false;
    setLoading(false);
  }
}

// ── Apply current render state ────────────────────────────
function applyRender() {
  if (!lastData) return;

  const layers = getLayerState();
  const visibleTypes = getVisibleMovementTypes();

  stopAnimation();
  clearTracks();
  clearHeatmap();

  const selectedIds = new Set(getSelectedDeviceIds());
  const segments = renderTracks(lastData, visibleTypes, deviceColorMap, selectedIds);
  setTracksVisible(layers.paths);

  if (layers.heatmap) {
    renderHeatmap(lastData, deviceColorMap, selectedIds);
    setHeatmapVisible(true);
  }

  setAnimationEnabled(layers.animation);
  if (layers.animation) {
    startAnimation(segments);
  }
}

// ── Loading overlay ───────────────────────────────────────
function setLoading(val) {
  const el = document.getElementById('loading-overlay');
  if (val) {
    el.classList.remove('hidden');
  } else {
    el.classList.add('hidden');
  }
}
