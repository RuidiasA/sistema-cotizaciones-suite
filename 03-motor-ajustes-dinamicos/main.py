"""Orquestador Principal del Módulo 03: Motor de Ajustes Dinámicos.

Ejecuta secuencialmente la compilación del tarifario maestro multicapa (Excel -> JSON)
y la auditoría global de tolerancia comercial sobre el dataset histórico.
"""

from pathlib import Path
import sys
import time

from src.audit import ejecutar_auditoria_global
from src.compiler import ExcelCompiler

BASE_DIR: Path = Path(__file__).resolve().parent
CONFIG_DIR: Path = BASE_DIR / "config"
DATA_DIR: Path = BASE_DIR / "data"

EXCEL_REGLAS: Path = CONFIG_DIR / "tarifario_diseno.xlsx"
MATRICES_JSON: Path = CONFIG_DIR / "matrices_margen.json"
AJUSTES_JSON: Path = CONFIG_DIR / "ajustes_margen.json"

DATA_INPUT: Path = DATA_DIR / "input" / "debug_scan_raw_recent.xlsx"
DATA_OUTPUT: Path = DATA_DIR / "output" / "auditoria_global.xlsx"


def main() -> None:
    """Orquesta el pipeline secuencial de compilación y auditoría del módulo."""
    tiempo_inicio: float = time.perf_counter()

    print("==================================================")
    print("MOTOR DE AJUSTES DINÁMICOS - COMPILACIÓN Y AUDITORÍA")
    print("==================================================")

    if not EXCEL_REGLAS.exists():
        print(f"[ERROR] No se encontró el tarifario maestro en: {EXCEL_REGLAS}")
        sys.exit(1)

    try:
        print("\n[INFO] FASE 1: Compilando Tarifario Maestro Multicapa...")
        compiler = ExcelCompiler(EXCEL_REGLAS, CONFIG_DIR)
        compiler.compilar_todo()

        print("\n[INFO] FASE 2: Ejecutando Auditoría Global (Tolerancia ±2.00 PEN)...")
        ejecutar_auditoria_global(DATA_INPUT, MATRICES_JSON, AJUSTES_JSON, DATA_OUTPUT)

        tiempo_total: float = time.perf_counter() - tiempo_inicio

        print("\n--------------------------------------------------")
        print("[SUCCESS] Pipeline del Módulo 03 completado exitosamente.")
        print(f"[STATUS] Tiempo total de procesamiento RAM: {tiempo_total:.2f} segundos.")
        print("==================================================")

    except Exception as exc:
        print(f"\n[ERROR] Fallo crítico durante la ejecución del Módulo 03: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()