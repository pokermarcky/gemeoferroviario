"""Cabeçalho fotográfico com movimento de enquadramento discreto."""
import base64
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import html


@st.cache_data(show_spinner=False)
def _image_data():
    asset = Path(__file__).resolve().parents[1] / 'assets/hero-ferrovia-natural-v1.webp'
    return base64.b64encode(asset.read_bytes()).decode('ascii')


def realistic_header():
    with st.container(key='hero'):
        st.markdown('<span class="hero-eyebrow">PLANEJE · CONFIGURE · ESTIME</span>', unsafe_allow_html=True)
        st.title('Parametric Rails')
        st.caption('Engenharia de custos ferroviários, com clareza do primeiro parâmetro ao orçamento.')
        scene = '''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><style>
        body{margin:0;background:#fff;font-family:system-ui,sans-serif}
        .scene{position:relative;height:218px;overflow:hidden;border-radius:12px;background:#edf2ef}
        img{width:100%;height:100%;object-fit:cover;object-position:50% 58%;display:block;animation:camera 28s ease-in-out infinite alternate}
        @keyframes camera{from{transform:scale(1.015) translateX(-.35%)}to{transform:scale(1.045) translateX(.35%)}}
        .control{position:absolute;z-index:2;right:10px;top:10px;display:flex;align-items:center;gap:6px;padding:6px 9px;border-radius:8px;background:#ffffffed;color:#35534f;font-size:11px;cursor:pointer;border:1px solid #dce6e1}
        #pause{accent-color:#28776f;margin:0}.scene:has(#pause:checked) img{animation-play-state:paused}
        @media(prefers-reduced-motion:reduce){img{animation:none}}
        @media(max-width:600px){.scene{height:190px}img{object-fit:contain;background:#edf2ef}}
        </style></head><body><div class="scene">
        <label class="control"><input id="pause" type="checkbox">Pausar movimento</label>
        <img src="data:image/webp;base64,__IMAGE__" alt="Cena ferroviária realista em luz natural: locomotiva com vagões, trem de passageiros e VLT em vias paralelas.">
        </div></body></html>'''.replace('__IMAGE__', _image_data())
        html(scene, height=230, scrolling=False)
