"""Punto de entrada principal del Módulo 02 - Automatización de Márgenes.

Orquesta la lectura del histórico Excel (obtenido del Módulo 01), ejecuta 
el pipeline de limpieza, exporta las matrices suavizadas a formato JSON
e inyecta los márgenes base en el tarifario maestro del Módulo 03.
"""

from pathlib import Path
import sys
import time
from typing import Optional

from src.analizador import analizar_y_optimizar_margenes


def main() -> None:
    """Orquesta la ejecución del pipeline de análisis y suavizado de márgenes."""
    base_dir: Path = Path(__file__).resolve().parent
    data_dir: Path = base_dir / "data"

    ruta_excel_tarifario: Path = (
        base_dir.parent / "03-motor-ajustes-dinamicos" / "config" / "tarifario_diseno.xlsx"
    )

    ruta_excel: Optional[Path] = next(
        (
            f for f in data_dir.glob("*.xlsx")
            if "matrices" not in f.name and not f.name.startswith("~$")
        ),
        None,
    )

    ruta_json_salida: Path = data_dir / "matriz_margenes.json"

    print("==============================================")
    print(" MOTOR DE OPTIMIZACIÓN DE MÁRGENES (GLOBAL)   ")
    print("==============================================")

    if not ruta_excel or not ruta_excel.exists():
        print(f"Error Crítico: No se encontró ningún archivo Excel válido en:\n   -> {data_dir}")
        print("\nSolución:")
        print("   Asegúrate de colocar tu archivo Excel de cotizaciones dentro de la carpeta 'data/'")
        print("==================================================================")
        sys.exit(1)

    print(f"Archivo de entrada detectado: {ruta_excel.name}")
    tiempo_inicio: float = time.perf_counter()

    try:
        analizar_y_optimizar_margenes(
            ruta_excel_entrada=ruta_excel,
            ruta_json_salida=ruta_json_salida,
            ruta_excel_tarifario=ruta_excel_tarifario,
        )
        tiempo_total: float = time.perf_counter() - tiempo_inicio

        print("==================================================================")
        print("¡Pipeline de análisis masivo ejecutado con éxito!")
        print(f"Tiempo de procesamiento RAM: {tiempo_total:.2f} segundos.")
        print(f"Archivo JSON autogenerado en: {ruta_json_salida}")
        print(f"Hoja 'Margenes_Base' inyectada en: {ruta_excel_tarifario.name}")
        print("Márgenes listos para inyección en el cotizador principal (Compipro).")
        print("==================================================================")

    except Exception as exc:
        print("\nSe produjo un fallo crítico durante la ejecución del proceso:")
        print(f"   -> Error: {exc}")
        print("\nRecomendación de debugging:")
        print("   Verifica que las columnas 'Descripcion / Articulo', 'Cantidad Detectada',")
        print("   'Costo Prov' y 'Precio Cli' existan en el Excel.")
        print("==================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()