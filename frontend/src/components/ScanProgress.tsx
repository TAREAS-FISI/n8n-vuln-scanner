"use client";

import type { Phase } from "@/lib/types";
import { PHASE_LABELS } from "@/lib/types";

interface ScanProgressProps {
  phases: Phase[];
  status: string;
}

function PhaseIcon({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/40">
        <svg className="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  if (status === "running") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40">
        <svg className="h-5 w-5 animate-spin text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/40">
        <svg className="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }
  if (status === "skipped") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
        <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      </div>
    );
  }
  // pending
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-300 dark:border-gray-600">
      <div className="h-2.5 w-2.5 rounded-full bg-gray-300 dark:bg-gray-600" />
    </div>
  );
}

export default function ScanProgress({ phases, status }: ScanProgressProps) {
  const completedCount = phases.filter((p) => p.status === "completed").length;
  const totalCount = phases.length;
  const progressPercent = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="w-full rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Progreso del Escaneo
        </h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {status === "completed"
            ? "Completado"
            : status === "failed"
            ? "Error"
            : `${completedCount}/${totalCount} fases`}
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-6 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-2 rounded-full bg-blue-600 transition-all duration-500 ease-out dark:bg-blue-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Phase list */}
      <div className="space-y-3">
        {phases.map((phase, i) => (
          <div key={phase.phase_name} className="flex items-center gap-3">
            <PhaseIcon status={phase.status} />

            {/* Connector line */}
            {i < phases.length - 1 && (
              <div className="absolute ml-[15px] mt-12 h-4 w-0.5 bg-gray-200 dark:bg-gray-700" />
            )}

            <div className="flex flex-1 items-center justify-between">
              <div>
                <span
                  className={`text-sm font-medium ${
                    phase.status === "running"
                      ? "text-blue-600 dark:text-blue-400"
                      : phase.status === "completed"
                      ? "text-gray-900 dark:text-white"
                      : "text-gray-500 dark:text-gray-400"
                  }`}
                >
                  {PHASE_LABELS[phase.phase_name] || phase.phase_name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {phase.findings_count > 0 && (
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                    {phase.findings_count} hallazgos
                  </span>
                )}
                {phase.status === "running" && (
                  <span className="text-xs text-blue-500 dark:text-blue-400">En progreso...</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
