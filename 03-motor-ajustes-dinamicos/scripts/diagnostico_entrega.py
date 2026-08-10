"""Módulo de Diagnóstico y Análisis Quirúrgico de Auditoría Comercial.

Evalúa los registros de entregas corporativas (pedidos >= 50 unidades)
que se encuentran fuera de la tolerancia de precio (±2 PEN), identificando
concentración por arquetipo, desvíos financieros y factores de personalización.
"""

from pathlib import Path
from typing import Tuple
import pandas as pd

# Configuración de rutas y parámetros globales
BASE_DIR: Path = Path(__file__).resolve().parent.parent
RUTA_AUDITORIA: Path = BASE_DIR / "data" / "output" / "auditoria_global.xlsx"

KEYWORDS_TECNICAS: Tuple[str, ...] = (
    "color", "colores", "logo", "full", "dtf", 
    "uv", "estampado", "bordado", "tapasol", "pvc"
)


def ejecutar_diagnostico_critico() -> None:
    """Ejecuta el análisis de desviaciones comerciales sobre la auditoría global."""
    if not RUTA_AUDITORIA.exists():
        print(f"[ERROR] Archivo de auditoría no encontrado en: {RUTA_AUDITORIA}")
        print("[INFO] Ejecute 'python main.py' en el Módulo 03 para generar la auditoría.")
        return

    df: pd.DataFrame = pd.read_excel(RUTA_AUDITORIA)

    # Filtrar únicamente entregas corporativas (>= 50 unidades) fuera de tolerancia
    df_critico: pd.DataFrame = df[
        (df["Cantidad"] >= 50) & (df["Fuera_de_Tolerancia"] == "SI")
    ].copy()

    total_criticos: int = len(df_critico)

    print("==================================================")
    print("DIAGNÓSTICO COMERCIAL: ENTREGAS CORPORATIVAS (>= 50 UNITS)")
    print("==================================================")
    print(f"[STATUS] Total de registros fuera de tolerancia: {total_criticos}\n")

    if df_critico.empty:
        print("[SUCCESS] No se encontraron registros fuera de tolerancia en este tramo.")
        print("==================================================")
        return

    # 1. Concentración de errores por arquetipo comercial
    print("1. ARQUETIPOS CRÍTICOS (TOP 5):")
    top_5_series = df_critico.groupby("Arquetipo").size().sort_values(ascending=False).head(5)
    
    for arquetipo, total_casos in top_5_series.items():
        pct = (total_casos / total_criticos) * 100
        print(f"   -> {arquetipo:<32} | Casos: {total_casos:>3} ({pct:>5.1f}%)")
    print("-" * 50)

    # 2. Desvío financiero promedio (PEN) por arquetipo crítico
    print("2. DESVÍO MONETARIO PROMEDIO POR ARQUETIPO (PEN):")
    desvios_promedio = df_critico.groupby("Arquetipo")["Diferencia"].mean().loc[top_5_series.index]
    
    for arquetipo, desvio in desvios_promedio.items():
        signo = "+" if desvio > 0 else ""
        print(f"   -> {arquetipo:<32} | Desvío Promedio: {signo}{desvio:>6.2f} PEN")
    print("-" * 50)

    # 3. Detección de factores técnicos de impresión/personalización
    print("3. INCIDENCIA DE PARÁMETROS TÉCNICOS EN ERRORES:")
    desc_series = df_critico["Descripcion"].astype(str).str.lower()
    
    for kw in KEYWORDS_TECNICAS:
        coincidencias = desc_series.str.contains(kw, na=False).sum()
        if coincidencias > 0:
            pct_kw = (coincidencias / total_criticos) * 100
            print(f"   -> Parámetro '{kw:<10}': {coincidencias:>3} menciones ({pct_kw:>5.1f}%)")

    print("==================================================")


if __name__ == "__main__":
    ejecutar_diagnostico_critico()