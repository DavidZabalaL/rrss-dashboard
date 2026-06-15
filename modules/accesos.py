# modules/accesos.py — Gestión de usuarios y respaldo (solo admin)

from datetime import date
from pathlib import Path

import streamlit as st

from database import (
    DB_PATH,
    get_usuarios_lista,
    update_usuario_password,
    add_usuario,
    delete_usuario,
)

_ROLE_LABEL = {
    'admin':    ('🛡️', 'Admin',    '#ffd700'),
    'uploader': ('📁', 'Importar', '#1e90ff'),
    'viewer':   ('👁️', 'Lectura',  '#5b8db8'),
    'visita':   ('👤', 'Visita',   '#8892a4'),
}


def show_accesos():
    st.markdown("""
    <h2 style="color:#1e90ff;font-size:1.5rem;font-weight:700;margin-bottom:2px;">
      🔐 Accesos
    </h2>
    <p style="color:#5b8db8;font-size:.85rem;margin-top:0;">
      Gestión de usuarios, contraseñas y respaldo de datos.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    lista = get_usuarios_lista()

    # ── Tabla de usuarios ──────────────────────────────────────────────────────
    st.markdown("#### 👥 Usuarios registrados")

    # Encabezado
    hcols = st.columns([2, 2.5, 2.5, 1.8])
    for lbl in ("Usuario", "Nombre completo", "Contraseña", "Rol"):
        hcols[["Usuario", "Nombre completo", "Contraseña", "Rol"].index(lbl)].markdown(
            f"<div style='font-size:.72rem;font-weight:700;color:#5b8db8;"
            f"text-transform:uppercase;letter-spacing:.08em;padding-bottom:4px;"
            f"border-bottom:2px solid rgba(30,144,255,.25);'>{lbl}</div>",
            unsafe_allow_html=True,
        )

    for u in lista:
        icon, label, color = _ROLE_LABEL.get(u['role'], ('👤', u['role'], '#5b8db8'))
        rcols = st.columns([2, 2.5, 2.5, 1.8])
        rcols[0].markdown(
            f"<div style='padding:10px 0 8px;font-weight:700;font-size:.9rem;'>"
            f"{u['username']}</div>",
            unsafe_allow_html=True,
        )
        rcols[1].markdown(
            f"<div style='padding:10px 0 8px;color:#8892a4;font-size:.88rem;'>"
            f"{u['nombre']}</div>",
            unsafe_allow_html=True,
        )
        rcols[2].markdown(
            f"<div style='padding:10px 0 8px;font-family:monospace;"
            f"color:#1e90ff;font-size:.88rem;letter-spacing:.05em;'>"
            f"{u['password']}</div>",
            unsafe_allow_html=True,
        )
        rcols[3].markdown(
            f"<div style='padding:10px 0 8px;'>"
            f"<span style='background:rgba(30,144,255,.1);border:1px solid rgba(30,144,255,.25);"
            f"border-radius:20px;padding:3px 10px;font-size:.72rem;font-weight:600;"
            f"color:{color};white-space:nowrap;'>{icon} {label}</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<hr style='margin:0;border-color:rgba(100,120,160,.12);'>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gestión + Respaldo en dos columnas ─────────────────────────────────────
    col_mgmt, col_gap, col_backup = st.columns([5, 0.4, 4])

    with col_mgmt:
        st.markdown("#### ✏️ Gestión de usuarios")

        # Cambiar contraseña
        with st.expander("🔑 Cambiar contraseña", expanded=True):
            usernames = [u['username'] for u in lista]
            sel_user = st.selectbox("Usuario", usernames, key="pg_acc_sel_user")
            new_pw = st.text_input(
                "Nueva contraseña", type="password",
                key="pg_acc_new_pw", placeholder="Nueva contraseña",
            )
            if st.button("💾 Guardar contraseña", use_container_width=True,
                         key="pg_acc_save_pw", type="primary"):
                if new_pw.strip():
                    update_usuario_password(sel_user, new_pw.strip())
                    st.success(f"✅ Contraseña de **{sel_user}** actualizada.")
                    st.rerun()
                else:
                    st.warning("Escribe la nueva contraseña.")

        # Agregar usuario
        with st.expander("➕ Agregar usuario"):
            new_un = st.text_input("Nombre de usuario", key="pg_acc_new_un",
                                   placeholder="nombre_usuario")
            new_nb = st.text_input("Nombre completo", key="pg_acc_new_nb",
                                   placeholder="Nombre Apellido")
            new_p  = st.text_input("Contraseña", type="password",
                                   key="pg_acc_new_p", placeholder="Contraseña")
            _rol_labels = {
                'visita':   '👤 Solo ve parrilla y KPIs',
                'viewer':   '👁️ Lectura completa',
                'uploader': '📁 Puede importar datos',
            }
            new_rl = st.selectbox(
                "Rol",
                list(_rol_labels.keys()),
                format_func=lambda r: _rol_labels[r],
                key="pg_acc_new_rl",
            )
            if st.button("➕ Crear usuario", use_container_width=True,
                         key="pg_acc_add", type="primary"):
                if new_un.strip() and new_nb.strip() and new_p.strip():
                    add_usuario(new_un.strip(), new_p.strip(),
                                new_nb.strip(), role=new_rl)
                    st.success(f"✅ Usuario **{new_un}** creado con rol **{new_rl}**.")
                    st.rerun()
                else:
                    st.warning("Completa todos los campos.")

        # Eliminar usuario
        non_admins = [u['username'] for u in lista if u['role'] != 'admin']
        if non_admins:
            with st.expander("🗑️ Eliminar usuario"):
                del_u = st.selectbox("Selecciona usuario a eliminar", non_admins,
                                     key="pg_acc_del_u")
                st.caption("Esta acción no puede deshacerse.")
                if st.button("🗑️ Eliminar", use_container_width=True,
                             key="pg_acc_del_btn", type="secondary"):
                    delete_usuario(del_u)
                    st.success(f"✅ Usuario **{del_u}** eliminado.")
                    st.rerun()

    with col_backup:
        st.markdown("#### 💾 Respaldo de datos")

        st.markdown("""
        <div style='background:rgba(30,144,255,.06);border:1px solid rgba(30,144,255,.2);
                    border-radius:10px;padding:14px 16px;font-size:.83rem;color:#8892a4;
                    margin-bottom:16px;line-height:1.6;'>
          El respaldo incluye <strong style='color:#dde3ee;'>todos los datos</strong>:
          métricas importadas, KPIs y metas, publicaciones y usuarios.<br><br>
          Descarga periódicamente para tener un punto de restauración en caso de
          error humano o pérdida de archivos.
        </div>
        """, unsafe_allow_html=True)

        # Descargar
        if DB_PATH.exists():
            st.download_button(
                label="📥 Descargar respaldo",
                data=DB_PATH.read_bytes(),
                file_name=f"rrss_backup_{date.today():%Y%m%d}.db",
                mime="application/octet-stream",
                use_container_width=True,
                key="pg_acc_download",
                type="primary",
            )
        else:
            st.warning("Base de datos no encontrada.")

        # Sincronizar DB con GitHub
        if st.button("📤 Sincronizar DB con GitHub", use_container_width=True,
                     key="pg_acc_gh_sync"):
            from modules.parrilla import _github_sync_db
            with st.spinner("Sincronizando con GitHub..."):
                ok = _github_sync_db()
            if ok:
                st.success("✅ Base de datos sincronizada con GitHub.")
            else:
                st.error(
                    "No se pudo sincronizar. Verifica que GITHUB_TOKEN y "
                    "GITHUB_REPO estén configurados en los Secrets de Streamlit."
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(
            "<div style='font-size:.8rem;font-weight:700;margin-bottom:8px;'>"
            "📤 Restaurar desde respaldo</div>",
            unsafe_allow_html=True,
        )
        st.caption("Solo acepta archivos `.db` generados por esta plataforma.")

        restore_file = st.file_uploader(
            "Selecciona archivo .db",
            type=["db"],
            key="pg_acc_restore_file",
            label_visibility="collapsed",
        )
        if restore_file:
            st.error(
                "⚠️ **Advertencia:** esto reemplazará TODOS los datos actuales "
                "con los del respaldo. La acción no puede deshacerse."
            )
            if st.button("📤 Restaurar ahora", use_container_width=True,
                         key="pg_acc_restore_btn", type="secondary"):
                DB_PATH.write_bytes(restore_file.read())
                st.success("✅ Respaldo restaurado correctamente. Recarga la página.")
                st.rerun()
