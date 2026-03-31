/**
 * Centripetal Catmull-Rom spline interpolation for GPS paths.
 * Alpha=0.5 prevents cusps and loops with unevenly-spaced points.
 */
export function catmullRomSmooth(latlngs, subdivisions = 6) {
  if (latlngs.length < 3) return latlngs;

  // Mirror endpoints to create virtual boundary control points
  const pts = [
    [2 * latlngs[0][0] - latlngs[1][0], 2 * latlngs[0][1] - latlngs[1][1]],
    ...latlngs,
    [2 * latlngs[latlngs.length - 1][0] - latlngs[latlngs.length - 2][0],
     2 * latlngs[latlngs.length - 1][1] - latlngs[latlngs.length - 2][1]],
  ];

  const result = [];

  for (let i = 1; i < pts.length - 2; i++) {
    const p0 = pts[i - 1], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2];

    // Centripetal parameterization (alpha = 0.5)
    const t0 = 0;
    const t1 = t0 + Math.sqrt(dist(p0, p1));
    const t2 = t1 + Math.sqrt(dist(p1, p2));
    const t3 = t2 + Math.sqrt(dist(p2, p3));

    // Always include the start point of each span
    if (i === 1) result.push(p1);

    for (let s = 1; s <= subdivisions; s++) {
      const t = t1 + (t2 - t1) * (s / subdivisions);

      const a1 = lerpPt(p0, p1, t0, t1, t);
      const a2 = lerpPt(p1, p2, t1, t2, t);
      const a3 = lerpPt(p2, p3, t2, t3, t);

      const b1 = lerpPt(a1, a2, t0, t2, t);
      const b2 = lerpPt(a2, a3, t1, t3, t);

      result.push(lerpPt(b1, b2, t0, t3, t));
    }
  }

  return result;
}

function dist(a, b) {
  const dlat = b[0] - a[0], dlon = b[1] - a[1];
  return dlat * dlat + dlon * dlon;
}

function lerpPt(a, b, t0, t1, t) {
  if (t1 === t0) return a;
  const f = (t - t0) / (t1 - t0);
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
}
