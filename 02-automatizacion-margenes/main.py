"""Punto de entrada principal del Módulo 02 - Automatización de Márgenes.

Orquesta la lectura del histórico Excel (obtenido del Módulo 01), ejecuta 
el pipeline de limpieza y exporta las matrices suavizadas a formato JSON.
"""

from pathlib import Path
import time
from src.analizador import analizar_y_optimizar_margenes


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    
    # Búsqueda defensiva del archivo Excel histórico en data/ (debug_scan_raw)
    archivos_excel = list(data_dir.glob("*.xlsx"))
    ruta_excel = None

    for archivo in archivos_excel:
        if "matrices" not in archivo.name and not archivo.name.startswith("~$"):
            ruta_excel = archivo
            break

    ruta_json_salida = data_dir / "matriz_margenes.json"

    print("==============================================")
    print(" MOTOR DE OPTIMIZACIÓN DE MÁRGENES (GLOBAL)   ")
    print("==============================================")

    if not ruta_excel or not ruta_excel.exists():
        print(f"Error Crítico: No se encontró ningún archivo Excel válido en:\n   -> {data_dir}")
        print("\nSolución:")
        print("   Asegúrate de colocar tu archivo Excel de cotizaciones dentro de la carpeta 'data/'")
        print("==================================================================")
        return

    print(f"Archivo de entrada detectado: {ruta_excel.name}")
    tiempo_inicio = time.time()

    try:
        analizar_y_optimizar_margenes(ruta_excel, ruta_json_salida)
        tiempo_total = time.time() - tiempo_inicio

        print("==================================================================")
        print("¡Pipeline de análisis masivo ejecutado con éxito!")
        print(f"Tiempo de procesamiento RAM: {tiempo_total:.2f} segundos.")
        print(f"Archivo JSON autogenerado en: {ruta_json_salida}")
        print("Márgenes listos para inyección en el cotizador principal (Compipro).")
        print("==================================================================")

    except Exception as e:
        print("\nSe produjo un fallo crítico durante la ejecución del proceso:")
        print(f"   -> Error: {e}")
        print("\nRecomendación de debugging:")
        print("   Verifica que las columnas 'Descripcion / Articulo', 'Cantidad Detectada',")
        print("   'Costo Prov' y 'Precio Cli' existan en el Excel.")
        print("==================================================================")


if __name__ == "__main__":
    main()