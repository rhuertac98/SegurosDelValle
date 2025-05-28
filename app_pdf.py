import streamlit as st
import boto3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import yaml

# Cargamos configuracion
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)


S3_BUCKET = config['s3']['bucket_name']
S3_PREFIX = config['s3']['prefix_pdf']
SMTP_SERVER = config['email']['smtp_server']
SMTP_PORT = config['email']['smtp_port']
EMAIL_ADDRESS = config['email']['sender_address']
EMAIL_PASSWORD = config['email']['sender_password']

s3 = boto3.client(
    's3',
    aws_access_key_id=config['aws']['access_key_id'],
    aws_secret_access_key=config['aws']['secret_access_key']
)


# Usuarios autorizados (usuario: contraseña)



# ============== FUNCIONES ==============
def check_login(username, password):
    """
    *Función que verifica si el usuario y contraseña son correctos*
    
    **Parameters**:
        
        username (str): Nombre de usuario
        
        password (str): Contraseña del usuario
        
    **Returns**:
        
        bool: True si las credenciales son correctas, False en caso contrario
    """
    
    USERS = {
    "admin": "admin123",
    "usuario1": "password1",
    "demo": "demo123"
}

    return username in USERS and USERS[username] == password

def get_pdf_list():
    """*Obtiene la lista de PDFs desde S3*
    
    **Returns**:

        list: Lista de diccionarios con información de los PDFs (nombre, clave, tamaño)
    
    """
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        pdfs = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.pdf'):
                    pdfs.append({
                        'name': obj['Key'].split('/')[-1],
                        'key': obj['Key'],
                        'size': obj['Size'] / (1024 * 1024)  # Convertir a MB
                    })
        return pdfs
    except Exception as e:
        st.error(f"Error al conectar con S3: {str(e)}")
        return []

def download_pdf(s3_key):
    """*Función que descarga un PDF desde S3*
    
    **Parameters**:
    
        s3_key (str): Clave del objeto en S3
    
    **Returns**:
    
        bytes: Contenido del PDF descargado, o None si hubo un error
    """
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return response['Body'].read()
    except Exception as e:
        st.error(f"Error al descargar: {str(e)}")
        return None

def send_email(to_email, pdf_data, pdf_name):
    """Envía el PDF por correo"""
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = f'Envío de cotización - COCO (Seguros del Valle): {pdf_name}'
        
        # Cuerpo del mensaje
        body = f"""
        Buen día,
        
        Se envía el PDF de la cotización de la empresa: {pdf_name}
        
        Saludos,
        Core: Sistema de descarga y envío de solicitudes
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Adjuntar PDF
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(pdf_data)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={pdf_name}')
        msg.attach(attachment)
        
        # Enviar
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {str(e)}")
        return False

# ============== INTERFAZ STREAMLIT ==============
st.set_page_config(page_title="CORE: Sistema de información de Seguros Del Valle", page_icon="📄")

# Inicializar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# PÁGINA DE LOGIN
if not st.session_state.logged_in:
    st.title("🔐 Iniciar Sesión")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            login_button = st.form_submit_button("Entrar", use_container_width=True)
            
            if login_button:
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

# PÁGINA PRINCIPAL (después del login)
else:
    # Header con botón de logout
    col1, col2 = st.columns([6,1])
    with col1:
        st.title("CORE: Sistema de información de Seguros Del Valle")
        st.caption(f"Usuario: {st.session_state.username}")
    with col2:
        if st.button("Salir"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.divider()
    
    # Obtener lista de PDFs
    pdf_list = get_pdf_list()
    
    if pdf_list:
        # Seleccionar PDF
        selected_pdf = st.selectbox(
            "Selecciona un archivo de cotización:",
            options=[pdf['name'] for pdf in pdf_list],
            format_func=lambda x: f"{x} ({next(p['size'] for p in pdf_list if p['name'] == x):.1f} MB)"
        )
        
        # Obtener datos del PDF seleccionado
        pdf_info = next(p for p in pdf_list if p['name'] == selected_pdf)
        
        st.divider()
        
        # Opciones: Descargar o Enviar por correo
        col1, col2 = st.columns(2)
        
        # OPCIÓN 1: DESCARGAR
        with col1:
            st.subheader("Descargar PDF")
            if st.button("Descargar", type="primary", use_container_width=True):
                pdf_data = download_pdf(pdf_info['key'])
                if pdf_data:
                    st.download_button(
                        label="Guardar archivo",
                        data=pdf_data,
                        file_name=selected_pdf,
                        mime="application/pdf",
                        use_container_width=True
                    )
        
        # OPCIÓN 2: ENVIAR POR CORREO
        with col2:
            st.subheader("Enviar por correo")
            email_to = st.text_input("Correo destino:", placeholder="ejemplo@correo.com")
            
            if st.button("Enviar", type="secondary", use_container_width=True):
                if email_to:
                    with st.spinner("Enviando..."):
                        pdf_data = download_pdf(pdf_info['key'])
                        if pdf_data and send_email(email_to, pdf_data, selected_pdf):
                            st.success(f"Enviado a {email_to}")
                        else:
                            st.error("Error al enviar")
                else:
                    st.warning("Ingresa un correo electrónico")
    
    else:
        st.warning("No se encontraron PDFs en el bucket")