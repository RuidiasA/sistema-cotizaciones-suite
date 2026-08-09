"""Servicio Motor de Escaneo Paralelizado de Archivos Excel.

Inspecciona recursivamente directorios, detecta tablas de cotización con encabezados
variables, aplica extracción forense de precios/márgenes (radar financiero) y fallbacks
ante formatos inconsistentes.

Principios aplicados:
    - Single Responsibility (SRP): Responsable del I/O, parsing e inspección resiliente de Excels.
    - Open/Closed (OCP): Extensible mediante configuraciones de search_pack sin alterar el motor.
"""

from __future__ import annotations

from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from openpyxl import load_workbook
import pandas as pd

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ..models.entities import FileScanReport, PriceStats, ScanRow
from .text_utils import (
    extraer_material,
    extraer_producto_base,
    extraer_segmento_calidad,
    limpiar_precio,
    limpiar_y_entero,
    normalizar_texto,
    recortar_detalle,
)


class ExcelScanService:
    """Motor de lectura y extracción multihilo para libros de Excel desestructurados."""

    KEYWORDS_DESCARTAR = ["SERVICIO", "DELIVERY", "SUBTOTAL", "SUB TOTAL", "TOTAL", "IGV", "1RA"]

    RAW_DEBUG_COLUMNS = [
        "Ruta Archivo",
        "Hoja",
        "Proveedor",
        "Cantidad Detectada",
        "Descripcion / Articulo",
        "Arquetipo",
        "Costo Prov",
        "Precio Cli",
        "Margen",
    ]

    def __init__(self, hojas_excluidas: Sequence[str]) -> None:
        """Inicializa el servicio configurando las hojas ignoradas.

        Args:
            hojas_excluidas: Nombres de pestañas a descartar.
        """
        self._hojas_excluidas = [h.lower() for h in hojas_excluidas]
        self._last_raw_records: List[Dict[str, object]] = []

    def scan_folder(
        self, 
        folder_path: str, 
        search_pack: dict, 
        stop_event: threading.Event,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None
    ) -> List[FileScanReport]:
        """Escanea una carpeta recursivamente ejecutando hilos concurrentes.

        Args:
            folder_path: Ruta del directorio raíz.
            search_pack: Configuración de inclusión/exclusión de palabras clave.
            stop_event: Evento para señalizar cancelación de hilos.
            progress_callback: Función opcional para reportar progreso en tiempo real.

        Returns:
            Lista de reportes generados por archivo.
        """
        checkpoint_path = os.path.join(folder_path, "scan_checkpoint.json")
        error_log_path = os.path.join(folder_path, "log_errores.txt")

        procesados = []
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    procesados = json.load(f)
            except Exception:
                pass

        archivos = self._list_excel_files(folder_path)
        archivos_pendientes = [a for a in archivos if os.path.basename(a) not in procesados]

        reports: List[FileScanReport] = []
        raw_records: List[Dict[str, object]] = []

        total = len(archivos_pendientes)
        if total == 0:
            self._last_raw_records = raw_records
            return reports

        start_all = time.time()
        if stop_event.is_set():
            self._last_raw_records = raw_records
            return reports

        lock = threading.Lock()

        def _scan_one(ruta: str) -> Tuple[FileScanReport, List[Dict[str, object]], float]:
            local_raw: List[Dict[str, object]] = []
            t0 = time.time()
            report = self.scan_file(ruta, search_pack, local_raw)
            return report, local_raw, time.time() - t0

        max_workers = min(6, os.cpu_count() or 1)
        executor = ThreadPoolExecutor(max_workers=max_workers)
        futures = {}

        try:
            for ruta in archivos_pendientes:
                if stop_event.is_set():
                    break
                futures[executor.submit(_scan_one, ruta)] = ruta

            completed = 0
            recent_times: deque[float] = deque(maxlen=10)

            for future in as_completed(futures):
                ruta = futures[future]
                file_name = os.path.basename(ruta)

                try:
                    report, local_raw, file_elapsed = future.result()
                except Exception as exc:
                    report = FileScanReport(file_name=file_name, error_message=f"Error Crítico del Motor: {str(exc)}")
                    local_raw = []
                    file_elapsed = 0.0

                with lock:
                    reports.append(report)
                    raw_records.extend(local_raw)

                    if report.error_message:
                        with open(error_log_path, "a", encoding="utf-8") as err_file:
                            err_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {file_name} -> {report.error_message}\n")
                    elif file_name not in procesados:
                        procesados.append(file_name)

                    completed += 1
                    recent_times.append(file_elapsed)

                    elapsed = time.time() - start_all
                    avg = elapsed / completed if completed > 0 else 0
                    recent_avg = sum(recent_times) / len(recent_times) if recent_times else avg
                    avg_use = recent_avg if completed >= 3 else avg
                    remaining = max(0, total - completed)
                    eta = remaining * avg_use
                    eta_str = f"{eta:.0f}s" if eta < 60 else f"{eta/60:.1f} min"

                    # Disparar callback a la UI en tiempo real
                    if progress_callback:
                        progress_callback(completed, total, file_name, eta_str)

                    if completed % 50 == 0 or completed == total:
                        try:
                            with open(checkpoint_path, "w", encoding="utf-8") as f:
                                json.dump(procesados, f, ensure_ascii=False, indent=2)
                            self._last_raw_records = raw_records
                            self.export_raw_scan_dataframe(self.get_last_raw_scan_dataframe(), folder_path)
                        except Exception:
                            pass

        finally:
            executor.shutdown(wait=False)
            self._last_raw_records = raw_records

        return reports

    def scan_file(self, file_path: str, search_pack: dict, raw_records: Optional[List[Dict[str, object]]] = None) -> FileScanReport:
        """Procesa un archivo individual leyendo todas sus pestañas válidas.

        Args:
            file_path: Ruta absoluta del libro de Excel.
            search_pack: Filtros de búsqueda compilados.
            raw_records: Colección mutable para almacenar registros crudos.

        Returns:
            Instancia de FileScanReport con el resultado.
        """
        file_name = os.path.basename(file_path)
        report = FileScanReport(file_name=file_name)

        try:
            xls = pd.ExcelFile(file_path)
            wb_data_only = self._open_workbook_data_only(file_path)
            sheets_processed: List[str] = []

            for sheet_name in xls.sheet_names:
                if any(ex in sheet_name.lower().strip() for ex in self._hojas_excluidas):
                    continue

                try:
                    df_check = (
                        self._read_sheet_data_only(wb_data_only, sheet_name, header=None, nrows=25)
                        if wb_data_only
                        else pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=25)
                    )
                except Exception:
                    continue

                header_row = self._detect_header_row(df_check)
                if header_row is None:
                    continue

                try:
                    df_temp = (
                        self._read_sheet_data_only(wb_data_only, sheet_name, header=header_row)
                        if wb_data_only
                        else pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                    )
                except Exception:
                    continue

                df_temp.columns = [str(c).replace("\n", " ").strip() for c in df_temp.columns]

                vars_codigo = ["código", "codigo", "cod.", "cod", "cód. artíc."]
                vars_articulo = ["artículo", "articulo", "art."]
                vars_detalle = ["detalle", "detalles", "observacion", "obseracion", "descripción", "descripcion"]

                c_codigo = next((c for c in df_temp.columns if normalizar_texto(c) in vars_codigo), None)
                c_articulo = next((c for c in df_temp.columns if normalizar_texto(c) in vars_articulo), None)
                c_detalle = next((c for c in df_temp.columns if normalizar_texto(c) in vars_detalle), None)

                c_cant = next((c for c in df_temp.columns if any(kw in c.lower() for kw in ["cant. min.", "cant.", "cant", "cantidad"])), None)
                c_finals = [c for c in df_temp.columns if any(kw in c.lower() for kw in ["costo uni sin igv", "costo uni", "unit", "uni ", "no igv", "venta"])]
                c_provs = [c for c in df_temp.columns if any(kw in c.lower() for kw in ["costo s/.", "costo prov"]) and c not in c_finals and "total" not in c.lower()]
                c_proveedor = next((c for c in df_temp.columns if "proveedor" in c.lower()), None)

                if c_cant and (c_provs or c_finals):
                    df_temp[c_cant] = df_temp[c_cant].ffill()
                    for c in [c_codigo, c_articulo, c_detalle]:
                        if c:
                            df_temp[c] = df_temp[c].ffill()

                    cols_ordenadas = [c for c in [c_detalle, c_articulo, c_codigo] if c is not None]
                    if cols_ordenadas:
                        df_temp[cols_ordenadas] = df_temp[cols_ordenadas].fillna("")
                        texto_unido = df_temp[cols_ordenadas].astype(str).agg(" ".join, axis=1)
                        df_temp["texto_consolidado"] = texto_unido.str.replace(r"\s+", " ", regex=True).str.strip()
                    else:
                        df_temp["texto_consolidado"] = ""

                    mask = df_temp.apply(lambda row: self._cumple_busqueda_tokenizada(row, search_pack), axis=1)

                    if int(mask.sum()) > 0:
                        sheets_processed.append(sheet_name)
                        col_map = {
                            "cant": c_cant,
                            "provs": c_provs,
                            "finals": c_finals,
                            "detalle": c_detalle,
                            "proveedor_col": c_proveedor,
                        }
                        self._process_rows(df_temp, col_map, search_pack, report, file_path, sheet_name, raw_records)

            if not report.matched_rows and not report.failed_rows:
                report.error_message = "No se detectó una tabla válida."
                return report

            report.sheet_name = ", ".join(sheets_processed) if sheets_processed else None
            return report

        except PermissionError:
            report.error_message = "Archivo abierto por otro programa. Ciérralo."
            return report
        except Exception as exc:
            report.error_message = f"Error: {str(exc)}"
            return report

    def _list_excel_files(self, folder_path: str) -> List[str]:
        if not folder_path or not os.path.isdir(folder_path):
            return []
        archivos: List[str] = []
        root = Path(folder_path)
        for pattern in ("*.xlsx", "*.xls"):
            for p in root.rglob(pattern):
                if p.name.startswith("~$") or p.name in ("debug_scan_raw.xlsx", "scan_checkpoint.json"):
                    continue
                if p.is_file():
                    archivos.append(str(p))
        return archivos

    def _open_workbook_data_only(self, file_path: str):
        ext = Path(file_path).suffix.lower()
        if ext not in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
            return None
        try:
            return load_workbook(file_path, data_only=True, read_only=True)
        except Exception:
            return None

    def _read_sheet_data_only(self, wb, sheet_name: str, header: Optional[int] = None, nrows: Optional[int] = None) -> pd.DataFrame:
        ws = wb[sheet_name]
        rows_iter = ws.values
        rows = list(islice(rows_iter, nrows)) if nrows is not None else list(rows_iter)
        df = pd.DataFrame(rows)
        if header is None or header >= len(df.index):
            return df if header is None else pd.DataFrame()

        header_values = list(df.iloc[header].values)
        if len(header_values) < df.shape[1]:
            header_values += [""] * (df.shape[1] - len(header_values))
        else:
            header_values = header_values[: df.shape[1]]

        df.columns = header_values
        return df.iloc[header + 1:].reset_index(drop=True)

    def _detect_header_row(self, df_check: pd.DataFrame) -> Optional[int]:
        for idx, fila in df_check.iterrows():
            linea = " ".join([str(x).lower() for x in fila.values])
            if ("cant" in linea or "cantidad" in linea) and ("costo" in linea or "s/." in linea or "uni" in linea):
                return int(idx)
        return None

    def _cumple_busqueda_tokenizada(self, fila: pd.Series, search_pack: dict) -> bool:
        if "compiled_tags" not in search_pack:
            tags = search_pack.get("tags", [])
            tags_norm = list({normalizar_texto(tag) for tag in tags if tag})
            if tags_norm:
                tags_norm.sort(key=len, reverse=True)
                pattern = r"\b(?:" + "|".join(map(re.escape, tags_norm)) + r")\b"
                search_pack["compiled_tags"] = re.compile(pattern)
            else:
                search_pack["compiled_tags"] = None

        if "compiled_excludes" not in search_pack:
            base_excludes = search_pack.get("exclude", []) + self.KEYWORDS_DESCARTAR
            excludes_norm = list({normalizar_texto(exc) for exc in base_excludes if exc})
            if excludes_norm:
                excludes_norm.sort(key=len, reverse=True)
                pattern = r"\b(?:" + "|".join(map(re.escape, excludes_norm)) + r")\b"
                search_pack["compiled_excludes"] = re.compile(pattern)
            else:
                search_pack["compiled_excludes"] = None

        if "texto_consolidado" in fila:
            contenido_norm = normalizar_texto(str(fila.get("texto_consolidado", "")))
        else:
            tokens = [str(v).split("Presentación:")[0].strip() for v in fila.values if pd.notna(v)]
            contenido_norm = normalizar_texto(" ".join(tokens))

        if search_pack["compiled_excludes"] and search_pack["compiled_excludes"].search(contenido_norm):
            return False

        if search_pack["compiled_tags"]:
            return bool(search_pack["compiled_tags"].search(contenido_norm))

        return True

    def _extract_number(self, cell: object) -> Tuple[bool, float]:
        """Extrae números limpios de celdas desestructuradas."""
        if cell is None:
            return False, 0.0
        if isinstance(cell, (int, float)):
            if isinstance(cell, float) and math.isnan(cell):
                return False, 0.0
            return True, float(cell)

        s = str(cell).strip()
        if not s or s.lower() in ("nan", "none"):
            return False, 0.0

        cleaned = s.replace("s/.", "").replace("%", "").replace("$", "").replace(",", "").replace(" ", "")
        if re.search(r"[A-Za-zÀ-ÿ]", cleaned):
            return False, 0.0

        neg = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            neg = True
            cleaned = cleaned[1:-1]

        if cleaned in ("", "-", "."):
            return False, 0.0

        try:
            val = float(cleaned)
            return True, -val if neg else val
        except Exception:
            return False, 0.0

    def _buscar_precio_cliente(self, fila: pd.Series, cols_finals: Sequence[str], v1: float) -> float:
        candidatos: List[float] = []
        for c in cols_finals:
            val = limpiar_precio(fila[c])
            if val > v1:
                candidatos.append(val)
        return round(min(candidatos), 2) if candidatos else 0.0

    def _process_rows(
        self,
        df: pd.DataFrame,
        col_map: Dict[str, object],
        search_pack: dict,
        report: FileScanReport,
        file_path: str,
        sheet_name: str,
        raw_records: Optional[List[Dict[str, object]]] = None,
    ) -> None:
        vistos = set()
        stats = PriceStats()
        col_detalle = col_map.get("detalle")
        col_proveedor = col_map.get("proveedor_col")

        cols_detalle_real = [
            c for c in df.columns if any(k in str(c).lower() for k in ["detalle", "detalles", "descripcion", "observac", "obs"])
        ]
        cols_producto_plan_b = [
            c for c in df.columns if any(k in str(c).lower() for k in ["articulo", "art.", "producto", "item"]) and c not in cols_detalle_real
        ]

        def es_identificador_o_numero(v: object) -> bool:
            s = str(v).strip()
            if not s:
                return True
            try:
                float(s)
                return True
            except ValueError:
                pass
            return len(s) < 20 and " " not in s

        for idx, fila in df.iterrows():
            if not self._cumple_busqueda_tokenizada(fila, search_pack):
                continue

            try:
                cantidad = limpiar_y_entero(fila[col_map["cant"]])

                # Fallback multi-columna para extraer el detalle del artículo
                detalle_raw = str(fila.get("texto_consolidado", "")).strip()
                if not detalle_raw and col_detalle and col_detalle in fila:
                    detalle_raw = fila[col_detalle]

                if pd.isna(detalle_raw) or str(detalle_raw).strip() == "" or es_identificador_o_numero(detalle_raw):
                    encontrado = False
                    for c in cols_detalle_real:
                        val = fila.get(c)
                        if pd.notna(val) and str(val).strip() and not es_identificador_o_numero(val):
                            detalle_raw = val
                            encontrado = True
                            break

                    if not encontrado:
                        for c in cols_producto_plan_b:
                            val = fila.get(c)
                            if pd.notna(val) and str(val).strip() and not es_identificador_o_numero(val):
                                detalle_raw = val
                                encontrado = True
                                break

                if cantidad <= 0:
                    report.failed_rows.append(
                        ScanRow(
                            fila_id=int(idx),
                            articulo=recortar_detalle(detalle_raw),
                            cantidad=cantidad,
                            precio_prov=0.0,
                            precio_cli=0.0,
                            margen=0.0,
                            motivo="cantidad",
                        )
                    )
                    continue

                col_names = list(df.columns)

                # FASE 1: Extracción defensiva del precio cliente (v2)
                col_detalle_idx = next(
                    (i for i, c in enumerate(col_names) if col_detalle is not None and str(c) == str(col_detalle)), len(col_names)
                )
                cols_finals_validas = [c for c in col_map.get("finals", []) if c in col_names and col_names.index(c) < col_detalle_idx]
                v2 = float(self._buscar_precio_cliente(fila, cols_finals_validas, 0.0) or 0.0)

                # FASE 2: Radar financiero y Checksum para hallar el costo del proveedor (v1)
                v1 = 0.0
                prov_start_idx = next(
                    (i for i, c in enumerate(col_names) if any(kw in str(c).lower() for kw in ["proveedor", "costo s/."])), None
                )
                if prov_start_idx is None:
                    idx_cant = next((i for i, c in enumerate(col_names) if "cant" in str(c).lower()), None)
                    prov_start_idx = min(idx_cant + 1, len(col_names)) if idx_cant is not None else 0

                window_cols = col_names[prov_start_idx : min(prov_start_idx + 15, len(col_names))]
                bloque_final: List[float] = []

                for col in window_cols:
                    ok, val = self._extract_number(fila.get(col))
                    if ok:
                        bloque_final.append(val)
                        if len(bloque_final) >= 5:
                            break

                if len(bloque_final) >= 3:
                    n1, n2, n3 = bloque_final[0], bloque_final[1], bloque_final[2]
                    base_candidate = None
                    if abs(n1 * (n2 / 100.0) - n3) < 0.1:
                        base_candidate = n1
                    elif abs(n2 * (n1 / 100.0) - n3) < 0.1:
                        base_candidate = n2

                    if base_candidate is not None:
                        v1 = round(float(base_candidate), 2)

                if v1 == 0.0:
                    for pc in col_map.get("provs", []):
                        if pc in col_names:
                            ok, candidate = self._extract_number(fila.get(pc))
                            if ok and candidate > 0.0:
                                v1 = round(candidate, 2)
                                break

                # Validaciones de coherencia financiera
                min_diff = 0.5 if v1 >= 5 else 0.1
                if v1 <= 0 or v2 <= 0 or (v2 - v1) < min_diff:
                    report.failed_rows.append(
                        ScanRow(
                            fila_id=int(idx),
                            articulo=recortar_detalle(detalle_raw),
                            cantidad=cantidad,
                            precio_prov=v1,
                            precio_cli=v2,
                            margen=0.0,
                            motivo="precios",
                        )
                    )
                    continue

                huella = (cantidad, round(v1, 2), round(v2, 2))
                if huella in vistos:
                    report.failed_rows.append(
                        ScanRow(
                            fila_id=int(idx),
                            articulo=recortar_detalle(detalle_raw),
                            cantidad=cantidad,
                            precio_prov=v1,
                            precio_cli=v2,
                            margen=0.0,
                            motivo="duplicado",
                        )
                    )
                    continue

                margen_val = ((v2 - v1) / v1) * 100.0 if v1 > 0 else 999.0
                if margen_val > 900:
                    report.failed_rows.append(
                        ScanRow(
                            fila_id=int(idx),
                            articulo=recortar_detalle(detalle_raw),
                            cantidad=cantidad,
                            precio_prov=v1,
                            precio_cli=v2,
                            margen=round(margen_val, 2),
                            motivo="margen",
                        )
                    )
                    continue

                # Registro exitoso
                vistos.add(huella)
                report.matched_rows.append(
                    ScanRow(
                        fila_id=int(idx),
                        articulo=recortar_detalle(detalle_raw),
                        cantidad=cantidad,
                        precio_prov=v1,
                        precio_cli=v2,
                        margen=round(margen_val, 2),
                    )
                )
                stats.add_margin(cantidad, margen_val)

                if raw_records is not None:
                    base_p = extraer_producto_base(str(detalle_raw))
                    mat_p = extraer_material(str(detalle_raw))
                    seg_p = extraer_segmento_calidad(str(detalle_raw))
                    partes_p = [base_p] if base_p else []
                    if mat_p and mat_p not in partes_p:
                        partes_p.append(mat_p)
                    if seg_p and seg_p not in partes_p:
                        partes_p.append(seg_p)
                    arquetipo_calculado = " ".join(partes_p).strip()

                    prov_final = "ANONIMO"
                    if col_proveedor and col_proveedor in fila and pd.notna(fila[col_proveedor]):
                        val_celda = str(fila[col_proveedor]).strip()
                        if val_celda:
                            prov_final = val_celda.upper()

                    raw_records.append(
                        {
                            "Ruta Archivo": file_path,
                            "Hoja": sheet_name,
                            "Proveedor": prov_final,
                            "Cantidad Detectada": cantidad,
                            "Descripcion / Articulo": str(detalle_raw).strip(),
                            "Arquetipo": arquetipo_calculado,
                            "Costo Prov": float(v1),
                            "Precio Cli": float(v2),
                            "Margen": round(margen_val, 2),
                        }
                    )

            except Exception:
                report.failed_rows.append(
                    ScanRow(
                        fila_id=int(idx),
                        articulo=recortar_detalle(
                            detalle_raw if ("detalle_raw" in locals() and detalle_raw) else (fila[col_detalle] if col_detalle else "")
                        ),
                        cantidad=0,
                        precio_prov=0.0,
                        precio_cli=0.0,
                        margen=0.0,
                        motivo="error",
                    )
                )

        report.matched_rows.sort(key=lambda row: (str(row.articulo).strip().lower() if row.articulo else ""))
        report.stats.merge(stats)

    def get_last_raw_scan_dataframe(self) -> pd.DataFrame:
        """Devuelve un DataFrame con los registros de la última ejecución."""
        if not self._last_raw_records:
            return pd.DataFrame(columns=self.RAW_DEBUG_COLUMNS)
        df = pd.DataFrame(self._last_raw_records)
        return df.reindex(columns=self.RAW_DEBUG_COLUMNS).fillna(0)

    def export_raw_scan_dataframe(self, df: pd.DataFrame, output_path: str) -> str:
        """Exporta el DataFrame de depuración a Excel en disco."""
        output_dir = output_path or os.getcwd()
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "debug_scan_raw.xlsx")
        df.to_excel(output_file, index=False)
        return output_file