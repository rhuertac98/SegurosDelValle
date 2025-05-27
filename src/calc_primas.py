"""
Descripción
===========
Este modulo implementa funciones utilizadas para la cotizacón de primas de seguros.

Funciones
===========
"""
import numpy as np
import pandas as pd
import boto3
from io import BytesIO
from datetime import datetime
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from typing import Any

def calcular_edad(fecha_nac, fecha_ref):
    """
    Calcula la edad de una persona a partir de su fecha de nacimiento y una fecha de referencia.

    Parameters:
        fecha_nac (datetime.date): Fecha de nacimiento de la persona.
        fecha_ref (datetime.date): Fecha de referencia para el cálculo de la edad.

    Returns:
        int: Edad de la persona en años.
    """
    
    # AGREGAR ESTAS CONVERSIONES AL INICIO
    try:
        # Convertir a pandas datetime para manejar numpy.datetime64
        fecha_nac_conv = pd.to_datetime(fecha_nac)
        fecha_ref_conv = pd.to_datetime(fecha_ref)
        
        # Verifica si la fecha de referencia es anterior a la fecha de nacimiento
        if fecha_ref_conv < fecha_nac_conv:
            return -1
        
        # Usar las fechas convertidas para acceder a year, month, day
        return fecha_ref_conv.year - fecha_nac_conv.year - ((fecha_ref_conv.month, fecha_ref_conv.day) < (fecha_nac_conv.month, fecha_nac_conv.day))
        
    except Exception as e:
        print(f"Error calculando edad para {fecha_nac}, {fecha_ref}: {e}")
        return 0


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
    
    MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    mes_numero = pd.to_datetime(fecha).month
    return MESES[mes_numero]


def obtener_parametros_forma_pago(forma_pago):
    """
    Obtiene Recargo por Pago Fraccionado (RPF) y número de recibos según forma de pago
    
    Parameters:
        forma_pago (str): Forma de pago (Anual, Semestral, Trimestral, Mensual)
        
    Returns:
        dict: Diccionario con 'rpf' y 'num_recibos'
    """
    RECARGOS_FORMA_PAGO = {
        "anual": {"rpf": 0.0, "num_recibos": 1},
        "semestral": {"rpf": 0.037, "num_recibos": 2},
        "trimestral": {"rpf": 0.055, "num_recibos": 4},
        "mensual": {"rpf": 0.065, "num_recibos": 12}
    }
    
    try:
        forma_pago_clean = forma_pago.strip().lower()
        
        if forma_pago_clean in RECARGOS_FORMA_PAGO:
            resultado = RECARGOS_FORMA_PAGO[forma_pago_clean]
            return resultado
        else:
            return {"rpf": 0.0, "num_recibos": 1}
            
    except Exception as e:
        return {"rpf": 0.0, "num_recibos": 1}


def obtener_descuento_comision(comision):
    """
    Obtiene descuento según nivel de comisión
    
    Parameters:
    
        comision (float): Nivel de comisión (0.05 a 0.20)
        
    Returns:
        
        float: Descuento correspondiente
    """
    try:

        DESCUENTOS_COMISION = {
        0.20: 0.00, 0.19: 0.02, 0.18: 0.03, 0.17: 0.04, 0.16: 0.06,
        0.15: 0.07, 0.14: 0.09, 0.13: 0.10, 0.12: 0.12, 0.11: 0.13,
        0.10: 0.15, 0.09: 0.16, 0.08: 0.18, 0.07: 0.19, 0.06: 0.21, 0.05: 0.22
        }
        return DESCUENTOS_COMISION[comision]
    
    except Exception as e:
        print(f"Error al obtener el descuento de comisión: {e}")
        return 0.0


def obtener_nombre_cobertura(codigo_cobertura):
    """
    Convierte código de cobertura a nombre completo
    
    Parameters:
        codigo_cobertura (str): Código de cobertura (F, FMA, FBPAI, FMABPAI)
        
    Returns:
        str: Nombre completo de la cobertura
    """
    try:
        coberturas_map = {
            "F": "FALLECIMIENTO",
            "FMA": "FALLECIMIENTO Y MUERTE ACCIDENTAL",
            "FBPAI": "FALLECIMIENTO E INVALIDEZ TOTAL",
            "FMABPAI": "FALLECIMIENTO, MUERTE ACCIDENTAL E INVALIDEZ TOTAL"
        }
        return coberturas_map.get(codigo_cobertura, codigo_cobertura)
    
    except Exception as e:
        print(f"Error al obtener el nombre de la cobertura: {e}")
        return codigo_cobertura
    

def generar_memoria_calculo(contratante:str, fecha_corte:np.datetime64, df_parametros: pd.DataFrame, df_calculo: pd.DataFrame,
                            df_cuotas:pd.DataFrame, descuento: float, rpf: float)-> pd.DataFrame:
    """
    *Función que genera la memoria de cálculo para la cotización*
    
    **Parameters**:
    
        df_parametros (DataFrame): DataFrame con datos de cálculo
        
        df_calculo (DataFrame): DataFrame con datos de asegurados y edades
        
        df_emisiones (DataFrame): DataFrame con datos de emisiones
        
        df_cuotas (DataFrame): DataFrame con datos de cuotas
        
        ticket (int): Número de ticket de la cotización
    
    **Returns**:
    
        DataFrame: DataFrame con la memoria de cálculo
    """
    try:

        df_contratante = df_parametros[df_parametros['Contratante'] == contratante]
        df_calculo_copy = df_calculo.copy()
        df_calculo_copy["Edad"] = df_calculo_copy["Fecha de Nacimiento"].apply(lambda x: calcular_edad(x, fecha_corte))



        if df_contratante["Coberturas"].values[0] == "F":
            df_calculo_copy = df_calculo_copy.merge(df_cuotas[["Edad","Fallecimiento"]], on="Edad", how="left")
            df_calculo_copy["Fallecimiento"] = df_calculo_copy["Fallecimiento"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
        elif df_contratante["Coberturas"].values[0] == "FMA":
            df_calculo_copy = df_calculo_copy.merge(df_cuotas[["Edad","Fallecimiento","MA"]], on="Edad", how="left")
            df_calculo_copy["Fallecimiento"] = df_calculo_copy["Fallecimiento"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
            df_calculo_copy["MA"] = df_calculo_copy["MA"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
        elif df_contratante["Coberturas"].values[0] == "FBPAI":
            df_calculo_copy = df_calculo_copy.merge(df_cuotas[["Edad","Fallecimiento","BPAI"]], on="Edad", how="left")
            df_calculo_copy["Fallecimiento"] = df_calculo_copy["Fallecimiento"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
            df_calculo_copy["BPAI"] = df_calculo_copy["BPAI"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
        elif df_contratante["Coberturas"].values[0] == "FMABPAI":
            df_calculo_copy = df_calculo_copy.merge(df_cuotas, on="Edad", how="left")
            df_calculo_copy["Fallecimiento"] = df_calculo_copy["Fallecimiento"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
            df_calculo_copy["MA"] = df_calculo_copy["MA"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000
            df_calculo_copy["BPAI"] = df_calculo_copy["BPAI"]*(1-descuento)*(1+rpf)*df_contratante["SumaAsegurada"].values[0]/1000

        return df_calculo_copy
    
    except Exception as e:
        print(f"Error al generar la memoria de cálculo: {e}")
        return pd.DataFrame()


def creacion_cotizacion_dict(df_parametros: pd.DataFrame, contratante:str, ticket:int, df_calculo:pd.DataFrame,
                             df_emisiones:pd.DataFrame, df_cuotas:pd.DataFrame)-> dict:
    """
    *Función que crea un diccionario con los datos de la cotización*
    
    **Parameters**:
    
        df_parametros (DataFrame): DataFrame con datos de cálculo
        
        contratante (str): Nombre del contratante

        ticket (int): Número de ticket de la cotización
        
        df_calculo (DataFrame): DataFrame con datos de asegurados y edades

        df_emisiones (DataFrame): DataFrame con datos de emisiones

        df_cuotas (DataFrame): DataFrame con datos de cuotas
        
    
    **Returns**:
    
        dict: Diccionario con los datos de la cotización
    """
    try:
    
        # Para rellenar más facilmente el diccionario
        df_contratante = df_parametros[df_parametros["Contratante"] == contratante]

        # Creamos una copia del DataFrame de cálculo para evitar modificar el original
        df_calculo_copy = df_calculo.copy()

        # Para crear la edad promedio de los asegurados
        fecha_corte = df_contratante["Inicio"].values[0]
        df_calculo_copy["Edad"] = df_calculo_copy["Fecha de Nacimiento"].apply(lambda x: calcular_edad(x, fecha_corte))

        # Recargo por pago fraccionado y número de recibos
        forma_pago = df_contratante["FormaPago"].values[0]
        _ = obtener_parametros_forma_pago(forma_pago)
        rpf = _["rpf"]
        num_recibos = _["num_recibos"]

        # Comisión y descuento
        comision = df_contratante["Comision"].values[0]
        descuento = obtener_descuento_comision(comision)

        # Memoria de cálculo
        memoria_calculo = generar_memoria_calculo(contratante, fecha_corte, df_parametros, df_calculo,
                            df_cuotas, descuento, rpf)
        
        # Primas
        prima = memoria_calculo[memoria_calculo.columns[3:]].sum().sum()

        cotizacion_dict = {
            "Contratante": [contratante],
            "Coberturas": [df_contratante["Coberturas"].values[0]],
            "SumaAsegurada": [df_contratante["SumaAsegurada"].values[0]],
            "Administracion": [df_contratante["Administracion"].values[0]],
            "Agente": [df_contratante["Agente"].values[0]],
            "Comision": [df_contratante["Comision"].values[0]],
            "FormaPago": [df_contratante["FormaPago"].values[0]],
            "Inicio": [df_contratante["Inicio"].values[0]],
            "Fin": [df_contratante["Fin"].values[0]],
            "Renovacion": [df_contratante["Renovacion"].values[0]],
            "Poliza": [df_contratante["Poliza"].values[0]],
            "Ticket": [ticket],
            "Oficina": [df_contratante["Oficina"].values[0]],
            "RPF": [rpf],
            "NumRecibos": [num_recibos],
            "Comision": [comision],
            "Descuento": [descuento],
            "Prima": [],
            "EdadPromedio": [df_calculo_copy["Edad"].mean()],
            "SAMI": [df_contratante["SumaAsegurada"].values[0]],
            "Asegurados": [df_calculo_copy["Edad"].count()],
            "Mes": [obtener_nombre_mes(df_contratante["Inicio"].values[0])],
            "Evento": []
        }

        if df_contratante["Renovacion"].values[0] == "Si":
            siniestralidad = df_emisiones.loc[df_emisiones["Poliza"] == df_contratante["Poliza"].values[0], "Siniestralidad"].values[0]
            
            if siniestralidad < 0.50:
                cotizacion_dict["Prima"].append(prima)
                cotizacion_dict["Evento"].append("na")
            else:
                cotizacion_dict["Prima"].append("La siniestralidad está desviada, consulte a un suscriptor")
                cotizacion_dict["Evento"].append("Fuera de política")
                prima = "La siniestralidad está desviada, consulte a un suscriptor"
            
        else:
            cotizacion_dict["Prima"].append(prima)
            cotizacion_dict["Evento"].append("na")            
            


        return cotizacion_dict
    
    except Exception as e:
        print(f"Error al crear el diccionario de cotización: {e}")
        return {}
    