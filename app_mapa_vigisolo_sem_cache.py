import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from folium import Element

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

# 🎛️ Filtros
st.markdown("### Filtros")
col1, col2, col3, col4 = st.columns([1, 1, 1.2, 1.2])

anos = sorted(df['ANO'].dropna().unique())
meses_nome = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
              7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
meses_numeros = sorted(df['MES'].dropna().unique())
bairros = sorted(df['BAIRRO'].dropna().unique())
contaminantes = sorted(df['CONTAMINANTES'].dropna().unique())

ano_selecionado = col1.selectbox("Ano", ["Todos"] + list(anos))
mes_selecionado_nome = col2.selectbox("Mês", ["Todos"] + [meses_nome[m] for m in meses_numeros])
bairro_selecionado = col3.selectbox("Bairro", ["Todos"] + bairros)
contaminante_selecionado = col4.selectbox("Contaminante", ["Todos"] + contaminantes)

if st.button("Gerar Mapa"):
    st.session_state.mostrar_mapa = True

# 🔍 Filtragem
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

# 🗺️ Mapa com popups e legenda
if st.session_state.mostrar_mapa:
    if not df_filtrado.empty:
        map_center = df_filtrado[['lat', 'lon']].mean().tolist()
        m = folium.Map(location=map_center, zoom_start=12, tiles="CartoDB positron")
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in df_filtrado.iterrows():
            imagem_html = f"<br><img src='{row['URL_FOTO']}' width='250'>" if pd.notna(row.get("URL_FOTO")) else ""

            risco = str(row.get('RISCO', '')).lower().strip()
            if "alto" in risco:
                cor_icon = "darkred"
            elif "médio" in risco or "medio" in risco:
                cor_icon = "orange"
            elif "baixo" in risco:
                cor_icon = "green"
            else:
                cor_icon = "gray"

            popup_html = f"""
            <div style='font-family:Arial, sans-serif; background-color:#fff; border-radius:8px;
                 padding:10px; box-shadow:0 2px 6px rgba(0,0,0,0.3);'>
                <h4 style='margin-top:0; color:#2F4F4F;'>{row['DENOMINAÇÃO DA ÁREA']}</h4>
                <p><strong>Bairro:</strong> {row['BAIRRO']}<br>
                   <strong>Contaminantes:</strong> {row['CONTAMINANTES']}<br>
                   <strong>População Exposta:</strong> {row['POPULAÇÃO EXPOSTA']}<br>
                   <strong>Data:</strong> {row['DATA'].date()}<br>
                   <strong>Coordenadas:</strong> {row['lat']}, {row['lon']}</p>
                {imagem_html}
            </div>
            """
            iframe = folium.IFrame(html=popup_html, width=300, height=320)
            popup = folium.Popup(iframe, max_width=320)

            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=popup,
                icon=folium.Icon(color=cor_icon, icon="exclamation-sign")
            ).add_to(marker_cluster)

        # 🔖 Legenda de risco
        legenda_html = """
        <div style='position: fixed; bottom: 40px; left: 40px; z-index:9999; background-color: white;
             border: 1px solid #ccc; padding: 10px; border-radius: 5px; font-size:14px;
             box-shadow:0 2px 6px rgba(0,0,0,0.3);'>
          <b>Legenda de Risco</b><br>
          <i class="fa fa-map-marker fa-lg" style="color:darkred"></i> Alto<br>
          <i class="fa fa-map-marker fa-lg" style="color:orange"></i> Médio<br>
          <i class="fa fa-map-marker fa-lg" style="color:green"></i> Baixo<br>
          <i class="fa fa-map-marker fa-lg" style="color:gray"></i> Indefinido
        </div>
        """
        m.get_root().html.add_child(Element(legenda_html))

        st_folium(m, width=1000, height=600, returned_objects=[])
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

st.markdown("---")
st.caption("Desenvolvido por Walter Alves usando Streamlit.")
