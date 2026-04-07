import streamlit as st

configs = st.Page("configs/modules.py", title="Configuración de módulos", icon=":material/settings:")
asistencia = st.Page("attendance/attendance.py", title="Registro de asistencia", icon=":material/check_circle:") 
pg = st.navigation(
    {
        "Asistencia" : [asistencia],
        "Configuración" : [configs]
    }
)
pg.run()