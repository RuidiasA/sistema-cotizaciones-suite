"""Módulo de Análisis Estadístico y Suavizado de Márgenes.

Aplica filtros estadísticos (IQR) por tramo de cantidad, elimina outliers
y realiza un suavizado monótono para construir curvas de margen comerciales.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import numpy as np
import pandas as pd

from src.limpiador import CONFIG_PRODUCTOS, clasificar_producto_estricto

ESCALAS_ESTANDAR: List[int] = [
    10, 25, 50, 100, 250, 500, 1000,
    2000, 3000, 5000, 10000, 20000, 30000, 50000, 100000
]


def ajustar_a_escala_comercial(cantidad: float) -> int:
    """Mapea una cantidad real a la escala comercial estándar más cercana."""
    return min(ESCALAS_ESTANDAR, key=lambda x: abs(x - cantidad))


def suavizar_curva_comercial(margenes_dict: Dict[str, float]) -> Dict[str, float]:
    """Aplica suavizado monótono decreciente sobre los márgenes por volumen."""
    cantidades = sorted([int(k) for k in margenes_dict.keys()])
    if not cantidades:
        return margenes_dict

    valores_limpios = {str(c): margenes_dict[str(c)] for c in cantidades}

    # Ajuste de izquierda a derecha (Evitar picos incongruentes al subir volumen)
    for i in range(1, len(cantidades)):
        key_prev = str(cantidades[i - 1])
        key_act = str(cantidades[i])

        if valores_limpios[key_act] > valores_limpios[key_prev]:
            ratio = cantidades[i] / cantidades[i - 1]
            factor = 1.0 - min(0.08, 0.02 * np.log2(ratio))
            valores_limpios[key_act] = round(valores_limpios[key_prev] * factor, 1)
        else:
            limite_caida_maxima = valores_limpios[key_prev] * 0.70
            if valores_limpios[key_act] < limite_caida_maxima:
                valores_limpios[key_act] = round(limite_caida_maxima, 1)

    # Ajuste de derecha a izquierda (Ajustar valles iniciales)
    for i in range(len(cantidades) - 2, -1, -1):
        key_act = str(cantidades[i])
        key_sig = str(cantidades[i + 1])

        if valores_limpios[key_act] < valores_limpios[key_sig]:
            ratio = cantidades[i + 1] / cantidades[i]
            factor = 1.0 + min(0.08, 0.02 * np.log2(ratio))
            valores_limpios[key_act] = round(valores_limpios[key_sig] * factor, 1)

    for k in valores_limpios:
        valores_limpios[k] = max(10.0, valores_limpios[k])

    return valores_limpios


def analizar_y_optimizar_margenes(
    ruta_excel_entrada: Union[str, Path],
    ruta_json_salida: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """Procesa el Excel histórico, aplica filtro IQR y genera la matriz de márgenes.

    Args:
        ruta_excel_entrada: Ruta al archivo Excel con histórico de cotizaciones.
        ruta_json_salida: Ruta de destino para la exportación en formato JSON.

    Returns:
        Diccionario con la matriz final de márgenes por arquetipo.
    """
    print("Iniciando la trituración de datos históricos con motor modular...")

    df = pd.read_excel(ruta_excel_entrada, engine='openpyxl')
    df.columns = [str(col).strip() for col in df.columns]

    col_desc = 'Descripcion / Articulo'
    col_cant = 'Cantidad Detectada'
    col_prov = 'Costo Prov'
    col_cli = 'Precio Cli'

    # Limpieza estricta de tipos de datos
    df[col_cant] = pd.to_numeric(df[col_cant], errors='coerce')
    df[col_prov] = pd.to_numeric(df[col_prov], errors='coerce')
    df[col_cli] = pd.to_numeric(df[col_cli], errors='coerce')
    df = df.dropna(subset=[col_cant, col_prov, col_cli])
    df = df[(df[col_prov] > 0) & (df[col_cant] > 0)]

    print("Clasificando arquetipos dinámicamente mediante el diccionario maestro...")
    df['Arquetipo_Limpio'] = df[col_desc].apply(clasificar_producto_estricto)
    df_filtrado = df[df['Arquetipo_Limpio'].notna()].copy()

    df_filtrado['Escala_Comercial'] = df_filtrado[col_cant].apply(ajustar_a_escala_comercial)
    df_filtrado['Margen_Calculado'] = (df_filtrado[col_cli] / df_filtrado[col_prov]) - 1
    df_filtrado = df_filtrado[df_filtrado['Margen_Calculado'] >= 0]

    matrices_crudas: Dict[str, Dict[str, float]] = {}
    grouped = df_filtrado.groupby(['Arquetipo_Limpio', 'Escala_Comercial'])

    print("Agrupando bloques y ejecutando control estadístico IQR por tramo...")
    for (arquetipo, escala), tramo in grouped:
        if len(tramo) < 2:
            margen_optimo = float(tramo['Margen_Calculado'].values[0])
        else:
            q1 = tramo['Margen_Calculado'].quantile(0.25)
            q3 = tramo['Margen_Calculado'].quantile(0.75)
            iqr = q3 - q1
            tramo_filtrado = tramo[
                (tramo['Margen_Calculado'] >= (q1 - 1.5 * iqr)) &
                (tramo['Margen_Calculado'] <= (q3 + 1.5 * iqr))
            ]
            margen_optimo = (
                float(tramo_filtrado['Margen_Calculado'].median())
                if not tramo_filtrado.empty
                else float(tramo['Margen_Calculado'].median())
            )

        if arquetipo not in matrices_crudas:
            matrices_crudas[arquetipo] = {}

        matrices_crudas[arquetipo][str(int(escala))] = round(margen_optimo * 100, 1)

    print("Aplicando suavizado monótono e inyectando claves estructurales...")
    matrices_finales: Dict[str, Any] = {}

    for arquetipo, margenes_sucios in matrices_crudas.items():
        margenes_ordenados = dict(sorted(margenes_sucios.items(), key=lambda item: int(item[0])))
        margenes_limpios = suavizar_curva_comercial(margenes_ordenados)

        meta_config = CONFIG_PRODUCTOS[arquetipo]

        matrices_finales[arquetipo] = {
            "nombre_comercial": meta_config["nombre_comercial"],
            "macro_categoria": meta_config.get("macro_categoria", ""),
            "subcategoria": meta_config.get("subcategoria", ""),
            "filtros_prenda": meta_config["filtros_prenda"],
            "filtros_material": meta_config["filtros_material"],
            "margenes": margenes_limpios
        }

    if ruta_json_salida:
        path_salida = Path(ruta_json_salida)
        path_salida.parent.mkdir(parents=True, exist_ok=True)
        with open(path_salida, 'w', encoding='utf-8') as f:
            json.dump(matrices_finales, f, ensure_ascii=False, indent=2)
        print(f"¡Matriz unificada exportada con éxito en: {path_salida.resolve()}!")

    return matrices_finales