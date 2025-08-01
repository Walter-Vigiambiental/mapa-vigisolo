import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from branca.element import Element

# URL da planilha pública (CSV)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4rNqe1-YHIaKxLgyEbhN0tNytQixaNJnVfcyI0PN6ajT0KXzIGlh_dBrWFs6R9QqCEJ_UTGp3KOmL/pub?gid=317759421&single=true&output=csv"

# Configuração da página
st.set_page_config(page_title="Mapa VigiSolo", layout="wide")
st.title("🗺️ Mapa Áreas Programa VigiSolo")

if "mostrar_mapa" not in st.session_state:
    st.session_state.mostrar_mapa = False

def carregar_dados():
    df = pd.read_csv(sheet_url)
    df[['lat', 'lon']] = df['COORDENADAS'].str.split(', ', expand=True).astype(float)
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce', dayfirst=True)
    df['ANO'] = df['DATA'].dt.year
    df['MES'] = df['DATA'].dt.month
    return df

df = carregar_dados()

# Filtros
st.markdown("### Filtros")
col1, col2, col3, col4 = st.columns([1, 1, 1.2, 1.2])

anos = sorted(df['ANO'].dropna().unique())
meses_numeros = sorted(df['MES'].dropna().unique())
meses_nome = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
bairros = sorted(df['BAIRRO'].dropna().unique())
contaminantes = sorted(df['CONTAMINANTES'].dropna().unique())

with col1:
    ano_selecionado = st.selectbox("Ano", options=["Todos"] + list(anos))
with col2:
    mes_selecionado_nome = st.selectbox("Mês", options=["Todos"] + [meses_nome[m] for m in meses_numeros])
with col3:
    bairro_selecionado = st.selectbox("Bairro", options=["Todos"] + bairros)
with col4:
    contaminante_selecionado = st.selectbox("Contaminante", options=["Todos"] + contaminantes)

if st.button("Gerar Mapa"):
    st.session_state.mostrar_mapa = True

# Aplicar filtros
df_filtrado = df.copy()
if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ANO'] == ano_selecionado]
if mes_selecionado_nome != "Todos":
    mes_num = [num for num, nome in meses_nome.items() if nome == mes_selecionado_nome][0]
    df_filtrado = df_filtrado[df_filtrado['MES'] == mes_num]
if bairro_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['BAIRRO'] == bairro_selecionado]
if contaminante_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['CONTAMINANTES'] == contaminante_selecionado]

if st.session_state.mostrar_mapa:
    if not df_filtrado.empty:
        map_center = df_filtrado[['lat', 'lon']].mean().tolist()
        m = folium.Map(location=map_center, zoom_start=12)
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in df_filtrado.iterrows():
            imagem_html = f'<br><img src="{row["URL_FOTO"]}" width="250">' if pd.notna(row.get("URL_FOTO")) else ""

            popup_text = (
                f"<strong>Área:</strong> {row['DENOMINAÇÃO DA ÁREA']}<br>"
                f"<strong>Bairro:</strong> {row['BAIRRO']}<br>"
                f"<strong>Contaminantes:</strong> {row['CONTAMINANTES']}<br>"
                f"<strong>População Exposta:</strong> {row['POPULAÇÃO EXPOSTA']}<br>"
                f"<strong>Data:</strong> {row['DATA'].date()}<br>"
                f"<strong>Coordenadas:</strong> {row['lat']}, {row['lon']}"
                f"{imagem_html}"
            )

            risco = str(row['POPULAÇÃO EXPOSTA']).lower()
            if "alta" in risco:
                cor_icon = "darkred"
            elif "média" in risco or "media" in risco:
                cor_icon = "orange"
            elif "baixa" in risco:
                cor_icon = "green"
            else:
                cor_icon = "gray"

            iframe = folium.IFrame(html=popup_text, width=300, height=300)
            popup = folium.Popup(iframe, max_width=300)

            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=popup,
                icon=folium.Icon(color=cor_icon, icon="circle", prefix="fa"),
            ).add_to(marker_cluster)

        # Legenda fixa no canto inferior direito DENTRO do mapa
        legenda_html = """
        <div style="
            position: absolute;
            bottom: 30px;
            right: 30px;
            z-index: 9999;
            background-color: white;
            padding: 10px;
            border: 2px solid gray;
            border-radius: 8px;
            font-size: 14px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        ">
            <strong>Legenda - Risco</strong><br>
            <svg height="10" width="10"><circle cx="5" cy="5" r="5" fill="darkred"/></svg> Alta<br>
            <svg height="10" width="10"><circle cx="5" cy="5" r="5" fill="orange"/></svg> Média<br>
            <svg height="10" width="10"><circle cx="5" cy="5" r="5" fill="green"/></svg> Baixa<br>
            <svg height="10" width="10"><circle cx="5" cy="5" r="5" fill="gray"/></svg> Não informado
        </div>
        """
        m.get_root().html.add_child(Element(legenda_html))

        st_folium(m, width=1000, height=600, returned_objects=[])
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

st.markdown("---")
st.caption("Desenvolvido por Walter Alves usando Streamlit.")

