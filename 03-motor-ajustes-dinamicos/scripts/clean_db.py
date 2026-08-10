"""Módulo ETL para el saneamiento y curación del Data Lake histórico.

Resuelve registros huérfanos o sin proveedor asignado ("ANONIMO", "NAN")
mediante la imputación cruzada basada en firmas de texto únicas.
"""

import re
from pathlib import Path
from typing import Dict, Set
import pandas as pd

# Definición de rutas relativas basadas en la estructura del proyecto
BASE_DIR: Path = Path(__file__).resolve().parent.parent
INPUT_DIR: Path = BASE_DIR / "data" / "input"

FILE_ORIGINAL: Path = INPUT_DIR / "debug_scan_raw.xlsx"
FILE_BACKUP: Path = INPUT_DIR / "debug_scan_raw_BACKUP.xlsx"

INVALID_PROV_TOKENS: Set[str] = {"ANONIMO", "ANÓNIMO", "NAN", "", "NONE"}


def sanar_data_lake() -> None:
    """Ejecuta la canalización de curación sobre el archivo maestro de datos."""
    if not FILE_ORIGINAL.exists():
        print(f"[ERROR] Archivo origen no encontrado: {FILE_ORIGINAL}")
        return

    print("==================================================")
    print("ETL DATA LAKE: SANAMIENTO Y CURACION DE REGISTROS")
    print("==================================================")

    print(f"[INFO] Cargando dataset: {FILE_ORIGINAL.name}")
    df: pd.DataFrame = pd.read_excel(FILE_ORIGINAL)

    # Respaldo preventivo de seguridad
    df.to_excel(FILE_BACKUP, index=False)
    print(f"[INFO] Backup de seguridad generado en: {FILE_BACKUP.name}")

    # Normalización de columnas temporales para procesamiento en memoria
    df["_desc_clean"] = df["Descripcion / Articulo"].astype(str).str.strip()
    df["_prov_norm"] = (
        df["Proveedor"]
        .astype(str)
        .apply(lambda x: re.sub(r"\s+", " ", x).strip().upper())
    )

    # Aislar registros con proveedores válidos para mapeo de referencia
    df_validos = df[~df["_prov_norm"].isin(INVALID_PROV_TOKENS)]

    mapa_desc_prov: Dict[str, str] = {}
    for _, row in df_validos.iterrows():
        desc: str = row["_desc_clean"]
        prov_real: str = str(row["Proveedor"]).strip()

        # Priorizar la cadena de mayor longitud para evitar abreviaciones
        if desc in mapa_desc_prov:
            if len(prov_real) > len(mapa_desc_prov[desc]):
                mapa_desc_prov[desc] = prov_real
        else:
            mapa_desc_prov[desc] = prov_real

    # Imputación vectorizada de registros inválidos mediante el mapa de referencia
    mascara_invalida = df["_prov_norm"].isin(INVALID_PROV_TOKENS)
    proveedores_recuperados = df.loc[mascara_invalida, "_desc_clean"].map(mapa_desc_prov)
    
    # Contar únicamente los registros que efectivamente fueron corregidos
    registros_reparados: int = int(proveedores_recuperados.notna().sum())

    if registros_reparados > 0:
        df.loc[mascara_invalida, "Proveedor"] = proveedores_recuperados.fillna(
            df.loc[mascara_invalida, "Proveedor"]
        )

    # Limpieza de columnas temporales de cálculo
    df.drop(columns=["_desc_clean", "_prov_norm"], inplace=True)

    # Persistencia de los datos saneados
    df.to_excel(FILE_ORIGINAL, index=False)

    print("--------------------------------------------------")
    print("[SUCCESS] Proceso ETL completado satisfactoriamente.")
    print(f"[STATUS] Filas huérfanas imputadas: {registros_reparados}")
    print(f"[STATUS] Archivo maestro actualizado: {FILE_ORIGINAL.resolve()}")
    print("==================================================")


if __name__ == "__main__":
    sanar_data_lake()