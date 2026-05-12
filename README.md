# 📊 RRSS Analytics — Kabat One & SYM

Dashboard de métricas de redes sociales para Kabat One y SYM Servicios Integrales.

---

## 🚀 Despliegue en Streamlit Cloud

### 1. Crear repositorio en GitHub

```bash
git init
git add .
git commit -m "feat: initial dashboard"
git remote add origin https://github.com/TU_USUARIO/rrss-analytics.git
git push -u origin main
```

### 2. Conectar con Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu cuenta de GitHub
3. Selecciona el repositorio y `app.py` como punto de entrada
4. Configura los **Secrets** (ver sección siguiente)

### 3. Secrets en Streamlit Cloud

En Streamlit Cloud → App Settings → Secrets, agrega:

```toml
# Credenciales de acceso
[USERS.admin]
password = "tu_password_seguro"
nombre   = "Administrador"
role     = "admin"

[USERS.cliente]
password = "password_cliente"
nombre   = "Cliente"
role     = "viewer"

# Opcional: GitHub como almacén de datos persistente
GITHUB_TOKEN   = "ghp_xxxxxxxxxxxx"
GITHUB_REPO    = "TU_USUARIO/rrss-analytics"
GITHUB_DB_PATH = "data/rrss.db"
```

### 4. Persistencia de datos con GitHub

Para que los datos **no se pierdan** cuando Streamlit Cloud reinicia la app:

1. Genera un **Personal Access Token** en GitHub:
   - GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
   - Permisos: `Contents` → Read and write
2. Agrega el token a los Secrets como `GITHUB_TOKEN`
3. La app sincroniza automáticamente la base de datos al arrancar y después de cada carga de datos

---

## 🗂️ Estructura de archivos

```
app.py               # Punto de entrada
config.py            # Constantes y definición de KPIs
auth.py              # Sistema de login
database.py          # Persistencia SQLite
sync.py              # Sincronización opcional con GitHub
parsers.py           # Parseo de archivos Excel/CSV
utils.py             # Helpers UI y formato
modules/
  dashboard.py       # Resumen, tendencias y MoM
  kpi_monitor.py     # Registro y seguimiento de KPIs
  data_loader.py     # Importar archivos
  analista.py        # Analista de contenido (Top/Bottom posts)
  ai_insights.py     # Generador de script para IA
styles/custom.css    # Tema Tech Blueprint
```

---

## 📁 Nomenclatura de archivos

| Archivo | Red | Descripción |
|---|---|---|
| `k1_linkedin.xlsx` | LinkedIn | Métricas generales Kabat One |
| `k1_linkedin_seguidores.xlsx` | LinkedIn | Seguidores nuevos Kabat One |
| `k1_contenido.xlsx` | LinkedIn | Posts individuales Kabat One |
| `k1_facebook_visualizaciones.xlsx` | Facebook | Visualizaciones Kabat One |
| `k1_facebook_interaccion.xlsx` | Facebook | Interacciones Kabat One |
| `sym_instagram_alcance.xlsx` | Instagram | Alcance SYM |

**Prefijos de marca:** `k1_` = Kabat One · `sym_` = SYM

---

## 📋 Estructura de columnas por red

### LinkedIn (export Analytics)

| Columna requerida | KPI |
|---|---|
| `Fecha` | Fecha (MM/DD/YYYY) |
| `Impresiones (totales)` | Impresiones |
| `Impresiones únicas (orgánicas)` | Alcance |
| `Reacciones (total)` | Reacciones |
| `Comentarios (orgánicos)` | Comentarios |
| `Nuevos seguidores` | Incremento seguidores |

### LinkedIn Contenido (k1_contenido.xlsx / sym_contenido.xlsx)

| Columna | Campo |
|---|---|
| `Fecha de creación` | Fecha |
| `Título` | Título del post |
| `Tipo` | Tipo de contenido |
| `Impresiones` | Impresiones |
| `Recomendaciones` | Reacciones |
| `Comentarios` | Comentarios |
| `Tasa de interacción` | Tasa (0–100 o 0–1) |
| `Enlace` | URL del post |

### Facebook / Instagram

Formato de 2 columnas: `Fecha` + valor (`Primary` / `Total` / `Valor`).  
Incluye el tipo de métrica en el nombre del archivo: `_visualizaciones`, `_alcance`, `_interaccion`, `_seguidores`, `_visitas`.

---

## 🔑 Credenciales por defecto (desarrollo local)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `kabat2026` | Administrador |
| `cliente` | `sym2026` | Viewer |

> **Cambia las contraseñas** antes de desplegar en producción.

---

## 🛠️ Ejecución local

```bash
pip install -r requirements.txt
python3 -m streamlit run app.py
```

App disponible en: `http://localhost:8501`
