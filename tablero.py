import streamlit as st
import pandas as pd
import boto3
from io import BytesIO
import plotly.express as px

# Conexión con S3 (debes tener las credenciales configuradas)
def cargar_datos_s3(bucket, archivo):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=archivo)
    df = pd.read_excel(BytesIO(obj['Body'].read()), engine='openpyxl')
    return df

# Filtros para la variable Prima
def filtrar_prima(df, prima_min, prima_max):
    return df[(df['Prima'] >= prima_min) & (df['Prima'] <= prima_max)]

# Función para aplicar filtros
def aplicar_filtros(df, mes, oficina, agente, prima_min, prima_max, evento, tipo):
    if "Todos" not in mes:
        df = df[df['Mes'].isin(mes)]
    if "Todos" not in oficina:
        df = df[df['Oficina'].isin(oficina)]
    if "Todos" not in agente:
        df = df[df['Agente'].isin(agente)]
    if "Todos" not in evento:
        df = df[df['Evento'].isin(evento)]
    if "Todos" not in tipo:
        df = df[df['Tipo'].isin(tipo)]
    df = filtrar_prima(df, prima_min, prima_max)
    return df

# Título de la app en Streamlit
st.title("Cotizaciones de Vida Grupo por Oficina")

# Cargar datos
bucket = 'itam-analytics-werther98'
archivo = 'coco/cotizaciones.xlsx'  # Cambiar la extensión a .xlsx
df = cargar_datos_s3(bucket, archivo)

# Filtros con la opción de seleccionar múltiples valores y "Todos"
meses = ['Todos'] + list(df['Mes'].unique())
oficinas = ['Todos'] + list(df['Oficina'].unique())
agentes = ['Todos'] + list(df['Agente'].unique())
eventos = ['Todos'] + list(df['Evento'].unique())
tipos = ['Todos'] + list(df['Tipo'].unique())

# Filtrar por Mes
mes = st.multiselect("Selecciona el Mes", meses, default=["Todos"])
# Filtrar por Oficina
oficina = st.multiselect("Selecciona la Oficina", oficinas, default=["Todos"])
# Filtrar por Agente
agente = st.multiselect("Selecciona el Agente", agentes, default=["Todos"])
# Filtro de Prima
prima_range = st.slider("Selecciona el rango de Prima", min_value=0, max_value=2000000, step=100000, value=(0, 200000))
prima_min, prima_max = prima_range
# Filtrar por Evento
evento = st.multiselect("Selecciona el Evento", eventos, default=["Todos"])
# Filtrar por Tipo
tipo = st.multiselect("Selecciona el Tipo", tipos, default=["Todos"])

# Aplicar filtros
df_filtrado = aplicar_filtros(df, mes, oficina, agente, prima_min, prima_max, evento, tipo)

# Contar los registros por Oficina
conteo = df_filtrado.groupby('Oficina').size().reset_index(name='Número de Registros')

# Gráfica
fig = px.bar(conteo, x='Oficina', y='Número de Registros', title="Número de Registros por Oficina", labels={'Oficina': 'Oficina', 'Número de Registros': 'Número de Registros'})
st.plotly_chart(fig)
