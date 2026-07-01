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
> [1 · ¿Qué es?](#1) · [2 · Navegación](#2) · [3 · Importar Datos](#3) ·
> [4 · Monitor de KPIs](#4) · [5 · Dashboard](#5) · [6 · Analista de Contenido](#6) ·
> [7 · Insights con IA](#7) · [8 · Parrilla de Contenido](#8) · [9 · Post Rápido](#9) ·
> [10 · Editor de Imágenes](#10) · [11 · Nomenclatura](#11) · [12 · Métricas especiales](#12)
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
- Generar análisis estratégico con Claude o Gemini directamente en la plataforma
- **Crear la parrilla de contenido mensual con IA**, basada en los datos reales de rendimiento
- **Generar imágenes y artes para redes sociales** con editor integrado
- **Publicar posts rápidos** sin esperar a la parrilla mensual

**Marcas disponibles:** Kabat One (`k1_`) · SYM (`sym_`)

**Redes sociales:** LinkedIn · Facebook · Instagram

**Motor de IA disponibles:** Gemini 2.5 Flash (gratis) · Claude (requiere API key)
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
| **Motor IA** | Indica qué motor IA está activo (Gemini gratis / Claude) |
| **👤 Usuario** | Muestra tu nombre, rol y versión del commit activo |
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

```
PASO 1 — Cierre del mes anterior
  📁 Importar Datos
     └─ Sube los exports de LinkedIn, Facebook e Instagram del mes cerrado

PASO 2 — Registrar KPIs
  🎯 Monitor de KPIs
     └─ Captura metas y valores reales del mes cerrado

PASO 3 — Análisis con IA  ← CRÍTICO para la parrilla
  🤖 Insights para IA
     └─ Repite para las 3 redes: LinkedIn → Facebook → Instagram
     └─ Estos análisis quedan guardados y la Parrilla los usará

PASO 4 — Generar Parrilla
  📅 Parrilla de Contenido
     └─ Selecciona el mes a planificar
     └─ Investiga fechas especiales
     └─ Elige el objetivo del mes
     └─ Genera la parrilla
     └─ Edita con el cuadro de ajustes si necesitas
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
- **Facebook / Instagram** → copy conversacional, tono cercano, 1-2 párrafos

Las **fechas especiales** se agregan como publicaciones **extra** en esa fecha —
no reemplazan los días regulares.

---

## Secciones de la Parrilla

### Tab Parrilla — Tabla compacta
La tabla muestra 7 columnas clave (Fecha, Día, Tipo, Tema, Pilar, Formato, Estado)
sin scroll horizontal. Usa los **checkboxes** para seleccionar posts y el botón
**🗑️ Eliminar marcados** para borrarlos (requiere confirmación explícita).

### Cards de contenido por post
Debajo de la tabla aparece una card colapsada por cada post. Al expandirla ves y editas:

| Campo | Contenido |
|---|---|
| **Tema** | Título conciso del post |
| **CTA** | Llamado a la acción |
| **Copy LinkedIn** | Texto completo para LinkedIn |
| **Copy Facebook / Instagram** | Texto completo para Facebook e Instagram |
| **✏️ Texto en Imagen** | Headline, subtítulo, texto de slides o datos de infografía — el copy que va DENTRO del arte |
| **Hashtags** | Set de 5-7 hashtags |
| **Arte Sugerida** | Descripción detallada para el diseñador |

Haz clic en **💾 Actualizar este post** para guardar los cambios del card.
Luego presiona **💾 Guardar cambios** (botón principal) para persistir en la base de datos.

### Texto en Imagen — Completar con IA
Si uno o más posts tienen el campo "Texto en Imagen" vacío, aparece el banner:

> ✏️ **N post(s) sin Texto en Imagen** — haz clic para que la IA los complete

La IA genera automáticamente según el formato de cada post:
- **Carrusel** → texto y arte por cada slide
- **Infografía** → título + puntos de dato clave
- **Video / Reel** → hook de apertura + frases en pantalla
- **Imagen estática** → Headline + subtítulo

### 🎠 Configuración de Carrusel
Cuando el formato del post es **Carrusel**, aparece una sección adicional al final del card:

1. **Número de slides** — define cuántos slides tendrá el carrusel (1-15, portada incluida)
2. **✨ Generar texto para N slide(s)** — la IA genera para cada slide:
   - `Slide N: [título o texto breve]`
   - `Arte N: [descripción visual del arte de ese slide]`

El texto generado reemplaza el campo "Texto en Imagen" y se guarda automáticamente.

### 📆 Fechas Especiales del Mes
Clic en **🔍 Investigar fechas del mes** para que Claude busque:
- Fechas nacionales mexicanas relevantes para seguridad pública
- Días internacionales adaptables al sector
- Efemérides tecnológicas o de innovación gubernamental

Aparece un **calendario visual** con:
- 🔵 Días azules = publicaciones regulares
- 🟡 Días amarillos = fechas especiales

Selecciona con los **checkboxes** cuáles incluir.

### 💬 Cuadro de Ajustes
Después de generar, pide cambios a Claude en lenguaje natural:

> *"Los temas de posicionamiento ya los tengo cubiertos. Cámbiame esos posts por educación técnica."*

> *"El copy de LinkedIn de la primera semana está muy largo, acórtalo a máximo 2 párrafos."*

Claude ajusta solo lo que le pides y explica brevemente qué cambió.

### 📥 Descargar Excel
El Excel incluye todas las columnas + **columna "Copy Instagram"** (copia exacta de Facebook),
con formato profesional para entregar al equipo de diseño.

---

## Estados de publicación

| Estado | Significado |
|---|---|
| ⚪ Borrador | Post pendiente de revisión |
| 🟡 En revisión | Copy enviado al cliente o equipo |
| 🔵 Aprobado | Listo para programar |
| 🟢 Publicado | Ya se publicó |
| 🔴 Pausado | Detenido temporalmente |

Los estados se sincronizan con **Monday.com** si está configurado.

---

## Conexión Insights → Parrilla

Si generaste los análisis de Insights antes de crear la parrilla, la plataforma confirma:

> ✅ *Insights de IA disponibles (LinkedIn, Facebook, Instagram) — se usarán como base estratégica.*

Claude conoce: pilares con mejor engagement, formatos que funcionaron, temas recomendados
y tendencias de rendimiento — y toma decisiones editoriales basadas en datos reales.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 9. POST RÁPIDO
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("9 · Post Rápido — Crear y agregar posts individuales"):
        st.markdown("""
**Post Rápido** permite crear una publicación individual sin generar toda la parrilla del mes.
Útil para posts de oportunidad, reacciones a noticias o contenido urgente.

### ¿Cómo funciona?

1. Ve a **✏️ Post Rápido** en el menú lateral
2. Completa los campos del formulario:

| Campo | Descripción |
|---|---|
| **Red social** | LinkedIn, Facebook, Instagram o Multi-red |
| **Tema** | Sobre qué trata el post |
| **Pilar** | Pillar de contenido (Posicionamiento, Educación, etc.) |
| **Tono** | Formal / Conversacional / Inspiracional / Urgente |
| **CTA** | Llamado a la acción deseado |
| **Notas adicionales** | Contexto extra para la IA |

3. Haz clic en **✨ Generar Post** — la IA crea el copy completo
4. Revisa el resultado y edita si necesitas
5. Haz clic en **📅 Agregar a Parrilla** para enviarlo a la parrilla del mes

### Agregar a Parrilla

Al hacer clic en **📅 Agregar a Parrilla**, aparece un formulario:

| Campo | Descripción |
|---|---|
| **Mes / Año** | A qué mes pertenece el post |
| **Fecha** | Día exacto de publicación |
| **Formato** | Imagen estática, Carrusel, Video, etc. |
| **Arte Sugerida** | Descripción para el diseñador |
| **✏️ Texto en Imagen** | Headline o texto que irá dentro del arte |

El post se agrega directamente a la parrilla del mes y aparece de inmediato sin necesidad de
hacer refresh. Se sincroniza automáticamente con la base de datos en GitHub.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 10. EDITOR DE IMÁGENES
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("10 · Editor de Imágenes — Generación y edición de artes"):
        st.markdown("""
La sección **Prompts de Imagen** dentro de la Parrilla de Contenido incluye un editor
completo para generar y personalizar los artes de cada post.

---

## Formatos disponibles

| Formato | Dimensiones | Uso |
|---|---|---|
| **Cuadrado 1:1** | 1080 × 1080 px | Feed Instagram / Facebook |
| **Vertical 4:5** | 1080 × 1350 px | Feed Instagram optimizado para móvil |
| **Horizontal 16:9** | 1920 × 1080 px | LinkedIn / portadas |
| **Story 9:16** | 1080 × 1920 px | Stories / Reels verticales |

---

## Agregar Logo

El botón **🖼️ Agregar logo** abre el panel de posicionamiento del logo de marca.

### Posiciones disponibles (9 puntos)

```
┌─────────────────────────────┐
│ Superior-Izq  Superior-Cen  Superior-Der │
│                             │
│ Centro-Izq      Centro      Centro-Der   │
│                             │
│ Inferior-Izq  Inferior-Cen  Inferior-Der │
└─────────────────────────────┘
```

### Controles de logo

| Control | Descripción |
|---|---|
| **Tamaño (%)** | Qué porcentaje del ancho de la imagen ocupa el logo |
| **Variante** | Blanco / Color / Negro |
| **Logo personalizado** | Sube tu propio archivo PNG |
| **← Horizontal →** | Desplazamiento fino horizontal (±30% del ancho) |
| **↑ Vertical ↓** | Desplazamiento fino vertical (±30% del alto) |

---

## Agregar Pleca

El botón **🎨 Agregar pleca** abre el panel de bandas de color de marca.

### ¿Qué es una pleca?

Una pleca es una banda de color (generalmente del color de la marca) que:
- Enmarca visualmente la imagen
- Sirve de fondo para texto o logos
- Refuerza la identidad de la marca

### Posiciones de pleca

| Opción | Descripción |
|---|---|
| ⬇ Inferior | Banda horizontal en la parte de abajo |
| ⬆ Superior | Banda horizontal en la parte de arriba |
| ↔ Centro horizontal | Banda horizontal al centro |
| ⬅ Izquierda | Banda vertical al lado izquierdo |
| ➡ Derecha | Banda vertical al lado derecho |
| ↕ Centro vertical | Banda vertical al centro |

### Controles de pleca

| Control | Descripción |
|---|---|
| **Color de marca** | Selector de colores predefinidos de la marca (primario, secundario, acento…) |
| **O elige color libre** | Color picker para cualquier tono |
| **Grosor (%)** | Qué porcentaje de la imagen ocupa la pleca (2-35%) |
| **Opacidad (%)** | Transparencia de la pleca (20-100%) |
| **☑ Sombra paralela** | Agrega una sombra difuminada en el borde interior de la pleca |
| **Intensidad sombra (%)** | Qué tan oscura y visible es la sombra (10-100%) |

### Vista previa en tiempo real

Cada vez que cambias un control, la imagen se actualiza en tiempo real (vista previa).
Haz clic en **✅ Aplicar pleca** para guardar el resultado.

---

## Edición con IA

Además de logo y pleca, el editor permite instrucciones en lenguaje natural:

> *"Aumenta el contraste"*
> *"Cambia el fondo a azul oscuro"*
> *"Agrega un filtro cálido"*

La IA (Gemini) aplica los cambios y muestra el resultado. Puedes deshacer y rehacer
en el historial de ediciones.

---

## Generación de imagen

Desde el tab **Prompts de Imagen**, puedes generar una imagen desde cero describiendo lo que quieres.
La IA genera la imagen base que luego puedes editar con logo, pleca y ajustes.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 11. NOMENCLATURA
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("11 · Archivos que se usan"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
**LinkedIn** (un archivo trae todas las métricas)
```
k1_linkedin.xlsx          →  Kabat One
sym_linkedin.xlsx         →  SYM
```
```
k1_contenido_linkedin.xlsx
sym_contenido_linkedin.xlsx
```

**Facebook** (Meta exporta una métrica por archivo)
```
k1_facebook_visualizaciones.xlsx
k1_facebook_incremento_seguidores.xlsx
k1_facebook_interaccion.xlsx
k1_facebook_visitas.xlsx
```
Mismo patrón con `sym_` para SYM.
            """)
        with col2:
            st.markdown("""
**Instagram** (Meta exporta una métrica por archivo)
```
k1_instagram_visualizaciones.xlsx
k1_instagram_incremento_seguidores.xlsx
k1_instagram_interaccion.xlsx
k1_instagram_visitas.xlsx
```
Mismo patrón con `sym_` para SYM.

> **Alcance Instagram**: se captura manualmente en el Monitor de KPIs.
> No se importa por archivo.
            """)
        st.info("""
**Reglas:**
- Todo en minúsculas, sin acentos, separado por `_` · Extensión `.xlsx`
- El prefijo `k1_` o `sym_` asigna la marca automáticamente. Sin prefijo → marca activa en la app.
- **LinkedIn**: un solo archivo ya trae todas las métricas — no necesitas archivos separados por métrica.
- **Facebook / Instagram**: Meta exporta una métrica por archivo — sube uno por cada tipo.
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # 12. MÉTRICAS ESPECIALES
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("12 · Métricas especiales y casos particulares"):
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
3. Renombra siguiendo la nomenclatura (`k1_facebook_visitas.xlsx`)
        """)

    st.markdown("---")
    st.markdown(
        "<div style='color:#5b8db8;font-size:.75rem;text-align:center;'>"
        "RRSS Analytics · Kabat One &amp; SYM · v2.1 — IA integrada con Claude + Gemini"
        "</div>",
        unsafe_allow_html=True,
    )
