import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vulnerability Scanner",
  description: "Scanner de vulnerabilidades web inteligente",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 bg-gray-900">
          <div className="mx-auto max-w-7xl px-4 py-3 flex items-center gap-3">
            <span className="text-xl">🛡️</span>
            <span className="font-bold text-lg">Vuln Scanner</span>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
