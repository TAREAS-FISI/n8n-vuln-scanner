"use client";

interface ScoreGaugeProps {
  score: number | null;
  size?: number;
}

export default function ScoreGauge({ score, size = 160 }: ScoreGaugeProps) {
  const value = score ?? 0;
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (value / 100) * circumference;
  const center = size / 2;

  // Color based on score
  let strokeColor = "#ef4444"; // red
  let label = "Crítico";
  if (value >= 80) {
    strokeColor = "#22c55e"; // green
    label = "Bueno";
  } else if (value >= 50) {
    strokeColor = "#eab308"; // yellow
    label = "Regular";
  } else if (value >= 30) {
    strokeColor = "#f97316"; // orange
    label = "Bajo";
  }

  if (score === null) {
    return (
      <div className="flex flex-col items-center gap-2">
        <div
          className="flex items-center justify-center rounded-full border-4 border-gray-200 dark:border-gray-700"
          style={{ width: size, height: size }}
        >
          <span className="text-lg text-gray-400">—</span>
        </div>
        <span className="text-sm text-gray-500">Sin score</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      {/* Score number overlay */}
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: size, height: size }}
      >
        <span className="text-3xl font-bold" style={{ color: strokeColor }}>
          {Math.round(value)}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">/100</span>
      </div>
      <span className="text-sm font-medium" style={{ color: strokeColor }}>
        {label}
      </span>
    </div>
  );
}
