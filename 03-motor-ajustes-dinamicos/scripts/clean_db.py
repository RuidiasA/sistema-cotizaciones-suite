"""Módulo ETL para el saneamiento y curación del Data Lake histórico.

Resuelve registros huérfanos o sin proveedor asignado ("ANONIMO", "NAN")
mediante imputación cruzada basada en firmas de texto descriptivas.
"""

import re
from pathlib import Path
from typing import Dict, Set

import pandas as pd

BASE_DIR: Path = Path(__file__).resolve().parent.parent
INPUT_DIR: Path = BASE_DIR / "data" / "input"

FILE_ORIGINAL: Path = INPUT_DIR / "debug_scan_raw.xlsx"
FILE_BACKUP: Path = INPUT_DIR / "debug_scan_raw_BACKUP.xlsx"

INVALID_PROV_TOKENS: Set[str] = {"ANONIMO", "ANÓNIMO", "NAN", "", "NONE"}


def sanar_data_lake() -> None:
    """Ejecuta la canalización de curación e imputación sobre el Data Lake maestro."""
    if not FILE_ORIGINAL.exists():
        print(f"[ERROR] Archivo origen no encontrado: {FILE_ORIGINAL}")
        return

    print("==================================================")
    print("ETL DATA LAKE: SANEAMIENTO Y CURACIÓN DE REGISTROS")
    print("==================================================")

    print(f"[INFO] Cargando dataset: {FILE_ORIGINAL.name}")
    df: pd.DataFrame = pd.read_excel(FILE_ORIGINAL)

    df.to_excel(FILE_BACKUP, index=False)
    print(f"[INFO] Backup de seguridad generado en: {FILE_BACKUP.name}")

    df["_desc_clean"] = df["Descripcion / Articulo"].astype(str).str.strip()
    df["_prov_norm"] = (
        df["Proveedor"]
        .astype(str)
        .apply(lambda x: re.sub(r"\s+", " ", x).strip().upper())
    )

    df_validos = df[~df["_prov_norm"].isin(INVALID_PROV_TOKENS)]

    mapa_desc_prov: Dict[str, str] = {}
    for desc, prov_real in zip(df_validos["_desc_clean"], df_validos["Proveedor"]):
        prov_str = str(prov_real).strip()
        # Prioriza la cadena de mayor longitud para preservar razones sociales completas
        if desc not in mapa_desc_prov or len(prov_str) > len(mapa_desc_prov[desc]):
            mapa_desc_prov[desc] = prov_str

    mascara_invalida = df["_prov_norm"].isin(INVALID_PROV_TOKENS)
    proveedores_recuperados = df.loc[mascara_invalida, "_desc_clean"].map(mapa_desc_prov)
    
    registros_reparados: int = int(proveedores_recuperados.notna().sum())

    if registros_reparados > 0:
        df.loc[mascara_invalida, "Proveedor"] = proveedores_recuperados.fillna(
            df.loc[mascara_invalida, "Proveedor"]
        )

    df.drop(columns=["_desc_clean", "_prov_norm"], inplace=True)
    df.to_excel(FILE_ORIGINAL, index=False)

    print("--------------------------------------------------")
    print("[SUCCESS] Proceso ETL completado satisfactoriamente.")
    print(f"[STATUS] Filas huérfanas imputadas: {registros_reparados}")
    print(f"[STATUS] Archivo maestro actualizado: {FILE_ORIGINAL.resolve()}")
    print("==================================================")


if __name__ == "__main__":
    sanar_data_lake()