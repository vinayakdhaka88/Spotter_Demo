import { useState } from "react";
import PostureChecker from "./PostureChecker";
import ExerciseSelector from "./ExerciseSelector";
import "./App.css";

export default function App() {
  const [selectedExercise, setSelectedExercise] = useState(null);

  return (
    <div className="app">
      {!selectedExercise ? (
        <ExerciseSelector onSelect={setSelectedExercise} />
      ) : (
        <PostureChecker
          exercise={selectedExercise}
          onBack={() => setSelectedExercise(null)}
        />
      )}
    </div>
  );
}
