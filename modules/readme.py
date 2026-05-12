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

    # ── Índice rápido ──────────────────────────────────────────────────────────
    st.markdown("""
    > **Contenido de esta guía:**
    > [¿Qué es esta plataforma?](#1) · [Navegación y filtros](#2) · [Importar datos](#3) ·
    > [Monitor de KPIs](#4) · [Dashboard](#5) · [Analista de Contenido](#6) ·
    > [Insights para IA](#7) · [Nomenclatura de archivos](#8) · [Métricas especiales](#9)
    """)

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. QUÉ ES
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("1 · ¿Qué es esta plataforma?", expanded=True):
        st.markdown("""
**RRSS Analytics** es un dashboard privado de análisis de redes sociales diseñado para
**Kabat One** y **SYM**. Centraliza en un solo lugar los datos exportados de LinkedIn,
Facebook e Instagram, permite registrar y monitorear KPIs mensuales, visualizar tendencias
históricas y generar scripts listos para analizar con inteligencia artificial.

**Lo que puedes hacer:**
- Importar los archivos Excel descargados directamente de Meta y LinkedIn
- Establecer metas mensuales por métrica y red social
- Ver el cumplimiento de KPIs con indicadores visuales
- Comparar el rendimiento mes a mes con gráficas históricas
- Analizar el desempeño de publicaciones individuales
- Generar un prompt completo listo para pegar en Claude o Gemini y obtener análisis y recomendaciones

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

Todos los módulos respetan el mismo filtro global que aparece en la parte superior:

| Filtro | Descripción |
|---|---|
| **Red Social** | LinkedIn, Facebook o Instagram |
| **Año** | Año del período a analizar |
| **Mes** | Mes del período a analizar |

Al entrar por primera vez, los filtros se posicionan automáticamente en el **último mes
con datos disponibles** para la marca y red activas.

Al cambiar de marca (Kabat One ↔ SYM) los filtros se reinician para evitar ver datos
cruzados.

El botón **📁 Importar Datos** en la esquina superior derecha lleva directamente a la
sección de carga sin perder los filtros.
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

| Prefijo | Marca |
|---|---|
| `k1_` | Kabat One |
| `sym_` | SYM |

**Ejemplos — métricas diarias:**
```
k1_linkedin_impresiones.xlsx
k1_linkedin_incremento_seguidores.xlsx
k1_facebook_visualizaciones.xlsx
k1_instagram_visitas.xlsx
sym_linkedin_impresiones.xlsx
sym_instagram_interaccion.xlsx
```

**Ejemplos — contenido (publicaciones):**
```
k1_contenido_linkedin.xlsx
k1_contenido_facebook.xlsx
sym_contenido_linkedin.xlsx
sym_contenido_facebook.xlsx
```

---

### Comportamiento al reimportar

- Los datos se **actualizan por día**: si ya existe un registro para esa fecha y métrica,
  se sobreescribe con el nuevo valor
- Los meses que **no están en el archivo nuevo no se tocan** — el historial se preserva
- Puedes subir el mismo archivo varias veces sin duplicar datos

---

### Formato de los archivos

Los archivos deben ser los **exports directos de Meta o LinkedIn** sin modificar.
El sistema detecta el formato automáticamente.

| Tipo | Estructura esperada del Excel |
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

### Columnas del formulario

| Columna | Descripción |
|---|---|
| **Métrica** | Nombre del indicador |
| **Meta del mes** | El objetivo que quieres alcanzar ese mes |
| **Real** | El valor real obtenido |
| **Cumpl.** | Porcentaje de cumplimiento (Real ÷ Meta) |
| **Tipo** | Cómo se obtiene el dato (ver tabla abajo) |

---

### Tipos de métrica

| Tipo | Significado |
|---|---|
| `archivo` | El valor real se importa automáticamente desde el Excel |
| `manual` | Debes escribir el valor real en el formulario cada mes |
| `auto_4pct` | La meta se calcula sola como el 4% de las impresiones del mes |
| `manual_50pct` | La meta se calcula como el 50% de las visualizaciones; el real se captura a mano |

---

### Indicadores de cumplimiento

| Indicador | Rango |
|---|---|
| ✅ Verde | 100% o más |
| 🟡 Amarillo | Entre 75% y 99% |
| 🔴 Rojo | Menos del 75% |

---

### ¿Cómo registrar KPIs?

1. Selecciona la **red social**, **año** y **mes** en los filtros superiores
2. Escribe las **metas** en los campos editables
3. Para métricas `manual`, escribe también el **valor real**
4. Haz clic en **💾 Guardar KPIs**
5. Los indicadores y gauges se actualizan automáticamente

Las métricas `archivo` muestran el real en gris — ese valor viene del archivo importado
y no es editable desde aquí.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("5 · Dashboard"):
        st.markdown("""
El Dashboard ofrece una vista visual del rendimiento del mes seleccionado y la
evolución histórica.

### Tarjetas de KPI

Muestra las 4 métricas principales del mes con:
- Valor real del mes
- Variación respecto al mes anterior (▲ sube / ▼ baja)
- Color según cumplimiento de meta

### Tendencia histórica

Gráfica de líneas con la evolución mensual de las métricas que elijas.
Puedes seleccionar qué métricas visualizar con el selector múltiple.

### Comparativa mes a mes

Gráfica de barras agrupadas con los últimos 6 meses. Útil para identificar
patrones estacionales o el impacto de acciones concretas.

### Tabla de cumplimiento

Resumen tabular con Real, Meta y % de cumplimiento para todas las métricas
del mes filtrado.

> **Nota:** Si el Dashboard aparece vacío, verifica que hayas importado datos
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

- Tabla con todas las publicaciones del mes (o del período completo)
- Ordenadas por tasa de interacción o impresiones
- Top publicaciones vs. publicaciones de menor rendimiento
- Desglose por tipo de contenido (imagen, video, carrusel, etc.)

---

### Archivos de contenido — LinkedIn

| Archivo | Descripción |
|---|---|
| `k1_contenido_linkedin.xlsx` | Publicaciones LinkedIn Kabat One |
| `sym_contenido_linkedin.xlsx` | Publicaciones LinkedIn SYM |

Es el export de **LinkedIn Analytics → Análisis → Publicaciones → Exportar**.
Contiene una fila por post con métricas individuales.

**Columnas que reconoce el sistema:**

| Columna | Aliases aceptados |
|---|---|
| Fecha | Fecha de creación · Date |
| Título / Copy | Título · Title · Copy · Caption |
| Tipo | Tipo de publicación · Formato |
| Impresiones | Impresiones · Impressions |
| Reacciones | Recomendaciones · Likes · Reactions |
| Comentarios | Comentarios · Comments |
| Compartidos | Veces compartido · Shares · Reposts |
| Tasa de interacción | Tasa de interacción · Engagement rate |

---

### Archivos de contenido — Facebook

| Archivo | Descripción |
|---|---|
| `k1_contenido_facebook.xlsx` | Publicaciones Facebook Kabat One |
| `sym_contenido_facebook.xlsx` | Publicaciones Facebook SYM |

Es el export de **Meta Business Suite → Publicaciones → Exportar datos**.

**Cómo descargarlo:**
1. Ve a [business.facebook.com](https://business.facebook.com) → tu página
2. Menú izquierdo → **Publicaciones**
3. Selecciona el rango de fechas deseado
4. Clic en **Exportar datos** → descarga el archivo `.csv`
5. Renómbralo como `k1_contenido_facebook.xlsx` (o `sym_contenido_facebook.xlsx`)
6. Si el archivo descargado es `.csv`, ábrelo en Excel → Guardar como `.xlsx`

**Columnas que reconoce el sistema:**

| Columna del export | Métrica guardada |
|---|---|
| Hora de publicación | Fecha del post |
| Título / Descripción | Copy del post |
| Tipo de publicación | Fotos · Videos · Enlaces |
| Enlace permanente | URL del post |
| Alcance | Impresiones (reach) |
| Visualizaciones | Vistas de video |
| Total de clics | Clics |
| Reacciones | Reacciones |
| Comentarios | Comentarios |
| Veces que se compartió | Compartidos |

> La tasa de interacción se calcula automáticamente:
> **(Reacciones + Comentarios + Compartidos) ÷ Alcance**

---

### Archivos de contenido — Instagram

| Archivo | Descripción |
|---|---|
| `k1_contenido_instagram.xlsx` | Publicaciones Instagram Kabat One |
| `sym_contenido_instagram.xlsx` | Publicaciones Instagram SYM |

Es el export de **Meta Business Suite → Instagram → Publicaciones → Exportar datos**.

**Cómo descargarlo:**
1. Ve a [business.facebook.com](https://business.facebook.com) → selecciona tu cuenta de Instagram
2. Menú izquierdo → **Publicaciones**
3. Selecciona el rango de fechas deseado
4. Clic en **Exportar datos** → descarga el archivo `.csv`
5. Renómbralo como `k1_contenido_instagram.xlsx` (o `sym_contenido_instagram.xlsx`)
6. Si el archivo descargado es `.csv`, ábrelo en Excel → Guardar como `.xlsx`

**Columnas que reconoce el sistema:**

| Columna del export | Métrica guardada |
|---|---|
| Hora de publicación | Fecha del post |
| Descripción | Copy / caption del post |
| Tipo de publicación | Imagen · Reel · Secuencia |
| Enlace permanente | URL del post |
| Alcance | Impresiones (reach) |
| Visualizaciones | Reproducciones (Reels) |
| Me gusta | Reacciones |
| Comentarios | Comentarios |
| Veces que se compartió | Compartidos |
| Seguimientos | Seguidores ganados |
| Veces que se guardó | Guardados (registrado como clics) |

> La tasa de interacción se calcula automáticamente:
> **(Me gusta + Comentarios + Compartidos) ÷ Alcance**

> El archivo puede contener publicaciones de cualquier período —
> el sistema las filtra por mes usando los filtros del panel superior.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 7. INSIGHTS PARA IA
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("7 · Insights para IA"):
        st.markdown("""
Genera automáticamente un prompt estructurado listo para analizar con una IA
como Claude o Gemini.

### ¿Qué incluye el script generado?

1. **Datos de KPIs del mes** — todas las métricas con su real, meta y % de cumplimiento
2. **Top 5 publicaciones** — las de mayor engagement del mes
3. **Bottom 5 publicaciones** — las de menor rendimiento
4. **Rendimiento por tipo de contenido** — promedio de tasa de interacción por formato

### ¿Qué pide a la IA?

El prompt instruye a la IA para que entregue:
1. Diagnóstico de salud de la cuenta (Excelente / Bueno / Regular / Crítico)
2. Análisis de contenido ganador vs. perdedor
3. Mínimo 5 ideas de temas para el próximo mes
4. 3 posts completos listos para publicar (copy + hashtags + CTA)
5. Una acción de impacto inmediato para esta semana

### Botones de acción

| Botón | Acción |
|---|---|
| **📋 Copiar** | Copia el script al portapapeles |
| **🤖 Claude.ai** | Abre Claude en una nueva pestaña |
| **✨ Gemini** | Abre Gemini en una nueva pestaña |

**Flujo recomendado:** Copia el script → abre Claude o Gemini → pega y envía.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 8. NOMENCLATURA DE ARCHIVOS
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("8 · Nomenclatura completa de archivos"):
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
    # 9. MÉTRICAS ESPECIALES
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("9 · Métricas especiales y casos particulares"):
        st.markdown("""
### Reacciones — LinkedIn (`auto_4pct`)

La meta de Reacciones en LinkedIn **no se configura manualmente**. Se calcula
automáticamente como el **4% de las impresiones reales del mes**. Si importas
un nuevo archivo de impresiones, la meta de reacciones se recalcula sola.

---

### Visualizaciones de Seguidores y No Seguidores — Facebook (`manual_50pct`)

Facebook **no exporta estas métricas en CSV**. Por eso:
- La **meta** se calcula automáticamente como el 50% de las visualizaciones totales del mes
- El **real** debes capturarlo manualmente en el Monitor de KPIs leyendo el dato directamente
  desde tu cuenta de Meta Business Suite

---

### Alcance — Instagram (`manual`)

El Alcance (Reach) de Instagram **no puede sumarse desde valores diarios** porque Meta
lo deduplica por cuenta única. El CSV exporta cuántas cuentas vieron contenido cada día,
pero una misma cuenta puede aparecer en múltiples días y Meta la cuenta solo una vez en
el total mensual.

Por eso el Alcance de Instagram se captura **manualmente** desde el reporte mensual de
Meta Business Suite → sección Alcance.

---

### Publicaciones — todas las redes (`manual`)

Ninguna red social exporta un CSV con el conteo mensual de publicaciones propias.
Tanto la meta como el real se capturan manualmente en el Monitor de KPIs.

---

### Conversión de archivos CSV → XLSX

Si Meta te entrega un archivo `.csv`, conviértelo a `.xlsx` antes de subirlo.
El sistema solo acepta archivos Excel (`.xlsx`).

Pasos rápidos en Excel o Google Sheets:
1. Abre el `.csv`
2. Archivo → Guardar como → `.xlsx`
3. Renombra el archivo siguiendo la nomenclatura (`k1_instagram_visitas.xlsx`)
        """)

    st.markdown("---")
    st.markdown(
        "<div style='color:#5b8db8;font-size:.75rem;text-align:center;'>"
        "RRSS Analytics · Kabat One &amp; SYM · v1.0"
        "</div>",
        unsafe_allow_html=True,
    )
