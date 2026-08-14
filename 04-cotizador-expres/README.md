# 04 - Cotizador Exprés Multiproducto

Módulo frontend y aplicación de escritorio de la suite **SistemaCotizaciones**, diseñado para la cotización ágil y comercial de requerimientos multiproducto. 

Integra en caliente el motor de búsqueda en cascada sobre los Data Lakes históricos, aplica las curvas de márgenes interpoladas y reglas de ajuste dinámico compiladas en el Módulo 03, y genera reportes comerciales en Excel (.xlsx) estructurados con bloques verticales y columnas de auditoría multilínea.

---

## Capacidades y Características Clave

* **Interfaz Gráfica Dinámica (Tkinter MVC):** Formulario modular desacoplado que permite agregar de 1 a 7 requerimientos simultáneos con menús desplegables en cascada (`Categoría` ➔ `Subproducto`).
* **Búsqueda Jerárquica en Cascada (Priority Fallback):** Consulta en memoria RAM primero el Data Lake reciente (`debug_scan_raw_recent.xlsx` ~1,800 filas 2026); si no existen registros para el arquetipo, conmuta de forma transparente al Data Lake histórico (`debug_scan_raw.xlsx` ~14,000 filas).
* **Segmentación por Bracket de Volumen:** Filtra opciones de proveedores dentro del tramo de escala comercial correspondiente ($q_{min} \le Q \le q_{max}$) con apertura total en caso de ausencia de registros.
* **Selección del Costo Más Cercano:** Identifica la cotización histórica más próxima a la cantidad solicitada ($\vert{}Q_{detectada} - Q_{solicitada}\vert{} \to \min$) para aplicar los márgenes sobre un costo de taller real.
* **Consolidación Multilínea por Proveedor:** Deduplica opciones técnicas idénticas (mismo proveedor y detalle) agrupando sus variaciones de cantidad, costo y precio histórico en celdas consolidadas con saltos de línea (`\n---------------\n`).
* **Exportación Maquetada en Excel:** Genera propuestas comerciales con cabeceras institucionales amarillas y tres columnas de control gris a la derecha (`Cantidad`, `Costo Prov`, `Ref Real 2026`) para verificación visual en $\pm 2.00$ PEN.

---

## Flujo de Procesamiento y Cotización

```text
[ Formulario UI: Selección de Productos y Cantidades ]
                       │
                       ▼
[ AppController: Orquestación en Hilo Asíncrono (daemon) ]
                       │
                       ▼
[ DataEngine: Búsqueda en Cascada (Recent ➔ Historic) ]
                       │
                       ▼
[ Bracket de Volumen + Selección de Costo Más Cercano ]
                       │
                       ▼
[ Recálculo Financiero: Margen Base + Reglas de Ajuste Dinámico ]
                       │
                       ▼
[ Agrupamiento Multilínea: (Proveedor + Detalle Técnico) ]
                       │
                       ▼
[ ExcelExporter: Generación de Libro .xlsx en data/output/ ]
```

---

## Tecnologías y Dependencias

* **Python 3.12+**
* **Tkinter & TTK:** Interfaz gráfica de escritorio nativa con estilos `clam`.
* **Pandas & NumPy:** Filtrado vectorial de DataFrames y agrupamiento de proveedores.
* **Openpyxl:** Construcción programática de libros de Excel con estilos de celda, anchos dinámicos y formatos de moneda (`"S/." #,##0.00`).
* **Pillow (PIL):** Procesamiento y anclaje de imágenes referenciales en celdas de Excel.

### Integración Modular con Módulo 03

El módulo resuelve dinámicamente las rutas de configuración hacia `03-motor-ajustes-dinamicos/config/`:

* `matrices_margen.json`: Consulta de escalas de volumen y nombres comerciales.
* `ajustes_margen.json`: Inyección de reglas condicionales por descripción, acabados y tramos.

---

## Estructura del Módulo

```text
04-cotizador-expres/
├── data/
│   ├── input/                                   # Datasets de entrada para la búsqueda jerárquica.
│   │   ├── debug_scan_raw_recent.xlsx           # PRIORIDAD 1: Data Lake de cotizaciones recientes (~1,800 filas 2026).
│   │   └── debug_scan_raw.xlsx                  # FALLBACK: Data Lake histórico consolidado (~14,000 filas).
│   └── output/                                  # Directorio de exportación de cotizaciones generadas.
│       └── [Cant]_[Prod1], [Cant]_[Prod2].xlsx  # Cotizaciones comerciales maquetadas.
├── src/
│   ├── controllers/
│   │   └── app_controller.py                    # Controlador MVC y orquestador asíncrono en segundo plano.
│   ├── services/
│   │   ├── data_engine.py                       # Motor de búsqueda en cascada, brackets y agrupación multilínea.
│   │   └── excel_exporter.py                    # Generador de reportes Excel con bloques y columnas de control.
│   └── views/
│       └── cotizador_view.py                    # Interfaz gráfica modular de usuario (Tkinter).
├── main.py                                      # Punto de entrada de la aplicación de escritorio.
└── README.md                                    # Documentación técnica del módulo.
```

---

## Ejecución

Asegúrate de contar con los archivos `debug_scan_raw_recent.xlsx` o `debug_scan_raw.xlsx` en `data/input/`, activa el entorno virtual del monorepo (`.venv`) y ejecuta:
```bash
python 04-cotizador-expres/main.py
```

---

## Características de la Propuesta Generada (Excel)

* **Bloques Verticales:** Cada ítem solicitado genera una sección independiente con título institucional azul.
* **Zona Comercial (Columnas A - I | Amarillo):** `N°`, `Proveedor`, `Producto`, `Foto`, `Cant.`, `Costo uni. NO IGV (S/.)`, `Tiempo Entrega`, `Detalle`, `Costo TOTAL NO IGV (S/.)`.
* **Zona de Control y Auditoría (Columnas J - L | Gris):**
* `Cantidad`: Muestra las cantidades con las que se cotizó históricamente en formato multilínea.
* `Costo Prov`: Costo original del taller/proveedor.
* `Ref Real 2026`: Precio cliente histórico para validación en tolerancia $\pm 2.00$ PEN.