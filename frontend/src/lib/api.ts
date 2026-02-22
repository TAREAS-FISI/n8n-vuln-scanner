// ─── HTTP Client hacia FastAPI Backend ───

import type { ScanReport, ScanResponse, ScanSummary } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

/** Crear un nuevo escaneo */
export async function createScan(url: string): Promise<ScanResponse> {
  return request<ScanResponse>("/scan", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

/** Obtener reporte completo de un scan */
export async function getScan(scanId: string): Promise<ScanReport> {
  return request<ScanReport>(`/scan/${scanId}`);
}

/** Listar últimos 20 escaneos */
export async function listScans(): Promise<ScanSummary[]> {
  return request<ScanSummary[]>("/scans");
}
