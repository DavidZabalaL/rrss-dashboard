# modules/readme.py — Manual de uso de la plataforma

import streamlit as st


def show_readme():
    st.markdown("""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      📖 Manual de Uso
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      Guía completa de la plataforma RRSS Analytics · Kabat One &amp; SYM
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
> **Contenido de esta guía:**
> [¿Qué es esta plataforma?](#1) · [Navegación y filtros](#2) · [Importar datos](#3) ·
> [Monitor de KPIs](#4) · [Dashboard](#5) · [Analista de Contenido](#6) ·
> [Insights con IA](#7) · [Parrilla de Contenido](#8) · [Nomenclatura de archivos](#9) · [Métricas especiales](#10)
    """)

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. QUÉ ES
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("1 · ¿Qué es esta plataforma?", expanded=True):
        st.markdown("""
**RRSS Analytics** es un dashboard privado de análisis y planificación de redes sociales diseñado para
**Kabat One** y **SYM**. Centraliza en un solo lugar los datos exportados de LinkedIn,
Facebook e Instagram, permite registrar y monitorear KPIs mensuales, visualizar tendencias
históricas y generar contenido mensual asistido por inteligencia artificial.

**Lo que puedes hacer:**
- Importar los archivos Excel descargados directamente de Meta y LinkedIn
- Establecer metas mensuales por métrica y red social
- Ver el cumplimiento de KPIs con indicadores visuales
- Comparar el rendimiento mes a mes con gráficas históricas
- Analizar el desempeño de publicaciones individuales
- **Generar análisis estratégico con Claude directamente en la plataforma**
- **Crear la parrilla de contenido mensual con IA**, basada en los datos reales de rendimiento

**Marcas disponibles:** Kabat One (`k1_`) · SYM (`sym_`)

**Redes sociales:** LinkedIn · Facebook · Instagram
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 2. NAVEGACIÓN Y FILTROS
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("2 · Navegación y filtros"):
        st.markdown("""
### Menú lateral (sidebar)

| Elemento | Función |
|---|---|
| **Logo** | Muestra la marca activa |
| **Kabat One / SYM** | Cambia entre marcas; los filtros se reinician al cambiar |
| **Módulos** | Navegación principal entre secciones |
| **☀️ / 🌙 Modo** | Alterna entre tema claro y tema oscuro |
| **👤 Usuario** | Muestra tu nombre y rol |
| **🚪 Cerrar sesión** | Cierra la sesión actual |

---

### Barra de filtros superior

Todos los módulos respetan el mismo filtro global:

| Filtro | Descripción |
|---|---|
| **Red Social** | LinkedIn, Facebook o Instagram |
| **Año** | Año del período a analizar |
| **Mes** | Mes del período a analizar |

Al entrar por primera vez, los filtros se posicionan automáticamente en el **último mes
con datos disponibles** para la marca y red activas.

Al cambiar de marca (Kabat One ↔ SYM) los filtros se reinician para evitar ver datos cruzados.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 3. IMPORTAR DATOS
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("3 · Importar Datos"):
        st.markdown("""
### ¿Cómo subir archivos?

1. Ve a **📁 Importar Datos** desde el menú o el botón superior
2. Arrastra o selecciona uno o varios archivos `.xlsx`
3. Haz clic en **⬆️ Procesar archivos**
4. El sistema muestra cuántos registros se guardaron por archivo

Puedes subir archivos de Kabat One y SYM al mismo tiempo — el sistema los enruta
automáticamente por el prefijo del nombre (`k1_` o `sym_`).

---

### Reglas del nombre de archivo

```
{marca}_{red}_{metrica}.xlsx        ← métricas diarias
{marca}_contenido_{red}.xlsx        ← publicaciones para análisis
```

**Ejemplos — métricas diarias:**
```
k1_linkedin_impresiones.xlsx
k1_facebook_visualizaciones.xlsx
sym_instagram_interaccion.xlsx
```

**Ejemplos — contenido (publicaciones):**
```
k1_contenido_linkedin.xlsx
sym_contenido_facebook.xlsx
```

---

### Comportamiento al reimportar

- Los datos se **actualizan por día**: si ya existe un registro para esa fecha y métrica, se sobreescribe
- Los meses que **no están en el archivo nuevo no se tocan** — el historial se preserva
- Puedes subir el mismo archivo varias veces sin duplicar datos

---

### Formato de los archivos

| Tipo | Estructura esperada |
|---|---|
| **LinkedIn métricas** | Fila 1: título · Fila 2: encabezados · Fila 3+: datos diarios |
| **LinkedIn contenido** | Fila 1: encabezados · una fila por publicación |
| **Facebook / Instagram métricas** | Fila 1: `sep=` · Fila 2: nombre métrica · Fila 3: Fecha, Primary |
| **Facebook contenido** | Fila 1: encabezados · una fila por publicación (export Meta Business Suite) |
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 4. MONITOR DE KPIs
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("4 · Monitor de KPIs"):
        st.markdown("""
Esta es la sección principal. Muestra y permite registrar metas y valores reales
por red social y mes.

### Tipos de métrica

| Tipo | Significado |
|---|---|
| `archivo` | El valor real se importa automáticamente desde el Excel |
| `manual` | Debes escribir el valor real en el formulario cada mes |
| `auto_4pct` | La meta se calcula sola como el 4% de las impresiones del mes |
| `manual_50pct` | La meta = 50% de visualizaciones; el real se captura a mano |

### Indicadores de cumplimiento

| Indicador | Rango |
|---|---|
| ✅ Verde | 100% o más |
| 🟡 Amarillo | Entre 75% y 99% |
| 🔴 Rojo | Menos del 75% |

### ¿Cómo registrar KPIs?

1. Selecciona la **red social**, **año** y **mes** en los filtros superiores
2. Escribe las **metas** en los campos editables
3. Para métricas `manual`, escribe también el **valor real**
4. Haz clic en **💾 Guardar KPIs**
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("5 · Dashboard"):
        st.markdown("""
El Dashboard ofrece una vista visual del rendimiento del mes seleccionado y la evolución histórica.

- **Tarjetas de KPI** — valor real, variación vs. mes anterior, color por cumplimiento
- **Tendencia histórica** — gráfica de líneas con evolución mensual
- **Comparativa mes a mes** — barras agrupadas con los últimos 6 meses
- **Tabla de cumplimiento** — resumen de Real, Meta y % para todas las métricas

> Si el Dashboard aparece vacío, verifica que hayas importado datos
> para la red y mes seleccionados en los filtros.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 6. ANALISTA DE CONTENIDO
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("6 · Analista de Contenido"):
        st.markdown("""
Analiza el rendimiento de publicaciones individuales por red social.
Requiere haber importado el archivo de contenido correspondiente.

### ¿Qué muestra?

- Tabla con todas las publicaciones del período
- Ordenadas por tasa de interacción o impresiones
- Top publicaciones vs. publicaciones de menor rendimiento
- Desglose por tipo de contenido (imagen, video, carrusel, etc.)

### Archivos de contenido

| Archivo | Red |
|---|---|
| `k1_contenido_linkedin.xlsx` | LinkedIn Kabat One |
| `k1_contenido_facebook.xlsx` | Facebook Kabat One |
| `k1_contenido_instagram.xlsx` | Instagram Kabat One |
| `sym_contenido_linkedin.xlsx` | LinkedIn SYM |
| `sym_contenido_facebook.xlsx` | Facebook SYM |
| `sym_contenido_instagram.xlsx` | Instagram SYM |

Los exports vienen directamente de **LinkedIn Analytics** y **Meta Business Suite**.
La tasa de interacción se calcula automáticamente: **(Reacciones + Comentarios + Compartidos) ÷ Alcance**
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 7. INSIGHTS CON IA
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("7 · Insights con IA (análisis directo con Claude)"):
        st.markdown("""
Genera un **análisis estratégico completo directamente con Claude**, sin necesidad de
copiar y pegar en ninguna herramienta externa.

### ¿Qué analiza?

Con los datos del mes seleccionado en los filtros, Claude entrega:

1. **Diagnóstico de salud** — calificación Excelente / Bueno / Regular / Crítico con justificación
2. **Análisis de contenido ganador vs. perdedor** — qué tienen en común los posts del Top 5 y qué falló en el Bottom 5
3. **Mínimo 5 ideas de temas** para el próximo mes con formato recomendado y justificación basada en datos
4. **3 posts completos** listos para publicar (gancho, cuerpo, CTA y hashtags)
5. **Una acción de impacto inmediato** — la única cosa que, hecha esta semana, más impacta los KPIs

### ¿Cómo usarlo?

1. Selecciona **marca**, **red social** y **mes** en los filtros superiores
2. Clic en **🤖 Analizar con Claude**
3. El análisis aparece progresivamente en pantalla (~20-40 segundos)
4. Puedes **descargar el análisis** como `.txt` para compartirlo

### Importancia para la Parrilla de Contenido

> ⭐ **El análisis de Insights se conecta directamente con la Parrilla.**
> Si generas el análisis de LinkedIn, Facebook e Instagram del mes cerrado **antes** de
> crear la parrilla del mes siguiente, Claude usará esas recomendaciones como base
> estratégica para decidir qué publicar, qué pilares priorizar y qué formatos usar.

**Recomendación:** genera el análisis de las 3 redes antes de crear la parrilla mensual.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 8. PARRILLA DE CONTENIDO
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("8 · Parrilla de Contenido — Flujo de trabajo completo"):
        st.markdown("""
La **Parrilla de Contenido** genera automáticamente el calendario editorial mensual
usando inteligencia artificial. Claude actúa como Community Manager Senior especializado
en marcas B2G del sector seguridad pública.

---

## Flujo de trabajo recomendado

Sigue estos pasos en orden para obtener la parrilla más estratégica posible:

```
PASO 1 — Cierre del mes anterior
  📁 Importar Datos
     └─ Sube los exports de LinkedIn, Facebook e Instagram del mes cerrado
        para las 2 marcas (Kabat One y SYM)

PASO 2 — Registrar KPIs
  🎯 Monitor de KPIs
     └─ Captura metas y valores reales del mes cerrado
        (especialmente las métricas manuales: alcance Instagram,
         visualizaciones de seguidores Facebook)

PASO 3 — Análisis con IA  ← CRÍTICO para la parrilla
  🤖 Insights para IA
     └─ Selecciona la marca (Kabat One o SYM)
     └─ Repite para las 3 redes: LinkedIn → Facebook → Instagram
     └─ Clic en "Analizar con Claude" en cada una
     └─ Estos análisis quedan guardados y la Parrilla los usará

PASO 4 — Generar Parrilla
  📅 Parrilla de Contenido
     └─ Selecciona el mes a planificar
     └─ Investiga fechas especiales
     └─ Elige el objetivo del mes
     └─ Genera la parrilla
     └─ Ajusta con el cuadro de diálogo si necesitas
     └─ Descarga el Excel para el equipo de diseño
```

---

## Lógica de publicaciones

| Marca | Días de publicación | Redes |
|---|---|---|
| **Kabat One** | Lunes y Miércoles | LinkedIn · Facebook · Instagram |
| **SYM** | Martes y Jueves | LinkedIn · Facebook · Instagram |

Cada día de publicación genera **una sola pieza de contenido** adaptada a las 3 redes:
- **LinkedIn** → copy formal, lenguaje de autoridad y liderazgo, 2-3 párrafos
- **Facebook** → copy conversacional, tono cercano, 1-2 párrafos
- **Instagram** → **idéntico a Facebook** (espejo 100%)

Las **fechas especiales** (efemérides, días mundiales) se agregan como publicaciones
**extra** en esa fecha específica — no reemplazan los días regulares.

---

## Secciones de la Parrilla

### 📆 Fechas Especiales del Mes
Clic en **🔍 Investigar fechas del mes** para que Claude busque automáticamente:
- Fechas nacionales mexicanas relevantes para el sector seguridad
- Días internacionales adaptables a un mensaje de seguridad
- Efemérides tecnológicas o de innovación gubernamental

Aparece un **calendario visual** con:
- 🔵 Días azules = publicaciones regulares
- 🟡 Días amarillos = fechas especiales encontradas

Selecciona con los **checkboxes** cuáles incluir como publicaciones extra.
Puedes deseleccionar cualquier fecha que no quieras incluir.

---

### 🎯 Objetivo del Mes
Elige entre 6 opciones predefinidas o escribe uno personalizado:

| Opción | Cuándo usarla |
|---|---|
| Posicionamiento y liderazgo | Meses de consolidación de marca |
| Generación de leads | Cuando hay campaña activa o evento próximo |
| Educación técnica | Para audiencias nuevas o post-evento |
| Construcción de confianza | Cuando hay casos de éxito o testimonios disponibles |
| Presencia en evento | Mes de expo, conferencia o temporada relevante |
| Lanzamiento de producto | Cuando hay un nuevo módulo o funcionalidad |
| Personalizado | Objetivos específicos que no encajan en las opciones anteriores |

---

### ✨ Generar Parrilla
Claude recibe:
- Brief completo de la marca (pilares, tono, hashtags, CTAs, mensajes clave)
- Análisis de Insights del mes anterior (si fueron generados en el Paso 3)
- Fechas especiales seleccionadas
- Objetivo del mes
- Días de publicación configurados

El resultado es una tabla editable con una fila por pieza de contenido:

| Columna | Contenido |
|---|---|
| Fecha | Fecha exacta de publicación |
| Día | Día de la semana |
| Tipo | Regular o Especial |
| Pilar | Pilar de contenido |
| Formato | Imagen estática, Carrusel, etc. |
| Tema | Título conciso del post |
| Copy LinkedIn | Texto completo para LinkedIn |
| Copy Facebook / Instagram | Texto completo para Facebook e Instagram |
| Arte Sugerida | Descripción detallada para el diseñador |
| Hashtags | Set de 5-7 hashtags |
| CTA | Llamado a la acción |

Puedes **editar cualquier celda** directamente en la tabla antes de descargar.

---

### 💬 Cuadro de Ajustes
Después de generar la parrilla, puedes pedirle cambios a Claude en lenguaje natural:

**Ejemplos de ajustes:**
> *"Los temas de posicionamiento ya los tengo cubiertos con 3 publicaciones que hice la semana pasada. Cámbiame esos posts por educación técnica."*

> *"El post del lunes 7 hazlo sobre el lanzamiento del nuevo módulo de LPR que anunciamos."*

> *"Quiero que el mes tenga más peso en casos de uso y menos en posicionamiento genérico."*

> *"El copy de LinkedIn de la primera semana está muy largo, acórtalo a máximo 2 párrafos."*

Claude ajusta solo lo que le pides, mantiene el resto igual y te explica brevemente qué cambió.
El historial de ajustes queda visible para que puedas rastrear los cambios.

---

### 📥 Descargar Excel
El archivo Excel incluye:
- Todas las columnas visibles en la tabla
- **Columna "Copy Instagram"** generada automáticamente como copia exacta de Facebook
- Formato profesional con encabezados, ajuste de columnas y word-wrap

Entrega el Excel al equipo de diseño con las columnas **Arte Sugerida** para guiar la producción visual.

---

## Conexión Insights → Parrilla

Si generaste los análisis de Insights **antes** de crear la parrilla, la plataforma
muestra una confirmación verde:

> ✅ *Insights de IA de Mayo 2026 disponibles (LinkedIn, Facebook, Instagram) — se usarán como base estratégica.*

En ese caso, Claude conoce:
- Qué pilares tuvieron mejor engagement el mes anterior
- Qué formatos funcionaron y cuáles no
- Las recomendaciones de temas que ya identificó
- Las tendencias de rendimiento por tipo de contenido

Y toma decisiones editoriales basadas en datos reales, no solo en el brief.

Si **no** hay análisis previo disponible, la parrilla se genera igualmente usando los
datos históricos de la base de datos como referencia.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 9. NOMENCLATURA
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("9 · Nomenclatura completa de archivos"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
**KABAT ONE — LinkedIn**
```
k1_linkedin_impresiones.xlsx
k1_linkedin_incremento_seguidores.xlsx
k1_contenido_linkedin.xlsx
```

**KABAT ONE — Facebook**
```
k1_facebook_visualizaciones.xlsx
k1_facebook_incremento_seguidores.xlsx
k1_facebook_interaccion.xlsx
k1_facebook_visitas.xlsx
k1_contenido_facebook.xlsx
```

**KABAT ONE — Instagram**
```
k1_instagram_visualizaciones.xlsx
k1_instagram_incremento_seguidores.xlsx
k1_instagram_interaccion.xlsx
k1_instagram_visitas.xlsx
k1_contenido_instagram.xlsx
```
            """)
        with col2:
            st.markdown("""
**SYM — LinkedIn**
```
sym_linkedin_impresiones.xlsx
sym_linkedin_incremento_seguidores.xlsx
sym_contenido_linkedin.xlsx
```

**SYM — Facebook**
```
sym_facebook_visualizaciones.xlsx
sym_facebook_incremento_seguidores.xlsx
sym_facebook_interaccion.xlsx
sym_facebook_visitas.xlsx
sym_contenido_facebook.xlsx
```

**SYM — Instagram**
```
sym_instagram_visualizaciones.xlsx
sym_instagram_incremento_seguidores.xlsx
sym_instagram_interaccion.xlsx
sym_instagram_visitas.xlsx
sym_contenido_instagram.xlsx
```
            """)
        st.info("""
**Reglas generales:**
- Todo en minúsculas, sin acentos, separado por `_`
- Extensión siempre `.xlsx` (no `.csv`, no `.xls`)
- Una métrica por archivo
- El prefijo `k1_` o `sym_` determina la marca automáticamente
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 10. MÉTRICAS ESPECIALES
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("10 · Métricas especiales y casos particulares"):
        st.markdown("""
### Reacciones — LinkedIn (`auto_4pct`)
La meta de Reacciones en LinkedIn **no se configura manualmente**. Se calcula
automáticamente como el **4% de las impresiones reales del mes**.

---

### Visualizaciones de Seguidores y No Seguidores — Facebook (`manual_50pct`)
Facebook **no exporta estas métricas en CSV**. Por eso:
- La **meta** se calcula automáticamente como el 50% de las visualizaciones totales del mes
- El **real** debes capturarlo manualmente en el Monitor de KPIs

---

### Alcance — Instagram (`manual`)
El Alcance de Instagram se captura **manualmente** porque Meta deduplica cuentas únicas
y el CSV diario no refleja el total mensual real.
Fuente: Meta Business Suite → sección Alcance del período.

---

### Publicaciones — todas las redes (`contenido`)
El conteo de publicaciones se calcula automáticamente desde los archivos de contenido
importados. No necesitas capturarlo manualmente — el sistema cuenta los posts en la base
de datos para el mes y red seleccionados.

---

### Conversión de archivos CSV → XLSX
Si Meta te entrega un `.csv`, conviértelo antes de subir:
1. Abre el `.csv` en Excel o Google Sheets
2. Archivo → Guardar como → `.xlsx`
3. Renombra siguiendo la nomenclatura (`k1_instagram_visitas.xlsx`)
        """)

    st.markdown("---")
    st.markdown(
        "<div style='color:#5b8db8;font-size:.75rem;text-align:center;'>"
        "RRSS Analytics · Kabat One &amp; SYM · v2.0 — IA integrada con Claude Opus"
        "</div>",
        unsafe_allow_html=True,
    )
