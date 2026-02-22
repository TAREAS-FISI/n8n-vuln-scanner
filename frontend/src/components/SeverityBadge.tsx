"use client";

import { type Severity, SEVERITY_COLORS } from "@/lib/types";

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export default function SeverityBadge({ severity, className = "" }: SeverityBadgeProps) {
  const colors = SEVERITY_COLORS[severity] ?? SEVERITY_COLORS.Info;

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${colors.bg} ${colors.text} ${colors.border} ${className}`}
    >
      {severity}
    </span>
  );
}
