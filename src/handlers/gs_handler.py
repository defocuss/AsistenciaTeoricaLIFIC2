from gspread import worksheet
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import gspread_dataframe as gd
import sys
from pathlib import Path

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.sp_connection import SP_Handler

def prepare_students_dataframe(students: pd.DataFrame) -> pd.DataFrame:
    df = students.copy()
    if "Matricula" in df.columns:
        df["Matricula"] = df["Matricula"].astype(str)
    
    if "Estado" in df.columns and "Matricula" in df.columns:
        df["Matricula Presente"] = df["Matricula"].where(df["Estado"] == "Presente", "")
    
    return df

def upload_presents_spreadsheet(class_number: str, subject_module:int, subject_code:str, students:pd.DataFrame, reunion_time: str) -> bool:
    with st.spinner("Subiendo datos a Sheets..."):
        try:
            sheet = get_sheet(subject_module, subject_code) # Se obtiene la hoja de google sheets.
            total_rows = len(students) + 1

            sheet_name = f"Clase {class_number}" # Revisar, ya que nunca va a encontrar la hoja
            worksheet = get_worksheet(sheet, sheet_name, total_rows) # Se obtiene la hoja de la clase

            worksheet = format_worksheet(worksheet, total_rows) # Se formatea la hoja

            students_transformed = prepare_students_dataframe(students)

            gd.set_with_dataframe(worksheet, students_transformed, string_escaping="full")

            worksheet.update_acell('I3', 'Tiempo (min)') # Se actualzia la celda con titulo de tiempo
            worksheet.update_acell('I4', reunion_time) # Se actualiza la celda con el tiempo de reunion
                        
            st.success("Asistencia subida exitosamente a sheets")
        except Exception as e:
            st.error(f"Error al subir asistencia: {e}")

# Se arregla el formato de la hoja, como bordes negros y el centrado.
def format_worksheet(worksheet: gspread.Worksheet, range: int) -> gspread.Worksheet:
    worksheet.format("A1:G1", {
                "textFormat": {
                    "bold": True,
                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                },
                "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                "horizontalAlignment": "CENTER"
            })

    # Formato de texto para columnas de matrícula (A y G)
    worksheet.format(f"A2:A{range}", {
        "numberFormat" : {
            "type" : "TEXT"
        }
    })
    worksheet.format(f"G2:G{range}", {
        "numberFormat" : {
            "type" : "TEXT"
        }
    })

    # Formato de bordes negros para toda la tabla y centrar el texto, se puede cambiar
    worksheet.format(f"A1:G{range}", {
        "borders": {
            "top": {"style": "SOLID"},
            "bottom": {"style": "SOLID"},
            "left": {"style": "SOLID"},
            "right": {"style": "SOLID"}
        },
        "wrapStrategy": "WRAP"
    })

    # Formato encabezado
    worksheet.format("I3", {
        "textFormat": {
            "bold": True,
            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
        },
        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
        "horizontalAlignment": "CENTER"
    })

    # Formato bordes y centrado para la duracion de la clase
    worksheet.format("I3:I4", {
        "borders": {
            "top": {"style": "SOLID"},
            "bottom": {"style": "SOLID"},
            "left": {"style": "SOLID"},
            "right": {"style": "SOLID"}
        },
        "horizontalAlignment": "CENTER", # Para que el tiempo en I4 también quede centrado
        "wrapStrategy": "WRAP"
    })

    return worksheet

# Se obtiene la hoja de la clase, si no existe, crea una nueva con el nombre ingresado.
def get_worksheet(sheet: gspread.Spreadsheet, worksheet_name: str, total_rows: int) -> gspread.Worksheet:
    try:
        worksheet = sheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=worksheet_name, rows=f"{total_rows}", cols="20")
    return worksheet

# Obtener y devolver la hoja del google sheets.
def get_sheet(subject_module:int, subject_code:str) -> gspread.Spreadsheet:
    handler = SP_Handler()
    url = handler.get_spreadsheet_url(subject_module, subject_code)
    client = gs_connect()
    sheet = client.open_by_url(url)
    return sheet

# Conexion con google sheets, devuelve un cliente.
def gs_connect():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(credentials=credentials)
    return client