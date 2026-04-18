# 🤸 Spotter — Real-time Exercise Form Correction

Computer vision posture checker for **Plank**, **Squat**, and **Bicep Curl**
using **MediaPipe Pose** + **FastAPI** + **React**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React (Vite)                                               │
│  ┌─────────────┐   base64 frame    ┌──────────────────────┐│
│  │  Webcam     │──── WebSocket ───▶│   FastAPI            ││
│  │  Canvas     │◀── landmarks ─────│   /ws/analyze        ││
│  │  FeedbackUI │    + feedback      │                      ││
│  └─────────────┘                   │  MediaPipe Pose      ││
│                                    │  (33-landmark model) ││
│                                    │                      ││
│                                    │  posture_analyzer.py ││
│                                    │  angle calculations  ││
│                                    └──────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**No model training needed.** MediaPipe Pose is a pre-trained Google model
that runs inference in ~10ms per frame.

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## How It Works

### MediaPipe Pose
- Pre-trained Google model, no GPU required
- Detects **33 body landmarks** (x, y, z + visibility) per frame
- Runs at ~25–30 FPS on CPU

### Posture Analysis (angle-based)

| Exercise    | Key Angles Measured                    | What's Checked                          |
|-------------|----------------------------------------|-----------------------------------------|
| Plank       | Body alignment (shoulder→hip→ankle)    | Hip height, body line, neck position    |
| Squat       | Knee angle, torso lean                 | Depth, back angle, knee cave, overshoot |
| Bicep Curl  | Elbow angle (both arms)               | Elbow swing, back sway, rep stage       |

### Rep Counting (Bicep Curl)
Stage machine: `down (>155°) → up (<45°) → down` = **1 rep**

---

## Project Structure

```
posture-app/
├── backend/
│   ├── main.py              ← FastAPI + WebSocket server
│   ├── posture_analyzer.py  ← All exercise analysis logic
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   ├── components/
    │   │   ├── ExerciseSelector.jsx
    │   │   ├── PostureChecker.jsx   ← Webcam + WebSocket + Canvas
    │   │   └── FeedbackPanel.jsx
    │   └── utils/
    │       └── skeletonDrawer.js    ← Canvas skeleton overlay
    ├── package.json
    └── vite.config.js
```

---

## Extending the App

### Add a new exercise
1. Add analysis function to `posture_analyzer.py`
2. Add `elif exercise == "your_exercise":` in `main.py`
3. Add to `EXERCISES` array in `ExerciseSelector.jsx`
4. Add tips in `FeedbackPanel.jsx`

### Improve accuracy
- Increase `model_complexity` to `2` in `main.py` (slower but more accurate)
- Add smoothing: average landmark positions over last N frames
- Add confidence thresholds per landmark

---

## Environment Variables

Create `frontend/.env` to customise the WebSocket URL:
```
VITE_WS_URL=ws://your-backend-host:8000/ws/analyze
```

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| CV Model  | MediaPipe Pose (Google, pre-trained) |
| Backend   | FastAPI + Uvicorn                 |
| CV Lib    | OpenCV (headless)                 |
| Frontend  | React 18 + Vite                   |
| Transport | WebSocket (binary-safe JSON)      |
