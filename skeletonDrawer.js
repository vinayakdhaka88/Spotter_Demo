/**
 * skeletonDrawer.js
 * Draws the MediaPipe 33-landmark skeleton onto a canvas.
 * Landmark indices: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
 */

// ── Connections (pairs of landmark indices) ──────────────────────────────────
const POSE_CONNECTIONS = [
  // Face
  [0, 1], [1, 2], [2, 3], [3, 7],
  [0, 4], [4, 5], [5, 6], [6, 8],
  // Torso
  [11, 12], [11, 23], [12, 24], [23, 24],
  // Left arm
  [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], [17, 19],
  // Right arm
  [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], [18, 20],
  // Left leg
  [23, 25], [25, 27], [27, 29], [27, 31], [29, 31],
  // Right leg
  [24, 26], [26, 28], [28, 30], [28, 32], [30, 32],
];

// Key landmark indices to draw as dots (skip face micro-landmarks)
const KEY_LANDMARKS = [
  11, 12,       // shoulders
  13, 14,       // elbows
  15, 16,       // wrists
  23, 24,       // hips
  25, 26,       // knees
  27, 28,       // ankles
];

/**
 * @param {CanvasRenderingContext2D} ctx
 * @param {Array<{x, y, visibility}>} landmarks  - normalised 0-1 coords
 * @param {number} width   - canvas pixel width
 * @param {number} height  - canvas pixel height
 * @param {boolean} isCorrect - controls colour scheme
 */
export function drawSkeleton(ctx, landmarks, width, height, isCorrect) {
  if (!landmarks || landmarks.length < 33) return;

  const goodColor = "#22c55e";   // green
  const badColor  = "#ef4444";   // red
  const lineColor = isCorrect ? goodColor : badColor;
  const dotColor  = "#ffffff";

  const px = (lm) => ({
    x: lm.x * width,
    y: lm.y * height,
  });

  // ── Draw connections ─────────────────────────────────────────────────────
  ctx.lineWidth   = 3;
  ctx.strokeStyle = lineColor;
  ctx.shadowColor = lineColor;
  ctx.shadowBlur  = 8;

  for (const [i, j] of POSE_CONNECTIONS) {
    const a = landmarks[i];
    const b = landmarks[j];
    if (!a || !b) continue;
    if (a.visibility < 0.3 || b.visibility < 0.3) continue;

    const pa = px(a);
    const pb = px(b);
    ctx.beginPath();
    ctx.moveTo(pa.x, pa.y);
    ctx.lineTo(pb.x, pb.y);
    ctx.stroke();
  }

  ctx.shadowBlur = 0;

  // ── Draw key joint dots ──────────────────────────────────────────────────
  for (const idx of KEY_LANDMARKS) {
    const lm = landmarks[idx];
    if (!lm || lm.visibility < 0.4) continue;
    const { x, y } = px(lm);

    // Outer ring (colour coded)
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, 2 * Math.PI);
    ctx.fillStyle = lineColor;
    ctx.fill();

    // White centre dot
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fillStyle = dotColor;
    ctx.fill();
  }
}
