"""Módulo de Auditoría Global de Tolerancia Comercial.

Evalúa el dataset de pruebas históricas contra las matrices de márgenes base
y el motor de reglas de ajuste dinámico, midiendo la tasa de efectividad comercial.
"""

import json
from pathlib import Path
import sys
import unicodedata
from typing import Any, Dict, List, Union

import pandas as pd

# Conexión dinámica con el motor de clasificación del Módulo 02
BASE_DIR: Path = Path(__file__).resolve().parent.parent
MODULO_02_PATH: Path = BASE_DIR.parent / "02-automatizacion-margenes"

if str(MODULO_02_PATH) not in sys.path:
    sys.path.append(str(MODULO_02_PATH))

from src.limpiador import clasificar_producto_estricto


def cargar_json(path: Path) -> Union[Dict[str, Any], List[Any]]:
    """Carga de forma segura un archivo JSON desde el disco.

    Args:
        path: Ruta hacia el archivo JSON.

    Returns:
        Estructura de datos deserializada (dict o list).
    """
    if path.exists():
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


def _normalizar_texto(texto: str) -> str:
    """Normaliza texto eliminando acentos, caracteres diacríticos y espacios redundantes.

    Args:
        texto: Cadena de texto a procesar.

    Returns:
        Texto en minúsculas sin tildes.
    """
    texto_norm = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in texto_norm if unicodedata.category(c) != "Mn")


def _interpolar_margen_piso(cantidad: int, escala_margenes: Dict[str, Any]) -> float:
    """Calcula el margen base aplicando el algoritmo de escalón duro (Piso Comercial).

    Args:
        cantidad: Volumen de unidades cotizadas.
        escala_margenes: Mapeo de porcentajes por tramo de cantidad.

    Returns:
        Margen porcentual base.
    """
    cantidades_ordenadas = sorted([int(q) for q in escala_margenes.keys()])
    if not cantidades_ordenadas:
        return 0.0

    if cantidad <= cantidades_ordenadas[0]:
        return float(escala_margenes[str(cantidades_ordenadas[0])])

    cantidad_objetivo = cantidades_ordenadas[0]
    for q in cantidades_ordenadas:
        if cantidad >= q:
            cantidad_objetivo = q
        else:
            break

    return float(escala_margenes[str(cantidad_objetivo)])


def _evaluar_condicion_regla(cond: Dict[str, Any], cantidad: int, texto_norm: str) -> bool:
    """Evalúa si un registro satisface una condición unitaria de una regla de ajuste.

    Args:
        cond: Diccionario que define la variable, operador y valor de referencia.
        cantidad: Cantidad de unidades del registro actual.
        texto_norm: Descripción normalizada del producto.

    Returns:
        True si la condición se cumple; False en caso contrario.
    """
    var = cond.get("variable", "")
    op = cond.get("condicion", "")
    ref = cond.get("valor_referencia", "")

    if var == "cantidad":
        try:
            val_actual = float(cantidad)
            val_ref = float(ref)

            if ("menor o igual" in op or "<=" in op) and not (val_actual <= val_ref):
                return False
            elif ("mayor o igual" in op or ">=" in op) and not (val_actual >= val_ref):
                return False
            elif ("menor" in op or "<" in op) and not (val_actual < val_ref):
                return False
            elif ("mayor" in op or ">" in op) and not (val_actual > val_ref):
                return False
            elif ("igual" in op or "==" in op) and not (val_actual == val_ref):
                return False
        except ValueError:
            return False

    elif var in ["descripcion", "detalle", "texto"]:
        token = _normalizar_texto(str(ref))
        if "contiene" in op and token not in texto_norm:
            return False
        elif "no contiene" in op and token in texto_norm:
            return False
        elif "igual" in op and texto_norm != token:
            return False

    return True


def ejecutar_auditoria_global(
    db_path: Path, matrices_path: Path, ajustes_path: Path, output_path: Path
) -> None:
    """Procesa el dataset histórico y genera el reporte de tolerancia comercial.

    Args:
        db_path: Ruta del Data Lake histórico de entrada.
        matrices_path: Ruta del artefacto JSON de márgenes base.
        ajustes_path: Ruta del artefacto JSON de reglas condicionales.
        output_path: Ruta destino del archivo Excel de auditoría.
    """
    if not db_path.exists():
        print(f"[ERROR] Archivo origen no encontrado: {db_path}")
        return

    print("==================================================")
    print("AUDITORÍA COMERCIAL: CLASIFICADOR CENTRALIZADO (MÓDULO 02)")
    print("==================================================")

    df: pd.DataFrame = pd.read_excel(db_path)
    matrices: Dict[str, Any] = cargar_json(matrices_path)
    ajustes: List[Dict[str, Any]] = cargar_json(ajustes_path)

    resultados: List[Dict[str, Any]] = []

    # Procesamiento en memoria de alta velocidad mediante diccionarios
    for idx, row in enumerate(df.to_dict(orient="records"), start=2):
        desc: str = str(row["Descripcion / Articulo"])
        costo_prov: float = float(row["Costo Prov"])
        precio_cli_original: float = float(row["Precio Cli"])
        cantidad: int = int(row["Cantidad Detectada"])
        proveedor: str = str(row.get("Proveedor", "ANONIMO")).strip().upper()

        matched_key = clasificar_producto_estricto(desc, costo_prov) or "MERCHANDISING_GENERAL"

        margin_scale = matrices.get(matched_key, {}).get("margenes", {})
        margen_calculado = _interpolar_margen_piso(cantidad, margin_scale)

        texto_norm = _normalizar_texto(desc)

        for regla in ajustes:
            if regla.get("producto") != matched_key and regla.get("producto") != "TODOS":
                continue

            condiciones = regla.get("condiciones", [])
            if condiciones and all(
                _evaluar_condicion_regla(cond, cantidad, texto_norm) for cond in condiciones
            ):
                tipo = regla.get("tipo_ajuste", "")
                impacto = float(regla.get("valor_impacto", 0.0))

                if tipo == "margen fijo":
                    margen_calculado = impacto
                elif tipo == "sumar puntos":
                    margen_calculado += impacto
                elif tipo == "restar puntos":
                    margen_calculado -= impacto

        factor = 1.0 + (margen_calculado / 100.0)
        precio_calculado = round(costo_prov * factor, 2)
        diferencia = round(precio_calculado - precio_cli_original, 2)
        fuera_tolerancia = "SI" if abs(diferencia) > 2.0 else "NO"

        resultados.append({
            "Fila_Excel": idx,
            "Proveedor": proveedor,
            "Arquetipo": matched_key,
            "Cantidad": cantidad,
            "Costo_Prov": costo_prov,
            "Precio_Cli_Original": precio_cli_original,
            "Precio_Calculado": precio_calculado,
            "Diferencia": diferencia,
            "Fuera_de_Tolerancia": fuera_tolerancia,
            "Descripcion": desc,
        })

    df_res = pd.DataFrame(resultados)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_res.to_excel(output_path, index=False)

    print(f"[SUCCESS] Reporte de auditoría generado: {output_path.resolve()}")
    print(f"[STATUS] Registros totales analizados: {len(df_res)}")
    print(f"[STATUS] Registros fuera de tolerancia: {len(df_res[df_res['Fuera_de_Tolerancia'] == 'SI'])}")

    df_filtrado_50 = df_res[df_res["Cantidad"] >= 50]
    total_50 = len(df_filtrado_50)
    fuera_50 = len(df_filtrado_50[df_filtrado_50["Fuera_de_Tolerancia"] == "SI"])

    print("--------------------------------------------------")
    print("CONTROL DE ENTREGAS CRÍTICAS (Pedidos >= 50 Unidades):")
    print(f"   -> Total analizado corporativo: {total_50} filas")
    print(f"   -> Fuera de tolerancia (SI): {fuera_50} filas")
    if total_50 > 0:
        efectividad = round(((total_50 - fuera_50) / total_50) * 100, 2)
        print(f"   -> Efectividad corporativa actual: {efectividad}%")
    print("==================================================")