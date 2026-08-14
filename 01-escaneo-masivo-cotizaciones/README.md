# 01 - Motor de Escaneo Masivo y Benchmarking

Módulo core de la **SistemaCotizaciones Suite**, diseñado para procesar, limpiar y consolidar miles de cotizaciones históricas en formato Excel, generando la base del Data Lake (`debug_scan_raw.xlsx`), extrayendo catálogos de artículos únicos y permitiendo la consulta rápida mediante benchmarking.

---

## Capacidades y Rendimiento Probado

Este motor ha sido optimizado y validado en entornos reales de producción con cargas masivas:
* **Escaneo Concurrente:** Procesamiento de más de **908+ archivos Excel** y **2,000+ hojas válidas** en paralelo mediante hilos (`ThreadPoolExecutor`).
* **Volumen Soportado:** Extracción y cálculo fluido de más de **14,000+ filas crudas** y mapeo de **1,220 productos únicos**.
* **UI Fluida y Cancelación Asíncrona:** Renderizado incremental por lotes (`after()`) que evita congelamientos en CustomTkinter y permite interrupción instantánea en caliente (`stop_event.is_set()`).
* **Búsqueda Vectorizada y Caché de Variaciones:** Búsquedas sobre estructuras `pandas` con expresiones regulares precompiladas y almacenamiento en memoria RAM de tokens normalizados en `variation_service.py`.
* **Crawl y Parsing de Hojas:** Detección de tablas sin importar celdas desalineadas o combinadas.

---

## Características Principales de la Interfaz

* **Selector de Directorio de Datos:** Apunta dinámicamente a la carpeta contenedora de los excels históricos.
* **Filtros por Categoría y Tokenización:** Búsqueda rápida por palabras clave o segmentación por familias de productos.
* **Calculadora Rápida Integrada:** Consulta automatizada de márgenes y precios sugeridos basados en el benchmarking consolidado.
* **Exportación y Depuración Asíncrona:** Generación de reportes limpios (`debug_scan_raw.xlsx`), registro de errores de lectura (`log_errores.txt`) y checkpoints de sesión (`scan_checkpoint.json`).

---

## Tecnologías y Dependencias

* **Python 3.12+**
* **CustomTkinter:** Interfaz gráfica moderna con modo oscuro nativo.
* **Pandas & NumPy:** Procesamiento y vectorización de datos tabulares.
* **Openpyxl & xlrd:** Lectura robusta de libros de Excel modernos (`.xlsx`) y legados (`.xls`).

---

## Estructura del Módulo

```text
01-escaneo-masivo-cotizaciones/
├── data/                               # Datasets de entrada (.xlsx, .xls), logs y reportes exportados.
│   ├── cotizaciones-pasadas/           # Directorio fuente de archivos Excel históricos.
│   │   ├── debug_scan_raw.xlsx         # Reporte consolidado y limpio con el extracto de todas las filas parseadas tras la ejecución del motor.
│   │   ├── log_errores.txt             # Registro de auditoría de hojas corruptas, celdas omitidas o fallos de lectura durante el escaneo concurrente.
│   │   └── scan_checkpoint.json        # Caché de estado y checkpoint del escáner para reanudar sesiones o evitar el re-procesamiento de archivos no modificados.
│   ├── cotizaciones-recientes/         # Directorio fuente de archivos Excel recientes.
│   ├── mapeo_productos_pasados.xlsx    # Catálogo consolidado de productos únicos extraídos del histórico de cotizaciones pasadas.
│   └── mapeo_productos_recientes.xlsx  # Catálogo de 1,220 productos únicos sin duplicados detectados en el ciclo reciente.
├── docs/                               # Especificaciones y reportes de implementación.
├── scripts/                            # Scripts de utilidad e ingesta ETL.
│   ├── busqueda_productos.py           # Test de búsqueda por tokens sobre el Data Lake.
│   ├── extract_articles.py             # Crawler dinámico para extracción de artículos únicos.
│   └── headless_scan_check.py          # Verificación rápida de estado por línea de comandos.
├── src/
│   ├── controllers/                    # Orquestador del ciclo de vida y UI (AppController: handle_scan, handle_cancel, _on_scan_done).
│   ├── models/                         # Entidades de dominio (ScanRow, PriceStats, constants).
│   ├── services/                       # Motor de escaneo (excel_scan_service), benchmarking (benchmarking_service) y variaciones (variation_service).
│   └── views/                          # Vistas modulares, controles y render por lotes (results_view).
├── ARCHITECTURE.md                     # Documentación técnica del diseño de arquitectura.
├── main.py                             # Punto de entrada de la interfaz gráfica.
└── README.md                           # Documentación técnica del módulo.
```

---

## Ejecución

### 1. Interfaz Gráfica (UI Desktop)

Asegúrate de tener el entorno virtual del monorepo activo (`.venv` en la raíz) y ejecuta:
```bash
python 01-escaneo-masivo-cotizaciones/main.py
```

### 2. Extractor Dinámico de Artículos Únicos (CLI)

Para re-escanear las cotizaciones y actualizar el catálogo de productos unificados:
```bash
python 01-escaneo-masivo-cotizaciones/scripts/extract_articles.py
```

---

## Métricas de Desempeño

* **Archivos Procesados:** Más de 908+ archivos Excel concurrentes.
* **Hojas Válidas Indexadas:** Más de 2,000+ pestañas sin bloqueo de UI.
* **Filas Crudas Consolidadas:** 14,000+ registros históricos.
* **Productos Únicos Mapeados:** 1,220 artículos comerciales.