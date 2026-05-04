import sys
from pathlib import Path
from time import sleep
import pandas as pd
import streamlit as st

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.sp_connection import SP_Handler


def main():
    st.title("Configuración de módulos")
    st.write("Página para configuración de los módulos de cada asignatura.",
        "Selecciona la asignatura y el módulo para configurar los parámetros de asistencia.")
    
    sp_handler = SP_Handler()

    show_all_info(sp_handler)

def show_all_info(sp_handler: SP_Handler) -> None:
    signature_tabs = [row["abrevacion"] for row in sp_handler.get_signatures()]
    profesors = [row["nombre"] for row in sp_handler.get_professors()]
    if not signature_tabs:
        st.info("No hay asignaturas configuradas.")
        return
    tabs = st.tabs(signature_tabs)
    # iterate through both lists simultaneously
    for tab_name, tab_container in zip(signature_tabs, tabs):
        with tab_container:
            edited_df = create_data_editor(tab_name, profesors, sp_handler)
            has_errors = data_editor_checkers(edited_df)
            if st.button(f"Guardar cambios de {tab_name}", key=f"save_{tab_name}", disabled=has_errors):
                with st.spinner("Guardando cambios...", show_time=True):
                    upload_edited_data(sp_handler, tab_name, edited_df)
                st.success("Cambios guardados exitosamente.")
                sleep(1)
                if tab_name in st.session_state:
                    del st.session_state[tab_name]
                st.rerun()

def create_data_editor(tab_name:str, profesors:list, sp_handler: SP_Handler) -> None:
    return st.data_editor(
        create_data_frame(tab_name, sp_handler), 
        num_rows="dynamic", key=tab_name,
        hide_index=True,
        column_config= {
            "id_modulo": None,
            "Módulo": st.column_config.NumberColumn(
                "Módulo", 
                min_value=1, max_value=40, step=1,
                disabled=False,required=False),
            "Profesores": st.column_config.MultiselectColumn( #array de profes 
                "Profesores", options=profesors, required=False),
            "Práctico": st.column_config.CheckboxColumn("Práctico", disabled=False),
            "Clases": st.column_config.TextColumn("Clases", required=False),
            "Hoja de asistencia": st.column_config.LinkColumn("Hoja de asistencia", disabled=False, required=False)
    })

def data_editor_checkers(edited_df : pd.DataFrame) -> bool:
    output = False
    if edited_df["Módulo"].isnull().any() or edited_df["Módulo"].eq("").any():
        st.error("Todos los módulos deben tener un número asignado.")
        output = True
    if edited_df["Módulo"].duplicated().any() or edited_df["Módulo"].eq(0).any():
        st.error("No puede haber módulos con el mismo número.")
        output = True
    if edited_df["Clases"].isnull().any() or edited_df["Clases"].eq("").any():
        st.error("Todos los módulos deben tener clases asignadas.")
        output = True
    if edited_df["Hoja de asistencia"].isnull().any() or edited_df["Hoja de asistencia"].eq("").any():
        st.error("Todos los módulos deben tener una hoja de asistencia asignada.")
        output = True
    elif not edited_df["Hoja de asistencia"].apply(lambda x: x.startswith("https://")).all():
        st.error("Todas las hojas de asistencia deben ser URLs válidas.")
        output = True
    return output

def create_data_frame(signature:str, sp_handler: SP_Handler) -> pd.DataFrame:
    modules = sp_handler.get_subject_modules(signature)
    if modules is None:
        st.error("Error al cargar los módulos.")
    data = []
    for module in modules:

        clases = ", ".join(module["clases"]) if module["clases"] else ""

        data.append({
            "id_modulo": module["id_modulo"],
            "Módulo": module["numero_modulo"],
            "Profesores": [x["nombre"] for x in module["Profesor"]],
            "Práctico": module["es_practico"],
            "Clases": clases,
            "Hoja de asistencia": module["hoja_de_calculo"]
        })

    if data == []:
        data.append({
            "id_modulo": None, 
            "Módulo": "",
            "Profesores": [],
            "Práctico": "",
            "Clases": "",
            "Hoja de asistencia": ""
        })
    return pd.DataFrame(data)

def upload_edited_data(sp_handler: SP_Handler, signature: str, edited_df: pd.DataFrame) -> None:
    existing_modules = sp_handler.get_subject_modules(signature)
    professors = sp_handler.get_professors()

    # 1) Delete records that were removed in the editor

    edited_df = delete_modules(sp_handler, edited_df, existing_modules)
    
    # 2) Upsert new and edited records of Modulo table

    edited_df = upsert_modules(sp_handler, signature, edited_df)

    # 3 ) Update Profesor_Modulo table
    
    upsert_modulo_profesor(sp_handler, edited_df, professors)

def upsert_modulo_profesor(sp_handler: SP_Handler, edited_df: pd.DataFrame, professors:list) -> None:
    for index, row in edited_df.iterrows():
        
        if not sp_handler.drop_professors_from_module(row["id_modulo"]):
            break
        if row["Profesores"] == None or row["Profesores"] == []:
            continue
        id_profesores = [profesor["id_profesor"] for profesor in professors if profesor["nombre"] in row["Profesores"]]
        if not sp_handler.insert_professors_to_module(row["id_modulo"], id_profesores):
            break

def upsert_modules(sp_handler: SP_Handler, signature: str, edited_df: pd.DataFrame) -> pd.DataFrame:
    id_asignatura = sp_handler.get_signature_id(signature)
    for index, row in edited_df.iterrows():
        payload = {
            "id_asignatura": id_asignatura,
            "numero_modulo": row["Módulo"],
            "hoja_de_calculo": row["Hoja de asistencia"],
            "clases" : clases_parser_out(row["Clases"], row["Módulo"]),
            "es_practico": row["Práctico"],
        }
        if pd.notna(row["id_modulo"]):
            payload["id_modulo"] = int(row["id_modulo"])
        # Table Module upsert
        id_modulo = sp_handler.upsert_module(payload)
        if id_modulo is None:
            break;
        if id_modulo > 0:
            edited_df.at[index, "id_modulo"] = id_modulo
    
    return edited_df

def clases_parser_out(clases_str:str, modulo: int) -> list[str]:
    clases_out = []
    for clase in clases_str.split(","):
        clase = clase.strip()
        clase = (clase.replace(" ", "").replace("-", "").replace(".", "")
            .replace("_", "").replace('"', '').replace("(", "")
            .replace(")", "").replace("[", "").replace("]", ""))
        if clase == "" or not clase.isdigit():
            continue
        if len(clase) == 1 and clase != "0":
            clase = "0" + clase
        if len(clase) > 2:
            st.error(f"Clase {clase} no válida para Módulo {modulo}. Debe ser un número de dos dígitos. Continuando...")
            continue
        if clase in clases_out:
            st.error(f"Clase {clase} repetida para Módulo {modulo}. Continuando...")
            continue
        clases_out.append(clase)
    clases_out.sort()
    return clases_out

def delete_modules(sp_handler: SP_Handler, edited_df: pd.DataFrame, existing_modules: list) -> pd.DataFrame:
    existing_ids = {module["id_modulo"] for module in existing_modules}
    removed_ids = existing_ids - set(edited_df["id_modulo"].dropna())
    for id_modulo in removed_ids:
        if not sp_handler.delete_module(id_modulo):
            break
        edited_df.drop(edited_df[edited_df["id_modulo"] == id_modulo].index, inplace=True)
    return edited_df

main()


