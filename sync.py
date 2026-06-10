# sync.py — Sincronización opcional con GitHub
#
# Configura en .streamlit/secrets.toml:
#   GITHUB_TOKEN   = "ghp_..."
#   GITHUB_REPO    = "usuario/repositorio"
#   GITHUB_DB_PATH = "data/rrss.db"   # ruta dentro del repo

import base64
import requests
import streamlit as st
from database import DB_PATH


def _cfg():
    try:
        return (
            st.secrets.get("GITHUB_TOKEN", ""),
            st.secrets.get("GITHUB_REPO",  ""),
            st.secrets.get("GITHUB_DB_PATH", "data/rrss.db"),
        )
    except Exception:
        return "", "", ""


def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def github_configured():
    token, repo, _ = _cfg()
    return bool(token and repo)


def pull():
    """Descarga la BD desde GitHub → local. Retorna True si exitoso."""
    token, repo, path = _cfg()
    if not token or not repo:
        return False
    url  = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(token), timeout=30, stream=True)
    if resp.status_code != 200:
        return False
    data = resp.json()
    # GitHub Contents API tiene límite de ~1 MB; archivos más grandes
    # devuelven content vacío pero incluyen download_url para descarga directa.
    raw_content = data.get("content", "").replace("\n", "")
    if raw_content:
        content = base64.b64decode(raw_content)
    elif data.get("download_url"):
        dl = requests.get(data["download_url"], timeout=60, stream=True)
        dl.raise_for_status()
        content = b"".join(dl.iter_content(chunk_size=65536))
    else:
        return False
    DB_PATH.parent.mkdir(exist_ok=True)
    DB_PATH.write_bytes(content)
    return True


def push():
    """Sube la BD local → GitHub. Retorna True si exitoso."""
    token, repo, path = _cfg()
    if not token or not repo or not DB_PATH.exists():
        return False
    content = base64.b64encode(DB_PATH.read_bytes()).decode()
    url     = f"https://api.github.com/repos/{repo}/contents/{path}"
    # Obtener SHA actual si el archivo ya existe
    r = requests.get(url, headers=_headers(token), timeout=15)
    sha = r.json().get("sha", "") if r.status_code == 200 else ""
    payload = {
        "message": "sync: update RRSS database",
        "content": content,
        "committer": {"name": "RRSS Bot", "email": "bot@rrss.local"},
    }
    if sha:
        payload["sha"] = sha
    resp = requests.put(url, json=payload, headers=_headers(token), timeout=30)
    return resp.status_code in (200, 201)
