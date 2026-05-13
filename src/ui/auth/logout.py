import streamlit as st
import time

def logout():
    Col1, Col2, Col3 = st.columns(3)
    st.title("¿Deseas cerrar sesión?")
    with st.container(border=True):
        st.subheader("Información de la cuenta")
        if hasattr(st, 'user') and st.user:
            email = getattr(st.user, 'email', 'Correo no disponible')
        
        if hasattr(st, 'user') and st.user:
            nombre = getattr(st.user, 'name', 'Nombre no disponible')
        
        st.info(f"**Nombre:**  \n{nombre}")
        st.info(f"**Correo institucional:**  \n{email}")
    if st.button("Cerrar sesión"):
        with st.spinner("Cerrando sesión..."):
            time.sleep(3) 
            st.success("Has cerrado sesión.")
            st.logout() 
        st.rerun()

logout()