# auth.py

from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).parent / "assets"


def _get_users():
    from database import get_usuarios
    try:
        users = get_usuarios()
        if users:
            return users
    except Exception:
        pass
    return {
        'admin':     {'password': 'kabat2026', 'nombre': 'Administrador', 'role': 'admin'},
        'Marketing': {'password': 'mkt2026',   'nombre': 'Marketing',     'role': 'viewer'},
    }


def check_login():
    if st.session_state.get('logged_in'):
        return True

    # Centrar el formulario
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        # Logo Grupo Kabat — versión según modo de color
        dark = st.session_state.get('dark_mode', True)
        logo = ASSETS / ("logo_kabat_grupo.png" if dark else "logo_kabat_grupo_day.png")
        if not logo.exists():
            logo = ASSETS / "logo_kabat_grupo.png"   # fallback
        if logo.exists():
            st.image(str(logo), use_container_width=True)
        else:
            st.markdown(
                "<h2 style='color:#1e90ff;text-align:center;'>📊 RRSS Analytics</h2>",
                unsafe_allow_html=True,
            )

        st.markdown("""
        <div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:14px;
                    padding:32px 28px;margin-top:16px;
                    box-shadow:0 0 48px rgba(30,144,255,.15);">
          <p style="color:#5b8db8;text-align:center;font-size:.8rem;margin:0 0 24px;">
            Kabat One &amp; SYM · Social Media Dashboard
          </p>
        </div>
        """, unsafe_allow_html=True)

        user = st.text_input("Usuario", key="login_user")
        pw   = st.text_input("Contraseña", type="password", key="login_pw")
        if st.button("Ingresar", use_container_width=True, type="primary"):
            users = _get_users()
            if user in users and users[user]['password'] == pw:
                st.session_state.logged_in = True
                st.session_state.current_user = {
                    'nombre': users[user]['nombre'],
                    'role':   users[user]['role'],
                }
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    return False


def get_user():
    return st.session_state.get('current_user', {'nombre': '—', 'role': 'viewer'})


def logout():
    st.session_state.pop('logged_in', None)
    st.session_state.pop('current_user', None)
    st.rerun()
