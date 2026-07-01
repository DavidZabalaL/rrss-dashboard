# sync.py — Sincronización con GitHub usando Git Data API (soporta hasta 100 MB)
#
# Configura en .streamlit/secrets.toml:
#   GITHUB_TOKEN   = "ghp_..."
#   GITHUB_REPO    = "usuario/repositorio"
#   GITHUB_DB_PATH = "data/rrss.db"   # ruta dentro del repo

import base64
import shutil
import sqlite3
import requests
import streamlit as st
from database import DB_PATH

_BRANCH = "main"


def _cfg():
    try:
        return (
            st.secrets.get("GITHUB_TOKEN", ""),
            st.secrets.get("GITHUB_REPO",  ""),
            st.secrets.get("GITHUB_DB_PATH", "data/rrss.db"),
        )
    except Exception:
        return "", "", ""


def _h(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def github_configured():
    token, repo, _ = _cfg()
    return bool(token and repo)


def pull():
    """Descarga la BD desde GitHub → local. Soporta archivos grandes."""
    token, repo, path = _cfg()
    if not token or not repo:
        return False
    api = f"https://api.github.com/repos/{repo}"

    # Obtener SHA del HEAD
    r = requests.get(f"{api}/git/refs/heads/{_BRANCH}", headers=_h(token), timeout=15)
    if r.status_code != 200:
        return False
    head_sha = r.json()["object"]["sha"]

    # Obtener el árbol del commit (recursive para encontrar el archivo)
    r = requests.get(f"{api}/git/trees/{head_sha}?recursive=1", headers=_h(token), timeout=30)
    if r.status_code != 200:
        return False
    tree = r.json().get("tree", [])
    blob = next((n for n in tree if n["path"] == path), None)
    if not blob:
        return False

    # Descargar el blob directamente (sin límite de tamaño)
    r = requests.get(f"{api}/git/blobs/{blob['sha']}", headers=_h(token), timeout=60)
    if r.status_code != 200:
        return False
    content = base64.b64decode(r.json()["content"].replace("\n", ""))
    DB_PATH.parent.mkdir(exist_ok=True)
    _bak = DB_PATH.with_suffix('.db.bak')
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, _bak)
    DB_PATH.write_bytes(content)
    # Verificar que la BD descargada es válida; si no, restaurar backup
    try:
        _conn = sqlite3.connect(str(DB_PATH))
        _conn.execute("SELECT 1")
        _conn.close()
    except Exception:
        if _bak.exists():
            shutil.copy2(_bak, DB_PATH)
        return False
    return True


def push():
    """Sube la BD local → GitHub usando Git Data API. Sin límite de 1 MB."""
    token, repo, path = _cfg()
    if not token or not repo or not DB_PATH.exists():
        return False

    api     = f"https://api.github.com/repos/{repo}"
    db_b64  = base64.b64encode(DB_PATH.read_bytes()).decode()

    # 1. Crear blob con el contenido del archivo
    r = requests.post(f"{api}/git/blobs",
                      json={"content": db_b64, "encoding": "base64"},
                      headers=_h(token), timeout=60)
    if r.status_code not in (200, 201):
        return False
    blob_sha = r.json()["sha"]

    # 2. Obtener el SHA del commit HEAD
    r = requests.get(f"{api}/git/refs/heads/{_BRANCH}", headers=_h(token), timeout=15)
    if r.status_code != 200:
        return False
    head_sha   = r.json()["object"]["sha"]

    # 3. Obtener el SHA del árbol del commit actual
    r = requests.get(f"{api}/git/commits/{head_sha}", headers=_h(token), timeout=15)
    if r.status_code != 200:
        return False
    tree_sha = r.json()["tree"]["sha"]

    # 4. Crear nuevo árbol con el archivo actualizado
    r = requests.post(f"{api}/git/trees",
                      json={"base_tree": tree_sha,
                            "tree": [{"path": path, "mode": "100644",
                                      "type": "blob", "sha": blob_sha}]},
                      headers=_h(token), timeout=30)
    if r.status_code not in (200, 201):
        return False
    new_tree_sha = r.json()["sha"]

    # 5. Crear commit
    r = requests.post(f"{api}/git/commits",
                      json={"message": "sync: update RRSS database",
                            "tree": new_tree_sha,
                            "parents": [head_sha],
                            "committer": {"name": "RRSS Bot", "email": "bot@rrss.local"}},
                      headers=_h(token), timeout=30)
    if r.status_code not in (200, 201):
        return False
    new_commit_sha = r.json()["sha"]

    # 6. Actualizar la referencia del branch
    r = requests.patch(f"{api}/git/refs/heads/{_BRANCH}",
                       json={"sha": new_commit_sha},
                       headers=_h(token), timeout=15)
    if r.status_code in (200, 201):
        return True

    # Reintento único si el SHA está desactualizado (conflicto 409/422)
    if r.status_code in (409, 422):
        try:
            pull()  # sincronizar HEAD remoto antes de reintentar
            # Re-obtener HEAD actualizado
            r2 = requests.get(f"{api}/git/refs/heads/{_BRANCH}", headers=_h(token), timeout=15)
            if r2.status_code != 200:
                return False
            head_sha2 = r2.json()["object"]["sha"]
            r3 = requests.get(f"{api}/git/commits/{head_sha2}", headers=_h(token), timeout=15)
            if r3.status_code != 200:
                return False
            tree_sha2 = r3.json()["tree"]["sha"]
            r4 = requests.post(f"{api}/git/trees",
                               json={"base_tree": tree_sha2,
                                     "tree": [{"path": path, "mode": "100644",
                                               "type": "blob", "sha": blob_sha}]},
                               headers=_h(token), timeout=30)
            if r4.status_code not in (200, 201):
                return False
            new_tree_sha2 = r4.json()["sha"]
            r5 = requests.post(f"{api}/git/commits",
                               json={"message": "sync: update RRSS database",
                                     "tree": new_tree_sha2,
                                     "parents": [head_sha2],
                                     "committer": {"name": "RRSS Bot", "email": "bot@rrss.local"}},
                               headers=_h(token), timeout=30)
            if r5.status_code not in (200, 201):
                return False
            new_commit_sha2 = r5.json()["sha"]
            r6 = requests.patch(f"{api}/git/refs/heads/{_BRANCH}",
                                json={"sha": new_commit_sha2},
                                headers=_h(token), timeout=15)
            return r6.status_code in (200, 201)
        except Exception:
            return False

    return False
