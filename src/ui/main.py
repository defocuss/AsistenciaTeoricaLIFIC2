from pathlib import Path
import sys
import streamlit as st

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.sp_connection import SP_Handler

sp_connection = SP_Handler()

st.logo(
    "https://i.imgur.com/YMei8p1.png",
    link="https://streamlit.io/gallery",
    icon_image="https://i.imgur.com/YMei8p1.png",
)

login_page = st.Page("auth/login.py", title="Iniciar sesión", icon=":material/login:")
logout_page = st.Page("auth/logout.py", title="Cerrar sesión", icon=":material/logout:")
configs = st.Page("configs/modules.py", title="Configuración de módulos", icon=":material/settings:")
asistencia = st.Page("attendance/attendance.py", title="Registro de asistencia", icon=":material/check_circle:") 

if not st.user.is_logged_in:
    pg = st.navigation({"Iniciar sesión" : [login_page]})
    pg.run()
    st.stop()
else: 
    if not sp_connection.verify_user(st.user.email):
        Col1, Col2, Col3 = st.columns(3)
        Col2.image('https://i.imgur.com/YMei8p1.png',width = "stretch")
        st.title("Acceso denegado")
        st.error(f"El email {st.user.email} no se encuentra en la base de datos.")
        st.text("Inicia sesión con un correo institucional registrado para acceder a la aplicación o contacta al administrador.")
        st.button("Cerrar sesión", on_click=st.logout)
        st.stop()

    pg = st.navigation(
        {
            "Asistencia" : [asistencia],
            "Configuración" : [configs],
            "Cuenta" : [logout_page]
        }
    )
    pg.run()
