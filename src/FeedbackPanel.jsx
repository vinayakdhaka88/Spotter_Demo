export default function FeedbackPanel({ feedback, exercise }) {
  if (!feedback) {
    return (
      <div className="feedback-panel">
        <div className="feedback-loading">
          <div className="spinner" />
          <p>Waiting for camera…</p>
        </div>
      </div>
    );
  }

  if (!feedback.detected) {
    return (
      <div className="feedback-panel">
        <div className="no-detect">
          <span className="no-detect-icon">👤</span>
          <p>{feedback.feedback}</p>
        </div>
      </div>
    );
  }

  const { is_correct, issues = [], angles = {}, feedback: mainFeedback } = feedback;

  return (
    <div className="feedback-panel">
      {/* Main feedback message */}
      <div className={`feedback-banner ${is_correct ? "correct" : "incorrect"}`}>
        <p>{mainFeedback}</p>
      </div>

      {/* Issues list */}
      {issues.length > 0 && (
        <div className="issues-section">
          <h4>Corrections needed:</h4>
          <ul className="issues-list">
            {issues.map((issue, i) => (
              <li key={i} className="issue-item">{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Angle readings */}
      {Object.keys(angles).length > 0 && (
        <div className="angles-section">
          <h4>Joint Angles</h4>
          <div className="angles-grid">
            {Object.entries(angles).map(([name, value]) => (
              <AngleCard key={name} name={name} value={value} exercise={exercise.id} />
            ))}
          </div>
        </div>
      )}

      {/* Exercise-specific tips */}
      <div className="tips-section">
        <h4>💡 Tips for {exercise.name}</h4>
        <ExerciseTips id={exercise.id} />
      </div>
    </div>
  );
}

function AngleCard({ name, value, exercise }) {
  const label = name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  // Ideal ranges per exercise / angle
  const ranges = {
    plank:       { body_alignment: [165, 180], neck: [140, 180] },
    squat:       { knee: [80, 120],  back_lean: [60, 100] },
    bicep_curl:  { left_elbow: [0, 180], right_elbow: [0, 180] },
  };

  const [min, max] = ranges[exercise]?.[name] ?? [0, 180];
  const inRange = value >= min && value <= max;

  return (
    <div className={`angle-card ${inRange ? "in-range" : "out-range"}`}>
      <span className="angle-value">{value}°</span>
      <span className="angle-label">{label}</span>
      <span className="angle-target">Target: {min}–{max}°</span>
    </div>
  );
}

function ExerciseTips({ id }) {
  const tips = {
    plank: [
      "Breathe steadily — don't hold your breath.",
      "Squeeze your glutes and core throughout.",
      "Stack wrists under shoulders.",
    ],
    squat: [
      "Drive through your heels on the way up.",
      "Keep your chest tall throughout the movement.",
      "Brace your core before descending.",
    ],
    bicep_curl: [
      "Full extension at the bottom, full contraction at the top.",
      "Control the descent — don't let gravity do the work.",
      "Both arms should curl symmetrically.",
    ],
  };

  return (
    <ul className="tips-list">
      {(tips[id] || []).map((t, i) => (
        <li key={i}>• {t}</li>
      ))}
    </ul>
  );
}
