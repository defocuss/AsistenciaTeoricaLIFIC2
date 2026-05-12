import subprocess
import streamlit as st

@st.cache_resource
def install_playwright():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("Playwright y Chromium instalados correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error crítico al instalar Playwright: {e}")
        st.error("Hubo un problema al configurar el navegador en el servidor.")

install_playwright()


st.logo(
    "https://i.imgur.com/YMei8p1.png",
    link="https://streamlit.io/gallery",
    icon_image="https://i.imgur.com/YMei8p1.png",
)

configs = st.Page("configs/modules.py", title="Configuración de módulos", icon=":material/settings:")
asistencia = st.Page("attendance/attendance.py", title="Registro de asistencia", icon=":material/check_circle:") 
pg = st.navigation(
    {
        "Asistencia" : [asistencia],
        "Configuración" : [configs]
    }
)
pg.run()