# 03 - Motor de Ajustes Dinámicos y Auditoría Comercial

Este módulo constituye el núcleo de compilación de reglas de negocio y validación de precios dentro de la suite **SistemaCotizaciones**. 

Procesa el archivo tarifario maestro multicapa (`tarifario_diseno.xlsx`), transforma las definiciones taxonómicas y reglas condicionales en artefactos JSON optimizados (`matrices_margen.json` y `ajustes_margen.json`), y ejecuta la auditoría global de tolerancia comercial sobre el dataset de prueba histórico.

---

## Arquitectura del Módulo

```text
03-motor-ajustes-dinamicos/
├── config/
│   ├── tarifario_diseno.xlsx              # Libro Excel maestro con las 5 hojas de reglas
│   ├── matrices_margen.json               # Artefacto autogenerado: Curvas de márgenes base
│   └── ajustes_margen.json                # Artefacto autogenerado: Reglas condicionales de ajuste
├── data/
│   ├── input/
│   │   └── debug_scan_raw_recent.xlsx     # Data Lake histórico para pruebas de auditoría
│   └── output/
│       └── auditoria_global.xlsx          # Reporte de precios calculados vs. precios históricos
├── scripts/
│   ├── clean_db.py                        # ETL utilitario para saneamiento de proveedores nulos
│   └── diagnostico_entrega.py             # Diagnóstico de desvíos en pedidos corporativos (>= 50u)
├── src/
│   ├── audit.py                           # Motor de auditoría global desacoplado (Reusa Módulo 02)
│   └── compiler.py                        # Compilador multicapa de tarifario (Excel -> JSON)
├── main.py                                # Orquestador principal del pipeline
└── README.md
```

---

## Componentes Principales

### 1. Compilador Multicapa (`src/compiler.py`)

La clase `ExcelCompiler` lee de forma secuencial las 5 hojas de `tarifario_diseno.xlsx`:

* **Hoja 5 (`Diccionario_Filtros_Globales`):** Carga los tokens de inclusión/exclusión.
* **Hoja 3 (`Diccionario_Categorias`):** Mapea arquetipos comerciales y variantes de material.
* **Hoja 1 (`Margenes_Base`):** Estructura los márgenes por tramos de volumen ($10, 25, 50, 100, \dots$).
* **Hoja 4 (`Diccionario_Productos`):** Inyecta sub-productos específicos vinculados a su categoría padre.
* **Hoja 2 (`Ajustes`):** Compila las reglas multi-condicionales de impacto financiero (margen fijo, sumar/restar puntos).

### 2. Motor de Auditoría Global (`src/audit.py`)

* Importa centralizadamente la función `clasificar_producto_estricto` del **Módulo 02** para garantizar una taxonomía uniforme sin duplicidad de código.
* Evalúa el dataset histórico aplicando el algoritmo de interpolación por **Piso Comercial / Escalón Duro**.
* Ejecuta las reglas condicionales dinámicas y genera el reporte consolidado `auditoria_global.xlsx` evaluando la tolerancia comercial ($\pm 2.00$ PEN).

### 3. Diagnóstico Quirúrgico (`scripts/diagnostico_entrega.py`)

Analiza los casos críticos fuera de tolerancia enfocándose en entregas corporativas ($\ge 50$ unidades):

* Muestra la concentración del error por Top 5 arquetipos.
* Calcula el desvío monetario promedio en PEN por categoría.
* Mide la incidencia de parámetros técnicos de personalización (color, logo, impresión UV, DTF, bordado).

### 4. Saneamiento del Data Lake (`scripts/clean_db.py`)

Proceso ETL que imputa registros huérfanos o proveedores `"ANONIMO"` en `debug_scan_raw.xlsx` mediante la firma de texto de descripciones previamente identificadas.

---

## Ejecución del Pipeline

### 1. Compilación y Auditoría Principal

Para compilar las reglas de diseño y ejecutar la auditoría global, corre desde la raíz del proyecto o dentro del módulo:

```bash
python 03-motor-ajustes-dinamicos/main.py
```

**Ejemplo de salida de consola:**

```text
==================================================
MOTOR DE AJUSTES DINÁMICOS - COMPILACIÓN Y AUDITORÍA
==================================================

[INFO] FASE 1: Compilando Tarifario Maestro Multicapa...
[SUCCESS] Filtros globales cargados (Diccionario_Filtros): 10 IDs.
[SUCCESS] Categorías procesadas: 40 definiciones.
[SUCCESS] Productos específicos inyectados: 4 ítems.
[SUCCESS] Reglas de ajuste compiladas: 446 reglas.
[SUCCESS] Artefacto de matrices exportado: matrices_margen.json
[SUCCESS] Artefacto de reglas exportado: ajustes_margen.json

[INFO] FASE 2: Ejecutando Auditoría Global (Tolerancia ±2.00 PEN)...
[SUCCESS] Reporte de auditoría generado: auditoria_global.xlsx
[STATUS] Registros totales analizados: 1808
[STATUS] Registros fuera de tolerancia: 684
--------------------------------------------------
CONTROL DE ENTREGAS CRÍTICAS (Pedidos >= 50 Unidades):
   -> Total analizado corporativo: 1457 filas
   -> Fuera de tolerancia (SI): 430 filas
   -> Efectividad corporativa actual: 70.49%
==================================================
[STATUS] Tiempo total de procesamiento RAM: 1.12 segundos.
```

### 2. Ejecución del Diagnóstico Corporativo

Para obtener la descomposición de errores y desvíos financieros:

```bash
python 03-motor-ajustes-dinamicos/scripts/diagnostico_entrega.py
```

### 3. Saneamiento Preventivo de Datos (Opcional)

Para reparar proveedores nulos en la base de datos de pruebas:

```bash
python 03-motor-ajustes-dinamicos/scripts/clean_db.py
```

---

## Métricas de Desempeño

* **Efectividad Comercial Corporativa ($\ge 50$ u):** $70.49\%$
* **Tiempo de Procesamiento RAM:** $\sim 1.12$ segundos para $1,808$ cotizaciones y $446$ reglas.
* **Tolerancia Permitida:** $\pm 2.00$ PEN sobre el precio histórico final.
