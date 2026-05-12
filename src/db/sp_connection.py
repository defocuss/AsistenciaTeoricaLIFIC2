from unicodedata import name
from st_supabase_connection import SupabaseConnection, execute_query
import streamlit as st

class SP_Handler:
    def __init__(self):
        self.client = st.connection(
            name="Supabase",
            type=SupabaseConnection,
            ttl=None)

    def get_signature_id(self, signature:str) -> int:
        try:
            return execute_query(
                self.client.table("Asignatura")
                .select("id_asignatura")
                .eq("abrevacion", signature)
                .limit(1),
                ttl=0).data[0]["id_asignatura"]
        except Exception as e:
            st.error(f"Error al obtener la asignatura: {e}")
            return None

    def get_subject_modules(self, signature:str) -> list:
        try:
            id = self.get_signature_id(signature) 
            return execute_query(
                self.client.table("Modulo")
                .select("*, Profesor(*)")
                .eq("id_asignatura", id),
                ttl=0).data
        except Exception as e:
            st.error(f"Error al obtener los módulos: {e}")
            return None
    
    def get_signatures(self) -> list:
        try:
            return execute_query(
                self.client.table("Asignatura")
                .select("abrevacion"),
                ttl=0).data
        except Exception as e:
            st.error(f"Error al obtener las asignaturas: {e}")
            return None

    def get_professors(self) -> list:
        try:
            return execute_query(
                self.client.table("Profesor")
                .select("id_profesor, nombre"),
                ttl=0).data
        except Exception as e:
            st.error(f"Error al obtener los profesores: {e}")
            return None

    def drop_professors_from_module(self, id_modulo:int) -> bool:
        try:
            execute_query(
                self.client.table("Modulo_Profesor")
                .delete()
                .eq("id_modulo", id_modulo),
                ttl=0)
            return True
        except Exception as e:
            st.error(f"Error al eliminar profesores del módulo {id_modulo}: {e}")
            return False

    def insert_professors_to_module(self, id_modulo:int, id_profesores:list) -> bool:
        try:
            for id_profesor in id_profesores:
                execute_query(
                    self.client.table("Modulo_Profesor")
                    .insert({"id_modulo": id_modulo, "id_profesor": id_profesor}),
                    ttl=0)
            return True
        except Exception as e:
            st.error(f"Error al insertar profesores en el módulo: {e}")
            return False

    def upsert_module(self, payload: dict) -> int:
        try:
            result = execute_query(
                self.client.table("Modulo")
                .upsert(payload),
                ttl=0).data
            if "id_modulo" not in payload and "id_modulo" in result[0]:
                return result[0]["id_modulo"]
            else: 
                return -1
        except Exception as e:
            st.error(f"Error al insertar o actualizar el módulo: {e}")
            return None

    def delete_module(self, id_modulo:int) -> bool:
        try:
            execute_query(
                self.client.table("Modulo")
                .delete()
                .eq("id_modulo", id_modulo),
                ttl=0)
            return True
        except Exception as e:
            st.error(f"Error al eliminar el módulo: {e}")
            return False

    def get_modules_by_code(self, code:str) -> list:
        try:
            modules_numbers = []
            result = execute_query(
                self.client.table("Asignatura")
                .select("codigo", "Modulo(*)")
                .eq("codigo", code),
                ttl=0).data[0]["Modulo"]
            for module in result:
                modules_numbers.append(module["numero_modulo"])
            return modules_numbers
        except Exception as e:
            st.error(f"Error al obtener el módulo por código: {e}")
            return None

    def get_spreadsheet_url(self, n_modulo:int, signature_code:str) -> str:
        try:
            id_asignatura = execute_query(
                self.client.table("Asignatura")
                .select("id_asignatura")
                .eq("codigo", signature_code)
                .limit(1),
                ttl=0).data[0]["id_asignatura"]
            return execute_query(
                self.client.table("Modulo")
                .select("hoja_de_calculo")
                .eq("numero_modulo", n_modulo)
                .eq("id_asignatura", id_asignatura)
                .limit(1),
                ttl=0).data[0]["hoja_de_calculo"]
        except Exception as e:
            st.error(f"Error al obtener la hoja de cálculo: {e}")
            return None
        
    def get_module_classes(self, n_modulo:int, signature_code:str) -> list:
        try:
            id_asignatura = execute_query(
                self.client.table("Asignatura")
                .select("id_asignatura")
                .eq("codigo", signature_code)
                .limit(1),
                ttl=0).data[0]["id_asignatura"]
            return execute_query(
                self.client.table("Modulo")
                .select("clases")
                .eq("numero_modulo", n_modulo)
                .eq("id_asignatura", id_asignatura)
                .limit(1),
                ttl=0).data[0]["clases"]
        except Exception as e:
            st.error(f"Error al obtener la hoja de cálculo: {e}")
            return None
