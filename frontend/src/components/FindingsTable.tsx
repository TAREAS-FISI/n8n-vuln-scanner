"use client";

import { useMemo, useState } from "react";
import type { Finding, Severity } from "@/lib/types";
import { SEVERITY_ORDER } from "@/lib/types";
import ReportCard from "./ReportCard";
import SeverityBadge from "./SeverityBadge";

interface FindingsTableProps {
  findings: Finding[];
}

const ALL_SEVERITIES: Severity[] = ["Critical", "High", "Medium", "Low", "Info"];

export default function FindingsTable({ findings }: FindingsTableProps) {
  const [filterSeverity, setFilterSeverity] = useState<Severity | "all">("all");
  const [filterSource, setFilterSource] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"cards" | "table">("cards");

  // Unique sources
  const sources = useMemo(
    () => Array.from(new Set(findings.map((f) => f.source))).sort(),
    [findings]
  );

  // Severity counts
  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const sev of ALL_SEVERITIES) {
      counts[sev] = findings.filter((f) => f.severity === sev).length;
    }
    return counts;
  }, [findings]);

  // Filtered findings
  const filtered = useMemo(() => {
    return findings
      .filter((f) => filterSeverity === "all" || f.severity === filterSeverity)
      .filter((f) => filterSource === "all" || f.source === filterSource)
      .sort((a, b) => {
        const sevDiff = (SEVERITY_ORDER[a.severity] ?? 5) - (SEVERITY_ORDER[b.severity] ?? 5);
        if (sevDiff !== 0) return sevDiff;
        return b.cvss_score - a.cvss_score;
      });
  }, [findings, filterSeverity, filterSource]);

  return (
    <div className="space-y-4">
      {/* Summary badges */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {findings.length} hallazgos:
        </span>
        {ALL_SEVERITIES.map((sev) =>
          severityCounts[sev] > 0 ? (
            <button
              key={sev}
              onClick={() =>
                setFilterSeverity(filterSeverity === sev ? "all" : sev)
              }
              className={`transition-opacity ${
                filterSeverity !== "all" && filterSeverity !== sev
                  ? "opacity-40"
                  : ""
              }`}
            >
              <SeverityBadge severity={sev} />
              <span className="ml-1 text-xs text-gray-500">{severityCounts[sev]}</span>
            </button>
          ) : null
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
        >
          <option value="all">Todas las fuentes</option>
          {sources.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <div className="ml-auto flex items-center gap-1 rounded-lg border border-gray-300 p-0.5 dark:border-gray-600">
          <button
            onClick={() => setViewMode("cards")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              viewMode === "cards"
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            Tarjetas
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              viewMode === "table"
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            Tabla
          </button>
        </div>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center dark:border-gray-600">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No se encontraron hallazgos con los filtros seleccionados.
          </p>
        </div>
      ) : viewMode === "cards" ? (
        <div className="space-y-2">
          {filtered.map((f) => (
            <ReportCard key={f.id} finding={f} />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-600 dark:bg-gray-800 dark:text-gray-400">
              <tr>
                <th className="px-4 py-3">Severidad</th>
                <th className="px-4 py-3">Título</th>
                <th className="px-4 py-3">Fuente</th>
                <th className="px-4 py-3">Categoría</th>
                <th className="px-4 py-3">CVSS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filtered.map((f) => (
                <tr
                  key={f.id}
                  className="bg-white hover:bg-gray-50 dark:bg-gray-900 dark:hover:bg-gray-800/50"
                >
                  <td className="px-4 py-3">
                    <SeverityBadge severity={f.severity} />
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                    {f.title}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {f.source}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {f.category}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">
                    {f.cvss_score > 0 ? f.cvss_score.toFixed(1) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
