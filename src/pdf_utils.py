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
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

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



def draw_header_bar(canvas_obj, y_pos, text, width, height_bar=25):
    """*Dibuja una barra naranja con texto blanco*
    
    **Parameters**:

        canvas_obj (Canvas): Objeto canvas de ReportLab donde se dibuja la barra.
    
        y_pos (float): Posición vertical donde se dibuja la barra.
    
        text (str): Texto a mostrar en la barra.
        
        width (float): Ancho total del PDF.
        
        height_bar (float): Altura de la barra (por defecto 25).
    
    **Returns**:
        float: Nueva posición vertical después de dibujar la barra."""

    NARANJA_CORPORATIVO = colors.Color(0.9, 0.4, 0.1)

    canvas_obj.setFillColor(NARANJA_CORPORATIVO)
    canvas_obj.rect(50, y_pos - height_bar, width-100, height_bar, fill=1)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.drawString(60, y_pos - 18, text)
    canvas_obj.setFillColor(colors.black)
    return y_pos - height_bar

def truncate_text(canvas_obj, text, max_width, font_name, font_size):
    """Función que trunca el texto si es muy largo
    
    **Parameters**:
    
        canvas_obj (Canvas): Objeto canvas de ReportLab donde se dibuja el texto.
    
        text (str): Texto a truncar.

        max_width (float): Ancho máximo permitido para el texto.
        
        font_name (str): Nombre de la fuente a utilizar.
        
        font_size (int): Tamaño de la fuente a utilizar.
    
    **Returns**:
    
        str: Texto truncado si es necesario, con "..." al final si se truncó."""
    
    text_width = canvas_obj.stringWidth(str(text), font_name, font_size)
    if text_width <= max_width:
        return str(text)
    
    # Si es muy largo, lo truncamos y agregamos "..."
    while text_width > max_width - 20:  # Dejamos espacio para "..."
        text = text[:-1]
        text_width = canvas_obj.stringWidth(text + "...", font_name, font_size)
    return text + "..."

def draw_table_with_borders(canvas_obj, data, start_y, width, row_height=25):
    """*Función que dibuja una tabla con bordes y datos organizados correctamente*
    
    **Parameters**:
        canvas_obj (Canvas): Objeto canvas de ReportLab donde se dibuja la tabla.

        data (list): Lista de listas con los datos a mostrar en la tabla.
        
        start_y (float): Posición vertical inicial para dibujar la tabla.
        
        width (float): Ancho total del PDF.
        
        row_height (float): Altura de cada fila de la tabla (por defecto 25).
    
    **Returns**:
        
        float: Nueva posición vertical después de dibujar la tabla."""
    
    table_width = width - 100  # Ancho total de la tabla
    col_width = table_width / 2  # Ancho de cada columna principal
    y_pos = start_y
    GRIS_CLARO = colors.Color(0.95, 0.95, 0.95)
    for i, row_data in enumerate(data):
        # Alternar colores de fila
        if i % 2 == 0:
            canvas_obj.setFillColor(colors.white)
        else:
            canvas_obj.setFillColor(GRIS_CLARO)
        
        # Dibujar rectángulo de fondo
        canvas_obj.rect(50, y_pos - row_height, table_width, row_height, fill=1)
        
        # Dibujar bordes
        canvas_obj.setStrokeColor(colors.grey)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.rect(50, y_pos - row_height, table_width, row_height, fill=0)
        
        # Dibujar línea vertical en el medio si hay 4 columnas
        if len(row_data) == 4 and row_data[2]:  # Solo si hay contenido en columna 3
            canvas_obj.line(50 + col_width, y_pos - row_height, 50 + col_width, y_pos)
        
        # Dibujar texto
        canvas_obj.setFillColor(colors.black)
        
        if len(row_data) == 2:  # Una sola fila con 2 columnas
            # Etiqueta
            canvas_obj.setFont("Helvetica-Bold", 9)
            label_text = truncate_text(canvas_obj, row_data[0], col_width * 0.4, "Helvetica-Bold", 9)
            canvas_obj.drawString(60, y_pos - 17, label_text)
            
            # Valor
            canvas_obj.setFont("Helvetica", 9)
            value_text = truncate_text(canvas_obj, row_data[1], col_width * 0.6, "Helvetica", 9)
            canvas_obj.drawString(60 + col_width * 0.4, y_pos - 17, value_text)
            
        elif len(row_data) == 4:  # Fila con 4 columnas (2 pares)
            # Primer par (izquierda)
            canvas_obj.setFont("Helvetica-Bold", 9)
            label1_text = truncate_text(canvas_obj, row_data[0], col_width * 0.4, "Helvetica-Bold", 9)
            canvas_obj.drawString(60, y_pos - 17, label1_text)
            
            canvas_obj.setFont("Helvetica", 9)
            value1_text = truncate_text(canvas_obj, row_data[1], col_width * 0.5, "Helvetica", 9)
            canvas_obj.drawString(60 + col_width * 0.35, y_pos - 17, value1_text)
            
            # Segundo par (derecha)
            if row_data[2]:  # Solo si hay contenido
                canvas_obj.setFont("Helvetica-Bold", 9)
                label2_text = truncate_text(canvas_obj, row_data[2], col_width * 0.4, "Helvetica-Bold", 9)
                canvas_obj.drawString(60 + col_width, y_pos - 17, label2_text)
                
                canvas_obj.setFont("Helvetica", 9)
                value2_text = truncate_text(canvas_obj, row_data[3], col_width * 0.5, "Helvetica", 9)
                canvas_obj.drawString(60 + col_width + col_width * 0.35, y_pos - 17, value2_text)
        
        y_pos -= row_height
    
    return y_pos

def draw_single_column_table(canvas_obj, data, start_y, width, row_height=25):
    """*Función que dibuja una tabla de una sola columna para información importante*
    
    **Parameters**:
        
        canvas_obj (Canvas): Objeto canvas de ReportLab donde se dibuja la tabla.
    
        data (list): Lista de strings con los datos a mostrar en la tabla.
        
        start_y (float): Posición vertical inicial para dibujar la tabla.
        
        width (float): Ancho total del PDF.
        
        row_height (float): Altura de cada fila de la tabla (por defecto 25).
        
    **Returns**:
        
        float: Nueva posición vertical después de dibujar la tabla."""

    GRIS_CLARO = colors.Color(0.95, 0.95, 0.95)
    table_width = width - 100
    y_pos = start_y
    
    for i, text in enumerate(data):
        # Alternar colores de fila
        if i % 2 == 0:
            canvas_obj.setFillColor(colors.white)
        else:
            canvas_obj.setFillColor(GRIS_CLARO)
        
        # Dibujar rectángulo de fondo
        canvas_obj.rect(50, y_pos - row_height, table_width, row_height, fill=1)
        
        # Dibujar bordes
        canvas_obj.setStrokeColor(colors.grey)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.rect(50, y_pos - row_height, table_width, row_height, fill=0)
        
        # Dibujar texto
        canvas_obj.setFillColor(colors.black)
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(60, y_pos - 17, str(text))
        
        y_pos -= row_height
    
    return y_pos

def generar_pdf_cotizacion(bucket_name: str, contratante_dict: dict) -> Any:
    """
    *Función que genera un PDF de cotización de seguro de vida grupal con formato profesional.*

    **Parameters**:
        bucket_name (str): Nombre del bucket de S3 donde se encuentran los logos.
        
        contratante_dict (dict): Diccionario que contiene los datos del contratante y la cotización.    

    **Returns**:
        BytesIO: Objeto BytesIO que contiene el PDF generado.
    """
    
    # Creamos un cliente de S3
    s3 = boto3.client('s3')
    logo_principal_key = "coco/data/master_data/logo/logo_SegurosDelValle.png"
    logo_secundario_key = "coco/data/master_data/logo/core.jpeg"
    
    # Cargamos las imágenes desde S3
    imagen_principal_buffer = BytesIO()
    s3.download_fileobj(bucket_name, logo_principal_key, imagen_principal_buffer)
    imagen_principal_buffer.seek(0)
    
    imagen_secundaria_buffer = BytesIO()
    s3.download_fileobj(bucket_name, logo_secundario_key, imagen_secundaria_buffer)
    imagen_secundaria_buffer.seek(0)
    
    # Creamos un PDF en memoria
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    # Extraer datos del diccionario
    contratante = contratante_dict["Contratante"][0]
    
    # Mapeo de coberturas
    coberturas_map = {
        "F": "FALLECIMIENTO",
        "FMA": "FALLECIMIENTO Y MUERTE ACCIDENTAL", 
        "FBPAI": "FALLECIMIENTO E INVALIDEZ TOTAL",
        "FMABPAI": "FALLECIMIENTO, MUERTE ACCIDENTAL E INVALIDEZ TOTAL"
    }
    coberturas = coberturas_map.get(contratante_dict["Coberturas"][0], contratante_dict["Coberturas"][0])
    
    suma_asegurada = contratante_dict["SumaAsegurada"][0]
    edad_promedio = int(contratante_dict["EdadPromedio"][0])
    administracion = contratante_dict["Administracion"][0]
    agente = contratante_dict["Agente"][0]
    inicio = contratante_dict['Inicio'][0]
    fin = contratante_dict['Fin'][0]
    vigencia = f"{inicio} - {fin}"
    prima = contratante_dict["Prima"][0]
    forma_pago = contratante_dict["FormaPago"][0]
    asegurados = int(contratante_dict['Asegurados'][0])
    num_recibos = contratante_dict["NumRecibos"][0]
    
    # === ENCABEZADO ===
    # Logo principal
    imagen_principal = ImageReader(imagen_principal_buffer)
    c.drawImage(imagen_principal, 50, height-100, width=150, height=60)
    
    # Logo secundario
    imagen_secundaria = ImageReader(imagen_secundaria_buffer)
    c.drawImage(imagen_secundaria, width-200, height-100, width=150, height=60)
    
    # Título principal
    c.setFont("Helvetica-Bold", 16)
    titulo = "DESGLOSE DE ESTUDIO DE SEGURO DE VIDA GRUPO"
    text_width = c.stringWidth(titulo, "Helvetica-Bold", 16)
    c.drawString((width - text_width) / 2, height-130, titulo)
    
    # === SECCIÓN: DATOS DEL CONTRATO ===
    current_y = height - 170
    current_y = draw_header_bar(c, current_y, "DATOS DEL CONTRATO", width)
    
    datos_contrato = [
        ["CONTRATANTE:", contratante, "AGENTE:", agente],
        ["COBERTURAS:", coberturas, "", ""],
        ["SUMA ASEGURADA:", f"$ {suma_asegurada:,.2f}", "VIGENCIA:", vigencia],
        ["EDAD PROMEDIO:", f"{edad_promedio} AÑOS", "ASEGURADOS:", str(asegurados)]
    ]
    
    current_y = draw_table_with_borders(c, datos_contrato, current_y, width)
    
    # === SECCIÓN: SISTEMA DE ADMINISTRACIÓN ===
    current_y -= 5
    current_y = draw_header_bar(c, current_y, "SISTEMA DE ADMINISTRACIÓN", width)
    
    datos_admin = [
        ["ADMINISTRACIÓN:", administracion, "CONTRIBUTORIO:", "NO CONTRIBUTORIO"],
        ["DIVIDENDOS:", "SIN DIVIDENDOS", "", ""]
    ]
    
    current_y = draw_table_with_borders(c, datos_admin, current_y, width)
    
    # === SECCIÓN: INFORMACIÓN FINANCIERA ===
    current_y -= 5
    current_y = draw_header_bar(c, current_y, "INFORMACIÓN FINANCIERA", width)
    
    if isinstance(prima, str):
        prima_texto = prima
        primer_recibo = prima
    else:
        prima_texto = f"$ {prima:,.2f}"
        primer_recibo = f"$ {prima/num_recibos:,.2f}"
    
    datos_financieros = [
        ["PRIMA TOTAL:", prima_texto, "FORMA DE PAGO:", forma_pago],
        ["PRIMER RECIBO:", primer_recibo, "SAMI:", f"$ {suma_asegurada:,.2f}"],
        ["RECARGO FRACCIONADO:", "MENSUAL: 6.5%", "TRIMESTRAL: 5.5%", "SEMESTRAL: 3.7%"]
    ]
    
    current_y = draw_table_with_borders(c, datos_financieros, current_y, width)
    
    # === SECCIÓN: CONDICIONES DE ACEPTACIÓN ===
    current_y -= 5
    current_y = draw_header_bar(c, current_y, "CONDICIONES DE ACEPTACIÓN", width)
    
    condiciones = [
        ["FALLECIMIENTO:", "HASTA 75 AÑOS", "", ""],
        ["MUERTE ACCIDENTAL:", "HASTA 69 AÑOS", "", ""],
        ["INVALIDEZ TOTAL:", "HASTA 64 AÑOS", "", ""]
    ]
    
    current_y = draw_table_with_borders(c, condiciones, current_y, width)
    
    # === INFORMACIÓN IMPORTANTE ===
    current_y -= 5
    current_y = draw_header_bar(c, current_y, "INFORMACIÓN IMPORTANTE", width)
    
    info_importante = [
        "• ESTA COTIZACIÓN NO REPRESENTA COMPROMISO DE COBERTURA ALGUNA",
        "• VIGENCIA DE 30 DÍAS A PARTIR DE LA FECHA QUE ES RECIBIDA"
    ]
    
    current_y = draw_single_column_table(c, info_importante, current_y, width)
    
    # === PIE DE PÁGINA ===
    footer_y = 60
    c.setFont("Helvetica", 7)
    footer_text = [
        "SEGUROS DEL VALLE, S.A. DE C.V. CON DOMICILIO EN AV. RÍO HONDO NO. 1, COL. ALTAVISTA, CP. 08000,",
        "ALCALDÍA BENITO JUÁREZ, CDMX. REGISTRO ANTE CONDUSEF: 1685. PARA CONSULTA DE PRODUCTOS,",
        "COBERTURAS, PRIMAS, COMISIONES Y PROCEDIMIENTOS DE CONTRATACIÓN CONSULTE WWW.SEGUROSDELVALLE.COM.MX"
    ]
    
    for line in footer_text:
        c.drawString(50, footer_y, line)
        footer_y -= 10
    
    # Finalizar PDF
    c.save()
    pdf_buffer.seek(0)
    
    return pdf_buffer