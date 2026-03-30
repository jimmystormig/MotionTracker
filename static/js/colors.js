export const COLORS = {
  stationary: { core: '#444a55', glow: '#2a2e38', particle: '#666' },
  walking:    { core: '#00f5ff', glow: 'rgba(0,245,255,0.25)', particle: '#80faff' },
  running:    { core: '#39ff14', glow: 'rgba(57,255,20,0.25)',  particle: '#a0ff80' },
  cycling:    { core: '#ff00e5', glow: 'rgba(255,0,229,0.25)', particle: '#ff80f4' },
  driving:    { core: '#ffe600', glow: 'rgba(255,230,0,0.25)', particle: '#ffee66' },
  unknown:    { core: '#555566', glow: 'rgba(80,80,100,0.2)',  particle: '#777788' },
};

// Distinct palette for per-device coloring (used for device dots in legend)
export const DEVICE_PALETTE = [
  '#00f5ff', '#ff00e5', '#ffe600', '#39ff14', '#ff6b00', '#a855f7',
];

export function deviceColor(index) {
  return DEVICE_PALETTE[index % DEVICE_PALETTE.length];
}
