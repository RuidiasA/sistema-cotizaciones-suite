"""Script de Prueba Integrada Headless (Sin GUI).

Ejecuta un escaneo completo en consola sobre la carpeta configurada (o la por
defecto) para auditar el rendimiento del motor y validar los reportes de error.

Principios aplicados:
    - Single Responsibility (SRP): Exclusivamente dedicado a auditorías por consola.
"""

import os
from pathlib import Path
import sys
import threading

# Asegurar que la raíz del subproyecto esté en el PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.models.constants import DEFAULT_EXCEL_FOLDER, HOJAS_EXCLUIDAS
from src.services.excel_scan_service import ExcelScanService


def main() -> None:
    """Ejecuta la prueba de humo del motor de escaneo."""
    folder = os.environ.get("SCAN_FOLDER", DEFAULT_EXCEL_FOLDER)
    print(f"🔍 Iniciando escaneo headless en: {folder}\n")

    stop_event = threading.Event()
    service = ExcelScanService(hojas_excluidas=HOJAS_EXCLUIDAS)
    
    # Escaneo global (sin filtros de tags ni exclusions)
    reports = service.scan_folder(folder, {"tags": [], "exclude": []}, stop_event)

    total_files = len(reports)
    valid_files = sum(1 for r in reports if not r.error_message)
    invalid_files = total_files - valid_files
    total_rows_generated = sum(len(r.matched_rows) for r in reports)

    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL DEL ESCANEO:")
    print(f"✔️ Total archivos procesados: {total_files}")
    print(f"✔️ Válidos: {valid_files} | ⚠️ Inválidos: {invalid_files}")
    print(f"✔️ Total filas generadas: {total_rows_generated}")
    print("=" * 50 + "\n")

    for r in reports:
        status = "OK" if not r.error_message else f"ERROR: {r.error_message}"
        print(f" - {r.file_name} ({r.sheet_name or 'N/A'}) -> {len(r.matched_rows)} filas -> {status}")


if __name__ == "__main__":
    main()