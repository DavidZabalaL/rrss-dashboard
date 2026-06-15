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

    dark = st.session_state.get('dark_mode', True)

    # ── Outer padding ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:6vh;'></div>", unsafe_allow_html=True)

    # ── Three-column layout: logo | separator | form ───────────────────────────
    col_logo, col_sep, col_form = st.columns([5, 1, 5])

    # ── LEFT: Group logo ───────────────────────────────────────────────────────
    with col_logo:
        st.markdown("<div style='height:8vh;'></div>", unsafe_allow_html=True)

        logo_file = "logo_kabat_grupo.png" if dark else "logo_kabat_grupo_day.png"
        logo_path = ASSETS / logo_file
        if not logo_path.exists():
            logo_path = ASSETS / "logo_kabat_grupo.png"

        # Constrain logo to 55% of column width
        _, lc, _ = st.columns([1, 4, 1])
        with lc:
            if logo_path.exists():
                st.image(str(logo_path), use_container_width=True)
            else:
                st.markdown(
                    "<h2 style='color:#1e90ff;text-align:center;'>Grupo Kabat</h2>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<p style='color:#5b8db8;font-size:.72rem;letter-spacing:.18em;"
            "text-transform:uppercase;text-align:center;margin-top:20px;'>"
            "Social Media Intelligence</p>",
            unsafe_allow_html=True,
        )

    # ── CENTER: Tech texture separator ────────────────────────────────────────
    with col_sep:
        st.markdown("""
        <div style='display:flex;justify-content:center;align-items:stretch;
                    min-height:480px;padding-top:10vh;'>
          <div style='position:relative;width:1px;
                      background:linear-gradient(
                        to bottom,
                        transparent 0%,
                        rgba(30,144,255,.15) 8%,
                        rgba(30,144,255,.85) 25%,
                        #1e90ff 50%,
                        rgba(30,144,255,.85) 75%,
                        rgba(30,144,255,.15) 92%,
                        transparent 100%
                      );
                      box-shadow:0 0 12px rgba(30,144,255,.4);'>
            <span style='position:absolute;top:18%;left:50%;
                         transform:translate(-50%,-50%);
                         width:7px;height:7px;border-radius:50%;
                         background:#1e90ff;
                         box-shadow:0 0 10px 2px rgba(30,144,255,.8);'></span>
            <span style='position:absolute;top:36%;left:50%;
                         transform:translate(-50%,-50%);
                         width:4px;height:4px;border-radius:50%;
                         background:#1e90ff;opacity:.5;'></span>
            <span style='position:absolute;top:54%;left:50%;
                         transform:translate(-50%,-50%);
                         width:7px;height:7px;border-radius:50%;
                         background:#1e90ff;
                         box-shadow:0 0 10px 2px rgba(30,144,255,.8);'></span>
            <span style='position:absolute;top:72%;left:50%;
                         transform:translate(-50%,-50%);
                         width:4px;height:4px;border-radius:50%;
                         background:#1e90ff;opacity:.5;'></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── RIGHT: Login form ──────────────────────────────────────────────────────
    with col_form:
        st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)

        st.markdown(
            "<h2 style='color:#dde3ee;font-size:1.4rem;font-weight:700;"
            "margin:0 0 4px;'>RRSS Analytics</h2>"
            "<p style='color:#5b8db8;font-size:.82rem;margin:0 0 32px;'>"
            "Kabat One &amp; SYM &nbsp;·&nbsp; Social Media Dashboard</p>",
            unsafe_allow_html=True,
        )

        # st.form handles Enter-key submission natively
        with st.form("login_form", border=False):
            user = st.text_input("Usuario", placeholder="nombre de usuario",
                                 key="login_user")
            pw   = st.text_input("Contraseña", type="password",
                                 placeholder="••••••••", key="login_pw")
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "Ingresar →",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            users = _get_users()
            if user in users and users[user]['password'] == pw:
                st.session_state.logged_in    = True
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
