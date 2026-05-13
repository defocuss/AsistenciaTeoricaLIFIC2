import subprocess
from pathlib import Path
import sys
import streamlit as st

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.sp_connection import SP_Handler

## Diagnóstico de red para la UFRO (bloqueo de IPs de datacenters)
import requests

st.subheader("🕵️‍♂️ Test de Conexión Definitivo (Con Disfraz)")

url_ufro = "https://intranet.ufro.cl/"

# Aquí "disfrazamos" nuestra petición para que parezca un humano usando Chrome
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

st.write("Enviando petición con cabeceras de navegador real...")

try:
    response = requests.get(url_ufro, headers=headers, timeout=15)
    st.write(f"**Código de respuesta:** `{response.status_code}`")
    
    if response.status_code == 200:
        st.success("✅ ¡Funcionó! El problema era que el servidor rechazaba bots básicos. Ahora sabemos que sí se puede entrar disfrazando la petición.")
    else:
        st.warning(f"⚠️ Respondió con código: {response.status_code}")

except requests.exceptions.Timeout:
    st.error("⏳ **Timeout de nuevo.** Diagnóstico definitivo: La UFRO tiene bloqueadas las IPs de la nube donde se aloja Streamlit a nivel de Firewall. No hay forma de entrar directamente desde este servidor.")
except Exception as e:
    st.error(f"❌ Otro error: {e}")
## Fin del diagnóstico de red

sp_connection = SP_Handler()

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
