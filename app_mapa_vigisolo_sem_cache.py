import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium

# Estilo visual personalizado
st.markdown("""
    <style>
    .stSelectbox > div, .stButton > button {
        font-size: 15px;
        padding: 6px 10px;
        border-radius: 6px;
    }
    iframe {
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
    }
    .legend-box {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 0 5px rgba(0,0,0,0.1);
    }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Configuração da página
st.set_page_config(page_title="Mapa VigiSolo", layout="wide")
st.title("🗺️ Mapa Áreas Programa VigiSolo")

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4rNqe1-YHIaKxLgyEbhN0NytQixaNJnVfcyI0PN6ajT0KXzIGlh_dBrWFs6R9QqCEJ_UTGp3KOmL/pub?gid=317759421&single=true&output=csv"
        df = pd.read_csv(url)
        df[['lat', 'lon']] = df['COORDENADAS'].str.split(', ', expand=True).astype(float)
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce', dayfirst=True)
        df['ANO'] = df['DATA'].dt.year
        df['MES'] = df['DATA'].dt.month
        return df
    except Exception:
        st.error("Erro ao carregar os dados da planilha. Verifique se o link está publicado como CSV.")
        st.stop()

df = carregar_dados()

# Filtros
st.markdown("### 🎛️ Filtros")
anos = sorted(df['ANO'].dropna().unique())
meses_numeros = sorted(df['MES'].dropna().unique())
meses_nome = {i: nome for i, nome in enumerate([
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
], start=1)}
bairros = sorted(df['BAIRRO'].dropna().unique())
areas = sorted(df['DENOMINAÇÃO DA ÁREA'].dropna().unique())
riscos = ["Todos", "🔴 Alto", "🟠 Médio", "🟢 Baixo", "⚪ Não informado"]

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1.2, 1.2, 1])
    with col1:
        ano_selecionado = st.selectbox("📅 Ano", ["Todos"] + list(anos))
    with col2:
        mes_selecionado_nome = st.selectbox("🗓️ Mês", ["Todos"] + [meses_nome[m] for m in meses_numeros])
    with col3:
        bairro_selecionado = st.selectbox("📍 Bairro", ["Todos"] + bairros)
    with col4:
        area_selecionada = st.selectbox("📌 Área", ["Todos"] + areas)
    with col5:
        risco_selecionado = st.selectbox("⚠️ Risco", riscos)

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
    df_filtrado = df_filtrado[df_filtrado['RISCO'].str.lower().str.fullmatch(risco_texto, na=False)]

# Criar mapa
if not df_filtrado.empty:
    map_center = df_filtrado[['lat', 'lon']].mean().tolist()
    m = folium.Map(location=map_center, zoom_start=12, tiles='CartoDB positron')
    MiniMap().add_to(m)
    marker_cluster = MarkerCluster().add_to(m)

    lista_areas_legenda = []

    for _, row in df_filtrado.iterrows():
        imagem_html = f'<br><img src="{row.get("URL_FOTO", "")}" width="250">' if pd.notna(row.get("URL_FOTO")) else ""
        risco = str(row.get('RISCO', 'Não informado')).strip().lower()
        if risco == "alto":
            cor_icon = "red"; emoji_risco = "🔴"; icon_name = "exclamation"
        elif risco in ["médio", "medio"]:
            cor_icon = "orange"; emoji_risco = "🟠"; icon_name = "adjust"
        elif risco == "baixo":
            cor_icon = "green"; emoji_risco = "🟢"; icon_name = "check"
        else:
            cor_icon = "gray"; emoji_risco = "⚪"; icon_name = "question"

        area_nome = row.get('DENOMINAÇÃO DA ÁREA', 'Área não informada')
        lista_areas_legenda.append(area_nome)

        popup_text = (
            f"<strong>Área:</strong> {area_nome}<br>"
            f"<strong>Bairro:</strong> {row.get('BAIRRO', '')}<br>"
            f"<strong>Contaminantes:</strong> {row.get('CONTAMINANTES', '')}<br>"
            f"<strong>População Exposta:</strong> {row.get('POPULAÇÃO EXPOSTA', '')}<br>"
            f"<strong>Data:</strong> {row.get('DATA').strftime('%d/%m/%Y') if pd.notna(row.get('DATA')) else 'Data não informada'}<br>"
            f"<strong>Coordenadas:</strong> {row.get('lat')}, {row.get('lon')}<br>"
            f"<strong>Risco:</strong> {emoji_risco} {risco.capitalize()}"
            f"{imagem_html}"
        )

        iframe = folium.IFrame(html=popup_text, width=300, height=320)
        popup = folium.Popup(iframe, max_width=300)

        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=popup,
            icon=folium.Icon(color=cor_icon, icon=icon_name, prefix='fa', spin=True),
        ).add_to(marker_cluster)

    # Layout: mapa e legenda lateral
    col_mapa, col_legenda = st.columns([4, 1])
    with col_mapa:
        st.markdown("### 🗺️ Mapa Gerado")
        st.divider()
        st_folium(m, width=950, height=600, returned_objects=[])

    with col_legenda:
        legenda_expande = False if risco_selecionado == "Todos" else True
        with st.expander("📋 Áreas Filtradas", expanded=legenda_expande):
            st.markdown('<div class="legend-box">', unsafe_allow_html=True)
            if lista_areas_legenda:
                for area in sorted(set(lista_areas_legenda)):
                    st.markdown(f"✅ {area}")
            else:
                st.info("Nenhuma área encontrada para o risco selecionado.")
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")

# Rodapé
st.markdown(
    "<div style='margin-top: -10px; text-align: center; font-size: 14px; color: gray;'>"
    "Desenvolvido por Walter Alves usando Streamlit."
    "</div>",
    unsafe_allow_html=True
)
