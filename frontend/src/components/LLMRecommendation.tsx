"use client";

import type { LLMAnalysis } from "@/lib/types";

interface LLMRecommendationProps {
  analysis: LLMAnalysis | null;
}

export default function LLMRecommendation({ analysis }: LLMRecommendationProps) {
  if (!analysis || !analysis.raw_response) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-6 dark:border-gray-600 dark:bg-gray-800/50">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 dark:bg-gray-700">
            <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              Análisis IA no disponible
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              El análisis con Ollama no se completó para este escaneo.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-purple-200 bg-linear-to-br from-purple-50 to-blue-50 p-6 dark:border-purple-800 dark:from-purple-900/20 dark:to-blue-900/20">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40">
          <svg className="h-5 w-5 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Análisis Inteligente
          </h3>
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            {analysis.model_used && <span>Modelo: {analysis.model_used}</span>}
            {analysis.duration_ms && (
              <>
                <span>&middot;</span>
                <span>{(analysis.duration_ms / 1000).toFixed(1)}s</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* LLM Response rendered as formatted text */}
      <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:rounded prose-code:bg-gray-100 prose-code:px-1 prose-code:text-sm dark:prose-headings:text-white dark:prose-p:text-gray-300 dark:prose-strong:text-white dark:prose-code:bg-gray-800">
        <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700 dark:text-gray-300">
          {analysis.raw_response}
        </div>
      </div>
    </div>
  );
}
