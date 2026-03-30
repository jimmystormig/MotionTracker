import { deviceColor } from './colors.js';

let _fp = null;
let _onChangeCb = null;    // date range changed → re-fetch
let _onRenderCb = null;    // device/type/layer changed → re-render only

export function initControls(onDataChange, onRenderChange) {
  _onChangeCb = onDataChange;
  _onRenderCb = onRenderChange;

  // Panel collapse toggle
  const panel = document.getElementById('control-panel');
  document.getElementById('panel-toggle').addEventListener('click', () => {
    panel.classList.toggle('collapsed');
    document.getElementById('panel-toggle').textContent = panel.classList.contains('collapsed') ? '▶' : '◀';
  });

  // Quick date buttons — re-fetch data
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.quick-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const range = btn.dataset.range;
      const customRow = document.getElementById('custom-date-row');
      if (range === 'custom') {
        customRow.style.display = 'block';
      } else {
        customRow.style.display = 'none';
        onDataChange();
      }
    });
  });

  // Flatpickr date range — re-fetch data
  _fp = flatpickr('#date-picker', {
    mode: 'range',
    dateFormat: 'Y-m-d',
    theme: 'dark',
    onClose(selectedDates) {
      if (selectedDates.length === 2) onDataChange();
    },
  });

  // Movement type chips — re-render only
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('active');
      onRenderChange();
    });
  });

  // Device checkboxes — re-render only
  // (listeners added per-device in populateDeviceList)

  // Layer toggles — re-render only
  ['toggle-paths', 'toggle-heatmap', 'toggle-animation'].forEach(id => {
    document.getElementById(id).addEventListener('change', onRenderChange);
  });
}

export function getDateRange() {
  const active = document.querySelector('.quick-btn.active');
  const range = active?.dataset.range || 'today';
  const now = new Date();

  if (range === 'today') {
    const start = new Date(now); start.setHours(0, 0, 0, 0);
    const end   = new Date(now); end.setHours(23, 59, 59, 0);
    return { start: toISO(start), end: toISO(end) };
  }
  if (range === '7d') {
    const start = new Date(now); start.setDate(now.getDate() - 6); start.setHours(0, 0, 0, 0);
    const end   = new Date(now); end.setHours(23, 59, 59, 0);
    return { start: toISO(start), end: toISO(end) };
  }
  if (range === '30d') {
    const start = new Date(now); start.setDate(now.getDate() - 29); start.setHours(0, 0, 0, 0);
    const end   = new Date(now); end.setHours(23, 59, 59, 0);
    return { start: toISO(start), end: toISO(end) };
  }
  if (range === 'custom' && _fp?.selectedDates?.length === 2) {
    const [s, e] = _fp.selectedDates;
    s.setHours(0, 0, 0, 0); e.setHours(23, 59, 59, 0);
    return { start: toISO(s), end: toISO(e) };
  }
  // Default to today
  const start = new Date(now); start.setHours(0, 0, 0, 0);
  return { start: toISO(start), end: toISO(now) };
}

export function getVisibleMovementTypes() {
  const active = new Set();
  document.querySelectorAll('.chip.active').forEach(c => active.add(c.dataset.type));
  return active;
}

export function getLayerState() {
  return {
    paths:     document.getElementById('toggle-paths').checked,
    heatmap:   document.getElementById('toggle-heatmap').checked,
    animation: document.getElementById('toggle-animation').checked,
  };
}

export function populateDeviceList(devices) {
  const container = document.getElementById('device-list');
  container.innerHTML = '';
  devices.forEach((dev, idx) => {
    const color = deviceColor(idx);
    const label = document.createElement('label');
    label.className = 'device-checkbox';
    label.innerHTML = `
      <input type="checkbox" checked data-device-id="${dev.id}" />
      <span class="device-dot" style="background:${color};box-shadow:0 0 6px ${color}"></span>
      <span>${dev.friendly_name}</span>
    `;
    label.querySelector('input').addEventListener('change', _onRenderCb);
    container.appendChild(label);
  });
}

export function getSelectedDeviceIds() {
  return Array.from(document.querySelectorAll('.device-checkbox input:checked'))
    .map(el => el.dataset.deviceId);
}

export function updateStats(data, statsData) {
  document.getElementById('stat-points').textContent = (data?.total_points ?? 0).toLocaleString();
  document.getElementById('stat-devices').textContent = statsData?.total_devices ?? '—';
  document.getElementById('stat-storage').textContent = statsData?.storage_mb ?? '—';
}

function toISO(d) {
  return d.toISOString().replace('T', 'T').split('.')[0];
}
