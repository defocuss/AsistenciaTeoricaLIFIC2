import streamlit as st
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.sp_connection import SP_Handler
from src.handlers.gs_handler import upload_presents_spreadsheet

@st.dialog("Seleccionar clase", dismissible=True)
def select_class(subject_code: str, subject_modules: list, students: pd.DataFrame) -> None:
    selected_module = st.selectbox("**Selecciona el módulo al que deseas subir la asistencia**", options=subject_modules)
    classes = get_clases_by_module(selected_module, subject_code) # Se obtiene la lista de clases del modulo seleccionado.
    selected_class = st.selectbox("**Selecciona la clase a la que deseas subir la asistencia**", options=classes)

    all_fields_filled = bool(selected_module and selected_class) # Verificar que todos los campos esten completos.
    if st.button("Subir asistencia sheets", disabled=not all_fields_filled):
        upload_presents_spreadsheet(selected_class, selected_module, subject_code, students)


def get_clases_by_module(n_modulo:int, signature_code:str) -> list:
    try:
        handler = SP_Handler()
        return handler.get_module_classes(n_modulo, signature_code)
    except Exception as e:
        st.error(f"Error al obtener las clases del módulo: {e}")