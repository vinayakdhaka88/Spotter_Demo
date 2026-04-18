from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import mediapipe as mp
import cv2
import numpy as np
import base64
import json
from posture_analyzer import analyze_plank, analyze_squat, analyze_bicep_curl

app = FastAPI(title="Posture Correction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.tasks.vision.PoseLandmarker

options = mp.tasks.vision.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path='pose_landmarker.task'),
    running_mode=mp.tasks.vision.RunningMode.IMAGE
)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Posture Correction API is running"}


@app.get("/exercises")
def get_exercises():
    return {
        "exercises": [
            {"id": "plank", "name": "Plank", "description": "Core stability hold"},
            {"id": "squat", "name": "Squat", "description": "Lower body compound movement"},
            {"id": "bicep_curl", "name": "Bicep Curl", "description": "Arm isolation exercise"},
        ]
    }


@app.websocket("/ws/analyze")
async def analyze_pose(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    rep_count = 0
    prev_stage = None

    print("Creating pose landmarker")
    with mp_pose.create_from_options(options) as pose:
        print("Pose landmarker created successfully")
        try:
            while True:
                raw = await websocket.receive_text()
                print(f"Received message: {len(raw)} chars")
                payload = json.loads(raw)

                exercise = payload.get("exercise", "squat")
                frame_data = payload.get("frame", "")

                if not frame_data:
                    print("No frame data")
                    continue

                print("Processing frame")
                # ── Decode base64 frame ──────────────────────────────────────
                try:
                    header, encoded = frame_data.split(",", 1)
                    img_bytes = base64.b64decode(encoded)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                except Exception as e:
                    print(f"Error decoding frame: {e}")
                    continue

                if frame is None:
                    print("Frame is None")
                    continue

                # ── MediaPipe inference ──────────────────────────────────────
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                results = pose.detect(mp_image)
                print(f"Detection results: {len(results.pose_landmarks) if results.pose_landmarks else 0} landmarks")

                if not results.pose_landmarks:
                    print("No pose landmarks detected")
                    await websocket.send_json(
                        {
                            "detected": False,
                            "feedback": "No person detected — step back so your full body is visible.",
                            "is_correct": False,
                            "issues": [],
                            "landmarks": [],
                            "rep_count": rep_count,
                        }
                    )
                    continue

                landmarks = results.pose_landmarks[0] if results.pose_landmarks else []

                print(f"Landmarks count: {len(landmarks)}")
                if landmarks:
                    print(f"Type of landmarks[0]: {type(landmarks[0])}, value: {landmarks[0]}")

                # ── Posture analysis ─────────────────────────────────────────
                try:
                    if exercise == "plank":
                        analysis = analyze_plank(landmarks)
                    elif exercise == "squat":
                        analysis = analyze_squat(landmarks)
                    elif exercise == "bicep_curl":
                        analysis = analyze_bicep_curl(landmarks)
                    else:
                        analysis = {
                            "feedback": "Unknown exercise type.",
                            "is_correct": False,
                            "issues": [],
                        }
                except Exception as e:
                    print(f"Error in analysis: {e}")
                    analysis = {
                        "feedback": f"Analysis error: {e}",
                        "is_correct": False,
                        "issues": [],
                    }

                # ── Rep counting via stage transitions ──────────────────────
                stage = analysis.get("stage")
                if prev_stage == "down" and stage == "up":
                    rep_count += 1
                prev_stage = stage
                analysis["rep_count"] = rep_count

                print(f"Sending analysis: {analysis['feedback']}")
                # ── Serialize landmarks ──────────────────────────────────────
                lm_list = [
                    {
                        "x": round(lm.x, 4),
                        "y": round(lm.y, 4),
                        "z": round(lm.z, 4),
                        "visibility": round(lm.visibility, 3),
                    }
                    for lm in landmarks
                ]

                await websocket.send_json(
                    {"detected": True, **analysis, "landmarks": lm_list, "rep_count": rep_count}
                )

        except WebSocketDisconnect:
            print("WebSocket disconnected")
            pass
        except Exception as e:
            print(f"Error in WS: {e}")
            try:
                await websocket.send_json({"error": str(e)})
            except Exception:
                pass
