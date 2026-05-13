import streamlit as st 

if not st.user.is_logged_in:
    Col1, Col2, Col3 = st.columns(3)

    Col2.image('https://i.imgur.com/YMei8p1.png', width = "stretch")

    st.title("Asistencia Teórica LIFIC")
    st.header("Aplicación para el registro de asistencia teórica de la línea integradora.")
    st.write("Para poder utilizar la aplicación, por favor inicie sesión con su correo institucional.")
    st.button("Iniciar sesión", on_click=st.login)