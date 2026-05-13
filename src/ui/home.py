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

st.subheader("🕵️‍♂️ Test de Conexión y Diagnóstico de Red")

# 1. Averiguar qué IP pública tiene tu app en Streamlit
try:
    ip_response = requests.get('https://api.ipify.org', timeout=5)
    st.info(f"🌐 La IP pública de este servidor (Streamlit) es: **{ip_response.text}**")
except Exception as e:
    st.error("No se pudo obtener la IP del servidor.")

# 2. Intentar conectarse a la intranet de la UFRO
url_ufro = "https://intranet.ufro.cl/"
st.write(f"Intentando conectar a: `{url_ufro}` ...")

try:
    # Usamos requests para hacer una visita básica (como un navegador simple)
    # Ponemos 10 segundos de límite.
    response = requests.get(url_ufro, timeout=10)
    
    st.write(f"**Código de respuesta HTTP:** `{response.status_code}`")
    
    if response.status_code == 200:
        st.success("✅ **Status 200 (OK):** ¡La conexión llegó perfecto! Esto significa que la IP NO está bloqueada por red. El problema podría ser que la página detecta a Playwright como un bot.")
    elif response.status_code == 403:
        st.error("🚫 **Status 403 (Forbidden):** El servidor de la UFRO rechazó la conexión. Tienen un Firewall (probablemente Cloudflare o similar) que bloquea IPs de datacenters o de otros países.")
    else:
        st.warning(f"⚠️ **Respuesta inesperada.** El servidor contestó, pero con este código: {response.status_code}")

except requests.exceptions.Timeout:
    st.error("⏳ **Timeout:** La conexión tardó demasiado y fue abortada. Este es el síntoma clásico de un **bloqueo estricto por Firewall**. La universidad simplemente ignora las peticiones que vienen de servidores en la nube.")
except requests.exceptions.ConnectionError:
    st.error("🔌 **Error de Conexión:** La conexión fue rechazada de plano (Connection Refused).")
except Exception as e:
    st.error(f"❌ **Otro error:** {e}")
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
