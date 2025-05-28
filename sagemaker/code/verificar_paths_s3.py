import boto3

bucket = "itam-analytics-danielmichell"
s3 = boto3.client("s3")

paths = {
    "Parametros": "coco/data/solicitudes/Parametros/parametros.xlsx",
    "Experiencia Global": "coco/modelo/experiencia_global.xlsx",
    "Emisiones": "coco/data/emisiones.xlsx",
    "Cotizaciones": "coco/data/cotizaciones.xlsx",
    "Solicitudes (carpeta)": "coco/data/solicitudes/Base_Datos/"
}

print("🔍 Verificando existencia de objetos en S3...\n")

for nombre, key in paths.items():
    if key.endswith("/"):
        # carpeta
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=key)
        existe = "Contents" in resp and len(resp["Contents"]) > 0
    else:
        # archivo
        try:
            s3.head_object(Bucket=bucket, Key=key)
            existe = True
        except s3.exceptions.ClientError:
            existe = False

    estado = "✅ Existe" if existe else "❌ No encontrado"
    print(f"{estado}: {nombre} ({key})")

print("\n✅ Verificación de paths S3 finalizada.")
