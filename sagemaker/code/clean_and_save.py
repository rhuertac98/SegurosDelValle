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
# Funciones de limpieza
# --------------------

def limpiar_parametros(df):
    print("  🔧 Limpiando parámetros...")
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")
    if "Comision" in df.columns:
        df["Comision"] = df["Comision"].astype(str).str.replace("%", "", regex=False).str.replace(",", ".").astype(float) / 100
    if "SumaAsegurada" in df.columns:
        df["SumaAsegurada"] = df["SumaAsegurada"].astype(str).str.replace(",", "", regex=False).str.extract(r'(\d+\.?\d*)')[0].astype(float)
    for col in ["Inicio", "Fin"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "FormaPago" in df.columns:
        df["FormaPago"] = df["FormaPago"].str.strip().str.lower().map({
            "mensual": "mensual",
            "trimestral": "trimestral",
            "semestral": "semestral",
            "anual": "anual"
        }).fillna("otros")
    # if "Renovacion" in df.columns:
    #    df["Renovacion"] = df["Renovacion"].astype(str).str.lower().map({"si": True, "sí": True, "no": False}).fillna(False)
    if "Oficina" in df.columns:
        df["Oficina"] = df["Oficina"].fillna("Desconocida").str.strip()
    return df

def limpiar_experiencia(df):
    print("  🔧 Limpiando experiencia...")
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["Edad", "Fallecimiento"])
    df["Edad"] = pd.to_numeric(df["Edad"], errors="coerce")
    for col in ["Fallecimiento", "MA", "BPAI"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["Edad"].notna()]
    return df

def limpiar_generico(df):
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")
    df = df.drop_duplicates()
    return df

# --------------------
# Ejecución principal
# --------------------

INPUT_DIR = "/opt/ml/processing"
OUTPUT_DIR = os.path.join(INPUT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

archivos = {
    "parametros": "parametros.xlsx",
    "experiencia": "experiencia_global.xlsx",
    "emisiones": "emisiones.xlsx",
    "cotizaciones": "cotizaciones.xlsx"
}

print("\n🔧 Iniciando limpieza extendida de archivos...")

for carpeta, archivo in archivos.items():
    ruta = os.path.join(INPUT_DIR, carpeta, archivo)
    print(f"\n📂 Leyendo: {ruta}")
    try:
        df = pd.read_excel(ruta, engine="openpyxl")
        print(f"  ✅ Leído: {df.shape[0]} filas, {df.shape[1]} columnas")

        if carpeta == "parametros":
            df = limpiar_parametros(df)
        elif carpeta == "experiencia":
            df = limpiar_experiencia(df)
        else:
            df = limpiar_generico(df) 
        df.to_csv(os.path.join(OUTPUT_DIR, f"{carpeta}.csv"), index=False)
        print(f"  💾 Guardado como {carpeta}.csv")

    except Exception as e:
        print(f"  ❌ Error al procesar {archivo}: {e}")

# Procesar múltiples solicitudes
sol_dir = os.path.join(INPUT_DIR, "solicitudes")
os.makedirs(os.path.join(OUTPUT_DIR, "solicitudes"), exist_ok=True)

for archivo in os.listdir(sol_dir):
    if archivo.endswith(".xlsx"):
        ruta = os.path.join(sol_dir, archivo)
        try:
            df = pd.read_excel(ruta, engine="openpyxl")
            df.columns = df.columns.str.strip()
            df = df.dropna(how="all").drop_duplicates()
            salida = os.path.join(OUTPUT_DIR, "solicitudes", archivo.replace(".xlsx", ".csv"))
            df.to_csv(salida, index=False)
            print(f"  ✅ Solicitud procesada: {archivo} → {salida}")
        except Exception as e:
            print(f"❌ Error en solicitud {archivo}: {e}")

print("\n✅ Limpieza extendida completada. Archivos disponibles en /opt/ml/processing/output")
