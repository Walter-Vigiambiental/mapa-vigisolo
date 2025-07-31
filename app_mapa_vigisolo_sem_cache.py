import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster

# Configurações da página
st.set_page_config(page_title="Mapa Interativo", layout="centered", initial_sidebar_state="collapsed")

# Título com fonte adaptativa
st.markdown("<h2 style='text-align: center;'>Mapa Interativo - Versão Mobile 🌍</h2>", unsafe_allow_html=True)

# Painel recolhível de filtros
with st.expander("🔍 Filtros e Opções"):
    categoria = st.selectbox("Categoria", ["Todos", "Locais", "Eventos", "Alertas"])
    mostrar_clust = st.checkbox("Agrupar marcadores", value=True)

# Dados fictícios (poderia vir de um DataFrame)
dados_marcadores = [
    {"nome": "Ponto A", "lat": -16.728, "lon": -43.872, "cat": "Locais"},
    {"nome": "Evento B", "lat": -16.730, "lon": -43.875, "cat": "Eventos"},
    {"nome": "Alerta C", "lat": -16.732, "lon": -43.878, "cat": "Alertas"},
]

# Filtragem
if categoria != "Todos":
    dados_marcadores = [d for d in dados_marcadores if d["cat"] == categoria]

# Criação do mapa
m = folium.Map(location=[-16.730, -43.874], zoom_start=15, control_scale=True)

# Adição de marcadores
if mostrar_clust:
    cluster = MarkerCluster()
    for dado in dados_marcadores:
        popup = folium.Popup(f"<b>{dado['nome']}</b> - {dado['cat']}", max_width=250)
        marker = folium.Marker(location=[dado["lat"], dado["lon"]], popup=popup)
        cluster.add_child(marker)
    m.add_child(cluster)
else:
    for dado in dados_marcadores:
        popup = folium.Popup(f"<b>{dado['nome']}</b> - {dado['cat']}", max_width=250)
        folium.Marker(location=[dado["lat"], dado["lon"]], popup=popup).add_to(m)

# Renderização passiva do mapa
st_folium(m, width="100%", height=500)

# Rodapé amigável
st.markdown("<p style='text-align:center; font-size: 14px;'>Desenvolvido por Walter Alves para o mobile</p>", unsafe_allow_html=True)
