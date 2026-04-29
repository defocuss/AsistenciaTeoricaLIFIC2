import streamlit as st
import pandas as pd
import plotly.express as px

def main():
    st.title("Asistencia")
    st.write("Aquí puedes gestionar la asistencia de los estudiantes.")
    meeting_files = attendance_uploader()

    if st.button("Mergear archivos") and meeting_files:
        merged_handler(meeting_files)

 
def show_meeting_files_table(meeting_files: list) -> None:
    rows = []
    for attendance_file, registration_file in meeting_files:
        attendance_parts = attendance_file.name.split("_")
        meeting_id = attendance_parts[1] if len(attendance_parts) > 1 else "No identificado"

        rows.append({
            "Meeting ID": meeting_id,
            "Attendance file": attendance_file.name,
            "Registration file": registration_file.name,
        })

    table = pd.DataFrame(rows)
    st.subheader("Archivos detectados por reunión")
    st.dataframe(table, use_container_width=True, hide_index=True)

# Verificar el formato interior del archivo participants
def verify_attendance_file(data) -> bool:
    valor = [data.iloc[0,0]]

    if valor[0] == "Tema":
        return True 
    else:
        return False

# Verificar el formato interior del archivo registration
def verify_registration_file(data) -> bool:
    valor = [data.iloc[0,2]]

    if valor[0] == "Horario programado":
        return True
    else:
        return False

def attendance_uploader() -> list:
    files = st.file_uploader("Sube el archivo de asistencia", 
        max_upload_size=10,
        type=["csv"], 
        accept_multiple_files=True)
    
    file_checker(files)
    meeting_files = get_same_meeting_files(files)
    return meeting_files

# Chekear la cantidad ingresada de archivos, retorna True si todo es correcto
def file_checker(files:list) -> bool:
    if len(files) % 2 != 0:
        st.write("Por favor sube ambos archivos: participantes y registro.")
        return False

    for file in files:
        if not format_checker(file):
            st.write(f"Archivo {file.name} no tiene el formato correcto.")
            return False
    
    if not date_checker(files):
        return False

    return True

# Verificar la fecha del archivo
def date_checker(files:list) -> bool:
    date = ""
    for file in files:
        if date == "":
            date = read_csv_date(file)
        elif date != read_csv_date(file):
            st.write("Los archivos subidos no corresponden a la misma fecha.")
            return False
    return True

# Leer la fecha del archivo para la verificacion de que ambos archivos corresponden a la misma reunion
def read_csv_date(file) -> str:
    date = ""
    file.seek(0)
    if file.name.split("_")[0] == "participants":
        data = pd.read_csv(file, header=None)
        file.seek(0)
        date = [data.iloc[1,4]]
        date = reformat_date(date[0].split(" ")[0])
    elif file.name.split("_")[0] == "registration":
        data = pd.read_csv(file, header=None, skiprows=2)
        file.seek(0)
        date = [data.iloc[1,2]]
        date = reformat_date(date[0].split(" ")[0])

    return date

# Reformatear la fecha para que sea igual en ambos archivos y se pueda comparar, el formato de fecha puede variar dependiendo del idioma del usuario, por eso se hace esta funcion para estandarizarlo a un formato unico y poder comparar las fechas de ambos archivos
def reformat_date(date:str) -> list:
    date_parts = date.split(" ")
    real_date = date_parts[0].split("/")

    if len(real_date[0]) != 4:
        real_date = [real_date[2], real_date[0], real_date[1]]
    return real_date

# Chekea el formato del archivo
def format_checker(file) -> bool:
    if "participants" in file.name:
        read_data = pd.read_csv(file, header=None)
        return verify_attendance_file(read_data)
    elif "registration" in file.name:
        read_data = pd.read_csv(file, header=None, skiprows=2)
        return verify_registration_file(read_data)
    else:
        st.write("Archivo no reconocido. Asegúrate de subir los archivos correctos.")
        return False


def get_same_meeting_files(files:list) -> list:
    meeting_organized_list = []
    seen_meetings_ids = set()
    for file in files:
        meeting_id = file.name.split("_")[1]
        print(meeting_id)
        if meeting_id in seen_meetings_ids:
            continue
        seen_meetings_ids.add(meeting_id)
        if "participants" in file.name:
            attendance_file = file
            for second_file in files:
                if meeting_id in second_file.name and "registration" in second_file.name:
                    registration_file = second_file
                    meeting_organized_list.append([attendance_file, registration_file])
        elif "registration" in file.name:
            registration_file = file
            for second_file in files:
                if meeting_id in second_file.name and "participants" in second_file.name:
                    attendance_file = second_file
                    meeting_organized_list.append([attendance_file, registration_file])
    
    print(len(meeting_organized_list))
    print(len(files))
    if len(meeting_organized_list) != len(files) // 2:
        st.write("No se encontraron archivos correspondientes a la misma reunión.")
        return []
    return meeting_organized_list

# Obtener un diccionario de la informacion de la reunion, duracion, minimo para presente, fecha y el profesor
def get_reunion_data(attendance_file) -> dict:
    attendance_file.seek(0)
    attendance = pd.read_csv(attendance_file, header=None)
    duration = attendance.iloc[1,3] # Duracion de la reunion
    minimum_presentent_duration = int(duration)*0.9*0.5 # Minimo de duracion para quedar presente
    date = [attendance.iloc[1,4]]
    date = date[0]
    id_reunion = attendance.iloc[1,1]

    reunion_data = {"Duracion": duration, "Minimum": minimum_presentent_duration, "Date": date, "ID": id_reunion}
    print(reunion_data)
    return reunion_data

# Obtener los datos de asistencia correo y duracion del estudiante en la reunion
def get_attendance_data(attendance_file) -> pd.DataFrame:
    attendance = pd.read_csv(attendance_file, header=None)
    attendance_data = attendance.iloc[3:, [1, 2, 3]]
    attendance_data = attendance_data[attendance_data[3] != "No"]
    attendance_data = attendance_data[[1, 2]]
    attendance_data.rename(columns={1:"Correo", 2:"Tiempo"}, inplace = True)
    attendance_data["Correo"] = attendance_data["Correo"].astype(str).str.strip().str.lower()
    
    return attendance_data

# Obtener los datos de registro, nombre apellido, matricula y correo
def get_registration_data(registration_file) -> pd.DataFrame:
    registration = pd.read_csv(registration_file, header=None, skiprows=2)
    registration_data = registration.iloc[4:,[0,1,2,5]] # Se obtienen los datos de los estudiantes nombre, apellido, matricula y correo
    registration_data.rename(columns={0:"Nombre", 1:"Apellido", 2:"Correo", 5:"Matrícula"}, inplace = True)
    registration_data["Correo"] = registration_data["Correo"].astype(str).str.strip().str.lower()
    return registration_data


# Unir los datos de asistencia y registro
def merge_data(files:list) -> pd.DataFrame:
    attendance_data = None
    registration_data = None
    merge_data = None
    for file_pair in files:
        file_pair[0].seek(0) # Reiniciar el puntero del archivo para que se pueda leer desde el principio
        file_pair[1].seek(0) # Reiniciar el puntero del archivo para que se pueda leer desde el principio
        attendance_data = get_attendance_data(file_pair[0])
        registration_data = get_registration_data(file_pair[1])
        var_merge_data= pd.merge(attendance_data, registration_data, how = "outer", on="Correo")
        var_merge_data = var_merge_data.reindex(columns=["Correo", "Matrícula", "Nombre", "Apellido", "Tiempo"])
        if merge_data is None:
            merge_data = var_merge_data
        else:
            merge_data = pd.concat([merge_data, var_merge_data], ignore_index=True)
    merge_data["Tiempo"] = merge_data["Tiempo"].fillna(0).astype(int) # Rellenar los valores nulos de tiempo con 0 y convertir a entero para poder comparar con el minimo de tiempo para quedar presente
    merge_data = clean_tuition_number(merge_data)
    merge_data_final = merge_data.groupby(["Matrícula", "Correo"], as_index=False).agg({
        "Nombre": "first",
        "Apellido": "first",
        "Tiempo": "sum"
    })

    return merge_data_final

# Se limpia la matricula
def clean_tuition_number(merge_data) -> pd.DataFrame:
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.replace(r'["=]', r"", regex=True)
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.replace(r" ", r"", regex=False) #Se quitan los espacios 
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.replace(r".", r"", regex=False) #Se quitan los puntos
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.replace(r",", r"", regex=False) #Se quitan los puntos
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.replace(r"-", r"", regex=False) #Se quitan los guiones 
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.replace(r"_", r"", regex=False) #Se quitan los guiones 
    merge_data['Matrícula'] = merge_data['Matrícula'].astype('str').str.upper() #Transforma a mayuscula
    return merge_data

# Unir la informacion
def write_merge_data(files:list, minimum_duration:int) -> pd.DataFrame:
    merged_data = merge_data(files)
    merged_data = clean_tuition_number(merged_data) 
    merged_data["Estado"] = ["Presente" if a >= minimum_duration else "Ausente" for a in merged_data["Tiempo"]]

    reunion_data = get_reunion_data(files[0][0])
    reunion_date = reunion_data['Date'].replace("/", "-").replace(" ", "--") # Reemplazar los caracteres de fecha para que sea compatible con el nombre del archivo

    return merged_data

# Manejar la logica de mergear los archivos y mostrar el resultado
def merged_handler(files:list) -> bool:
    for file_pair in files:
        file_pair[0].seek(0) # Reiniciar el puntero del archivo para que se pueda leer desde el principio
        file_pair[1].seek(0) # Reiniciar el puntero del archivo para que se pueda leer desde el principio
    date = get_reunion_data(files[0][0])["Date"]
    merged_data = write_merge_data(files, get_reunion_data(files[0][0])["Minimum"])
    if merged_data is not None:
        show_reunion_metrics(get_reunion_metrics(merged_data, get_reunion_data(files[0][0])["Minimum"]), date, get_reunion_data(files[0][0])["Duracion"])
        show_merged_csv(merged_data, "Todos los alumnos", "Archivo mergeado creado exitosamente.", date)
        show_present_students(merged_data, get_reunion_data(files[0][0])["Minimum"], date)
        show_absent_students(merged_data, get_reunion_data(files[0][0])["Minimum"], date)
        return True
    else:
        st.write("Error al crear el archivo mergeado.")
        return False

# Muestra los estudiantes presentes en la reunion.
def show_present_students(merged_file:pd.DataFrame, minimum_duration:int, fecha:str) -> bool:
    if merged_file is not None:
        present_students = merged_file[merged_file["Tiempo"] >= minimum_duration]
        st.write("### Estudiantes presentes")
        st.dataframe(present_students, use_container_width=True)
        csv_data = present_students.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar presentes", csv_data, "Alumnos presentes {}.csv".format(fecha), "text/csv", key='Presentes-csv')
        return True
    return False

# Muestra los estudiantes ausentes en la reunion.
def show_absent_students(merged_file:pd.DataFrame, minimum_duration:int, fecha:str) -> bool:
    if merged_file is not None:
        absent_students = merged_file[merged_file["Tiempo"] < minimum_duration]
        st.write("### Estudiantes ausentes")
        st.dataframe(absent_students, use_container_width=True)
        csv_data = absent_students.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar ausentes", csv_data, "Alumnos ausentes {}.csv".format(fecha), "text/csv", key='Ausentes-csv')
        return True
    return False

# Funcion para mostrar el csv mergeado en la interfaz, puede ser reutilizada para mostrar cualquier csv mergeado, solo se necesita el path del archivo, un titulo y un mensaje de exito
def show_merged_csv(merged_file:pd.DataFrame, title_text:str, succ_message:str, fecha:str)-> bool:
    if merged_file is not None:
        st.write(f"### {title_text}")
        st.write(succ_message)
        st.dataframe(merged_file, use_container_width=True)
        csv_data = merged_file.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar todos los alumnos", csv_data, "Alumnos {}.csv".format(fecha), "text/csv", key='Clasificados-csv')
        return True
    return False

# Obtener las metricas de la reunion, total de estudiantes, presentes, ausentes y porcentajes
def get_reunion_metrics(merged_file:pd.DataFrame, minimum_duration:int) -> dict:
    total_students = merged_file["Tiempo"].size
    present_students = merged_file[merged_file["Tiempo"] >= minimum_duration].shape[0]
    absent_students = merged_file[merged_file["Tiempo"] < minimum_duration].shape[0]
    percentage_present = (present_students * 100) / total_students if total_students > 0 else 0
    percentage_absent = (absent_students * 100) / total_students if total_students > 0 else 0

    metrics = {
        "Total": total_students,
        "Presentes": present_students,
        "Ausentes": absent_students,
        "Porcentaje Presentes": percentage_present,
        "Porcentaje Ausentes": percentage_absent,
        "Minimo": minimum_duration,
        "merged_file": merged_file
    }
    return metrics

# Mostrar las metricas de la reunion, total de estudiantes, presentes, ausentes y porcentajes
def show_reunion_metrics(metrics:dict, reunion_date:str, maximo:int) -> None:
    st.write(f"### Métricas de la reunión del {reunion_date}")
    col11, col22, col33 = st.columns(3)
    col33.metric("", "")
    col11.metric("Tiempo total", "{} min".format(maximo))
    col22.metric("Tiempo mínimo para estar presente", "{} min".format(metrics["Minimo"]))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de estudiantes", metrics["Total"])
    col2.metric("Presentes", metrics["Presentes"], f"{metrics['Porcentaje Presentes']:.2f}%")
    col3.metric("Ausentes", metrics["Ausentes"], f"{metrics['Porcentaje Ausentes']:.2f}%")
    show_graph(metrics)

# Mostrar el grafico de la reunion, porcentaje de presentes y ausentes
def show_graph(metrics:dict) -> None:
    fig = px.pie(metrics["merged_file"], values=[metrics["Presentes"], metrics["Ausentes"]], names=["Presentes", "Ausentes"], hole=0.4, title="Gráfico de asistencia")
    fig.update_traces(textposition="inside", textinfo="percent", textfont=dict(size=25))
    st.plotly_chart(fig)

main()