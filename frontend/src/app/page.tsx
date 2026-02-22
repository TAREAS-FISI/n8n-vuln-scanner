export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center gap-8 pt-20">
      <h1 className="text-4xl font-bold text-center">
        🛡️ Scanner de Vulnerabilidades Web
      </h1>
      <p className="text-gray-400 text-center max-w-lg">
        Ingresa una URL para analizar su seguridad con 4 fuentes de detección +
        análisis inteligente con IA local.
      </p>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 w-full max-w-md">
        <p className="text-gray-500 text-center text-sm">
          Formulario de escaneo — próximamente (Fase 4)
        </p>
      </div>
    </div>
  );
}
