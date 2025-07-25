
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# URL da planilha pública (CSV)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4rNqe1-YHIaKxLgyEbhN0tNytQixaNJnVfcyI0PN6ajT0KXzIGlh_dBrWFs6R9QqCEJ_UTGp3KOmL/pub?gid=317759421&single=true&output=csv"

# Configuração da página
st.set_page_config(page_title="Mapa VigiSolo", layout="wide")
st.title("🗺️ Mapa Áreas Programa VigiSolo ")

# Função para carregar os dados
def carregar_dados():
    df = pd.read_csv(sheet_url)
    df[['lat', 'lon']] = df['COORDENADAS'].str.split(', ', expand=True).astype(float)
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce', dayfirst=True)
    df['ANO'] = df['DATA'].dt.year
    df['MES'] = df['DATA'].dt.month
    return df

df = carregar_dados()

# Filtros
col1, col2 = st.columns(2)

anos = sorted(df['ANO'].dropna().unique())
meses_numeros = sorted(df['MES'].dropna().unique())

# Meses abreviados em português
meses_nome = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

ano_selecionado = col1.selectbox("Filtrar por ano:", options=["Todos"] + list(anos))
mes_selecionado_nome = col2.selectbox("Filtrar por mês:", options=["Todos"] + [meses_nome[m] for m in meses_numeros])

# Aplicar filtros
df_filtrado = df.copy()

if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ANO'] == ano_selecionado]

if mes_selecionado_nome != "Todos":
    mes_num = [num for num, nome in meses_nome.items() if nome == mes_selecionado_nome][0]
    df_filtrado = df_filtrado[df_filtrado['MES'] == mes_num]

# Criar mapa
if not df_filtrado.empty:
    map_center = df_filtrado[['lat', 'lon']].mean().tolist()
    m = folium.Map(location=map_center, zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df_filtrado.iterrows():
        popup_text = (
            f"<strong>Área:</strong> {row['DENOMINAÇÃO DA ÁREA']}<br>"
            f"<strong>Bairro:</strong> {row['BAIRRO']}<br>"
            f"<strong>Contaminantes:</strong> {row['CONTAMINANTES']}<br>"
            f"<strong>População Exposta:</strong> {row['POPULAÇÃO EXPOSTA']}<br>"
            f"<strong>Data:</strong> {row['DATA'].date()}<br>"
            f"<strong>Coordenadas:</strong> {row['lat']}, {row['lon']}"
        )
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color="red", icon="exclamation-sign"),
        ).add_to(marker_cluster)

    st_folium(m, width=1000, height=600)
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
