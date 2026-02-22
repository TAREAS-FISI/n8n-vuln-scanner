import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VulnScanner — Escáner de Vulnerabilidades Web",
  description: "Sistema inteligente de detección de vulnerabilidades web con IA",
};

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md dark:border-gray-800 dark:bg-gray-950/80">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-gray-900 dark:text-white">
          <svg className="h-6 w-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          VulnScanner
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="text-sm text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            Inicio
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            Dashboard
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            API
          </a>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50 dark:bg-gray-950`}
      >
        <Navbar />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
