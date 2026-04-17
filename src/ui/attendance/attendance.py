from pandas.io.formats.format import return_docstring
import streamlit as st
import pandas as pd
import os

def main():
    st.title("Asistencia")
    st.write("Aquí puedes gestionar la asistencia de los estudiantes.")
    meeting_files = attendance_uploader()

    if st.button("Mergear archivos"):
        merged_handler(meeting_files[0][0], meeting_files[0][1])

 
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
            date = file.name.split("_")[2]+"/"+file.name.split("_")[3]+"/"+file.name.split("_")[4]
        elif date != file.name.split("_")[2]+"/"+file.name.split("_")[3]+"/"+file.name.split("_")[4]:
            st.write("Los archivos subidos no corresponden a la misma fecha.")
            return False
    return True

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
    duration = [attendance_file.iloc[1,3]] # Duracion de la reunion
    minimum_presentent_duration = int(duration[0])*0.9*0.5 # Minimo de duracion para quedar presente
    date = [attendance_file.iloc[1,4]]
    date = date[0]
    professor = attendance_file[attendance_file[3] == "No"].iloc[0] # El profesor es el unico que no es invitado
    professor =  professor[0] # Nombre del profesor de la reunion
    id_reunion = attendance_file.iloc[1,1]

    reunion_data = {"Duracion": duration, "Minimun": minimum_presentent_duration, "Date": date, "Profesor": professor, "ID": id_reunion}

    return reunion_data

# Obtener los datos de asistencia correo y duracion del estudiante en la reunion
def get_attendance_data(attendance_file):
    attendance_data = attendance_file.iloc[3:, [1, 2, 3]]
    attendance_data = attendance_data[attendance_data[3] != "No"]
    attendance_data = attendance_data[[1, 2]]
    attendance_data.rename(columns={1:"Correo", 2:"Tiempo"}, inplace = True)
    attendance_data["Correo"] = attendance_data["Correo"].str.lower()
    
    return attendance_data

# Obtener los datos de registro, nombre apellido, matricula y correo
def get_registration_data(registration_file):
    registration_data = registration_file.iloc[5:,[0,1,2,5]] # Se obtienen los datos de los estudiantes nombre, apellido, matricula y correo
    registration_data.rename(columns={0:"Nombre", 1:"Apellido", 2:"Correo", 5:"Matrícula"}, inplace = True)
    registration_data["Correo"] = registration_data["Correo"].str.lower()
    return registration_data

# Unir los datos de asistencia y registro
def merge_data (attendance_file,registration_file):
    attendance_data = get_attendance_data(attendance_file)
    registration_data = get_registration_data(registration_file)
    merge_data= pd.merge(attendance_data, registration_data, how = "outer", on="Correo")
    merge_data = merge_data.reindex(columns=["Correo", "Matrícula", "Nombre", "Apellido", "Tiempo"])
    return merge_data

# Unir la informacion
def write_merge_data(attendance_file, registration_file) -> bool:
    merged_data = merge_data(attendance_file, registration_file)
    reunion_data = get_reunion_data(attendance_file)
    reunion_id = reunion_data['ID']
    merged_data.to_csv(f'Archivos/merge_data_{reunion_id}.csv', index=False, encoding='utf-8')

    if os.path.exists(f"Archivos/merge_data_{reunion_id}.csv"):
        return True
    return False

# Manejar la logica de mergear los archivos y mostrar el resultado
def merged_handler(attendance_file, registration_file) -> bool:
    attendance_file.seek(0) # Reiniciar el puntero del archivo para que se pueda leer desde el principio
    registration_file.seek(0) # Reiniciar el puntero del archivo para que se pueda leer desde el principio
    attendance = pd.read_csv(attendance_file, header=None)
    registration = pd.read_csv(registration_file, header=None, skiprows=2)
    if write_merge_data(attendance, registration):
        show_merged_csv(f'Archivos/merge_data_{get_reunion_data(attendance)["ID"]}.csv', "Alumnos", "Archivo mergeado creado exitosamente.")
        return True
    else:
        st.write("Error al crear el archivo mergeado.")
        return False

# Funcion para mostrar el csv mergeado en la interfaz, puede ser reutilizada para mostrar cualquier csv mergeado, solo se necesita el path del archivo, un titulo y un mensaje de exito
def show_merged_csv(merged_file, title_text:str, succ_message:str)-> bool:
    if merged_file is not None:
        df = pd.read_csv(merged_file)
        st.write(f"### {title_text}")
        st.write(succ_message)
        st.dataframe(df)             
        return True
    return False

main()