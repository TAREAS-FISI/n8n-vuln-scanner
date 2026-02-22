"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { getScan } from "@/lib/api";
import type { ScanReport } from "@/lib/types";
import ScanProgress from "@/components/ScanProgress";
import ScoreGauge from "@/components/ScoreGauge";
import FindingsTable from "@/components/FindingsTable";
import LLMRecommendation from "@/components/LLMRecommendation";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ScanDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const [report, setReport] = useState<ScanReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReport = useCallback(async () => {
    try {
      const data = await getScan(id);
      setReport(data);
      return data.status;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar el escaneo");
      return "error";
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    fetchReport().then((status) => {
      // Poll every 3s if scan is still running
      if (status === "pending" || status === "running") {
        interval = setInterval(async () => {
          const newStatus = await fetchReport();
          if (newStatus === "completed" || newStatus === "failed" || newStatus === "error") {
            if (interval) clearInterval(interval);
          }
        }, 3000);
      }
    });

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchReport]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <svg className="h-8 w-8 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Cargando escaneo...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20">
          <svg className="mx-auto h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p className="mt-2 text-sm text-red-700 dark:text-red-400">{error ?? "Escaneo no encontrado"}</p>
          <Link href="/" className="mt-4 inline-block text-sm text-blue-600 hover:underline dark:text-blue-400">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const isRunning = report.status === "pending" || report.status === "running";
  const isCompleted = report.status === "completed";

  // Severity summary
  const severitySummary = report.findings.reduce(
    (acc, f) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link href="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
            &larr; Volver
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
            {report.target_url}
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Iniciado: {new Date(report.created_at).toLocaleString("es-ES")}
            {report.completed_at && (
              <> &middot; Completado: {new Date(report.completed_at).toLocaleString("es-ES")}</>
            )}
          </p>
        </div>

        {isCompleted && (
          <div className="relative shrink-0">
            <ScoreGauge score={report.global_score} />
          </div>
        )}
      </div>

      {/* Error message */}
      {report.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm text-red-700 dark:text-red-400">{report.error_message}</p>
        </div>
      )}

      {/* Progress */}
      {report.phases.length > 0 && (
        <ScanProgress phases={report.phases} status={report.status} />
      )}

      {/* Still running indicator */}
      {isRunning && (
        <div className="flex items-center justify-center gap-2 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
          <svg className="h-5 w-5 animate-spin text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
            Escaneo en progreso... actualizando automáticamente
          </span>
        </div>
      )}

      {/* Stats cards (show when there are findings) */}
      {report.findings.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
            <p className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">Total</p>
            <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{report.total_findings}</p>
          </div>
          <div className="rounded-xl border border-red-200 bg-white p-4 dark:border-red-800 dark:bg-gray-900">
            <p className="text-xs font-medium uppercase text-red-600 dark:text-red-400">Críticas</p>
            <p className="mt-1 text-2xl font-bold text-red-600 dark:text-red-400">{severitySummary["Critical"] ?? 0}</p>
          </div>
          <div className="rounded-xl border border-orange-200 bg-white p-4 dark:border-orange-800 dark:bg-gray-900">
            <p className="text-xs font-medium uppercase text-orange-600 dark:text-orange-400">Altas</p>
            <p className="mt-1 text-2xl font-bold text-orange-600 dark:text-orange-400">{severitySummary["High"] ?? 0}</p>
          </div>
          <div className="rounded-xl border border-yellow-200 bg-white p-4 dark:border-yellow-800 dark:bg-gray-900">
            <p className="text-xs font-medium uppercase text-yellow-600 dark:text-yellow-400">Medias</p>
            <p className="mt-1 text-2xl font-bold text-yellow-600 dark:text-yellow-400">{severitySummary["Medium"] ?? 0}</p>
          </div>
        </div>
      )}

      {/* LLM Recommendations */}
      {(isCompleted || report.llm_analysis) && (
        <section>
          <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
            Recomendaciones de IA
          </h2>
          <LLMRecommendation analysis={report.llm_analysis} />
        </section>
      )}

      {/* Findings */}
      {report.findings.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
            Hallazgos
          </h2>
          <FindingsTable findings={report.findings} />
        </section>
      )}
    </div>
  );
}
