import pandas as pd
from typing import Callable
import requests
from bs4 import BeautifulSoup
from datetime import datetime


def intranet_workflow(link_proxy: str, link_intranet: str, login_url: str, rut: str, password: str, subject_code: str, subject_module: int, date: str, class_description: str, presentes: pd.DataFrame, logger: Callable[[str,str], None]) -> None:
    session = login_intranet_requests(link_proxy,login_url, link_intranet, rut, password, logger)
    if session:
        if not go_to_subject_requests(session, subject_code, subject_module, link_intranet, date, logger):
            return
        if not create_class_requests(session, date, class_description, link_intranet, logger):
            return
        class_id = get_class_id_requests(session, date, link_intranet, class_description, logger)
        if not class_id:
            logger("error", "No se pudo obtener el ID de la clase recién creada.")
            return
        if not submit_attendance_requests(session, class_id, presentes, link_intranet, logger):
            return 
        logger("success", "Asistencia registrada exitosamente a través de la API de requests.")
        return
    else:
        logger("error", "No se pudo iniciar sesión. Verifica tus credenciales.")
        return

def login_intranet_requests(link_proxy: str, login_url: str, intranet_url: str, rut: str, password: str, logger: Callable[[str, str], None]) -> requests.Session | None:
    session = requests.Session()

    if link_proxy:
        logger("info", f"Conectando a través del proxy local")
        session.proxies.update({
            "http": link_proxy,
            "https": link_proxy
        })
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"{intranet_url}",
        "Referer": f"{intranet_url}/",
        "Upgrade-Insecure-Requests": "1"
    }
    
    payload = {
        "Formulario[POPUSERNAME]": rut,
        "Formulario[XYZ]": password
    }
    
    logger("warning", f"Enviando POST a {login_url}")
    
    try:
        # POST de inicio sesion
        response = session.post(login_url, data=payload, headers=headers, timeout=15)
        
        # Verificar si se entro a la portada.
        if "portada.php" in response.url or "Bienvenido" in response.text or response.status_code == 200:
            logger("success", "Inicio de sesión exitoso.")
            return session
        else:
            logger("error", "Credenciales incorrectas o servidor rechazó el login.")
            return None
            
    except requests.exceptions.RequestException as e:
        logger("error", f"Error de red/proxy: {str(e)}")
        return None
    
def go_to_subject_requests(session: requests.Session, subject_code: str, subject_module: int, intranet_url: str, date: str, logger: Callable[[str, str], None]) -> bool:
    
    detalle_url = f"{intranet_url}/academico/asistencia/ver_regasist_det.php"
    
    conf_url = f"{intranet_url}/academico/asistencia/regasist_conf.php"
    
    headers_base = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Origin": f"{intranet_url}",
        "Referer": f"{intranet_url}/academico/asistencia/ver_regasist.php"
    }
    periodos = get_academic_period(date)

    payload_detalle = {
        "Formulario[periodo]": periodos["Formulario[periodo]"],  
        "Formulario[ano_asist]": periodos["Formulario[ano_asist]"],
        "Formulario[sem_asist]": periodos["Formulario[sem_asist]"],
        "Formulario[cod_asist]": subject_code,
        "Formulario[mod_asist]": str(subject_module)
    }

    payload_conf = {
        "MAX_FILE_SIZE": "10000000",
        "Formulario[parametro]": "",
        "Formulario[buscar]": "0",
        "Formulario[editar]": "0"
    }

    logger("warning", f"Ingresando a la asignatura {subject_code} con módulo {subject_module}...")
    try:
        res_detalle = session.post(detalle_url, data=payload_detalle, headers=headers_base, timeout=15)
        if res_detalle.status_code == 200 and subject_code in res_detalle.text:
            headers_ajax = headers_base.copy()
            headers_ajax["X-Requested-With"] = "XMLHttpRequest"
            headers_ajax["Referer"] = detalle_url
            session.post(conf_url, data=payload_conf, headers=headers_ajax, timeout=15)
            
            logger("success", "Asignatura seleccionada y configurada exitosamente en el servidor.")
            return True
        else:
            logger("error", "No se pudo acceder a la asignatura.")
            return False
            
    except Exception as e:
        logger("error", f"Error de red al navegar a la asignatura: {str(e)}")
        return False

def create_class_requests(session: requests.Session, date: str, class_description: str, intranet_url: str, logger: Callable[[str, str], None]) -> bool:
    crear_clase_url = f"{intranet_url}/academico/asistencia/regasist_clases_ing.php"
    
    headers_ajax = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"{intranet_url}",
        "Referer": f"{intranet_url}/academico/asistencia/ver_regasist_det.php"
    }

    payload = {
        "MAX_FILE_SIZE": "10000000",
        "Formulario[cod_tipcla]": "T",
        "Formulario[f_clase]": date,
        "Formulario[observac]": class_description,
        "Formulario[cod_tarch]": "",
        "Formulario[id_clase]": "",
        "Formulario[parametro]": "",
        "Formulario[buscar]": "0",
        "Formulario[editar]": "0"
    }

    logger("warning", f"Registrando la clase del {date} a nivel de red...")
    try:
        response = session.post(crear_clase_url, data=payload, headers=headers_ajax, timeout=15)
        if response.status_code == 200:
            logger("success", "Clase registrada correctamente en el servidor.")
            return True
        else:
            logger("error", f"Error al registrar la clase. Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        logger("error", f"Error de red al registrar la clase: {str(e)}")
        return False

def submit_attendance_requests(session: requests.Session, class_id: str, presentes: pd.DataFrame, intranet_url: str, logger: Callable[[str, str], None]) -> bool:
    list_url = f"{intranet_url}/academico/asistencia/regasist_asist_lst.php"

    submit_url = f"{intranet_url}/academico/asistencia/regasist_asist_ing.php"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"{intranet_url}",
        "Referer": f"{intranet_url}/academico/asistencia/ver_regasist_det.php"
    }

    payload_list = {
        "MAX_FILE_SIZE": "10000000",
        "Formulario[cb_id_clase]": class_id,
        "Formulario[parametro]": "",
        "Formulario[buscar]": "0",
        "Formulario[editar]": "0"
    }
    
    logger("warning", f"Obteniendo tabla HTML para la clase ID {class_id}...")
    
    try:
        response_list = session.post(list_url, data=payload_list, headers=headers, timeout=15)
        
        if response_list.status_code != 200:
            logger("error", f"Error al obtener la lista de alumnos. HTTP: {response_list.status_code}")
            return False

        soup = BeautifulSoup(response_list.text, 'html.parser')
        maestra_matriculas = {}
        
        for input_tag in soup.find_all('input'):
            name = input_tag.get('name', '')
            value_raw = str(input_tag.get('value', '')).strip().upper()
            
            if name.startswith('Formulario[') and '*1' in value_raw:
                # Indice del formulario
                index = name.split('[')[-1].replace(']', '')
                
                # Obtener matricula antes del '*'
                matricula = value_raw.split('*')[0]
                
                # Guardamos en el diccionario maestro si el índice es válido
                if index.isdigit():
                    maestra_matriculas[matricula] = index

        total_alumnos = len(maestra_matriculas)
        logger("info", f"Extracción exitosa: {total_alumnos} alumnos detectados usando los inputs de asistencia.")

        if total_alumnos == 0:
            logger("warning", "🚨 ALERTA: No se detectaron alumnos. El HTML podría estar vacío o haber caducado la sesión.")
            return False

        final_payload = {
            "MAX_FILE_SIZE": "10000000",
            "Formulario[cb_id_clase]": class_id,
            "Formulario[num_alum]": str(total_alumnos),
            "Formulario[id_clase]": class_id, 
            "Formulario[cod_tipcla]": "",
            "Formulario[accion]": "",
            "Formulario[parametro]": "",
            "Formulario[buscar]": "0",
            "Formulario[editar]": "0"
        }

        for matricula, index in maestra_matriculas.items():
            final_payload[f"Formulario[matricula][{index}]"] = matricula

        rut_presentes = set(presentes['Matricula'].astype(str).values)
        
        alumnos_marcados = 0
        for matricula, index in maestra_matriculas.items():
            if matricula in rut_presentes:
                final_payload[f"Formulario[{index}]"] = f"{matricula}*1"
                alumnos_marcados += 1

        logger("info", f"Marcando {alumnos_marcados} presentes (de {len(rut_presentes)} en CSV).")
        logger("info", "Enviando registro a la base de datos de la universidad...")
        response_submit = session.post(submit_url, data=final_payload, headers=headers, timeout=20)
        
        if response_submit.status_code == 200:
            logger("success", "¡Asistencia subida exitosamente!")
            return True
        else:
            logger("error", f"El servidor falló al registrar. HTTP: {response_submit.status_code}")
            return False
            
    except Exception as e:
        logger("error", f"Error crítico de red: {str(e)}")
        return False

# Recibe una fecha dia/mes/año y devuelve un diccionario con los campos necesarios para saber el semetre
def get_academic_period(date_str: str) -> dict:
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    
    year = str(date_obj.year)
    # De enero a julio semestre 1, de agosto a diciembre semestre 2
    semester = "1" if date_obj.month <= 7 else "2"
    
    return {
        "Formulario[periodo]": f"{year}{semester}",
        "Formulario[ano_asist]": year,              
        "Formulario[sem_asist]": semester     
    }

# Busca el id de la clase recien creada para subir la asistencia.
def get_class_id_requests(session: requests.Session, date: str, link:str,class_description: str, logger: Callable[[str, str], None]) -> str | None:

    url_tabla_clases = f"{link}/academico/asistencia/regasist_clases.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"{link}",
        "Referer": f"{link}academico/asistencia/ver_regasist_det.php"
    }

    payload = {
        "MAX_FILE_SIZE": "10000000",
        "Formulario[cod_tipcla]": "",
        "Formulario[f_clase]": "",
        "Formulario[observac]": "",
        "Formulario[cod_tarch]": "",
        "Formulario[id_clase]": "",
        "Formulario[parametro]": "",
        "Formulario[buscar]": "0",
        "Formulario[editar]": "0"
    }

    logger("info", f"Buscando ID interno para la clase del {date}...")

    try:
        response = session.post(url_tabla_clases, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 4:
                    f_clase = tds[2].text.strip()
                    desc = tds[3].text.strip()
                    if f_clase == date and desc == class_description:
                        class_id = tds[0].text.strip()
                        logger("info", f"¡Match encontrado! El ID de la clase es: {class_id}")
                        return class_id
            
            logger("warning", "No se encontró la clase en la tabla. Verifica si se creó correctamente.")
            return None
        else:
            logger("error", "Error al cargar la tabla de clases.")
            return None
            
    except Exception as e:
        logger("error", f"Error de red al buscar el ID: {str(e)}")
        return None