from pandas.io.formats.format import return_docstring
import streamlit as st
import pandas as pd

def main():
    st.title("Asistencia")
    st.write("Aquí puedes gestionar la asistencia de los estudiantes.")
    meeting_files = attendance_uploader()
    show_meeting_files_table(meeting_files)

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

def verify_attendance_file(data) -> bool:
    valor = [data.iloc[0,0]]

    if valor[0] == "Tema":
        return True 
    else:
        return False

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

def date_checker(files:list) -> bool:
    date = ""
    for file in files:
        if date == "":
            date = file.name.split("_")[2]+"/"+file.name.split("_")[3]+"/"+file.name.split("_")[4]
        elif date != file.name.split("_")[2]+"/"+file.name.split("_")[3]+"/"+file.name.split("_")[4]:
            st.write("Los archivos subidos no corresponden a la misma fecha.")
            return False
    return True

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

if __name__ == "__main__":
    main()