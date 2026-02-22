// ─── TypeScript interfaces for the Vuln Scanner ───

export type Severity = "Critical" | "High" | "Medium" | "Low" | "Info";

export interface Scan {
  scan_id: string;
  target_url: string;
  status: string;
  global_score: number | null;
  total_findings: number;
  created_at: string;
  completed_at: string | null;
}

export interface Finding {
  id: string;
  source: string;
  category: string;
  title: string;
  severity: Severity;
  cvss_score: number;
  description: string | null;
  remediation: string | null;
}

export interface Phase {
  phase_name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  findings_count: number;
}

export interface LLMAnalysis {
  raw_response: string | null;
  recommendations_json: unknown;
  model_used: string | null;
  duration_ms: number | null;
}

export interface ScanReport {
  scan_id: string;
  target_url: string;
  status: string;
  global_score: number | null;
  total_findings: number;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  findings: Finding[];
  phases: Phase[];
  llm_analysis: LLMAnalysis | null;
}

export interface ScanResponse {
  scan_id: string;
  status: string;
}

export interface ScanSummary {
  scan_id: string;
  target_url: string;
  status: string;
  global_score: number | null;
  total_findings: number;
  created_at: string;
}

// Severity helpers
export const SEVERITY_ORDER: Record<Severity, number> = {
  Critical: 0,
  High: 1,
  Medium: 2,
  Low: 3,
  Info: 4,
};

export const SEVERITY_COLORS: Record<Severity, { bg: string; text: string; border: string }> = {
  Critical: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-400", border: "border-red-300 dark:border-red-700" },
  High: { bg: "bg-orange-100 dark:bg-orange-900/30", text: "text-orange-700 dark:text-orange-400", border: "border-orange-300 dark:border-orange-700" },
  Medium: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-700 dark:text-yellow-400", border: "border-yellow-300 dark:border-yellow-700" },
  Low: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-400", border: "border-blue-300 dark:border-blue-700" },
  Info: { bg: "bg-gray-100 dark:bg-gray-800/50", text: "text-gray-600 dark:text-gray-400", border: "border-gray-300 dark:border-gray-600" },
};

export const PHASE_LABELS: Record<string, string> = {
  passive_checks: "Checks Pasivos",
  testssl: "testssl.sh (SSL/TLS)",
  nuclei: "Nuclei (CVEs)",
  zap: "OWASP ZAP (DAST)",
  scoring_llm: "Scoring + Análisis IA",
};

export const SOURCE_LABELS: Record<string, string> = {
  passive_headers: "Headers HTTP",
  passive_ssl: "SSL/TLS Básico",
  passive_ports: "Puertos Abiertos",
  passive_cookies: "Cookies",
  passive_cors: "CORS",
  passive_disclosure: "Info Disclosure",
  testssl: "testssl.sh",
  nuclei: "Nuclei",
  zap: "OWASP ZAP",
};
