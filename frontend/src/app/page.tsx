"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ScanForm from "@/components/ScanForm";
import SeverityBadge from "@/components/SeverityBadge";
import { listScans } from "@/lib/api";
import type { ScanSummary } from "@/lib/types";

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    running: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    pending: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
    failed: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[status] ?? styles.pending}`}>
      {status === "completed" ? "Completado" : status === "running" ? "En progreso" : status === "failed" ? "Error" : "Pendiente"}
    </span>
  );
}

function ScoreIndicator({ score }: { score: number | null }) {
  if (score === null) return <span className="text-sm text-gray-400">—</span>;

  let color = "text-red-600 dark:text-red-400";
  if (score >= 80) color = "text-green-600 dark:text-green-400";
  else if (score >= 50) color = "text-yellow-600 dark:text-yellow-400";
  else if (score >= 30) color = "text-orange-600 dark:text-orange-400";

  return <span className={`text-sm font-bold ${color}`}>{Math.round(score)}</span>;
}

export default function Home() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listScans()
      .then(setScans)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-10">
      {/* Hero / Scanner */}
      <section className="flex flex-col items-center gap-6 pt-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 dark:bg-blue-900/30">
          <svg className="h-8 w-8 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
            Escáner de Vulnerabilidades Web
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Ingresa una URL y obtén un reporte completo de seguridad con análisis de IA
          </p>
        </div>
        <ScanForm />
      </section>

      {/* Recent Scans */}
      <section>
        <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
          Escaneos Recientes
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <svg className="h-6 w-6 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : scans.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
            <svg className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
              No hay escaneos aún. Ingresa una URL arriba para comenzar.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                <tr>
                  <th className="px-4 py-3">URL</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3 text-center">Score</th>
                  <th className="px-4 py-3 text-center">Hallazgos</th>
                  <th className="px-4 py-3">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {scans.map((scan) => (
                  <tr
                    key={scan.scan_id}
                    className="bg-white transition-colors hover:bg-gray-50 dark:bg-gray-900 dark:hover:bg-gray-800/50"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/scan/${scan.scan_id}`}
                        className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                      >
                        {scan.target_url}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={scan.status} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <ScoreIndicator score={scan.global_score} />
                    </td>
                    <td className="px-4 py-3 text-center text-gray-600 dark:text-gray-400">
                      {scan.total_findings}
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                      {new Date(scan.created_at).toLocaleString("es-ES", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
