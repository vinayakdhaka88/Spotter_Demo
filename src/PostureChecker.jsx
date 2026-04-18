import { useEffect, useRef, useState, useCallback } from "react";
import FeedbackPanel from "./FeedbackPanel";
import { drawSkeleton } from "../skeletonDrawer";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8001/ws/analyze";
const SEND_INTERVAL_MS = 100; // ~10 fps to backend

export default function PostureChecker({ exercise, onBack }) {
  const videoRef   = useRef(null);
  const canvasRef  = useRef(null);
  const wsRef      = useRef(null);
  const intervalRef = useRef(null);
  const streamRef  = useRef(null);

  const [feedback, setFeedback]     = useState(null);
  const [wsStatus, setWsStatus]     = useState("connecting"); // connecting | open | closed
  const [repCount, setRepCount]     = useState(0);
  const [sessionTime, setSessionTime] = useState(0);

  // ── Timer ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const t = setInterval(() => setSessionTime((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const formatTime = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  // ── WebSocket ─────────────────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen  = () => setWsStatus("open");
    ws.onclose = () => { setWsStatus("closed"); setTimeout(connectWS, 2000); };
    ws.onerror = () => ws.close();

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setFeedback(data);
        if (data.rep_count !== undefined) setRepCount(data.rep_count);

        // Draw skeleton on canvas
        const canvas = canvasRef.current;
        const video  = videoRef.current;
        if (canvas && video && data.landmarks?.length) {
          const ctx = canvas.getContext("2d");
          canvas.width  = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          drawSkeleton(ctx, data.landmarks, canvas.width, canvas.height, data.is_correct);
        }
      } catch (_) {}
    };
  }, []);

  // ── Camera ────────────────────────────────────────────────────────────────
  useEffect(() => {
    let active = true;

    navigator.mediaDevices
      .getUserMedia({ video: { width: 1280, height: 720, facingMode: "user" }, audio: false })
      .then((stream) => {
        if (!active) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      })
      .catch((err) => console.error("Camera error:", err));

    connectWS();

    return () => {
      active = false;
      clearInterval(intervalRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      wsRef.current?.close();
    };
  }, [connectWS]);

  // ── Frame sender ──────────────────────────────────────────────────────────
  useEffect(() => {
    const offscreen = document.createElement("canvas");

    intervalRef.current = setInterval(() => {
      const video = videoRef.current;
      const ws    = wsRef.current;
      if (!video || !ws || ws.readyState !== WebSocket.OPEN || video.readyState < 2) return;

      offscreen.width  = 640;   // downscale for speed
      offscreen.height = 360;
      const ctx = offscreen.getContext("2d");
      ctx.drawImage(video, 0, 0, offscreen.width, offscreen.height);

      const frame = offscreen.toDataURL("image/jpeg", 0.6);
      ws.send(JSON.stringify({ exercise: exercise.id, frame }));
    }, SEND_INTERVAL_MS);

    return () => clearInterval(intervalRef.current);
  }, [exercise]);

  // ─────────────────────────────────────────────────────────────────────────

  const statusColor = wsStatus === "open" ? "#22c55e" : wsStatus === "connecting" ? "#f59e0b" : "#ef4444";
  const statusLabel = { connecting: "Connecting…", open: "Live", closed: "Reconnecting…" }[wsStatus];

  return (
    <div className="checker-screen">
      {/* ── Top bar ── */}
      <div className="top-bar">
        <button className="back-btn" onClick={onBack}>← Back</button>
        <h2>{exercise.icon} {exercise.name}</h2>
        <div className="status-row">
          <span className="status-dot" style={{ background: statusColor }} />
          <span style={{ color: statusColor, fontSize: 13 }}>{statusLabel}</span>
          <span className="session-timer">⏱ {formatTime(sessionTime)}</span>
        </div>
      </div>

      {/* ── Main layout ── */}
      <div className="main-layout">
        {/* Camera + skeleton canvas */}
        <div className="video-wrapper">
          <video ref={videoRef} className="video-feed" muted playsInline />
          <canvas ref={canvasRef} className="skeleton-canvas" />

          {/* Rep counter badge (bicep curl only) */}
          {exercise.id === "bicep_curl" && (
            <div className="rep-badge">
              <span className="rep-label">REPS</span>
              <span className="rep-number">{repCount}</span>
            </div>
          )}

          {/* Form status pill */}
          {feedback?.detected && (
            <div className={`form-pill ${feedback.is_correct ? "good" : "bad"}`}>
              {feedback.is_correct ? "✅ Good Form" : "⚠️ Fix Form"}
            </div>
          )}
        </div>

        {/* Feedback panel */}
        <FeedbackPanel feedback={feedback} exercise={exercise} />
      </div>
    </div>
  );
}
