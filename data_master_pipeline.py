import boto3
import yaml
import json
import pandas as pd
import numpy as np
from io import BytesIO
from src.calc_primas_utils import (
    obtener_lista_nombre_bases,
    obtener_base_parametros,
    obtener_base_cuotas,
    obtener_base_emisiones,
    obtener_base_historico,
    creacion_cotizacion_dict,
    generar_memoria_calculo
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
ruta_calculo = config['paths']['calculo_path']
ruta_parametros = config['paths']['parametros_path']
ruta_cuotas = config['paths']['cuotas_path']
ruta_emisiones = config['paths']['emisiones_path']
ruta_historico_cotizaciones = config['paths']['historico_path']
ruta_dict = config['paths']['dict_output_path']
ruta_memoria_calculo = config['paths']['memoria_calculo_output_path']

if __name__ == "__main__":
    try:
        
        # 1. Cargar bases de datos        
        lista_archivos_base_datos = obtener_lista_nombre_bases(ruta_calculo, bucket_name)
        df_parametros = obtener_base_parametros(ruta_parametros, bucket_name)
        df_cuotas = obtener_base_cuotas(ruta_cuotas, bucket_name)
        df_emisiones = obtener_base_emisiones(ruta_emisiones, bucket_name)
        df_hist_cotizaciones = obtener_base_historico(ruta_historico_cotizaciones, bucket_name)
                
        # 2. Cargar y concatenar bases de cálculo
        dfs_calculos = {}
        for ruta in lista_archivos_base_datos:
            response = s3.get_object(Bucket=bucket_name, Key=ruta)
            content = response['Body'].read()
            df_calculo = pd.read_excel(BytesIO(content), engine='openpyxl')
            dfs_calculos[ruta] = df_calculo
        
        df_calculo = pd.concat(dfs_calculos.values(), ignore_index=True)
        
        # 3. Procesar cada contratante        
        dicts_contratantes = {}
        ticket = len(df_hist_cotizaciones) + 1
        contratantes = df_parametros['Contratante'].unique()
        
        for i, contratante in enumerate(contratantes, 1):
            try:
                
                # Filtrar datos del contratante
                df_calculo_contratante = df_calculo[df_calculo['Contratante'] == contratante].copy()
                
                # Crear diccionario de cotización
                dict_contratante = creacion_cotizacion_dict(
                    df_parametros, contratante, ticket, 
                    df_calculo_contratante, df_emisiones, df_cuotas
                )
                
                df_dict_contratante = pd.DataFrame(dict_contratante)
                dicts_contratantes[contratante] = df_dict_contratante
                ticket += 1
                
                # Guardar diccionario como JSON
                ruta_dict_contratante = f'{ruta_dict}{contratante}.json'
                s3.put_object(
                    Bucket=bucket_name, 
                    Key=ruta_dict_contratante, 
                    Body=json.dumps(dict_contratante, indent=2, ensure_ascii=False, default=str).encode('utf-8'),
                    ContentType='application/json'
                )
                
                # Generar memoria de cálculo
                fecha_corte = dict_contratante['Inicio'][0]
                descuento = dict_contratante['Descuento'][0]
                rpf = dict_contratante['RPF'][0]
                
                memoria_calculo = generar_memoria_calculo(
                    contratante, fecha_corte, df_parametros, 
                    df_calculo_contratante, df_cuotas, descuento, rpf
                )
                
                # Subir memoria de cálculo
                ruta_memoria_calculo_completa = f'{ruta_memoria_calculo}{contratante}.csv'
                memoria_csv = memoria_calculo.to_csv(index=False)
                
                s3.put_object(
                    Bucket=bucket_name,
                    Key=ruta_memoria_calculo_completa,
                    Body=memoria_csv.encode('utf-8'),
                    ContentType='text/csv'
                )
                
            except Exception as e:
                print(f"Error con {contratante}: {e}")
                continue
        
        # 4. Actualizar historial de cotizaciones        
        df_dict_contratantes = pd.concat(dicts_contratantes.values(), ignore_index=True)
        df_dict_contratantes['Tipo'] = np.where(
            df_dict_contratantes['Renovacion'] == 'Si', 'renovación', 'nuevo'
        )
        df_dict_contratantes['Fecha de Inicio'] = df_dict_contratantes['Inicio']
        
        cols = ['Ticket', 'Fecha de Inicio', 'Mes', "Oficina", "Contratante", 
                "Agente", "Prima", "Evento", "Tipo"]
        df_dict_contratantes = df_dict_contratantes[cols]
        
        df_hist_cotizaciones_actualizado = pd.concat([df_hist_cotizaciones, df_dict_contratantes], ignore_index=True)
        
        # Subir historial actualizado
        ruta_hist_actualizado = 'coco/data/master_data/historico/historial_cotizaciones_actualizado.csv'
        hist_csv = df_hist_cotizaciones_actualizado.to_csv(index=False)
        s3.put_object(
            Bucket=bucket_name,
            Key=ruta_hist_actualizado,
            Body=hist_csv.encode('utf-8'),
            ContentType='text/csv'
        )
        
        
        # Reporte final
        print("\n=== PIPELINE COMPLETADO ===")
        print(f"Contratantes procesados: {len(dicts_contratantes)}")
        print(f"Diccionarios generados: {len(dicts_contratantes)}")
        print(f"Memorias de cálculo generadas: {len(dicts_contratantes)}")
        print(f"Historial actualizado con {len(df_dict_contratantes)} nuevos registros")
        
    except Exception as e:
        print(f"Error en el pipeline: {e}")
        raise