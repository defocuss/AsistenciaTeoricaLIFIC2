import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import gspread_dataframe as gd
import plotly.express as px
from PIL import Image


# Connect to Google Sheets

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)


client = gspread.authorize(credentials=credentials)


#Funciones

def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def verificar1(data):

    valor = [data.iloc[0,0]]

    if valor[0] == "Tema":
        return 1
    else:
        return 0

def verificar2(data):

    valor = [data.iloc[0,0]]

    if valor[0] == "First Name":
        return 1
    else:
        return 0


#Titulo y subir archivos

Col1, Col2, Col3 = st.columns(3)

#if st.theme() == 'light':

Col2.image('https://i.imgur.com/YMei8p1.png',use_container_width = True)

# else:

#     Col2.image('https://i.imgur.com/law7tvC.png',use_column_width='auto')

st.title("Asistencia Teórica")

st.header("Ingresar archivos")

link = '[Manual obtención archivos](https://docs.google.com/document/d/1W0GjteAhdSj_mM0hi0mL9GFfRTYB4hqnM9qlzVXSEiY/edit?usp=sharing)'
st.markdown(link, unsafe_allow_html=True)

asistenciaFile = st.file_uploader("Participantes (participants_xxxxxxxx.csv)", type="csv")
registroFile = st.file_uploader("Registro (xxxxxxxx_RegistrationReport.csv)", type="csv")

#Cuando se suben los archivos

if (asistenciaFile and registroFile) is not None: #Varificar si se suben los archivos

    #Trabajo de analisis de datos Pandas

    asistencia = pd.read_csv(asistenciaFile, header=None)
    registro = pd.read_csv(registroFile, header=None, skiprows = 2)

    if verificar1(asistencia) or verificar2(registro): #Verifica el formato de los csv subidos

        duracionTotal = [asistencia.iloc[1,3]]
        maximo =  int(duracionTotal[0])
        minimo = int(duracionTotal[0])*0.9*0.5
        fecha = [asistencia.iloc[1,4]]
        fecha = fecha[0]

        asistencia = asistencia[asistencia[3] != "No"] #Se quita el creador de la reunion

        datosAsistencia = asistencia.iloc[3:,[1,2]]
        datosRegistro = registro.iloc[1:,[0,1,5,2]]

        datosAsistencia.rename(columns={1:"Correo", 2:"Tiempo"}, inplace = True)
        datosRegistro.rename(columns={0:"Nombre", 1:"Apellido", 5:"Matrícula", 2:"Correo"}, inplace = True)

        datosRegistro["Correo"] = datosRegistro["Correo"].str.lower()

        datosMerge = pd.merge(datosAsistencia, datosRegistro, how = "outer")
        datosMerge = datosMerge.reindex(columns=["Correo", "Matrícula", "Nombre", "Apellido", "Tiempo"])

        
        datosMerge['Matrícula'] = datosMerge['Matrícula'].astype('str').str.replace(r" ", r"", regex=False) #Se quitan los espacios 
        datosMerge['Matrícula'] = datosMerge['Matrícula'].astype('str').str.replace(r".", r"", regex=False) #Se quitan los puntos
        datosMerge['Matrícula'] = datosMerge['Matrícula'].astype('str').str.replace(r",", r"", regex=False) #Se quitan los puntos
        datosMerge['Matrícula'] = datosMerge['Matrícula'].astype('str').str.replace(r"-", r"", regex=False) #Se quitan los guiones 
        datosMerge['Matrícula'] = datosMerge['Matrícula'].astype('str').str.replace(r"_", r"", regex=False) #Se quitan los guiones 
        datosMerge['Matrícula'] = datosMerge['Matrícula'].astype('str').str.upper() #Transforma a mayuscula


        datosMerge["Tiempo"] = datosMerge["Tiempo"].fillna(0).astype(int)
        datosMerge["Estado"] = ["Presente" if a >= minimo else "Ausente" for a in datosMerge["Tiempo"]]

        presentes = datosMerge[datosMerge["Tiempo"] >= minimo]
        ausentes = datosMerge[datosMerge["Tiempo"] < minimo]

        datosFinales = datosMerge.copy()
        datosFinales.insert(loc = 6, column = "Matrícula Presentes", value = presentes['Matrícula'])

        #Mostrar resultados y descargar

        #Variables

        total = datosMerge["Tiempo"].size
        totalPresentes = presentes["Tiempo"].size
        totalAusentes = ausentes["Tiempo"].size
        porcentajePresentes = (totalPresentes * 100)/total
        porcentajeAusentes = (totalAusentes * 100)/total

        st.header("Resultados")

        st.subheader("Resumen")

        st.write("<p style='margin:2px'>Fecha de la reunión</p>\n<p style='font-size:25px;margin-botton:20px;'>{}</p>".format(fecha), unsafe_allow_html=True)

        col11, col22, col33 = st.columns(3)

        col33.metric("", "")
        col11.metric("Tiempo total", "{} min".format(maximo))
        col22.metric("Tiempo mínimo para estar presente", "{} min".format(minimo))

        col1, col2, col3 = st.columns(3)
        col1.metric("Participantes", total,"", delta_color="off")
        col2.metric("Presentes", totalPresentes,  "{}%".format(int(porcentajePresentes)))
        col3.metric("Ausentes", totalAusentes,  "{}%". format(int(porcentajeAusentes)))

        fig = px.pie(datosMerge, values=[totalPresentes, totalAusentes], names=["Presentes", "Ausentes"], hole=0.4,  title="Gráfico de asistencia")

        fig.update_traces(textposition= "inside", textinfo= "percent", textfont=dict(size=25))

        st.plotly_chart(fig)
        
        archivoClass = convert_df(datosFinales)
        archivoPresentes = convert_df(presentes)
        archivoAusentes = convert_df(ausentes)

        st.subheader("Alumnos clasificados")
        st.write(datosFinales) 
        st.download_button("Descargar", archivoClass, "Alumnos Clasificados {}.csv".format(fecha), "text/csv", key='Clasificados-csv')
        st.subheader("Alumnos presentes")
        st.write(presentes) 
        st.download_button("Descargar", archivoPresentes, "Alumnos Clasificados {}.csv".format(fecha), "text/csv", key='presentes-csv')
        st.subheader("Alumnos ausentes")
        st.write(ausentes)
        st.download_button("Descargar", archivoAusentes, "Alumnos Clasificados {}.csv".format(fecha), "text/csv", key='ausentes-csv')

        #Subir a Google drive

        st.header("Subir datos a Google Drive")

        colAsignatura, colModulo, colClase = st.columns(3)

        with colAsignatura:

            asignatura = st.selectbox("Asignatura", ("A1", "A2", "A3", "A4"))

        with colModulo:

            if asignatura == "A1":

                modulo = st.selectbox("Módulo", ("1", "2"))

            if asignatura == "A2":

                modulo = st.selectbox("Módulo", ("1"))

            if asignatura == "A3":

                modulo = st.selectbox("Módulo", ("1", "2"))

            if asignatura == "A4":

                modulo = st.selectbox("Módulo", ("Mati", "Bryan", "x-Mati", "x-Bryan"))


        with colClase:

            if asignatura == "A1":

                clase = st.selectbox("Clase", ("01", "03", "05", "07", "09", "11", "13", "15", "17", "19", "21", "23", "25", "27", "29", "31"))

            if asignatura == "A2":

                clase = st.selectbox("Clase", ("01", "03", "05", "07", "09", "11", "13", "15", "17", "19", "21", "23", "25", "27", "29"))

            if asignatura == "A3":

                clase = st.selectbox("Clase", ("01", "03", "05", "07", "09", "11", "13", "15", "17", "19", "21", "23", "25", "27", "29"))

            if asignatura == "A4":

                if modulo == "x-Mati" or modulo == "x-Bryan":

                    clase = st.selectbox("Clase", ("02", "05", "08", "11", "14", "17", "20", "23", "26", "29", "32", "37", "40", "43"))

                else:
                    
                    clase = st.selectbox("Clase", ("01", "04", "07", "10", "13", "16", "19", "22", "25", "28", "31", "34", "36", "39", "42"))

        with st.spinner("Subiendo Datos, por favor esperar"):

            if st.button('Subir datos'):

                if asignatura == "A1" and modulo == "1":
                    sheet = client.open_by_url(st.secrets["A1modulo1"])
                elif asignatura == 'A1' and modulo == "2":
                    sheet = client.open_by_url(st.secrets["A1modulo2"])
                elif asignatura == "A2" and modulo == "1":
                    sheet = client.open_by_url(st.secrets["A2modulo1"])
                elif asignatura == "A2" and modulo == "2":
                    sheet = client.open_by_url(st.secrets["A2modulo2"])
                elif asignatura == "A3" and modulo == "1":
                    sheet = client.open_by_url(st.secrets["A3modulo1"])
                elif asignatura == "A4" and modulo == "Mati":
                    sheet = client.open_by_url(st.secrets["A4moduloMati"])
                elif asignatura == "A4" and modulo == "Bryan":
                    sheet = client.open_by_url(st.secrets["A4moduloBryan"])
                elif asignatura == "A4" and modulo == "x-Mati":
                    sheet = client.open_by_url(st.secrets["A4moduloxMati"])
                elif asignatura == "A4" and modulo == "x-Bryan":
                    sheet = client.open_by_url(st.secrets["A4moduloxBryan"])
                
                worksheet_list = sheet.worksheets()

                claseWS = "Clase {}".format(clase)

                worksheet = sheet.worksheet(claseWS)

                gd.set_with_dataframe(worksheet, datosFinales)

                st.success("Datos Subidos!")
    
    else:

        st.error("El formato de los archivos es incorrecto")

    
