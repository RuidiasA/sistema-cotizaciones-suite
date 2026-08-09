# Architecture

## 1. Resumen del Sistema y Propósito

El proyecto implementa un sistema de gestión de cotizaciones y análisis masivo de archivos Excel orientado a extraer productos, calcular márgenes y construir una base de conocimiento comercial para cotización rápida y benchmarking. La aplicación está pensada para trabajar sobre carpetas con grandes volúmenes de archivos de Excel, detectar tablas válidas de forma automática, normalizar descripciones de productos y devolver resultados procesados en una interfaz de escritorio.

El valor funcional del sistema se concentra en cuatro capacidades:

1. Procesamiento de datos masivos desde una carpeta de Excel con escaneo recursivo.
2. Lectura inteligente de hojas y detección de tablas sin estructura uniforme.
3. Motor de cotización basado en márgenes históricos, categorías y benchmarking por arquetipos.
4. Visualización operativa de resultados en una UI de escritorio con controles para escaneo, benchmarking, exportación y cotización rápida.

En términos de negocio, el sistema resuelve el problema de analizar cotizaciones históricas dispersas y heterogéneas para transformarlas en información utilizable: permite encontrar productos por familias semánticas, calcular márgenes por volumen y producir reportes exportables a Excel para toma de decisiones.

## 2. Arquitectura de Software y Patrón de Diseño

La aplicación sigue una arquitectura modular con patrón MVC práctico, reforzado por una capa de servicios independientes.

- **Modelos**: encapsulan la estructura de los datos de negocio y los contenedores del procesamiento.
- **Servicios**: contienen la lógica pesada de negocio, parsing, normalización textual, escaneo Excel, agrupación por arquetipos y cálculo de cotizaciones.
- **Controlador**: coordina UI, servicios, hilos, cancelación y exportación.
- **Vistas**: implementan la interfaz gráfica con `customtkinter` y `ttk`, sin lógica de negocio crítica.

### Estructura de directorios

#### Raíz del proyecto

- `main.py`: punto de entrada de la aplicación de escritorio.
- `requirements.txt`: dependencias runtime.
- `busqueda_productos.py`: script independiente de exploración y extracción de productos desde Excel.
- `scripts/headless_scan_check.py`: verificación rápida sin UI del motor de escaneo.
- `tools/run_scanner.py`: ejecutor headless para escaneo de carpeta.
- `docs/`: documentación funcional y técnica del proyecto.

#### `src/controllers`

- `app_controller.py`: orquestador central del sistema.
- Responsabilidad: inicializar servicios, levantar la vista principal, coordinar escaneo, benchmarking, cotización y exportación.
- Es la capa que conecta la interacción del usuario con la lógica de negocio.

#### `src/models`

- `constants.py`: catálogo de categorías, exclusiones, tags y folder por defecto.
- `entities.py`: dataclasses de dominio y contenedores de resultados.
- Responsabilidad: representar la estructura de datos sin acoplarla a la UI ni a la persistencia externa.

#### `src/services`

- `variation_service.py`: gestión de categorías, tags, exclusiones y matching semántico.
- `excel_scan_service.py`: motor de lectura, detección de tablas, extracción de filas y generación de reportes.
- `benchmarking_service.py`: construcción de arquetipos, agrupación por tier y matriz de benchmarking.
- `quote_service.py`: cálculo de cotización rápida con margen aplicado.
- `text_utils.py`: limpieza, normalización, extracción de arquetipos y filtros de ruido.
- Responsabilidad: ejecutar la lógica compleja del dominio sin depender de widgets ni de eventos de interfaz.

#### `src/views`

- `main_view.py`: ventana principal y composición de la interfaz.
- `scan_controls.py`: panel lateral de búsqueda, categoría, escaneo, benchmarking y exportación.
- `results_view.py`: tabla de resultados, tarjetas KPI y consola de logs.
- `quote_view.py`: formulario rápido para calcular cotizaciones.
- Responsabilidad: presentar información y enviar eventos al controlador.

## 3. Flujo de Datos y Comunicación entre Clases

### 3.1 Arranque de la aplicación

El arranque es directo:

- `main.py` instancia `AppController`.
- `AppController` crea los servicios de dominio y la vista principal.
- `MainView` ensambla `ScanControls`, `QuoteView` y `ResultsView`.
- La UI entra en el loop principal con `mainloop()`.

### 3.2 Flujo de escaneo de cotizaciones

1. El usuario selecciona carpeta, categoría y palabra clave desde `ScanControls`.
2. `ScanControls` invoca `AppController.handle_scan(folder, categoria, keyword)`.
3. El controlador:
   - limpia el estado de cancelación,
   - actualiza la UI a modo procesamiento,
   - deshabilita exportación,
   - construye un `search_pack` con `VariationService`.
4. `AppController` delega el escaneo a `ExcelScanService.scan_folder(...)` usando `ThreadPoolExecutor` para no bloquear la interfaz.
5. `ExcelScanService`:
   - busca archivos `.xlsx` y `.xls` de forma recursiva,
   - omite archivos temporales y archivos generados por debug,
   - recupera checkpoints previos si existen,
   - procesa varios archivos en paralelo,
   - detecta hojas válidas,
   - localiza cabeceras,
   - normaliza valores,
   - extrae cantidad, costo proveedor, precio cliente y margen,
   - construye `ScanRow` y `FileScanReport`.
6. Cuando el futuro termina, `AppController._on_scan_done(...)` consolida los reportes:
   - agrega logs por archivo,
   - suma estadísticas (`PriceStats`),
   - ordena el resultado global por artículo,
   - actualiza `ResultsView` con las filas finales,
   - guarda `self._last_scan_rows` para reutilizarlas en benchmarking.
7. Si la exportación de debug está activa, se genera `debug_scan_raw.xlsx` con las filas crudas del último escaneo.

### 3.3 Flujo de benchmarking

1. El usuario presiona `Generar Benchmarking` o cambia la categoría después de tener datos en memoria.
2. `ScanControls` invoca `AppController.handle_benchmarking(categoria)`.
3. El controlador filtra `self._last_scan_rows` con `VariationService.matches_category(...)`.
4. Se ejecuta `BenchmarkingService.generar_benchmarking(...)` en segundo plano.
5. El servicio:
   - descarta filas inválidas,
   - excluye servicios/logística,
   - extrae arquetipos con `extraer_arquetipo(...)`,
   - clasifica por tier de cantidad,
   - agrupa con pandas,
   - infiere márgenes faltantes,
   - calcula confianza,
   - devuelve una `BenchmarkingMatrix`.
6. `AppController._on_benchmarking_done(...)` convierte la matriz en filas de vista con `_benchmarking_rows_from_matrix(...)`.
7. `ResultsView` recibe esas filas y las muestra como una tabla de benchmarking con alternancia visual por bloques.
8. Se habilita la exportación a Excel.

### 3.4 Flujo de cotización rápida

1. El usuario ingresa producto, cantidad y costo proveedor en `QuoteView`.
2. `QuoteView` valida los tipos y llama a `AppController.handle_quote(...)`.
3. El controlador intenta reconocer el producto como arquetipo mediante `BenchmarkingService.extraer_arquetipo(...)`.
4. Si hay una matriz de benchmarking cargada y el arquetipo existe, se usa el margen del tier correspondiente.
5. Si no existe benchmarking aplicable, se usa `QuoteService.create_quote(...)` con `PriceStats` y un margen de respaldo.
6. `ResultsView` muestra el resultado en las tarjetas KPI y la UI actualiza el log si el producto fue reconocido por benchmarking.

### 3.5 Eventos clave del sistema

- Inicio de escaneo de carpeta.
- Cancelación del escaneo por señal de interrupción.
- Generación de benchmarking desde resultados ya cargados.
- Cambio de categoría con reutilización de datos en memoria.
- Exportación de benchmarking a Excel.
- Cotización rápida desde formulario lateral.

## 4. Catálogo de Componentes y Clases Principales

### 4.1 `AppController`

Archivo: `src/controllers/app_controller.py`

Responsabilidad: coordinar toda la aplicación.

Métodos centrales:

- `__init__()`: instancia `VariationService`, `ExcelScanService`, `QuoteService`, `BenchmarkingService` y la UI principal.
- `run()`: inicia el loop de la interfaz.
- `handle_scan(folder, categoria, keyword)`: prepara el escaneo y lanza el procesamiento en background.
- `handle_cancel()`: activa el evento de detención.
- `_on_scan_done(future)`: consume resultados del escaneo y actualiza la UI.
- `handle_quote(product_name, cantidad, precio_prov)`: calcula una cotización rápida.
- `handle_benchmarking(categoria)`: genera benchmarking a partir del último escaneo.
- `_on_benchmarking_done(future)`: renderiza la matriz de benchmarking en la UI.
- `handle_export_benchmarking(folder_path)`: exporta la matriz a Excel.
- `_export_benchmarking_by_blocks(...)`: escribe el archivo Excel segmentado por bloques.
- `_benchmarking_rows_from_matrix(...)`: transforma la matriz a filas de tabla.

Entradas: folder, categoría, keyword, producto, cantidad, precio proveedor.

Salidas: actualización de UI, matrices de benchmarking, reportes Excel y logs.

Dependencias directas: `VariationService`, `ExcelScanService`, `QuoteService`, `BenchmarkingService`, `MainView`, `ScanRow`, `PriceStats`, `BenchmarkingMatrix`.

### 4.2 `VariationService`

Archivo: `src/services/variation_service.py`

Responsabilidad: resolver categorías y paquetes de búsqueda semántica.

Métodos centrales:

- `get_categories()`: devuelve la lista de macrocategorías y subcategorías formateadas.
- `get_variations(categoria, keyword)`: devuelve tags y exclusiones del clúster correspondiente.
- `get_global_search_pack()`: construye un paquete global de búsqueda sin exclusiones por categoría.
- `matches_category(categoria, texto_producto)`: valida si un texto pertenece a una categoría.
- `is_known_product(product_name)`: detecta si un producto coincide con alguna variación conocida.

Entradas: categoría, keyword, texto de producto.

Salidas: search packs, booleanos de coincidencia y listas de categorías.

Dependencias directas: `normalizar_texto` y `MACRO_CATEGORIAS`.

### 4.3 `ExcelScanService`

Archivo: `src/services/excel_scan_service.py`

Responsabilidad: escaneo de archivos Excel, detección de tablas y extracción de filas de cotización.

Métodos centrales:

- `scan_folder(folder_path, search_pack, stop_event)`: orquesta el escaneo recursivo de una carpeta.
- `scan_file(file_path, search_pack, raw_records=None)`: procesa un archivo individual y devuelve un `FileScanReport`.
- `_list_excel_files(folder_path)`: localiza archivos Excel válidos en subcarpetas.
- `_open_workbook_data_only(file_path)`: abre libros compatibles con `openpyxl` en modo solo lectura y solo valores.
- `_read_sheet_data_only(...)`: convierte una hoja a `DataFrame` desde valores ya resueltos.
- `_detect_header_row(df_check)`: identifica la fila de cabeceras por heurística.
- `_cumple_busqueda_tokenizada(fila, search_pack)`: decide si una fila pasa el filtro semántico.
- `_process_rows(...)`: extrae filas válidas, calcula margen y llena `ScanRow`.
- `get_last_raw_scan_dataframe()`: expone el DataFrame crudo del último escaneo.
- `export_raw_scan_dataframe(df, output_path)`: escribe el debug raw a Excel.

Entradas: carpeta, archivo, search pack, evento de cancelación.

Salidas: `FileScanReport`, `PriceStats`, `ScanRow`, archivo `debug_scan_raw.xlsx` y `scan_checkpoint.json`.

Dependencias directas: `pandas`, `openpyxl`, `ScanRow`, `FileScanReport`, `PriceStats`, `text_utils`.

### 4.4 `BenchmarkingService`

Archivo: `src/services/benchmarking_service.py`

Responsabilidad: construir benchmarking por arquetipos y tiers de cantidad.

Métodos centrales:

- `extraer_arquetipo(fila_detalle, keyword='')`: limpia la descripción y deriva un arquetipo comercial.
- `es_servicio_excluido(articulo)`: filtra servicios/logística.
- `generar_benchmarking(scan_rows, categoria, keyword='')`: agrupa datos, calcula márgenes y genera `BenchmarkingMatrix`.
- `_inferir_margenes(...)`: completa tiers faltantes respetando monotonicidad y piso dinámico.
- `_weighted_avg(...)`: calcula promedios ponderados.
- `calcular_confianza(casos_totales)`: estima nivel de confianza del arquetipo.
- `_tier_para_cantidad(cantidad)`: clasifica en 100, 500 o 1000.

Entradas: filas escaneadas, categoría, keyword.

Salidas: `BenchmarkingMatrix` con `ArchetypeData`.

Dependencias directas: `pandas`, `ScanRow`, `ArchetypeData`, `BenchmarkingMatrix`, utilidades de texto.

### 4.5 `QuoteService`

Archivo: `src/services/quote_service.py`

Responsabilidad: cálculo de cotización básica a partir de una referencia de costo y un margen.

Método central:

- `create_quote(product_name, cantidad, precio_prov, stats, margen_defecto=35.0)`: calcula margen, precio unitario y total.

Entradas: nombre de producto, cantidad, costo proveedor, estadísticas agregadas.

Salidas: diccionario con `margen`, `precio_unit` y `total`.

Dependencias directas: `PriceStats`.

### 4.6 `PriceStats`

Archivo: `src/models/entities.py`

Responsabilidad: acumular márgenes por rango de cantidad.

Métodos centrales:

- `add_margin(cantidad, margen)`: acumula el margen en el tier correspondiente.
- `promedio_para_cantidad(cantidad, margen_defecto=35.0)`: calcula el promedio para 1000, 500 o resto.
- `merge(other)`: fusiona estadísticas parciales.

Entradas: cantidad y margen.

Salidas: promedios por tier.

### 4.7 `ScanRow`

Archivo: `src/models/entities.py`

Responsabilidad: representar una fila normalizada del escaneo.

Campos principales:

- `fila_id`
- `articulo`
- `cantidad`
- `precio_prov`
- `precio_cli`
- `margen`
- `motivo`
- `arquetipo`
- `margen_fila`

### 4.8 `FileScanReport`

Archivo: `src/models/entities.py`

Responsabilidad: contener el resultado de un archivo procesado.

Campos principales:

- `file_name`
- `sheet_name`
- `matched_rows`
- `failed_rows`
- `stats`
- `error_message`

### 4.9 `ArchetypeData`

Archivo: `src/models/entities.py`

Responsabilidad: representar un arquetipo con métricas por tier.

Campos principales:

- `nombre_arquetipo`
- `categoria`
- `margen_tier_100`
- `margen_tier_500`
- `margen_tier_1000`
- `casos_tier_100`
- `casos_tier_500`
- `casos_tier_1000`
- `costo_avg_100`
- `costo_avg_500`
- `costo_avg_1000`
- `precio_avg_100`
- `precio_avg_500`
- `precio_avg_1000`
- `actualizado_en`
- `confianza_general`

### 4.10 `BenchmarkingMatrix`

Archivo: `src/models/entities.py`

Responsabilidad: agrupar los arquetipos de una categoría completa.

Métodos centrales:

- `get_arquetipo_por_nombre(nombre)`: búsqueda exacta normalizada.
- `get_margen_para_cantidad(nombre_arquetipo, cantidad)`: devuelve el margen sugerido por tier.

### 4.11 Vistas principales

#### `MainView`

Archivo: `src/views/main_view.py`

Responsabilidad: componer la ventana principal y actuar como fachada visual.

Métodos clave:

- `set_scanning_state(is_scanning)`
- `set_benchmarking_state(is_benchmarking)`
- `enable_export(enabled)`
- `set_status(text)`
- `clear_results()`
- `clear_quote_cards()`
- `append_log(text)`
- `add_rows(rows)`
- `set_stats_text(text)`
- `show_quote_result(res, known)`
- `update_quote_cards(margen, precio_unit, total)`

#### `ScanControls`

Archivo: `src/views/scan_controls.py`

Responsabilidad: exponer la interacción operativa del usuario.

Funciones clave:

- selección de carpeta,
- selección de categoría,
- entrada de keyword,
- inicio de escaneo,
- cancelación,
- generación de benchmarking,
- exportación.

#### `ResultsView`

Archivo: `src/views/results_view.py`

Responsabilidad: renderizar KPIs, tabla de resultados y logs.

Métodos clave:

- `clear()`
- `append_log(text)`
- `add_rows(rows)`
- `set_group_size(size)`
- `set_stats_text(text)`
- `update_quote_cards(margen, precio_unit, total)`

#### `QuoteView`

Archivo: `src/views/quote_view.py`

Responsabilidad: capturar el formulario de cotización rápida.

Métodos clave:

- `_handle_quote()`
- `_handle_clear()`
- `show_result(result, known_product)`

## 5. Manejo de Datos Masivos y Rendimiento

El sistema está diseñado para manejar volúmenes altos de archivos y filas, incluyendo escenarios de más de 14 mil registros, con varias medidas de rendimiento.

### 5.1 Estrategia de lectura masiva

- El escaneo recorre la carpeta de forma recursiva con `Path.rglob()`.
- Se filtran archivos temporales de Excel y archivos generados por el propio motor.
- Se procesa cada archivo en paralelo con un `ThreadPoolExecutor` interno limitado a `min(6, cpu_count)`.
- El controlador ejecuta el trabajo pesado fuera del hilo principal de la UI.

### 5.2 Lectura eficiente de Excel

- Se usa `pandas.ExcelFile` para inspeccionar hojas.
- Cuando es posible, se abre un workbook con `openpyxl.load_workbook(..., data_only=True, read_only=True)`.
- Se lee un pequeño bloque inicial para detectar la fila de cabeceras antes de cargar toda la hoja.
- Se trabaja con `DataFrame` para normalizar, filtrar y extraer columnas de forma vectorizada cuando es viable.

### 5.3 Normalización y detección semántica

- `text_utils.normalizar_texto()` elimina tildes, signos y ruido ortográfico.
- Las búsquedas se hacen con expresiones regulares compiladas una vez por `search_pack`.
- Se usan límites de palabra para reducir falsos positivos.
- Los campos relevantes se reconstruyen con columnas de detalle, artículo y código, cuando existen.

### 5.4 Robustez ante datos sucios

- Se detectan cantidades inválidas, márgenes nulos, precios incoherentes y duplicados.
- Se registran filas rechazadas con un motivo concreto.
- Se aplica un techo de margen para evitar outliers extremos.
- Se excluyen servicios y logística por palabras clave.

### 5.5 Persistencia de soporte operativo

El motor no usa base de datos. La persistencia auxiliar es archivo local:

- `scan_checkpoint.json`: lista de archivos ya procesados.
- `debug_scan_raw.xlsx`: exportación cruda del último escaneo.
- `log_errores.txt`: bitácora de fallos por archivo.

### 5.6 Benchmarking y agregación

- Los márgenes se agrupan por arquetipo y tier de cantidad.
- Se usan `groupby`, `value_counts` y agregaciones de pandas para consolidar resultados.
- Se infieren tiers faltantes con un piso dinámico y reglas de monotonicidad.
- La exportación final a Excel se produce con `openpyxl` y formato visual por bloques.

## 6. Diagrama de Módulos

```mermaid
graph TD
    A[main.py] --> B[AppController]
    B --> C[MainView]
    C --> D[ScanControls]
    C --> E[QuoteView]
    C --> F[ResultsView]

    B --> G[VariationService]
    B --> H[ExcelScanService]
    B --> I[BenchmarkingService]
    B --> J[QuoteService]

    G --> K[text_utils.py]
    H --> K
    I --> K
    J --> L[PriceStats]

    H --> M[FileScanReport]
    H --> N[ScanRow]
    H --> O[PriceStats]
    I --> P[BenchmarkingMatrix]
    I --> Q[ArchetypeData]
    B --> P
    B --> Q
    B --> N

    D --> B
    E --> B
    F --> B

    R[constants.py] --> G
    R --> H
    R --> B

    S[busqueda_productos.py] -. script independiente .-> T[Excel consolidado]
    U[tools/run_scanner.py] -. smoke/headless .-> H
    V[scripts/headless_scan_check.py] -. smoke/headless .-> H
```

## 7. Observaciones Técnicas

- El sistema está desacoplado de cualquier backend web o base de datos; toda la operación vive en memoria y archivos Excel.
- La UI está construida con `customtkinter`, mientras que el render de tabla se apoya en `ttk.Treeview`.
- El controlador es el único componente que conoce simultáneamente la UI y la lógica de negocio.
- Los servicios son relativamente puros y reutilizables, lo que permite ejecutar el motor de escaneo de forma headless.
- El proyecto ya incluye scripts auxiliares para comprobación manual y extracción consolidada, lo que confirma que el núcleo del sistema es el procesamiento de Excel y no la interfaz.

## 8. Resumen Ejecutivo de Arquitectura

La arquitectura final es una variante modular de MVC con fuerte separación entre interfaz y procesamiento. La capa de servicios concentra la inteligencia del dominio: búsqueda semántica, lectura de Excel, extracción de filas, cálculo de márgenes, benchmarking y exportación. El controlador administra la experiencia del usuario, la concurrencia y el paso de datos entre capas. Las vistas se limitan a representar estado y emitir eventos.

El diseño es adecuado para escenarios de alto volumen porque:

- procesa en background,
- compila reglas de búsqueda,
- usa lectura selectiva de Excel,
- conserva checkpoints,
- y evita bloquear la UI mientras analiza datos masivos.

La consecuencia práctica es un sistema de escritorio orientado a cotización y benchmarking que puede trabajar sobre históricos amplios sin depender de infraestructura externa.
