"""
posture_analyzer.py
Angle-based posture checks for Plank, Squat, and Bicep Curl.
Uses MediaPipe's 33-landmark skeleton (normalised x/y coords, origin = top-left).
"""

import numpy as np
# import mediapipe as mp

# PL = mp.solutions.pose.PoseLandmark

# Define landmark indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_EAR = 7
RIGHT_EAR = 8


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _coords(landmarks, landmark_index):
    lm = landmarks[landmark_index]
    return np.array([lm.x, lm.y])


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """
    Returns the angle (degrees) at vertex b formed by rays b→a and b→c.
    Works on 2-D (x, y) normalised coordinates.
    """
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _visibility_ok(landmarks, *landmark_indices, threshold=0.5) -> bool:
    return all(landmarks[li].visibility >= threshold for li in landmark_indices)


# ─────────────────────────────────────────────────────────────────────────────
# Plank
# ─────────────────────────────────────────────────────────────────────────────

def analyze_plank(landmarks) -> dict:
    """
    Key checks:
      1. Body alignment — shoulder / hip / ankle should be ~180°
      2. Head in neutral position — ear should align with shoulder
      3. Elbow directly under shoulder (x proximity)
    """
    required = [LEFT_SHOULDER, LEFT_HIP, LEFT_ANKLE,
                LEFT_EAR, LEFT_ELBOW]

    if not _visibility_ok(landmarks, *required):
        return {
            "is_correct": False,
            "issues": ["Make sure your full side profile is visible to the camera."],
            "feedback": "Reposition camera — need full side view.",
            "angles": {},
        }

    shoulder = _coords(landmarks, LEFT_SHOULDER)
    hip      = _coords(landmarks, LEFT_HIP)
    ankle    = _coords(landmarks, LEFT_ANKLE)
    ear      = _coords(landmarks, LEFT_EAR)
    elbow    = _coords(landmarks, LEFT_ELBOW)

    body_angle    = _angle(shoulder, hip, ankle)
    # Neck angle: ear–shoulder–hip
    neck_angle    = _angle(ear, shoulder, hip)

    issues = []

    # ── Body alignment ────────────────────────────────────────────────────────
    if body_angle < 160:
        if hip[1] < shoulder[1] - 0.05:   # y increases downward in normalised coords
            issues.append("🍑 Hips too high — lower them to form a straight line.")
        else:
            issues.append("⬇️ Hips sagging — engage your core and lift them.")

    # ── Head / neck alignment ─────────────────────────────────────────────────
    if neck_angle < 140:
        issues.append("👀 Head dropping — keep your neck neutral, eyes to the floor.")
    elif neck_angle > 185:
        issues.append("🔼 Head too high — tuck your chin slightly.")

    # ── Elbow under shoulder ─────────────────────────────────────────────────
    if abs(elbow[0] - shoulder[0]) > 0.08:
        issues.append("💪 Move your elbows directly under your shoulders.")

    is_correct = len(issues) == 0
    return {
        "is_correct": is_correct,
        "issues": issues,
        "feedback": "✅ Perfect plank form! Hold steady." if is_correct else issues[0],
        "angles": {
            "body_alignment": round(body_angle, 1),
            "neck": round(neck_angle, 1),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Squat
# ─────────────────────────────────────────────────────────────────────────────

def analyze_squat(landmarks) -> dict:
    """
    Key checks:
      1. Knee angle  — 90–120° at the bottom of a squat is ideal
      2. Back angle  — torso should stay upright (hip–shoulder angle relative to vertical)
      3. Knee cave   — knee width should be at least as wide as ankle width
      4. Knee forward — knee x should not go far past ankle x
    """
    required = [LEFT_HIP, LEFT_KNEE, LEFT_ANKLE,
                RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE,
                LEFT_SHOULDER]

    if not _visibility_ok(landmarks, *required):
        return {
            "is_correct": False,
            "issues": ["Full body not visible — step back from the camera."],
            "feedback": "Reposition so your full body is in frame.",
            "angles": {},
        }

    l_shoulder = _coords(landmarks, LEFT_SHOULDER)
    l_hip      = _coords(landmarks, LEFT_HIP)
    l_knee     = _coords(landmarks, LEFT_KNEE)
    l_ankle    = _coords(landmarks, LEFT_ANKLE)
    r_hip      = _coords(landmarks, RIGHT_HIP)
    r_knee     = _coords(landmarks, RIGHT_KNEE)
    r_ankle    = _coords(landmarks, RIGHT_ANKLE)

    knee_angle = _angle(l_hip, l_knee, l_ankle)
    back_angle = _angle(l_shoulder, l_hip, l_knee)   # torso lean

    issues = []

    # ── Squat depth ───────────────────────────────────────────────────────────
    # Only check depth if person has started squatting (hip below shoulder line)
    hip_dropped = l_hip[1] > l_shoulder[1] + 0.1     # normalised y: bigger = lower
    if hip_dropped and knee_angle > 120:
        issues.append("⬇️ Go deeper — aim for thighs parallel to the floor (90–110°).")

    # ── Back upright ──────────────────────────────────────────────────────────
    if back_angle < 55:
        issues.append("🔙 Leaning too far forward — keep your chest up.")

    # ── Knee over toes ────────────────────────────────────────────────────────
    knee_overshoot = l_knee[0] - l_ankle[0]           # positive = knee ahead of ankle
    if knee_overshoot > 0.12:
        issues.append("🦵 Knees going too far forward — push your hips back more.")

    # ── Knee cave ─────────────────────────────────────────────────────────────
    knee_width  = abs(l_knee[0] - r_knee[0])
    ankle_width = abs(l_ankle[0] - r_ankle[0])
    if ankle_width > 0.01 and knee_width < ankle_width * 0.75:
        issues.append("🔁 Knees caving in — push them out in line with your toes.")

    is_correct = len(issues) == 0
    return {
        "is_correct": is_correct,
        "issues": issues,
        "feedback": "✅ Great squat!" if is_correct else issues[0],
        "angles": {
            "knee": round(knee_angle, 1),
            "back_lean": round(back_angle, 1),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Bicep Curl
# ─────────────────────────────────────────────────────────────────────────────

def analyze_bicep_curl(landmarks) -> dict:
    """
    Key checks:
      1. Elbow angle — full ROM: 160°+ (down) → < 40° (up)
      2. Elbow swing — elbow x should stay near the torso
      3. Back swing  — shoulder should not rock back on the curl
    Stage tracking for rep counting: "down" → "up" → "down" = 1 rep
    """
    required = [LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST,
                RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST,
                LEFT_HIP]

    if not _visibility_ok(landmarks, *required, threshold=0.45):
        return {
            "is_correct": False,
            "issues": ["Upper body not visible — face the camera from the front."],
            "feedback": "Reposition so your arms are visible.",
            "angles": {},
            "stage": None,
        }

    l_shoulder = _coords(landmarks, LEFT_SHOULDER)
    l_elbow    = _coords(landmarks, LEFT_ELBOW)
    l_wrist    = _coords(landmarks, LEFT_WRIST)
    r_shoulder = _coords(landmarks, RIGHT_SHOULDER)
    r_elbow    = _coords(landmarks, RIGHT_ELBOW)
    r_wrist    = _coords(landmarks, RIGHT_WRIST)
    l_hip      = _coords(landmarks, LEFT_HIP)

    l_angle = _angle(l_shoulder, l_elbow, l_wrist)
    r_angle = _angle(r_shoulder, r_elbow, r_wrist)
    avg_angle = (l_angle + r_angle) / 2.0

    issues = []

    # ── Elbow body contact (swing check) ──────────────────────────────────────
    # Elbow x should stay close to shoulder x (within ~15% of frame width)
    for side, elbow, shoulder in [("left", l_elbow, l_shoulder),
                                  ("right", r_elbow, r_shoulder)]:
        if abs(elbow[0] - shoulder[0]) > 0.15:
            issues.append(f"💪 {side.capitalize()} elbow swinging — pin it to your side.")

    # ── Back sway ────────────────────────────────────────────────────────────
    torso_lean = _angle(l_shoulder, l_hip, np.array([l_hip[0], l_hip[1] + 0.1]))
    if torso_lean > 20:
        issues.append("🔙 Don't lean back — keep your torso upright.")

    # ── Stage for rep counting ────────────────────────────────────────────────
    if avg_angle > 155:
        stage = "down"
    elif avg_angle < 45:
        stage = "up"
    else:
        stage = "mid"

    # ── Range of motion hint (only when mid-curl) ─────────────────────────────
    if stage == "mid" and not issues:
        pass   # acceptable transition position

    is_correct = len(issues) == 0
    return {
        "is_correct": is_correct,
        "issues": issues,
        "feedback": "✅ Clean curl!" if is_correct else issues[0],
        "angles": {
            "left_elbow": round(l_angle, 1),
            "right_elbow": round(r_angle, 1),
        },
        "stage": stage,
    }
