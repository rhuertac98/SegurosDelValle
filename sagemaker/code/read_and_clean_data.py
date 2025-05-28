import subprocess
import sys
import os
import pandas as pd

# Instala openpyxl si no está disponible
try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])

# --------------------
# Utilidades
# --------------------

def explorar_y_leer_archivo(directorio: str) -> pd.DataFrame:
    print(f"\n📁 Explorando: {directorio}")
    if os.path.exists(directorio):
        archivos = os.listdir(directorio)
        if archivos:
            for archivo in archivos:
                print(f"  - {archivo}")
                if archivo.endswith(".xlsx"):
                    ruta = os.path.join(directorio, archivo)
                    try:
                        df = pd.read_excel(ruta, engine="openpyxl")
                        print(f"    ✅ Leído correctamente: {df.shape[0]} filas, {df.shape[1]} columnas")
                    except Exception as e:
                        print(f"    ❌ Error al leer {archivo}: {e}")
        else:
            print("  ⚠️ Carpeta vacía")
    else:
        print("  ❌ Carpeta no encontrada")

# --------------------
# Ejecución principal
# --------------------

INPUT_DIR = "/opt/ml/processing"

subcarpetas = [
    "parametros",
    "experiencia",
    "emisiones",
    "cotizaciones",
    "solicitudes"
]

print("\n🔍 Verificando y leyendo archivos montados desde S3...")

for sub in subcarpetas:
    ruta = os.path.join(INPUT_DIR, sub)
    explorar_y_leer_archivo(ruta)

print("\n✅ Lectura de archivos completada.")
