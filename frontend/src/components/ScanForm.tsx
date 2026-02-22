"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createScan } from "@/lib/api";

export default function ScanForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError("Ingresa una URL");
      return;
    }

    // Basic URL validation
    try {
      new URL(trimmed);
    } catch {
      setError("URL inválida. Debe incluir http:// o https://");
      return;
    }

    setLoading(true);
    try {
      const result = await createScan(trimmed);
      router.push(`/scan/${result.scan_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar escaneo");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl">
      <div className="flex flex-col gap-3">
        <label htmlFor="url" className="text-sm font-medium text-gray-700 dark:text-gray-300">
          URL del sitio web a escanear
        </label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
            </div>
            <input
              id="url"
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://dvwa:8081"
              disabled={loading}
              className="block w-full rounded-lg border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500 dark:focus:border-blue-400"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            {loading ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Escaneando...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Escanear
              </>
            )}
          </button>
        </div>
        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
      </div>
    </form>
  );
}
