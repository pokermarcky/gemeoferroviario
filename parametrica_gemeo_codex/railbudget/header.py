"""Cabeçalho da aplicação com cena ferroviária das três modalidades."""
import streamlit as st


def render_header(hero_path):
    with st.container(key='hero'):
        st.markdown('<span class="hero-eyebrow">ENGENHARIA DE CUSTOS · FERROVIAS</span>',unsafe_allow_html=True)
        st.title('Parametric Rails')
        st.markdown('Orçamentos paramétricos para decisões de infraestrutura ferroviária.')
        st.image(str(hero_path),width='stretch')
