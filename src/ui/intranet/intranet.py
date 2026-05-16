import streamlit as st
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.handlers.intranet_handler import intranet_workflow
from src.db.sp_connection import SP_Handler

# Dialogo de ingreso de credenciales para acceder a la intranet, pide el rut, clave y la descipcion de la clase
@st.dialog("Credenciales Intranet", dismissible=True)
def intranet_access(date: str, subject_code: str, subject_modules: list, presentes: pd.DataFrame) -> None:
    rut = st.text_input("**RUT**")
    password = st.text_input("**Contraseña**", type="password")
    description = st.text_input("**Description de la clase (Ej: Clase 1, Clase 2, etc.)**", )
    selected_module = st.selectbox("**Selecciona el módulo al que deseas subir la asistencia**", options=subject_modules)

    all_fields_filled = bool(rut and password and description and selected_module) # Verificar que todos los campos esten completos.
    if st.button("Subir asistencia a intranet", disabled=not all_fields_filled):
        with st.spinner("Subiendo asistencia...", show_time=True):
            place_holder = st.empty() # Placeholder para mostrar los mensajes de ejecucion.

            def ui_logger(type: str, message: str): # Se crea una funcion logger, la cual permite mostrar y cambiar un mensaje.
                if type == "warning":
                    place_holder.warning(message)
                elif type == "success":
                    place_holder.success(message)
                elif type == "error":
                    place_holder.error(message)

            intranet_workflow(get_proxy_url, st.secrets["INTRANET_URL"], st.secrets["INTRANET_LOGIN_URL"], rut, password, subject_code, selected_module, date, description, presentes, ui_logger)# Se llama a la funcion de handler.

@st.cache_data(ttl=60)
def get_proxy_url() -> str:
    try:
        handler = SP_Handler()
        return handler.get_proxy_url().replace("tcp://", "https://")
    except KeyError:
        st.error("Error: PROXY_URL no encontrado en los secretos.")
        return None