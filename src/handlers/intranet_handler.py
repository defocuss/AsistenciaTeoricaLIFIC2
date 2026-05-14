from playwright.sync_api import sync_playwright, Page, TimeoutError
import pandas as pd
import time
from typing import Callable
import streamlit as st


def intranet_workflow(link: str, rut: str, password: str, subject_code: str, subject_module: int, date: str, class_description: str, presentes: pd.DataFrame, logger: Callable[[str,str], None]) -> None:
    with sync_playwright() as p:
        #test proxy
        proxy_url = st.secrets["PROXY_URL"]

        proxy_settings = {
            "server": proxy_url
        }
        # test proxy

        browser = p.chromium.launch(
            headless=True,
            proxy=proxy_settings,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page() # Crea una nueva página en el navegador
        if not login_intranet(page, link, rut, password, logger):
            return
        if not go_to_subject(page, subject_code, subject_module, logger):
            return
        if not select_class_tab(page, logger):
            return
        if not select_class_info(page, date, class_description, logger):
            return
        if not select_atten_tab(page, logger):
            return
        if not select_students(page, date, class_description, presentes, logger):
            return
        time.sleep(5) # Esperar a que se registre la asistencia antes de cerrar el navegador
        browser.close()

# Iniciar sesión en la intranet. Recibe como parametro elrut y la contraseña del profesor.
def login_intranet(page: Page, link: str, rut: str, password: str, logger: Callable[[str, str], None]) -> bool:
    logger("warning","Iniciando sesión en la intranet...")
    page.goto(link)
    page.fill('input#POPUSERNAME', rut)  # credenciales de profe vale
    page.fill('input#XYZ', password)  # credenciales de profe vale
    page.click('text=INGRESO INTRANET')  # ingresar a la intranet
    if not validate_login(page, logger): # Si el inicio de de sesion falla, muestra el mensaje de error y termina la función.
        time.sleep(5)
        return False
    page.wait_for_load_state('networkidle')
    return True

# Funcion para validar que el inicio de sesion fue exitoso.
def validate_login(page: Page, logger: Callable[[str, str], None]) -> bool:
    error_message_1 = page.locator('text=Su Rut o Clave no corresponden. Por favor intentelo nuevamente.')
    error_message_2 = page.locator('text=El Rut ingresado es inválido')
    error_message_3 = page.locator('text=Debe ingresar su Rut.')
    error_message_4 = page.locator('text=Debe ingresar su Clave.')
    if error_message_1.count() > 0 or error_message_2.count() > 0 or error_message_3.count() > 0 or error_message_4.count() > 0:
        logger("error","Error al iniciar sesión, por favor revise sus credenciales")
        time.sleep(5)
        return False
    logger("success","Inicio de sesión exitoso")
    return True
    

# Selecciona la asignatura a la cual se le va a registrar la asistencia. Recibe como parametro el codigo de la asignatura y el modulo.
def go_to_subject(page: Page, subject_code: str, subject_module: int, logger: Callable[[str, str], None]) -> bool:
    if validate_user(page, logger):
        logger("warning","Seleccionando asignatura...")
        page.click('text=Académico')
        page.click('text=Registro Asistencia')
        page.wait_for_load_state('networkidle')
        page.click(f'a.link_normal[href*="VerDetalle(2026,1,\'{subject_code}\',{subject_module})"]') # cliclear el ramo al que se le quiere subir la asistencia
        page.wait_for_load_state('networkidle')
        logger("success","Asignatura seleccionada exitosamente")
        return True
    return False

# Se valida que el usuario sea academico.
def validate_user(page: Page, logger: Callable[[str, str], None]) -> bool:
    try:
        page.wait_for_selector(
            "font:has-text('Académico')",
            timeout=4000
        )
    except TimeoutError:
        logger("error","El usuario no es academico.")
        time.sleep(5)
        return False

    logger("success","El usuario es academico.")
    time.sleep(1)
    return True

# Selecciona la pestaña de clases.
def select_class_tab(page: Page, logger: Callable[[str, str], None]) -> bool:
    logger("warning","Seleccionando pestaña de clases...")
    page.click('a#regasist_clases')
    page.wait_for_load_state('networkidle')
    if not validate_selected_class(page, logger):
        return False
    page.wait_for_load_state('networkidle') # Ayuda a esperar a que cargue la página antes de seguir con el siguiente paso
    return True

# Valida que la clase teorica este configurada.
def validate_selected_class(page: Page, logger: Callable[[str, str], None]) -> bool:
    try:
        page.wait_for_selector(
            "strong:has-text('NO HA CONFIGURADO LOS TIPOS DE CLASES QUE REGISTRARÁN ASISTENCIA')",
            timeout=5000
        )
    except TimeoutError:
        logger("success","Pestana de clases seleccionada exitosamente")
        return True

    logger("error","Los tipos de clases no están configurados")
    time.sleep(5)
    return False

# Selecciona la información de la clase, como el tipo, la fecha y la descripción de la clase.
def select_class_info(page: Page, date: str, class_description: str, logger: Callable[[str, str], None]) -> bool:
    logger("warning","Ingresando información de la clase...")
    page.select_option('select[name="Formulario[cod_tipcla]"]', "T") # Selecciona el tipo de clase
    page.fill('input#f_clase', date) # Ingresar la fecha de la clase
    page.fill('textarea#observac', class_description) # Ingresar la descripción de la clase
    page.click('text=AGREGAR') # Cliclear el botón de agregar para agregar la clase
    if not validate_selected_info(page, logger):
        return False
    page.wait_for_load_state('networkidle')
    time.sleep(5)
    return True

# Validar que la informacion de la clase haya sido seleccionada correctamente.
def validate_selected_info(page: Page, logger: Callable[[str, str], None]) -> bool:
    try:
        page.wait_for_selector(
            "strong:has-text('La clase fue registrada correctamente.')",
            timeout=3000
        )
    except TimeoutError:
        logger("error","No se ha registrado la clase.")
        time.sleep(5)
        return False

    logger("success","Clase registrada correctamente")
    return True

# Selecciona la pestana de asistencia
def select_atten_tab(page: Page, logger: Callable[[str, str], None]) -> bool:
    logger("warning","Seleccionando pestaña de asistencia...")
    page.click('a#regasist_asist') # cliclear la pestaña de asistencia para seleccionar a los estudiantes de la clase
    if not validate_selected_atten(page, logger):
        return False
    page.wait_for_load_state('networkidle')
    return True

# Se valida que se haya seleccionado la pestaña de asistencia.
def validate_selected_atten(page: Page, logger: Callable[[str, str], None]) -> bool:
    try:
        page.wait_for_selector(
            "p:has-text('INGRESO DE ASISTENCIA POR CLASE')",
            timeout=4000
        )
    except TimeoutError:
        logger("error","No se ha logrado seleccionar la pestaña de asistencia.")
        return False

    logger("success","Se ha seleccionado la pestaña de asistencia correctamente.")
    time.sleep(5)
    return True

# Selecciona a los estudiantes presentes en la clase
def select_students(page: Page, date: str, class_description: str, presents: pd.DataFrame, logger: Callable[[str, str], None]) -> bool:
    logger("warning","Seleccionando estudiantes presentes...")
    option = (page.locator('select#cb_id_clase option')
              .filter(has_text=date)
              .filter(has_text=class_description)
              .first) # Se obtiene el valor de la opcion que tiene la fecha de la case deseada
    value = option.get_attribute('value') # Se obtiene el valor del atributo value de la opcion
    page.select_option('select#cb_id_clase', value=value) # Se selecciona la clase con la fecha deseada en el select de clases
    time.sleep(5)
    click_present_students(page, presents, logger) # Se pasan las matriculas de los estudiantes presentes en la clase, se pueden obtener de un archivo excel o de una base de datos, pero como no tengo acceso a esa información, se pasan como ejemplo.
    time.sleep(5) # Esperar a que se seleccionen los estudiantes antes de registrar la asistencia
    if not register(page, logger): # Se registra la asistencia de los estudiantes presentes en la clase
        return False
    page.wait_for_load_state('networkidle')
    return True

# Clickea a los estudiantes que estan presentes en la clase.
def click_present_students(page: Page, presents: pd.DataFrame, logger: Callable[[str, str], None]) -> None:
    for matricula in presents['Matricula'].astype(str).values:
        locator = page.locator(f'input[value="{matricula}*1"]')
        page.wait_for_load_state('networkidle')
        if locator.count() > 0:
            locator.first.click(force=True)
        else:
            print(f"Matrícula {matricula} no encontrada en la página web. Saltando...")
    page.wait_for_load_state('networkidle')
    logger("success","Estudiantes marcados como presentes")

# Paso final del registro, se encarga de presionar el boton REGISTRAR y verificar si fue correcto
def register(page: Page, logger: Callable[[str, str], None]) -> bool:
    logger("warning","Registrando asistencia...")
    page.wait_for_load_state('networkidle')
    page.click('input[type="button"][value="REGISTRAR"]') # Cliclear registrar ultimo paso
    if not validate_registration(page, logger):
        return False
    return True

# Valida que la asistencia se haya registrado correctamente, buscando un mensaje de confirmación en la página.
def validate_registration(page: Page, logger: Callable[[str, str], None]) -> bool:
    try:
        page.wait_for_selector(
            "strong:has-text('La asistencia fue registrada exitósamente.')",
            timeout=5000
        )
    except TimeoutError:
        logger("error","Error al registrar la asistencia, por favor intente nuevamente")
        time.sleep(5)
        return False
    logger("success","Asistencia subida exitosamente a intranet")
    return True