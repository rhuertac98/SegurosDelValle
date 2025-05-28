# Arquitectura de datos
Integrantes:
- **Rodrigo Alejandro Huerta Cruz** 
- **Daniel Michell Pérez Ruiz** - 
- **Gerardo Rocha Benigno** - 

# Seguros del Valle - CORE: Automatización Proceso de Suscripción Pólizas Experiencia Global Vida Grupo
![logo Del Valle](logo_SegurosDelValle.png)

En este proyecto se implementa CORE, un sistema automatizado que optimiza el proceso de cotización de pólizas "experiencia global" y la generación de reportes de conversión para Seguros del Valle, una empresa con 25 años de experiencia en el ramo de las aseguradoras.

## Objetivo

Diseñar y ejecutar un flujo end-to-end (E2E) que permita la automatización completa del proceso de cotización de pólizas experiencia global, desde la carga de insumos hasta la generación de reportes estratégicos, mediante una arquitectura desacoplada, escalable y gestionada en servicios cloud.

## Descripción de la problemática

Tensión entre ventas y suscripción: No se alcanzan las metas en experiencia global y la experiencia propia es volátil. Hay quejas sobre cotizaciones fuera de mercado y el equipo de suscripción opera al límite.

Falta de control y trazabilidad: Atrasos en reportes, diferencias de productividad entre oficinas y falta de supervisión en siniestros relevantes afectan la toma de decisiones y el reaseguro.

## ¿Qué resuelve CORE?

 - Automatiza el proceso de suscripción de pólizas experiencia global, eliminando tareas manuales repetitivas.
 - Reduce la carga operativa del área de suscripción sin necesidad de ampliar el equipo.
 - Genera reportes automáticos y dashboards interactivos accesibles desde una interfaz segura.
 - Facilita la toma de decisiones al proporcionar indicadores clave por oficina y por periodo.
 - Permite identificar áreas de mejora y orientar esfuerzos comerciales con base en datos objetivos.


## Características Principales

### Cálculo Automatizado de Tarifas
- Algoritmo especializado para calcular primas de pólizas "experiencia global", polizas de seguro para trabajadores de grandes empresas
- Cálculo basado en condiciones específicas de la póliza
- Almacenamiento automático de cálculos para cumplimiento normativo
- Agilización del proceso de emisión

### Generación de Cotizaciones
- Formato de cotización automático con condiciones y prima calculada
- Información completa para emisión sin intervención del suscriptor
- Proceso streamlined desde cotización hasta emisión

### Resportes Avanzados (Acá complementen)
- **Reporte de índices de conversión**: Métricas de efectividad de cotizaciones
- **Reporte de cotizaciones por período**: Análisis temporal de actividad
- **Visualización gráfica**: Gráficas optimizadas para análisis de datos
- **Filtros en tiempo real**: Consultas rápidas y personalizadas

## Beneficios

- **Reducción de tiempo de respuesta al cliente**
- **Liberación de recursos del sistema central**
- **Automatización completa del proceso de suscripción**
- **Análisis de regiones para captación de nuevos agentes**
- **Mayor tiempo disponible para análisis exhaustivo de cuentas**

## Fecha de Lanzamiento

**01 de junio de 2025**

## Arquitectura del Sistema

### Componentes Principales
- **Motor de Cálculo**: Algoritmo de tarifas experiencia global
- **Generador de Documentos**: Formatos de cotización automatizados  
- **Motor de Reportería**: Generación de reportes e índices
- **Interfaz para el envío de cotizaciones**: Almacenamiento de cálculos y datos normativos

### Flujo de Proceso
1. **Carga de Layouts**: El ingeniero de datos carga los datos de entrada a S3 mediante el script `load_data.py`
   - Los datos incluyen información de pólizas, condiciones y tarifas
2. **Procesamiento**: CORE procesa y transforma los datos automáticamente
3. **Cálculo**: El sistema calcula la tarifa según condiciones de póliza
4. **Generación**: Se produce el formato de cotización completo
5. **Almacenamiento**: Los datos se guardan para cumplimiento y seguimiento

## Instalación y uso:

Para instalar y utilizar CORE, sigue estos pasos:

 1. Clona el repositorio:
```bash
git clone https://github.com/rhuertac98/SegurosDelValle.git
```
2. Clona el ambiente de conda:
```bash
conda env create -f environment.yml
```
3. Activa el ambiente:
```bash
conda activate architectura
```
4. Agrega las AWS y Google en `config/config.yaml`:

5. Para visualizar la app de streamlit que contiene el dashboard, ejecuta:
```bash
streamlit run dashboard.py
```

6. Para visualizar la app de streamlit que contiene la herramienta de generación de PDFs, ejecuta:
```bash
streamlit run app_pdf.py
```

Para mayior información de la documentación, consulta el archivo `docs/src.html`.