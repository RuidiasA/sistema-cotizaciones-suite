Este es el diseño integral del flujo y la lógica de **Compipro 2.0**, consolidando la arquitectura técnica, el motor de búsqueda y el nuevo sistema de inteligencia de negocios para **COMPINA S.A.C.**.

---

## 1. Arquitectura del Sistema (Patrón MVC)

El programa se estructura en cuatro capas desacopladas para garantizar escalabilidad y mantenimiento profesional:

* **Vistas (Views):** Construidas con `customtkinter`. Incluyen `ScanControls` (filtros), `ResultsView` (KPIs y tabla), y `QuoteView` (calculadora rápida).
* **Controlador (`AppController`):** Orquestador que gestiona hilos (`ThreadPoolExecutor`), eventos de interrupción (`stop_event`) y la comunicación entre servicios y UI.
* **Servicios (Services):**
* **`VariationService`:** Maneja los "Sacos Semánticos" y la circularidad de búsqueda.
* **`ExcelScanService`:** Motor de búsqueda multihilo con limpieza por Regex.
* **`QuoteService`:** Lógica matemática para cotizaciones rápidas.
* **`BenchmarkingService`:** (Nueva) Lógica de agrupación por arquetipos y exportación de reportes.


* **Modelos (Models):** Estructuras de datos como `PriceStats` y `ReportResult`.

---

## 2. Motor de Búsqueda y Escaneo

La lógica de procesamiento de archivos históricos sigue estos pilares:

* **Circularidad Semántica:** Al buscar un término, el sistema consulta automáticamente su clúster completo (ej: "bolsa" busca también "bolso", "morral", "tote").
* **Filtros de Exclusión:** Listas de palabras (`exclude`) que descartan filas irrelevantes (ej: "bolsas de basura" o "bolsas de plástico").
* **Normalización Forense:**
* Limpieza de caracteres especiales, guiones y conversión a MAYÚSCULAS.
* Uso de límites de palabra (`\b`) en Regex para evitar falsos positivos (ej: que "polo" no coincida con "poliester").


* **Concurrencia Segura:** Escaneo en segundo plano para evitar que la UI se congele, con estados de control (`set_scanning_state`) para bloquear/liberar botones.

---

## 3. Lógica de Benchmarking por Arquetipos

Esta funcionalidad transforma datos dispersos en una matriz de inteligencia comercial.

### A. Construcción del Arquetipo (Nombre del Grupo)

Para evitar la dispersión por proveedores o variaciones mínimas de texto, el nombre del grupo se genera mediante la fórmula:


$$\text{Arquetipo} = \text{Producto Base} + \text{Material} + \text{Segmento de Calidad}$$

* **Producto Base:** Identificación del sustantivo principal (Mochila, Casaca, Polo).
* **Material:** Extracción de términos críticos de costo (Notex, Taslan, Nylon, Softshell, Jersey, Lino).
* **Segmento de Calidad:** Se protegen y mantienen los términos **"Publicitario"** y **"Corporativo"**, ya que definen tiers de precios y acabados distintos según los requerimientos de la gerencia.

### B. Segmentación por Tiers de Cantidad

Cada registro encontrado en el historial se clasifica automáticamente en tres categorías de volumen para promediar su margen:

* **Tier 100 (Resto):** Cantidad $< 500$ unidades.
* **Tier 500:** Cantidad $\ge 500$ y $< 1000$ unidades.
* **Tier 1000:** Cantidad $\ge 1000$ unidades.

### C. Filtros de Calidad de Datos

* **Exclusión de Servicios:** El sistema descarta automáticamente filas de logística o servicios no tangibles (palabras clave: `MOVILIDAD`, `ENVÍO`, `EMBALAJE`, `ROTULADO`, `FLETE`).
* **Limpieza de Adjetivos de Bajo Valor:** Se eliminan términos que no afectan el margen estructural (ej: "Grande", "Modelo", "Color", "Tipo", "Fabricación Nacional").

---

## 4. Flujo de Salida (Reporte Excel)

El resultado final es un archivo `Benchmarking_[Categoria].xlsx` con la siguiente estructura de columnas:

| Columna | Descripción |
| --- | --- |
| **Producto (Arquetipo)** | Nombre normalizado (ej: GORRO DRILL PUBLICITARIO). |
| **Tier (Cantidad)** | Nivel de volumen (100, 500 o 1000). |
| **Margen Promedio** | Promedio de los márgenes históricos encontrados para ese tier. |
| **Muestra (Nro. Casos)** | Cantidad de registros que sustentan el dato (nivel de confianza). |

---

## 5. Lógica de la Calculadora Rápida (`QuoteView`)

Permite realizar una proyección instantánea basada en el aprendizaje del escaneo:

* **Entradas:** Producto, Cantidad y Costo de Proveedor.
* **Validación:** Manejo de errores de tipo (`ValueError`) para asegurar que solo se procesen números válidos.
* **Indicador de Confianza:** Si el producto es conocido, aplica el margen del tier correspondiente. Si es nuevo, aplica un margen de seguridad del **35%** (marcado con una advertencia visual ⚠️).