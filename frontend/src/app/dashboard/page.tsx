import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — VulnScanner",
  description: "Dashboard de seguridad con Grafana",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard de Seguridad
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Visualización de métricas y tendencias históricas de seguridad
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
        <iframe
          src="http://localhost:3001/d/security-overview/security-overview?orgId=1&theme=light&kiosk"
          title="Grafana Dashboard"
          className="h-[calc(100vh-200px)] w-full"
          style={{ minHeight: "600px" }}
        />
      </div>

      <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Si el dashboard no carga, accede directamente a Grafana.
        </p>
        <a
          href="http://localhost:3001"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          Abrir Grafana
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>
  );
}
