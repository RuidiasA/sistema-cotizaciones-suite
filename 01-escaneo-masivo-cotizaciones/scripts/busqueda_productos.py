"""Script utilitario de extracción recursiva de descripciones de productos.

Permite seleccionar un directorio de trabajo y realiza un escaneo plano 
y profundo sobre todos los libros de Excel (.xlsx, .xlsm, .xls) para extraer 
códigos, nombres de artículos y sus primeros 20 términos descriptivos.
"""

import os
import re
import sys
import tkinter as tk
from tkinter import filedialog
import warnings

import pandas as pd

# Suprimir advertencias de openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def seleccionar_carpeta() -> str:
    """Abre un diálogo nativo para seleccionar la carpeta de origen.

    Returns:
        Ruta del directorio seleccionado o cadena vacía si fue cancelado.
    """
    root = tk.Tk()
    root.withdraw()
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta con los archivos Excel")
    root.destroy()
    return carpeta


def limpiar_texto(texto: object) -> str:
    """Limpia cadenas omitiendo valores nulos.

    Args:
        texto: Objeto a limpiar.

    Returns:
        Cadena sin espacios excedentes.
    """
    if pd.isna(texto) or texto is None:
        return ""
    return str(texto).strip()


def limpiar_encabezado(texto: object) -> str:
    """Normaliza encabezados removiendo saltos de línea y símbolos.

    Args:
        texto: Texto del encabezado.

    Returns:
        Encabezado en minúsculas sin espacios dobles.
    """
    t = limpiar_texto(texto).lower()
    t = t.replace("\n", " ").replace("\xa0", " ")
    t = re.sub(r":$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def extraer_primeras_20_palabras(texto: str) -> str:
    """Recorta el texto devolviendo hasta un máximo de 20 palabras.

    Args:
        texto: Cadena original.

    Returns:
        Texto compuesto por las primeras 20 palabras.
    """
    if not texto:
        return ""
    palabras = texto.split()
    return " ".join(palabras[:20])


def es_solo_numero(texto: str) -> bool:
    """Evalúa si una cadena representa exclusivamente un número.

    Args:
        texto: Cadena a verificar.

    Returns:
        True si contiene únicamente dígitos o formato numérico simple.
    """
    t = texto.replace(".", "", 1).replace(",", "", 1).strip()
    return t.isdigit()


def main() -> None:
    """Ejecuta el flujo de extracción masiva."""
    carpeta_origen = seleccionar_carpeta()
    if not carpeta_origen:
        print("Operación cancelada.")
        return

    hojas_excluidas = [
        "criterio", "talla", "cronogram", "datos", "deuda",
        "produccion", "producción", "proveedor", "proveedores", "costo de proyecto",
        "registro", "red almenara"
    ]

    headers_codigo = [
        "código artículo", "codigo articulo", "cód. art.", "cod. ar.t",
        "cód art.", "cod. art", "cod art", "cód art", "cód. artíc.", 
        "cod. artic.", "código", "codigo", "cód.", "cod."
    ]
    
    headers_articulo = [
        "artículo", "articulos", "articulo", "artículos", "art."
    ] 
    
    headers_detalle = [
        "observación", "observacion", "detalle", "detalles", 
        "descripcion", "descripción", "observaciones", 
        "obseraciones", "detalles del servicio"
    ]

    datos_extraidos = []
    archivos_leidos_correctamente = 0

    print(f"Iniciando escaneo recursivo profundo en: {carpeta_origen} ...\n")

    for raiz, _, archivos in os.walk(carpeta_origen):
        for archivo in archivos:
            archivo_lower = archivo.lower()
            extensiones_validas = (".xlsx", ".xlsm", ".xls")
            
            if archivo_lower.endswith(extensiones_validas) and not archivo.startswith("~$"):
                ruta_completa = os.path.join(raiz, archivo)
                
                try:
                    xls = pd.ExcelFile(ruta_completa)
                    archivos_leidos_correctamente += 1
                    
                    for nombre_hoja in xls.sheet_names:
                        hoja_limpia = nombre_hoja.strip().lower()
                        if any(excluida in hoja_limpia for excluida in hojas_excluidas):
                            continue
                        
                        df = pd.read_excel(xls, sheet_name=nombre_hoja, header=None)
                        
                        cod_cols = []
                        art_cols = []
                        det_cols = []
                        
                        for _, fila in df.iterrows():
                            for col_idx, valor in enumerate(fila):
                                val_str = limpiar_encabezado(valor)
                                if not val_str: 
                                    continue
                                    
                                if val_str in headers_codigo and col_idx not in cod_cols:
                                    cod_cols.append(col_idx)
                                    
                                if val_str in headers_articulo and col_idx not in art_cols:
                                    art_cols.append(col_idx)
                                    
                                if val_str in headers_detalle and col_idx not in det_cols:
                                    det_cols.append(col_idx)
                            
                            if (art_cols or cod_cols) and det_cols:
                                best_cod = ""
                                best_art = ""
                                
                                for c_cod in cod_cols:
                                    if c_cod < len(fila):
                                        val = limpiar_texto(fila.iloc[c_cod])
                                        val_limpio = limpiar_encabezado(val)
                                        if val and val_limpio not in headers_codigo and not best_cod:
                                            best_cod = val
                                                
                                for c_art in art_cols:
                                    if c_art < len(fila):
                                        val = limpiar_texto(fila.iloc[c_art])
                                        val_limpio = limpiar_encabezado(val)
                                        if val and val_limpio not in headers_articulo:
                                            if not best_art:
                                                best_art = val
                                            elif es_solo_numero(best_art) and not es_solo_numero(val):
                                                best_art = val
                                
                                textos_detalle = []
                                for c_det in det_cols:
                                    if c_det < len(fila):
                                        val = limpiar_texto(fila.iloc[c_det])
                                        val_limpio = limpiar_encabezado(val)
                                        if val and val_limpio not in headers_detalle and val not in textos_detalle:
                                            textos_detalle.append(val)
                                
                                best_det = " | ".join(textos_detalle)
                                
                                if best_art or best_cod:
                                    det_procesado = extraer_primeras_20_palabras(best_det)
                                    if det_procesado.strip():
                                        datos_extraidos.append({
                                            "codigo": best_cod,
                                            "articulo": best_art,
                                            "detalle": det_procesado
                                        })
                except ImportError as ie:
                    if "xlrd" in str(ie):
                        print(f"[Error Crítico] Falta 'xlrd' para leer el archivo antiguo: {archivo}. Instala con: uv add xlrd")
                except Exception as e:
                    print(f"[Aviso] No se pudo procesar el archivo: {archivo}. Motivo: {e}")

    if datos_extraidos:
        df_final = pd.DataFrame(datos_extraidos)
        df_final = df_final.drop_duplicates()
        df_final = df_final[["codigo", "articulo", "detalle"]]
        df_final = df_final.sort_values(by=["articulo", "codigo"], key=lambda col: col.str.lower())
        
        archivo_salida = os.path.join(carpeta_origen, "Resultados.xlsx")
        df_final.to_excel(archivo_salida, index=False)
        
        print("\n" + "=" * 50)
        print("📊 REPORTE DE PROCESAMIENTO TOTAL RECURSIVO:")
        print(f"✔️ Total de archivos Excel analizados: {archivos_leidos_correctamente}")
        print(f"✔️ Filas útiles extraídas: {len(df_final)}")
        print(f"📂 Archivo guardado en:\n{archivo_salida}")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("No se encontraron tablas que cumplieran las condiciones.")
        print(f"Archivos analizados en total: {archivos_leidos_correctamente}")
        print("=" * 50)


if __name__ == "__main__":
    main()