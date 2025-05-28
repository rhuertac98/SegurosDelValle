#!/usr/bin/env python
# coding: utf-8

# In[27]:


import os
import boto3

def upload_folder_to_s3(ruta_folder_local, ruta_folder_s3):
    """
    Sube todos los archivos desde una carpeta local a una ruta específica de S3.
    
    Parámetros:
        ruta_folder_local (str): Ruta local de la carpeta con archivos a subir.
        ruta_folder_s3 (str): Ruta en S3 en el formato 'bucket_name/.../folder_s3/'.
    """
    # Separar el bucket y la carpeta destino
    if not ruta_folder_s3.startswith("s3://"):
        ruta_folder_s3 = "s3://" + ruta_folder_s3
    # Se quita el string s3:// a la ruta y se genera una lista con las carpetas de la ruta
    s3_path_parts = ruta_folder_s3.replace("s3://", "").split("/", 1)
    #Se guarda el primer elemento de la lista, este es el nombre del bucket
    bucket_name = s3_path_parts[0]
    #Se guarda el resto de la ruta en una variable. El if es por si son más de una carpeta desde el inicio del bucket
    s3_folder = s3_path_parts[1] if len(s3_path_parts) > 1 else ""

    # Crear cliente de S3
    s3 = boto3.client('s3')

    for root, dirs, files in os.walk(ruta_folder_local):
        for filename in files:
            local_file_path = os.path.join(root, filename)
            # Construir la ruta relativa dentro del S3
            relative_path = os.path.relpath(local_file_path, ruta_folder_local)
            s3_key = os.path.join(s3_folder, relative_path).replace("\\", "/")  # Para compatibilidad con Windows
            print(f"Subiendo {local_file_path} a s3://{bucket_name}/{s3_key}")
            s3.upload_file(local_file_path, bucket_name, s3_key)


# In[29]:

ruta_parametros_local='data/raw/'
ruta_parametros_s3='itam-analytics-grb/core/raw/'


# In[37]:


upload_folder_to_s3(ruta_parametros_local, ruta_parametros_s3)


# In[33]:

ruta_BasesDatosAsegurados_local='data/raw/solicitudes/'
ruta_BasesDatosAsegurados_s3='itam-analytics-grb/core/raw/solicitudes'


# In[35]:


upload_folder_to_s3(ruta_BasesDatosAsegurados_local, ruta_BasesDatosAsegurados_s3)


# In[ ]:




