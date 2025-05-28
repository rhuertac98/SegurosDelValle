import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import boto3
import io
from io import BytesIO
import yaml

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
ruta_dashboard = config['paths']['dashborad_path']

# Configurar Streamlit
st.set_page_config(
    page_title="📈 Dashboard CORE",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard CORE")

# Cargar datos
@st.cache_data
def load_data():
    #df = pd.read_csv("data_streamlit.csv")
    # Parámetros
    #bucket_name = 'itam-analytics-danielmichell'
    #s3_key = 'coco/master/historico/fecha=2025-05-27/cotizaciones.csv'  # path relativo en S3

    # Cliente de S3
    #s3 = boto3.client('s3')

    #Descargar archivo a memoria (usando BytesIO)
    response = s3.get_object(Bucket=bucket_name, Key=ruta_dashboard)
    df = pd.read_csv(io.BytesIO(response['Body'].read()))
    df['Fecha de Inicio'] = pd.to_datetime(df['Fecha de Inicio'], errors='coerce')
    if 'Fecha de Fin' in df.columns:
        df['Fecha de Fin'] = pd.to_datetime(df['Fecha de Fin'], errors='coerce')
        df['Duración'] = (df['Fecha de Fin'] - df['Fecha de Inicio']).dt.days
    df['Mes'] = df['Fecha de Inicio'].dt.to_period('M').astype(str)
    df["Oficina"] = df["Oficina"].replace({"MORELIA":"Morelia","LEON":"Leon","MEXICALI":"Mexicali","Matriz":"Ciudad de Mexico"})
    df = df[df["Fecha de Inicio"]<"2025-05-01"].reset_index(drop=True)
    df["Evento"] = df["Evento"].replace({"Fuera de política":'fuera de política'})
    dict_zonas = {'Ciudad de Mexico':'centro', 'Orizaba':'sur', 'Aguascalientes':'centro', 'Monterrey':'norte',
       'Leon':'centro', 'Queretaro':'centro', 'Puebla':'sur', 'Morelia':'centro', 'Satelite':'centro',
       'Guadalajara':'centro', 'Chihuahua':'norte', 'Tijuana':'norte', 'Mexicali':'norte', 'Merida':'sur',
       'Hermosillo':'norte', 'Torreon':'norte', 'Obregon':'norte'}
    df['Zona'] = df['Oficina'].map(dict_zonas)

    df_eventos = df.groupby('Oficina')['Evento'].value_counts().unstack(fill_value=0).reset_index().reset_index(drop=True)
    df_eventos["pct_fuera_politica"] = df_eventos["fuera de política"] / (df_eventos["na"]+df_eventos["fuera de política"] )
    #df_eventos[df_eventos["pct_capacitacion"]>= 0.25].sort_values(by=["pct_capacitacion"],ascending=False)


    return df, df_eventos

df, df_eventos = load_data()
colores_core = ["linen", "firebrick", "darkorange", "goldenrod", "saddlebrown"]
# Sidebar: filtros
st.sidebar.header("🔍 Filtros")

oficinas = st.sidebar.multiselect("Oficina(s)", df['Oficina'].dropna().unique(), default=df['Oficina'].dropna().unique())
tipos = st.sidebar.multiselect("Tipo de Póliza", df['Tipo'].dropna().unique(), default=df['Tipo'].dropna().unique())

rango_fechas_raw = st.sidebar.date_input("Rango de Fechas", [df["Fecha de Inicio"].min(), df["Fecha de Inicio"].max()])
rango_fechas = [pd.to_datetime(rango_fechas_raw[0]), pd.to_datetime(rango_fechas_raw[1])]

# Aplicar filtros
df_filtered = df[
    df["Oficina"].isin(oficinas) &
    df["Tipo"].isin(tipos) &
    df["Fecha de Inicio"].between(rango_fechas[0], rango_fechas[1])
]

# KPIs
st.subheader("📌 Métricas Generales")
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Pólizas Totales", df_filtered.shape[0])

with k2:
    st.metric("Prima Total", f"${df_filtered['Prima'].sum():,.0f}")

with k3:
    avg_prima = df_filtered[df_filtered["Prima"] > 0]["Prima"].mean()
    st.metric("Prima Promedio", f"${avg_prima:,.0f}" if not pd.isna(avg_prima) else "0.00")

with k4:
    ren = df_filtered[df_filtered["Tipo"] == "renovación"].shape[0]
    tasa = (ren / df_filtered.shape[0]) * 100 if df_filtered.shape[0] > 0 else 0
    st.metric("Tasa de Renovación", f"{tasa:.1f}%")

# Visualizaciones
tabs = st.tabs(["📍 Oficina", "📆 Tendencias", "🧑‍💼 Agentes", "🔍 Exploración","📆 Comparador de Períodos"])

with tabs[0]:
    st.subheader("📊 Pólizas por Oficina")
    group_office = df_filtered.groupby("Oficina")["Ticket"].count().sort_values(ascending=True)
    fig = go.Figure(go.Bar(
        x=group_office.values,
        y=group_office.index,
        orientation='h',
        marker=dict(color='steelblue', line=dict(width=2, color='royalblue')),

    ))
    fig.update_layout(
        xaxis_title="Pólizas",
        yaxis_title="Oficina",
        height=450,
        title="Distribución de Pólizas por Oficina",
        title_font=dict(size=22),
        xaxis=dict(title_font=dict(size=18), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=18), tickfont=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Resumen por Oficina")
    resumen = df_filtered.groupby("Oficina").agg(
        Pólizas=("Ticket", "count"),
        Prima_Total=("Prima", "sum"),
        Prima_Promedio=("Prima", "mean"),
        Agentes=("Agente", "nunique")
    ).reset_index().sort_values(by=["Pólizas"])
    df_eventos_aux = df_eventos[["Oficina","fuera de política","na","pct_fuera_politica"]]
    df_eventos_aux["pct_fuera_politica"] = round(df_eventos_aux["pct_fuera_politica"]*100,1)
    # Redondear y formatear métricas monetarias
    resumen["Prima_Total"] = resumen["Prima_Total"].round(0)
    resumen["Prima_Promedio"] = resumen["Prima_Promedio"].round(0)
    resumen = resumen.merge(df_eventos_aux, on = "Oficina", how ="inner")
    # Mostrar con formatos adecuados
    st.dataframe(
        resumen,
        use_container_width=True,
        column_config={
            "Prima_Total": st.column_config.NumberColumn(
                "Prima Total", format="$%d"
            ),
            "Prima_Promedio": st.column_config.NumberColumn(
                "Prima Promedio", format="$%d"
            ),
            "pct_fuera_politica": st.column_config.NumberColumn(
                "% Fuera de Política", format="%.1f%%"
            )
        }
    )

    # Paso 1: Agrupar y contar tickets por zona y oficina
    grouped = df.groupby(["Zona", "Oficina"]).agg({"Ticket": "count"}).reset_index()

    # Paso 2: Ordenar por zona y ticket ascendente
    grouped = grouped.sort_values(by=["Zona", "Ticket"])

    # Paso 3: Función personalizada para cada zona
    def calcular_diferencia(grupo):
        grupo = grupo.reset_index(drop=True)
        if len(grupo) < 3:
            grupo['Diferencia_para_Alcanzar'] = None
            grupo['Oficina_a_Alcanzar'] = None
            return grupo

        # Top 2 oficinas con menos tickets
        top_bajas = grupo.iloc[:2].copy()
        tercera_ticket = grupo.iloc[2]['Ticket']
        tercera_oficina = grupo.iloc[2]['Oficina']

        # Calcular diferencia y guardar el nombre de la oficina a alcanzar
        top_bajas['Diferencia_para_Alcanzar'] = tercera_ticket - top_bajas['Ticket']
        top_bajas['Oficina_a_Alcanzar'] = tercera_oficina

        # Las demás no se modifican
        otros = grupo.iloc[2:].copy()
        otros['Diferencia_para_Alcanzar'] = None
        otros['Oficina_a_Alcanzar'] = None

        return pd.concat([top_bajas, otros], ignore_index=True)

    # Paso 4: Aplicar por zona
    resultado = grouped.groupby("Zona", group_keys=False).apply(calcular_diferencia)
    st.subheader("📍 Oficinas que requieren atraer más agentes")
    # Filtrar sólo las filas donde se calculó la diferencia
    resultado_filtrado = resultado.dropna(subset=['Diferencia_para_Alcanzar'])
    st.dataframe(resultado_filtrado, use_container_width=True)

with tabs[1]:
    st.subheader("📈 Tendencia Diaria de Pólizas")
    diaria = df_filtered.groupby("Fecha de Inicio")["Ticket"].count().reset_index()
    fig_ticket = go.Figure(go.Scatter(
        x=diaria["Fecha de Inicio"],
        y=diaria["Ticket"],
        mode='lines+markers',
        line=dict(color='seagreen'),
        marker=dict(size=6),
        hovertemplate="Fecha: %{x}<br>Prima: %{y:,.2f}<extra></extra>"
    ))
    fig_ticket.update_layout(xaxis_title="Fecha", yaxis_title="Pólizas")
    st.plotly_chart(fig_ticket, use_container_width=True)


    st.subheader("📊 Comparación Mensual")
    mensual = df_filtered.groupby("Mes")["Ticket"].count().reset_index()

    fig3 = go.Figure(go.Bar(
        x=mensual["Mes"],
        y=mensual["Ticket"],
        marker_color="brown",
        text=[f"{x:,.0f}" for x in mensual["Ticket"]],
        textposition="inside",  # 👈 centrado dentro de la barra
        textfont=dict(size=40, color="white")  # 👈 fuente más grande y blanca
    ))
    fig3.update_layout(xaxis_title="Mes", yaxis_title="Pólizas")
    st.plotly_chart(fig3, use_container_width=True)
    #####################################


    st.subheader("📈 Tendencia Diaria de Primas")
    diaria = df_filtered.groupby("Fecha de Inicio")["Prima"].sum().reset_index()

    fig2 = go.Figure(go.Scatter(
        x=diaria["Fecha de Inicio"],
        y=diaria["Prima"],
        mode='lines+markers',
        line=dict(color='seagreen'),
        marker=dict(size=6),
        hovertemplate="Fecha: %{x}<br>Prima: $%{y:,.2f}<extra></extra>"
    ))
    fig2.update_layout(xaxis_title="Fecha", yaxis_title="Prima Total")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📊 Comparación Mensual")
    mensual = df_filtered.groupby("Mes")["Prima"].sum().reset_index()

    fig3 = go.Figure(go.Bar(
        x=mensual["Mes"],
        y=mensual["Prima"],
        marker_color="brown",
        text=[f"${x:,.0f}" for x in mensual["Prima"]],
        textposition="inside",  # 👈 centrado dentro de la barra
        textfont=dict(size=20, color="white")  # 👈 fuente más grande y blanca
    ))
    fig3.update_layout(xaxis_title="Mes", yaxis_title="Prima Total")
    st.plotly_chart(fig3, use_container_width=True)

with tabs[2]:
    st.subheader("🏆 Top Agentes por Póliza")
    top = df_filtered.groupby("Agente").agg(
        Prima_Total=("Prima", "sum"),
        Pólizas=("Ticket", "count")
    ).nlargest(10, "Prima_Total").reset_index()

    top1 = top.sort_values(by=["Pólizas"],ascending=False)
    top2 = top.sort_values(by=["Prima_Total"],ascending=False)

    fig4 = go.Figure(go.Bar(
        x=top1["Agente"],
        y=top1["Pólizas"],
        marker_color='brown',
        text=top1["Pólizas"].apply(lambda x: f"{x:,.0f}"),
        textposition="auto",
        textfont=dict(size=30)
    ))
    fig4.update_layout(xaxis_title="Agente", yaxis_title="Pólizas")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("🏆 Top Agentes por Prima")
    fig4 = go.Figure(go.Bar(
        x=top2["Agente"],
        y=top2["Prima_Total"],
        marker_color='brown',
        text=top2["Prima_Total"].apply(lambda x: f"${x:,.0f}"),
        textposition="auto",
        textfont=dict(size=15)
    ))
    fig4.update_layout(xaxis_title="Agente", yaxis_title="Prima Total")
    st.plotly_chart(fig4, use_container_width=True)

with tabs[3]:

    df_tend_oficina = df.groupby(["Oficina","Mes"]).agg({"Ticket":"count"}).reset_index()
    # Primero, asegúrate de que la columna 'Mes' sea de tipo datetime para ordenar correctamente
    df_tend_oficina['Mes'] = pd.to_datetime(df_tend_oficina['Mes'])

    # Ordenamos por Oficina y Mes
    df_tend_oficina = df_tend_oficina.sort_values(by=['Oficina', 'Mes'])

    # Calculamos la diferencia de tickets mes a mes por oficina
    df_tend_oficina['Desviacion_Tickets'] = df_tend_oficina.groupby('Oficina')['Ticket'].diff()

    df_tend_oficina = df_tend_oficina.groupby("Oficina").agg({"Desviacion_Tickets":["mean"]}).reset_index().sort_values(by=[('Desviacion_Tickets', 'mean')],ascending=False).reset_index(drop=True)
    #df_tend_oficina
    df_tend_oficina.columns = ["Oficina","Desviacion_Polizas"]
    df_tend_oficina["Desviacion_Polizas"] = round(df_tend_oficina["Desviacion_Polizas"],2)
    
    def polizas_tend(x):
        if x > 1:
            return "Positivo"
        elif x>0:
            return "Estancado"
        else:
            return "Negativo"

    df_tend_oficina["Tendencia"] = df_tend_oficina["Desviacion_Polizas"].map(lambda x: polizas_tend(x))
    st.subheader("🔍 Tendencias de oficinas")
    st.dataframe(df_tend_oficina, use_container_width=True)


    fig_extra = go.Figure()
    fig_extra = go.Figure(go.Bar(
        x=df_tend_oficina.sort_values("Desviacion_Polizas",ascending=False)["Desviacion_Polizas"],
        y=df_tend_oficina.sort_values("Desviacion_Polizas",ascending=False)["Oficina"],
        orientation='h',
        marker_color=df_tend_oficina["Tendencia"].map({
            "Positivo": "green", "Estancado": "orange", "Negativo": "red"
        }),
        text=df_tend_oficina["Desviacion_Polizas"].round(2),
        textposition="outside"
    ))
    fig_extra.update_layout(
        title="Desviación de Pólizas por Oficina",
        xaxis_title="Oficinas",
        yaxis_title="Tendencia",
        height=400
    )
    st.plotly_chart(fig_extra, use_container_width=True)


    st.subheader("🔍 Oficinas que requieren capacitación del Apetito")
    df_apetito_riesgo = df.groupby('Oficina')['Evento'].value_counts().unstack(fill_value=0).reset_index().reset_index(drop=True)
    df_apetito_riesgo["pct_capacitacion"] = df_apetito_riesgo["fuera de política"] / (df_apetito_riesgo["na"]+df_apetito_riesgo["fuera de política"] )
    df_apetito_riesgo = df_apetito_riesgo[df_apetito_riesgo["pct_capacitacion"]>= 0.25].sort_values(by=["pct_capacitacion"],ascending=False)
    df_apetito_riesgo["pct_capacitacion"] = round(df_apetito_riesgo["pct_capacitacion"]*100,2)
    st.dataframe(df_apetito_riesgo, use_container_width=True)





with tabs[4]:
    st.markdown("📆 Comparador de Períodos")

    col_a, col_b = st.columns(2)

    with col_a:
        st.write("### 📅 Período A")
        fecha_a = st.date_input("Rango A", [df['Fecha de Inicio'].min(), df['Fecha de Inicio'].max()], key='a')
        fecha_a = [pd.to_datetime(fecha_a[0]), pd.to_datetime(fecha_a[1])]

    with col_b:
        st.write("### 📅 Período B")
        fecha_b = st.date_input("Rango B", [df['Fecha de Inicio'].min(), df['Fecha de Inicio'].max()], key='b')
        fecha_b = [pd.to_datetime(fecha_b[0]), pd.to_datetime(fecha_b[1])]

    # Filtrado de datos
    df_a = df[df['Fecha de Inicio'].between(fecha_a[0], fecha_a[1])]
    df_b = df[df['Fecha de Inicio'].between(fecha_b[0], fecha_b[1])]

    # Cálculo de métricas
    def resumen_periodo(df_x):
        return {
            "Pólizas": df_x.shape[0],
            "Prima Total": df_x['Prima'].sum(),
            "Prima Promedio": df_x[df_x["Prima"] > 0]["Prima"].mean()
        }

    res_a = resumen_periodo(df_a)
    res_b = resumen_periodo(df_b)

    # Mostrar métricas
    st.markdown("### 🔎 Comparación de Métricas")
    col1, col2, col3 = st.columns(3)

    def format_diff(a, b):
        diff = b - a
        pct = (diff / a * 100) if a != 0 else 0
        return f"{diff:,.0f} ({pct:+.1f}%)"

    with col1:
        st.metric("Pólizas", res_a["Pólizas"], format_diff(res_a["Pólizas"], res_b["Pólizas"]))
    with col2:
        st.metric("Prima Total", f"${res_a['Prima Total']:,.2f}", format_diff(res_a["Prima Total"], res_b["Prima Total"]))
    with col3:
        st.metric("Prima Promedio", f"${res_a['Prima Promedio']:,.2f}", format_diff(res_a["Prima Promedio"], res_b["Prima Promedio"]))


# 📥 Descargar datos filtrados
st.subheader("📂 Exportar Datos Filtrados")

def convertir_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Datos Filtrados', index=False)
    output.seek(0)
    return output

btn = st.download_button(
    label="📥 Descargar como Excel",
    data=convertir_excel(df_filtered),
    file_name="datos_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("Dashboard CORE: Cotización y Reporte ❤️.")
