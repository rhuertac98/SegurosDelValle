import boto3
import yaml
from src.pdf_utils import (
    cargar_dict_cotizacion,
    convertir_campo_a_float, 
    convertir_campo_a_fecha,
    generar_pdf_cotizacion,
    obtener_nombres_empresas
)

# Cargar configuración
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Configurar S3
s3 = boto3.client(
    's3',
    aws_access_key_id=config['aws']['access_key_id'],
    aws_secret_access_key=config['aws']['secret_access_key']
)

# Variables de configuración
bucket_name = config['s3']['bucket_name']
ruta_dict = config['paths']['dict_path']
ruta_output = config['paths']['pdf_output_path']
campos_float = config['processing']['campos_float']
campos_fecha = config['processing']['campos_fecha']

if __name__ == "__main__":
    # Obtener empresas
    nombres_empresas = obtener_nombres_empresas(bucket_name, ruta_dict)
    
    # Procesar cada empresa
    for empresa in nombres_empresas:
        try:
            print(f"Procesando: {empresa}")
            
            # Cargar y formatear datos
            dict_empresa = cargar_dict_cotizacion(empresa, bucket_name)
            
            for campo in campos_float:
                dict_empresa = convertir_campo_a_float(dict_empresa, campo)
            
            for campo in campos_fecha:
                dict_empresa = convertir_campo_a_fecha(dict_empresa, campo)
            
            # Generar y subir PDF
            pdf_empresa = generar_pdf_cotizacion(bucket_name, dict_empresa)
            pdf_key = f"{ruta_output}{empresa}.pdf"
            s3.upload_fileobj(pdf_empresa, bucket_name, pdf_key)
            
            print(f"PDF generado: {empresa}")
            
        except Exception as e:
            print(f"Error con {empresa}: {e}")
    
    print("Pipeline completado!")