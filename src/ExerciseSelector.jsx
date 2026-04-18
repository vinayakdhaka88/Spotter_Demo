const EXERCISES = [
  {
    id: "plank",
    name: "Plank",
    icon: "🏋️",
    description: "Core stability hold — full side view recommended",
    tips: ["Side profile to camera", "Wrists or forearms on ground", "Hold for time"],
  },
  {
    id: "squat",
    name: "Squat",
    icon: "🦵",
    description: "Lower body compound movement — front or side view",
    tips: ["Full body in frame", "Feet shoulder-width apart", "Arms forward for balance"],
  },
  {
    id: "bicep_curl",
    name: "Bicep Curl",
    icon: "💪",
    description: "Arm isolation — face the camera front-on",
    tips: ["Face the camera", "Hold dumbbells or mimic the motion", "Keep elbows tucked"],
  },
];

export default function ExerciseSelector({ onSelect }) {
  return (
    <div className="selector-screen">
      <div className="selector-header">
        <h1>🤸 Spotter</h1>
        <p>Real-time exercise form correction powered by computer vision</p>
      </div>

      <div className="exercise-grid">
        {EXERCISES.map((ex) => (
          <button
            key={ex.id}
            className="exercise-card"
            onClick={() => onSelect(ex)}
          >
            <span className="exercise-icon">{ex.icon}</span>
            <h2>{ex.name}</h2>
            <p className="exercise-desc">{ex.description}</p>
            <ul className="exercise-tips">
              {ex.tips.map((tip, i) => (
                <li key={i}>• {tip}</li>
              ))}
            </ul>
            <span className="start-btn">Start →</span>
          </button>
        ))}
      </div>

      <p className="disclaimer">
        📷 Camera access required &nbsp;|&nbsp; Works best in good lighting
      </p>
    </div>
  );
}
