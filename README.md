# Sistema Cotizaciones Suite (COMPIPRO / COMPINA)

Suite de automatización y procesamiento masivo de cotizaciones desarrollada para optimizar el flujo comercial, reduciendo el tiempo de generación de cotizaciones de **3-4 horas manuales** a procesos automatizados de alta velocidad. Este monorepo recopila el trabajo de ingeniería realizado durante las prácticas preprofesionales en **COMPINA / COMPIPRO**.

---

## Contexto del Problema y Fases del Proyecto
La empresa manejaba un histórico masivo de más de **1000+ archivos Excel** de cotizaciones (desde antes de 2010 hasta 2026). Cada libro contenía múltiples hojas con estructuras altamente irregulares: celdas combinadas de forma aleatoria, columnas desplazadas en filas intermedias y descripciones escritas manualmente con errores tipográficos y de normalización. 

El flujo manual de cotización tomaba entre **3 a 4 horas por cliente**. Para automatizar este proceso y reducir el tiempo a segundos, el sistema se estructuró en **5 fases técnicas consecutivas**:

1. **Fase Inicial (Análisis de Costos y Taxonomía Comercial):** Aprendizaje y mapeo del desglose de costos (costo proveedor, movilidad, empaquetado, serigrafía/impresión, seguros CRT e IGV) para más de 20,000 productos de proveedores nacionales e internacionales. Se definió un margen de ganancia base mínimo del 30% con un umbral de tolerancia estricto de $\pm 2$ soles respecto al precio comercial real.
2. **Proyecto 1 — Motor de Escaneo Masivo y Benchmarking (`01-escaneo-masivo-cotizaciones`):** Script defensivo y concurrente en Python/Pandas capaz de superar celdas combinadas y desplazamientos de columnas para extraer, limpiar y concatenar atributos (`Descripcion / Articulo`). Generó la base de conocimiento primaria con más de **14,000+ filas consolidadas** e integró una UI interactiva en CustomTkinter para filtrado y exploración.
3. **Proyecto 2 — Automatización de Márgenes (`02-automatizacion-margenes`):** Pipeline estadístico que agrupa el dataset histórico por arquetipos/categorías y tramos comerciales de cantidad (desde 10 hasta 100k+ unidades). Aplica control de *outliers* mediante rango intercuartílico (IQR) y suavizado monótono decreciente, calculando la matriz de márgenes base:
   
   $$\text{Margen (\%)} = \left( \frac{\text{Precio Cliente} - \text{Costo Proveedor}}{\text{Costo Proveedor}} \right) \times 100$$

4. **Proyecto 3 — Motor de Ajustes Dinámicos (`03-motor-ajustes-dinamicos`):** Sistema de reglas condicionales evaluadas por ID y reglas sobre variables de texto o volumen. Permite aplicar modificadores al margen base ("sumar puntos", "restar puntos" o "sobreescribir margen fijo") según el material, acabado o variante del producto para garantizar el rango de precisión de $\pm 2$ soles frente a la inflación y precios actualizados de mercado.
5. **Proyecto 4 — Interfaz de Cotización Rápida (`04-cotizador-expres`):** Aplicación de escritorio final que orquesta la búsqueda en la base de 14k+ filas, consulta la matriz de márgenes y aplica los ajustes dinámicos para calcular instantáneamente el precio al cliente:

   $$\text{Precio Cliente} = \text{Costo Proveedor} \times (1 + \text{Margen Ajustado})$$

   Genera de forma automatizada la propuesta comercial en Excel lista para ser enviada al cliente con desglose de precios unitarios, tiempos de entrega y detalles técnicos.

---

## Estructura del Monorepo

```text
sistema-cotizaciones-suite/
├── 01-escaneo-masivo-cotizaciones/   # Módulo 1: Ingesta, limpieza regex, benchmarking y UI
├── 02-automatizacion-margenes/        # Módulo 2: Control IQR, suavizado monótono y JSON de márgenes
├── .venv/                             # Entorno virtual unificado del monorepo
├── requirements.txt                   # Dependencias globales del proyecto
└── README.md                          # Documentación central de la suite
```

---

## Módulos Disponibles

### 01 - Motor de Escaneo Masivo y Benchmarking

Módulo encargado de la ingesta masiva de excels históricos.

* **Rendimiento:** Validado con más de 900 archivos y 14k+ filas sin bloqueos de interfaz gracias a *UI Chunking* en CustomTkinter.
* **Tecnologías:** Python 3.12+, Pandas, Openpyxl, xlrd, CustomTkinter.

### 02 - Motor de Automatización y Suavizado de Márgenes

Módulo backend encargado del análisis estadístico sobre la data histórica consolidada.

* **Filtro IQR & Suavizado:** Eliminación de *outliers* de precio por rango intercuartílico y generación de curvas de margen decrecientes por escala comercial (10 a 100k unidades).
* **Taxonomía Dinámica:** Importación directa de categorías desde el Módulo 01 para exportar la matriz final en `matriz_margenes.json`.
* **Tecnologías:** Python 3.12+, Pandas, NumPy, Openpyxl.

---

## Configuración General del Repositorio

1. **Clonar el repositorio:**
```bash
git clone https://github.com/RuidiasA/sistema-cotizaciones-suite.git
cd sistema-cotizaciones-suite
```

2. **Crear y activar el entorno virtual único:**
```bash
python -m venv .venv
# En Windows (PowerShell):
.venv\Scripts\Activate
```

3. **Instalar dependencias unificadas:**
```bash
pip install -r requirements.txt
```

4. **Ejecución de los módulos:**

Accede a la carpeta de cada submódulo (cd 01-escaneo-masivo-cotizaciones o cd 02-automatizacion-margenes) y ejecuta python main.py.