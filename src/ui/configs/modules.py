import streamlit as st
from st_supabase_connection import SupabaseConnection, execute_query

st.title("Configuración de módulos")
st.write("Aquí puedes configurar los módulos de tu asignatura.",
    "Selecciona la asignatura y el módulo para configurar los parámetros de asistencia.")

st_supabase_client = st.connection(
    name="Supabase",
    type=SupabaseConnection,
    ttl=None,
)

signatures = execute_query(
    st_supabase_client.table("Asignatura").select("*"),
    ttl=0
)

# Preview of fetching data from Supabase

tab1, tab2, tab3, tab4 = st.tabs(["A1", "A2", "A3", "A4"])
with tab1:
    st.write(signatures.data[0])
with tab2:
    st.write(signatures.data[1])
with tab3:
    st.write(signatures.data[2])
with tab4:
    st.write(signatures.data[3])
