"use client";

import { useState } from "react";
import type { Finding } from "@/lib/types";
import { SOURCE_LABELS } from "@/lib/types";
import SeverityBadge from "./SeverityBadge";

interface ReportCardProps {
  finding: Finding;
}

export default function ReportCard({ finding }: ReportCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-gray-200 bg-white transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-900">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-3">
          <SeverityBadge severity={finding.severity} />
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
              {finding.title}
            </h4>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span>{SOURCE_LABELS[finding.source] || finding.source}</span>
              <span>&middot;</span>
              <span>{finding.category}</span>
              {finding.cvss_score > 0 && (
                <>
                  <span>&middot;</span>
                  <span className="font-mono">CVSS {finding.cvss_score.toFixed(1)}</span>
                </>
              )}
            </div>
          </div>
        </div>
        <svg
          className={`h-5 w-5 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-gray-200 p-4 dark:border-gray-700">
          {finding.description && (
            <div className="mb-3">
              <h5 className="mb-1 text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">
                Descripción
              </h5>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {finding.description}
              </p>
            </div>
          )}
          {finding.remediation && (
            <div>
              <h5 className="mb-1 text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">
                Remediación
              </h5>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {finding.remediation}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
