# 01 - Motor de Escaneo Masivo y Benchmarking

Módulo core de escritorio de la **Sistema Cotizaciones Suite**, diseñado para procesar, limpiar y consolidar miles de cotizaciones históricas en formato Excel, generando matrices de benchmarking y permitiendo la cotización rápida con márgenes inteligentes.

---

## Capacidades y Rendimiento Probado
Este motor ha sido optimizado y validado en entornos reales de producción con cargas masivas:
* **Escaneo Concurrente:** Procesamiento de más de **900+ archivos Excel** y **2,000+ hojas válidas** en paralelo mediante hilos (`ThreadPoolExecutor`).
* **Volumen Soportado:** Extracción y cálculo fluido de más de **14,000+ filas crudas** de cotización.
* **UI Fluida (Chunking):** Renderizado de resultados por lotes mediante el *mainloop* de CustomTkinter/Tkinter, evitando congelamientos visuales bajo alto volumen de datos.
* **Búsqueda Vectorizada:** Filtrado optimizado con expresiones regulares precompiladas sobre estructuras `pandas`.
* **Caché de Variaciones:** Reutilización de taxonomías por categorías para acelerar la generación de benchmarking.

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
├── data/                     # Datasets de entrada (.xlsx, .xls), logs y reportes exportados
│   ├── debug_scan_raw.xlsx   # Reporte consolidado y limpio con el extracto de todas las filas parseadas tras la ejecución del motor.
│   ├── scan_checkpoint.json  # Caché de estado y checkpoint del escáner para reanudar sesiones o evitar el re-procesamiento de archivos no modificados.
│   └── log_errores.txt       # Registro de auditoría de hojas corruptas, celdas omitidas o fallos de lectura durante el escaneo concurrente.
├── docs/                     # Especificaciones y reportes de implementación
├── scripts/                  # Scripts auxiliares (headless y tests de búsqueda)
├── src/
│   ├── controllers/          # Orquestador del ciclo de vida y UI (AppController)
│   ├── models/               # Entidades de dominio (ScanRow, PriceStats, constants)
│   ├── services/             # Motor de escaneo, benchmarking, variaciones y cotización
│   └── views/                # Vistas modulares, controles y render por lotes
├── ARCHITECTURE.md           # Documentación técnica profunda del diseño e ingeniería
├── main.py                   # Punto de entrada principal de la aplicación
└── README.md                 # Documentación técnica del módulo
```
---

## Ejecución

Asegúrate de tener el entorno virtual del monorepo activo (.venv en la raíz), entra a este módulo y ejecuta la interfaz gráfica:
```bash
cd 01-escaneo-masivo-cotizaciones
python main.py
```
---

## Características Principales de la Interfaz

* **Selector de Directorio de Datos:** Apunta dinámicamente a la carpeta contenedora de los excels históricos.
* **Filtros por Categoría y Tokenización:** Búsqueda rápida por palabras clave o segmentación por familias de productos.
* **Calculadora Rápida Integrada:** Consulta automatizada de márgenes y precios sugeridos basados en el benchmarking consolidado.
* **Exportación y Depuración:** Generación de reportes limpios y archivos de depuración asíncronos (`debug_scan_raw.xlsx`).
