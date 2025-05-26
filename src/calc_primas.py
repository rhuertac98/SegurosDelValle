"""
Descripción
===========
Este modulo implementa funciones utilizadas para la cotizacón de primas de seguros.

Funciones
===========
"""

import pandas as pd
import boto3
from io import BytesIO
from datetime import datetime
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def calcular_edad(fecha_nac, fecha_ref):
    """
    *Calcula la edad de una persona a partir de su fecha de nacimiento y una fecha de referencia.*

    **Parameters**:

        fecha_nac (datetime.date): Fecha de nacimiento de la persona.

        fecha_ref (datetime.date): Fecha de referencia para el cálculo de la edad.

    **Returns**:

        int: Edad de la persona en años.
    """
    # Verifica si la fecha de referencia es anterior a la fecha de nacimiento
    if fecha_ref < fecha_nac:
        # Si es así, devuelve un valor negativo para indicar un error
        return -1
    return fecha_ref.year - fecha_nac.year - ((fecha_ref.month, fecha_ref.day) < (fecha_nac.month, fecha_nac.day))


def obtener_lista_nombre_bases(ruta_s3_base_datos:str, nombre_bucket:str) -> list:
    
    """
    *Obtiene la base de datos desde S3*
    
    **Parameters**:

        ruta_s3_base_datos (str): Ruta del archivo en S3

        nombre_bucket (str): Nombre del bucket de S3

    **Returns**:

        list_base (list): Lista con los datos de la base de datos

    """
    
    try:
        # Obtenemos la lista de objetos en la carpeta especificada
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(Bucket=nombre_bucket, Prefix=ruta_s3_base_datos)

        if 'Contents' not in response:
            print("No se encontraron archivos en esa carpeta.")
            return []
        else:
            list_base = [obj['Key'] for obj in response['Contents']]
            # Filtramos los archivos que terminan con .xlsx
            list_base = [file for file in list_base if file.endswith('.xlsx')]
            return list_base            
    
    except Exception as e:
        print(f"Error al obtener la base de datos: {e}")
        return []

def obtener_base_parametros(ruta_archivo:str, nombre_bucket:str) -> pd.DataFrame:
    """*Función para cargar la base de datos que contiene los párametros de las cotizaciones alojada en S3.*
    
    **Parameters**:

        nombre_bucket (str): Nombre del bucket de S3 donde se encuentra la base de datos.

        ruta_archivo (str): Ruta (Key) del archivo dentro del bucket S3.
    
    **Returns**:

        parametros (DataFrame): DataFrame con los parámetros de las cotizaciones.
    """

    try:
        s3 = boto3.client('s3')
        # Se obtiene el objeto del bucket S3
        response = s3.get_object(Bucket=nombre_bucket, Key=ruta_archivo)
        
        if 'Body' not in response:
            print("No se encontró el archivo en el bucket.")
            return pd.DataFrame()
        else:
            # Se lee el contenido del archivo Excel
            content = response['Body'].read()
            parametros = pd.read_excel(BytesIO(content), engine='openpyxl')
            return parametros
    except Exception as e:
        print(f"Error al obtener la base de datos de parámetros: {e}")
        return pd.DataFrame()



def obtener_base_cuotas(ruta_archivo:str, nombre_bucket:str) -> pd.DataFrame:
    """Función para cargar la base de datos que contiene las cuotas de las cotizaciones al millar alojada en S3.

    **Parameters**:

        nombre_bucket (str): Nombre del bucket de S3 donde se encuentra la base de datos.

        ruta_archivo (str): Ruta (Key) del archivo dentro del bucket S3.
    
    **Returns**:

        cuotas (DataFrame): DataFrame con las cuotas de las cotizaciones.
    """

    try:
        # Se obtiene el objeto del bucket S3
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=nombre_bucket, Key=ruta_archivo)
        
        if 'Body' not in response:
            print("No se encontró el archivo en el bucket.")
            return pd.DataFrame()
        else:
            # Se lee el contenido del archivo Excel
            content = response['Body'].read()
            cuotas = pd.read_excel(BytesIO(content), engine='openpyxl')
            return cuotas
    except Exception as e:
        print(f"Error al obtener la base de datos de cuotas: {e}")
        return pd.DataFrame()


def obtener_base_emisiones(ruta_archivo:str, nombre_bucket:str) -> pd.DataFrame:
    """*Función para cargar la base de datos que contiene las emisiones y su siniestrridad alojada en S3.*

    **Parameters**:

        nombre_bucket (str): Nombre del bucket de S3 donde se encuentra la base de datos.

        ruta_archivo (str): Ruta (Key) del archivo dentro del bucket S3.
    **Returns**:
        
        emisiones (DataFrame): DataFrame con las emisiones.
    """

    try:
        # Se obtiene el objeto del bucket S3
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=nombre_bucket, Key=ruta_archivo)

        if 'Body' not in response:
            print("No se encontró el archivo en el bucket.")
            return pd.DataFrame()
        else:
            # Se lee el contenido del archivo Excel
            content = response['Body'].read()
            emisiones = pd.read_excel(BytesIO(content), engine='openpyxl')
            return emisiones
    except Exception as e:
        print(f"Error al obtener la base de datos de emisiones: {e}")
        return pd.DataFrame()
    

def obtener_base_historico(ruta_archivo:str, nombre_bucket:str) -> pd.DataFrame:
    """*Función para cargar la base de datos que contiene las cotizaciones históricas alojada en S3.*
    
    **Parameters**:
    
        nombre_bucket (str): Nombre del bucket de S3 donde se encuentra la base de datos.

        ruta_archivo (str): Ruta (Key) del archivo dentro del bucket S3.
    
    **Returns**:

        historico (DataFrame): DataFrame con las cotizaciones históricas.
    """

    try:
        # Se obtiene el objeto del bucket S3
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=nombre_bucket, Key=ruta_archivo)

        if 'Body' not in response:
            print("No se encontró el archivo en el bucket.")
            return pd.DataFrame()
        else:
            # Se lee el contenido del archivo Excel
            content = response['Body'].read()
            historico = pd.read_excel(BytesIO(content), engine='openpyxl')
            return historico
    except Exception as e:
        print(f"Error al obtener la base de datos de historico: {e}")
        return pd.DataFrame()
    

def obtener_nombre_mes(fecha):
    """
    *Función que convierte fecha a nombre del mes en español*
    
    **Parameters**:
        
        fecha: Fecha en formato datetime o string
        
    **Returns**:
        
        str: Nombre del mes en español
    """
    mes_numero = pd.to_datetime(fecha).month
    return MESES[mes_numero]


def obtener_parametros_forma_pago(forma_pago):
    """
    *Función que obtiene RPF y número de recibos según forma de pago*
    
    **Parameters**:
        
        forma_pago (str): Forma de pago (Anual, Semestral, Trimestral, Mensual)
        
    **Returns**:
        
        dict: Diccionario con 'rpf' y 'num_recibos'
    """
    return RECARGOS_FORMA_PAGO.get(forma_pago.lower(), RECARGOS_FORMA_PAGO["anual"])


def obtener_descuento_comision(comision):
    """
    Función que pbtiene descuento según nivel de comisión
    
    **Parameters**:

        comision (float): Nivel de comisión (0.05 a 0.20)
        
    **Returns**:

        float: Descuento correspondiente
    """
    return DESCUENTOS_COMISION.get(comision, 0.0)


def obtener_nombre_cobertura(codigo_cobertura):
    """
    Convierte código de cobertura a nombre completo
    
    Parameters:
        codigo_cobertura (str): Código de cobertura (F, FMA, FBPAI, FMABPAI)
        
    Returns:
        str: Nombre completo de la cobertura
    """
    coberturas_map = {
        "F": "FALLECIMIENTO",
        "FMA": "FALLECIMIENTO Y MUERTE ACCIDENTAL",
        "FBPAI": "FALLECIMIENTO E INVALIDEZ TOTAL",
        "FMABPAI": "FALLECIMIENTO, MUERTE ACCIDENTAL E INVALIDEZ TOTAL"
    }
    return coberturas_map.get(codigo_cobertura, codigo_cobertura)
