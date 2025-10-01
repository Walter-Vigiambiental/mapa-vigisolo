import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# URL da planilha pública (CSV)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4rNqe1-YHIaKxLgyEbhN0tNytQixaNJnVfcyI0PN6ajT0KXzIGlh_dBrWFs6R9QqCEJ_UTGp3KOmL/pub?gid=317759421&single=true&output=csv"

# Configuração da página
st.set_page_config(page_title="Mapa VigiSolo", layout="wide")

st.title("🗺️ Mapa Áreas Programa VigiSolo")

@st.cache_data
def carregar_dados():
    df = pd.read_csv(sheet_url)
    df[['lat', 'lon']] = df['COORDENADAS'].str.split(', ', expand=True).astype(float)
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce', dayfirst=True)
    df['ANO'] = df['DATA'].dt.year
    df['MES'] = df['DATA'].dt.month
    return df

df = carregar_dados()

# Filtros
st.markdown("### 🎛️ Filtros")
anos = sorted(df['ANO'].dropna().unique())
meses_numeros = sorted(df['MES'].dropna().unique())
meses_nome = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
bairros = sorted(df['BAIRRO'].dropna().unique())
areas = sorted(df['DENOMINAÇÃO DA ÁREA'].dropna().unique())
riscos = ["Todos", "🔴 Alto", "🟠 Médio", "🟢 Baixo", "⚪ Não informado"]

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1.2, 1.2, 1])
    with col1:
        ano_selecionado = st.selectbox("📅 Ano", options=["Todos"] + list(anos))
    with col2:
        mes_selecionado_nome = st.selectbox("🗓️ Mês", options=["Todos"] + [meses_nome[m] for m in meses_numeros])
    with col3:
        bairro_selecionado = st.selectbox("📍 Bairro", options=["Todos"] + bairros)
    with col4:
        area_selecionada = st.selectbox("📌 Área", options=["Todos"] + areas)
    with col5:
        risco_selecionado = st.selectbox("⚠️ Risco", options=riscos)

# Aplicar filtros
df_filtrado = df.copy()
if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ANO'] == ano_selecionado]
if mes_selecionado_nome != "Todos":
    mes_num = [num for num, nome in meses_nome.items() if nome == mes_selecionado_nome][0]
    df_filtrado = df_filtrado[df_filtrado['MES'] == mes_num]
if bairro_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['BAIRRO'] == bairro_selecionado]
if area_selecionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado['DENOMINAÇÃO DA ÁREA'] == area_selecionada]
if risco_selecionado != "Todos":
    risco_texto = risco_selecionado.split(" ", 1)[1].strip().lower()
    df_filtrado = df_filtrado[df_filtrado['RISCO'].str.lower().str.contains(risco_texto, na=False)]

# Criar mapa
if not df_filtrado.empty:
    map_center = df_filtrado[['lat', 'lon']].mean().tolist()
    m = folium.Map(location=map_center, zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)

    lista_areas_legenda = []

    for _, row in df_filtrado.iterrows():
        imagem_html = f'<br><img src="{row.get("URL_FOTO", "")}" width="250">' if pd.notna(row.get("URL_FOTO")) else ""

        risco = str(row.get('RISCO', 'Não informado')).strip()
        risco_lower = risco.lower()
        if "alto" in risco_lower:
            cor_icon = "darkred"
            emoji_risco = "🔴"
        elif "médio" in risco_lower or "medio" in risco_lower:
            cor_icon = "orange"
            emoji_risco = "🟠"
        elif "baixo" in risco_lower:
            cor_icon = "green"
            emoji_risco = "🟢"
        else:
            cor_icon = "darkgray"
            emoji_risco = "⚪"

        area_nome = row.get('DENOMINAÇÃO DA ÁREA', 'Área não informada')
        lista_areas_legenda.append(area_nome)

        popup_text = (
            f"<strong>Área:</strong> {area_nome}<br>"
            f"<strong>Bairro:</strong> {row.get('BAIRRO', '')}<br>"
            f"<strong>Contaminantes:</strong> {row.get('CONTAMINANTES', '')}<br>"
            f"<strong>População Exposta:</strong> {row.get('POPULAÇÃO EXPOSTA', '')}<br>"
            f"<strong>Data:</strong> {row.get('DATA').strftime('%d/%m/%Y') if pd.notna(row.get('DATA')) else 'Data não informada'}<br>"
            f"<strong>Coordenadas:</strong> {row.get('lat')}, {row.get('lon')}<br>"
            f"<strong>Risco:</strong> {emoji_risco} {risco}"
            f"{imagem_html}"
        )

        iframe = folium.IFrame(html=popup_text, width=300, height=320)
        popup = folium.Popup(iframe, max_width=300)

        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=popup,
            icon=folium.Icon(color=cor_icon, icon="exclamation-sign"),
        ).add_to(marker_cluster)

    # Layout: mapa e legenda lateral
    col_mapa, col_legenda = st.columns([4, 1])
    with col_mapa:
        st.markdown("### 🗺️ Mapa Gerado")
        st_folium(m, width=950, height=600, returned_objects=[])

    with col_legenda:
        st.markdown("### 📋 Áreas Filtradas")
        if lista_areas_legenda:
            for area in sorted(set(lista_areas_legenda)):
                st.markdown(f"- {area}")
        else:
            st.info("Nenhuma área encontrada para o risco selecionado.")
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")

# Rodapé
st.markdown(
    "<div style='margin-top: -10px; text-align: center; font-size: 14px; color: gray;'>"
    "Desenvolvido por Walter Alves usando Streamlit."
    "</div>",
    unsafe_allow_html=True
)
