import os
import re
import pandas as pd
from pathlib import Path


def limpiar_texto_cabecera(val):
    if pd.isna(val):
        return ""
    text = str(val).lower().strip()
    text = text.replace('á', 'a').replace('é', 'e').replace(
        'í', 'i').replace('ó', 'o').replace('ú', 'u')
    return text


def es_cabecera_clave(val):
    text_clean = limpiar_texto_cabecera(val)
    # Detecta tanto la columna de nombres como la de codigos para geolocalizar la tabla
    palabras_art = ['articulo', 'art.', 'art',
                    'articulo / descripcion', 'articulo/descripcion']
    palabras_cod = ['cod. artic.', 'cod. articulo',
                    'codigo articulo', 'cod.art.', 'cod.art', 'cod. partic.']

    if text_clean in palabras_art:
        return "ART"
    if text_clean in palabras_cod:
        return "COD"
    return None


def ejecutar_extractor_maestro():
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    carpeta_cotizaciones = BASE_DIR / "data" / "cotizaciones-pasadas"
    ruta_salida = BASE_DIR / "data" / "mapeo_productos_pasados.xlsx"

    if not carpeta_cotizaciones.exists():
        print(f"[ERROR] No se encontro la carpeta de origen en: {carpeta_cotizaciones}")
        return

    print("==================================================")
    print("INICIANDO EXTRACCION DINAMICA DE ARTICULOS")
    print("==================================================")

    archivos = [f for f in os.listdir(
        carpeta_cotizaciones) if f.endswith(('.xlsx', '.xls'))]
    total_archivos = len(archivos)

    print(f"[INFO] Se detectaron {total_archivos} archivos para procesar.")

    productos_unicos = set()
    total_filas_articulos = 0
    archivos_procesados = 0

    for nombre_archivo in archivos:
        ruta_archivo = os.path.join(carpeta_cotizaciones, nombre_archivo)
        archivos_procesados += 1

        print(
            f"[PROCESANDO] Archivo {archivos_procesados}/{total_archivos}: {nombre_archivo}")

        try:
            dict_hojas = pd.read_excel(
                ruta_archivo, sheet_name=None, header=None)

            for nombre_hoja, df_hoja in dict_hojas.items():
                if df_hoja.empty:
                    continue

                state = 0  # 0 = Buscando Tabla, 1 = Extrayendo
                idx_cod = None
                idx_art = None
                filas_tabla_actual = 0

                for idx, row in df_hoja.iterrows():
                    columnas_disponibles = min(8, len(row))
                    row_sliced = row.iloc[:columnas_disponibles]

                    if state == 0:
                        # Escaneo horizontal de las primeras 8 columnas buscando el par de cabeceras
                        for col_idx in range(columnas_disponibles):
                            tipo_deteccion = es_cabecera_clave(
                                row_sliced.iloc[col_idx])

                            if tipo_deteccion == "ART":
                                idx_art = col_idx
                                idx_cod = col_idx - 1 if col_idx > 0 else col_idx
                                state = 1
                                filas_tabla_actual = 0
                                break
                            elif tipo_deteccion == "COD":
                                idx_cod = col_idx
                                idx_art = col_idx + 1 if col_idx + \
                                    1 < len(row) else col_idx
                                state = 1
                                filas_tabla_actual = 0
                                break

                    elif state == 1:
                        # Extraemos los valores de ambas columnas de control
                        val_cod = row.iloc[idx_cod] if idx_cod < len(
                            row) else None
                        val_art = row.iloc[idx_art] if idx_art < len(
                            row) else None

                        str_cod = str(val_cod).strip(
                        ) if not pd.isna(val_cod) else ""
                        str_art = str(val_art).strip(
                        ) if not pd.isna(val_art) else ""

                        # La tabla termina estrictamente si ambas celdas estan vacias
                        if str_cod == "" and str_art == "":
                            state = 0
                            if filas_tabla_actual > 0:
                                print(
                                    f"  --> Tabla detectada (Columnas {idx_cod+1}-{idx_art+1}) en hoja '{nombre_hoja}'. Filas: {filas_tabla_actual}")
                            idx_cod = None
                            idx_art = None
                        # O si nos topamos con otra cabecera de tabla apilada abajo
                        elif es_cabecera_clave(val_cod) or es_cabecera_clave(val_art):
                            state = 0
                            if filas_tabla_actual > 0:
                                print(
                                    f"  --> Tabla detectada (Columnas {idx_cod+1}-{idx_art+1}) en hoja '{nombre_hoja}'. Filas: {filas_tabla_actual}")
                            idx_cod = None
                            idx_art = None
                        else:
                            # Regla de seleccion elistica para celdas combinadas o desplazadas
                            if str_art != "":
                                nombre_candidato = str_art
                            else:
                                nombre_candidato = str_cod

                            # Limpieza y formateo del producto detectado
                            nombre_limpio = re.sub(
                                r'\s+', ' ', nombre_candidato).strip().upper()
                            nombre_limpio = nombre_limpio.replace(
                                '"', '').replace("'", "")

                            # Validamos que no estemos guardando accidentalmente texto basura o de cabecera
                            if nombre_limpio and not es_cabecera_clave(nombre_limpio):
                                # Evitamos codigos puros de formato de cotizacion comun
                                if not re.match(r'^[A-Z]{2,4}-\d{3,5}$', nombre_limpio):
                                    productos_unicos.add(nombre_limpio)
                                    filas_tabla_actual += 1
                                    total_filas_articulos += 1

                if state == 1 and filas_tabla_actual > 0:
                    print(
                        f"  --> Tabla detectada (Columnas {idx_cod+1}-{idx_art+1}) en hoja '{nombre_hoja}'. Filas: {filas_tabla_actual}")

        except Exception as e:
            print(
                f"[RECHAZADO] No se pudo leer el archivo {nombre_archivo}. Motivo: {str(e)}")

    print("\n[INFO] Generando archivo de salida sin duplicados...")
    df_salida = pd.DataFrame(sorted(list(productos_unicos)), columns=[
                             "Producto Normalizado"])

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    df_salida.to_excel(ruta_salida, index=False)

    print("==================================================")
    print("PROCESO COMPLETADO")
    print(f"Total de archivos procesados: {archivos_procesados}")
    print(
        f"Total de filas validas de articulos leidas: {total_filas_articulos}")
    print(f"Total de productos unicos detectados: {len(productos_unicos)}")
    print(f"Archivo maestro guardado en: {ruta_salida}")
    print("==================================================")


if __name__ == "__main__":
    ejecutar_extractor_maestro()
