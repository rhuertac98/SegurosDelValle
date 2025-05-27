"""
Descripción
===========
Este modulo implementa funciones utilizadas para generar archivos PDF de cotizaciones de seguros.

Funciones
===========
"""
import boto3
import json
import pandas as pd
from typing import Any
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

def cargar_dict_cotizacion(contratante:str, nombre_bucket:str) -> dict:
    """
    *Función que carga el diccionario de cotización de un contratante específico desde S3.*
    
    **Parameters**:

        contratante (str): Nombre del contratante para el cual se desea cargar el diccionario de cotización.   

    **Returns**:

        dict_contratante (dict): Diccionario de cotización del contratante especificado.
    """
    try:
        s3 = boto3.client('s3')
        ruta_dict_contratante = f'coco/data/master_data/dict/{contratante}.json'
        response = s3.get_object(Bucket=nombre_bucket, Key=ruta_dict_contratante)
        content = response['Body'].read()
        dict_contratante = json.loads(content.decode('utf-8'))
        return dict_contratante
    
    except Exception as e:
        print(f"Error al cargar el diccionario de cotización para {contratante}: {e}")
        return None
    

def convertir_campo_a_float(diccionario:dict, campo:str) -> dict:
    """Función que convierte un campo específico a float en un diccionario.

    **Parameters**:

        diccionario (dict): Diccionario que contiene el campo a convertir.
        
        campo (str): Nombre del campo a convertir a float.

    **Returns**:

        dict: Diccionario con el campo convertido a float."""
    
    if campo in diccionario:
        try:
            valor = diccionario[campo][0] if isinstance(diccionario[campo], list) else diccionario[campo]
            diccionario[campo] = [float(str(valor).replace(',', '').replace('$', '').strip())]
        except:
            diccionario[campo] = [0.0]
    
    return diccionario


def convertir_campo_a_fecha(diccionario: dict, campo: str, formato: str = 'dd/mm/yyyy') -> dict:
    """
    *Función que convierte un campo específico a formato de fecha en un diccionario.*

    **Parameters**:

        diccionario (dict): Diccionario que contiene el campo a convertir.
        
        campo (str): Nombre del campo a convertir a formato de fecha.
        
        formato (str): Formato de salida deseado. Opciones:
            - 'dd/mm/yyyy' (por defecto): 15/06/2025
            - 'dd-mm-yyyy': 15-06-2025
            - 'yyyy-mm-dd': 2025-06-15
            - 'dd/mm/yy': 15/06/25

    **Returns**:

        dict: Diccionario con el campo convertido al formato de fecha especificado.
    """
    
    if campo in diccionario:
        try:
            # Extraer valor (de lista o directo)
            valor = diccionario[campo][0] if isinstance(diccionario[campo], list) else diccionario[campo]
            
            # Limpiar valor si es string (remover partes de tiempo)
            if isinstance(valor, str):
                valor = valor.split('T')[0] if 'T' in valor else valor
            
            # Convertir a pandas datetime
            fecha_dt = pd.to_datetime(valor)
            
            # Aplicar formato según opción
            if formato == 'dd/mm/yyyy':
                fecha_formateada = fecha_dt.strftime('%d/%m/%Y')
            elif formato == 'dd-mm-yyyy':
                fecha_formateada = fecha_dt.strftime('%d-%m-%Y')
            elif formato == 'yyyy-mm-dd':
                fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
            elif formato == 'dd/mm/yy':
                fecha_formateada = fecha_dt.strftime('%d/%m/%y')
            else:
                # Formato por defecto si no se reconoce
                fecha_formateada = fecha_dt.strftime('%d/%m/%Y')
            
            diccionario[campo] = [fecha_formateada]
            
        except:
            # Valor por defecto en caso de error
            diccionario[campo] = ["01/01/1900"] if formato != 'yyyy-mm-dd' else ["1900-01-01"]
    
    return diccionario


def generar_pdf_cotizacion(bucket_name:str, contratante_dict:dict) -> Any: 

        """
        Función que genera un PDF de cotización de seguro de vida grupal y lo sube a S3.
        Parámetros:
            bucket_name (str): Nombre del bucket de S3 donde se guardará el PDF.

            json_dict (dict): Diccionario con los datos del contratante

            df_parametros: DataFrame con los parámetros de la cotización.

            df_calculo: DataFrame con los datos de cálculo de la cotización.

        Retorna:
            PDF (Any) . Objeto con el pdf.

        """
        
        # Creamos un cliente de S3
        s3 = boto3.client('s3')
        imagen_s3_key = "coco/data/master_data/logo/logo_SegurosDelValle.png"
        

        #pdf_s3_key = "coco/solicitudes/formatos_pdf/" + contratante_dict["Contratante"][0] + ".pdf"
        
        
        # Cargamos la imagen del logo desde S3
        imagen_buffer = BytesIO()
        s3.download_fileobj(bucket_name, imagen_s3_key, imagen_buffer)   #Carga del logo
        imagen_buffer.seek(0)
        
        # Creamos un PDF en memoria
        pdf_buffer = BytesIO()        
        c = canvas.Canvas(pdf_buffer) # Canvas para el PDF
        
        # Campos variables del PDF
        contratante = contratante_dict["Contratante"][0]

        # Generamos campo de coberturas
        if contratante_dict["Coberturas"][0] == "F":
            coberturas = "FALLECIMIENTO"
        elif contratante_dict["Coberturas"][0] == "FMA":
            coberturas = "FALLECIMIENTO Y MUERTE ACCIDENTAL"
        elif contratante_dict["Coberturas"][0] == "FBPAI":
            coberturas = "FALLECIMIENTO E INVALIDEZ TOTAL"
        elif contratante_dict["Coberturas"][0] == "FMABPAI":
            coberturas = "FALLECIMIENTO, MUERTE ACCIDENTAL E INVALIDEZ TOTAL"

        # Generamos campos relevantes
        suma_asegurada = contratante_dict["SumaAsegurada"][0]

        edad_promedio = int(contratante_dict["EdadPromedio"][0])

        administracion = contratante_dict["Administracion"][0]

        SAMI = contratante_dict["SumaAsegurada"][0]

        agente = contratante_dict["Agente"][0]
        
        inicio = contratante_dict['Inicio'][0]
        fin = contratante_dict['Fin'][0]
        vigencia = f"{inicio} - {fin}"
        
        prima = contratante_dict["Prima"][0]
        forma_pago = contratante_dict["FormaPago"][0]
        
        asegurados = int(contratante_dict['Asegurados'][0])

        num_recibos = contratante_dict["NumRecibos"][0]
        
        # Insertar imagen en la parte superior izquierda (ajustar tamaño/posición si es necesario)
        imagen = ImageReader(imagen_buffer)
        c.drawImage(imagen, x=30, y=740, width=200, height=75)
        
        # Agregar texto
        c.drawString(50, 700, "DESGLOSE DE ESTUDIO DE SEGURO DE VIDA GRUPO")
        c.drawString(50, 685, f"CONTRATANTE: {contratante}")
        c.drawString(50, 670, f"COBERTURAS: {coberturas}")
        c.drawString(50, 655, f"SUMA ASEGURADA: $ {suma_asegurada:,.2f}")
        c.drawString(50, 640, f"EDAD PROMEDIO: {edad_promedio}")
        c.drawString(50, 625, f"SISTEMA DE ADMINISTRACIÓN: {administracion}")
        c.drawString(50, 610, f"SAMI: $ {SAMI:,.2f}")
        c.drawString(50, 595, "CONTRIBUTORIO: NO CONTRIBUTORIO")
        c.drawString(50, 580, "DIVIDENDOS: SIN DIVIDENDOS")
        c.drawString(50, 565, f"AGENTE: {agente}")
        c.drawString(50, 550, f"VIGENCIA: {vigencia}")
        if isinstance(prima, str):
            c.drawString(50, 535, f"PRIMA:  {prima}")
        else:
            c.drawString(50, 535, f"PRIMA: $ {prima:,.2f}")
        c.drawString(50, 520, f"FORMA DE PAGO: {forma_pago}")
        if isinstance(prima, str):
            c.drawString(50, 505, f"PRIMA:  {prima}")
        else:
            c.drawString(50, 505, f"PRIMER RECIBO Y SUBSECUENTES: $ {prima/num_recibos:,.2f}")
        c.drawString(50, 490, f"ASEGURADOS: {asegurados}")
        c.drawString(50, 475, "EDAD DE ACEPTACIÓN PARA LA COBERTURA DE FALLECIMIENTO: HASTA 75 AÑOS")
        c.drawString(50, 460, "EDAD DE ACEPTACIÓN PARA LA COBERTURA DE MUERTE ACCIDENTAL: HASTA 69 AÑOS")
        c.drawString(50, 445, "EDAD DE ACEPTACIÓN PARA LA COBERTURA DE INVALIDEZ TOTAL: HASTA 64 AÑOS")
        c.drawString(50, 415, "ESTA COTIZACIÓN NO REPRESENTA COMPROMISO DE COBERTURA ALGUNA Y TIENE")
        c.drawString(50, 403, "VIGENCIA DE 30 DÍAS A PARTIR DE LA FECHA QUE ES RECIBIDA")
        c.drawString(50, 385, "RECARGO POR PAGO FRACCIONADO (MENSUAL: 6.5%, TRIMESTRAL: 5.5% Y")
        c.drawString(50, 373, "SEMESTRAL: 3.7%)")
        c.drawString(50, 343, "SEGUROS DEL VALLE, S. A., CON DOMICILIO EN AV. RÍO HONDO, NO. 1, COL. ALTAVISTA,")
        c.drawString(50, 331, "CP 08000, ALCALDÍA BENITO JUÁREZ, CDMX PONE A SU DISPOSICIÓN SU AVISO DE")
        c.drawString(50, 319, "PRIVACIDAD INTEGRAL EN LA PÁGINA WEB WWW.SEGUROSDELVALLE.COM.MX Y LE")
        c.drawString(50, 307, "INFORMA QUE SUS DATOS ESTÁN PROTEGIDOS Y SON UTILIZADOS SOLO PARA REGULAR")
        c.drawString(50, 295, "LOS DERECHOS Y OBLIGACIONES QUE SURGEN DE LA CELEBRACIÓN DE SU CONTRATO")
        c.drawString(50, 283, "DE SEGURO.")
        
        # Finalizar y preparar el buffer
        c.save()
        pdf_buffer.seek(0)
        
        return pdf_buffer  # Retorna el buffer del PDF generado


def obtener_nombres_empresas(bucket_name, ruta_dict):
    """
    *Función para obtener los nombres de las empresas a partir de los archivos JSON en S3.*
    
    **Parameters**:
        
        bucket_name (str): Nombre del bucket de S3.
        
        ruta_dict (str): Ruta dentro del bucket donde se encuentran los archivos JSON.
    
    **Returns**:
        
        nombres_empresas (list): Lista de nombres de empresas extraídos de los archivos JSON.
    """
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=ruta_dict)
    nombres_empresas = []
    
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.json'):
                nombre_empresa = key.split('/')[-1].replace('.json', '')
                nombres_empresas.append(nombre_empresa)
    
    return nombres_empresas