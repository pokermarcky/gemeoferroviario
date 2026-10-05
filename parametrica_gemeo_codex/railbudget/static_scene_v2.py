"""Capa estática v2; módulo versionado para evitar cache do hot reload do Streamlit."""
import base64
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html


@st.cache_data(show_spinner=False)
def _static_sprites_v3():
    root=Path(__file__).resolve().parents[1]/'assets'
    files={'passenger':'train-passenger-bidirectional-v2.webp',
           'cargo':'train-cargo-v1.webp','vlt':'train-vlt-v1.webp'}
    return {name:base64.b64encode((root/filename).read_bytes()).decode('ascii')
            for name,filename in files.items()}


def static_header_v2():
    with st.container(key='hero'):
        st.markdown('<span class="hero-eyebrow">PLANEJE · CONFIGURE · ESTIME</span>',unsafe_allow_html=True)
        st.title('Parametric Rails')
        st.caption('Engenharia de custos ferroviários, com clareza do primeiro parâmetro ao orçamento.')
        scene='''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><style>
        body{margin:0;background:#fff;font-family:system-ui,sans-serif}.scene{position:relative;height:226px;overflow:hidden;border-radius:14px;background:linear-gradient(#eaf1f1 0%,#f6f7f3 42%,#edf1eb 100%)}
        .horizon{position:absolute;inset:30px 0 auto;height:58px;opacity:.18;background:linear-gradient(90deg,transparent 5%,#9cadaa 5% 9%,transparent 9% 12%,#9cadaa 12% 19%,transparent 19% 62%,#9cadaa 62% 65%,transparent 65% 72%,#9cadaa 72% 80%,transparent 80%);mask-image:linear-gradient(transparent,#000)}
        .track{position:absolute;left:0;right:0;box-sizing:border-box}.slab{top:98px;height:13px;border-top:2px solid #778784;border-bottom:3px solid #c3cbc7;background:linear-gradient(#d9dfdc,#eef1ef)}.slab:after{content:"";position:absolute;inset:5px 0 auto;height:1px;background:#8e9a97}
        .ballast{top:151px;height:20px;border-top:3px solid #687875;background-color:#b9bfbb;background-image:radial-gradient(#737f7c 1px,transparent 1.5px),radial-gradient(#89928f 1px,transparent 1.5px);background-position:0 0,5px 5px;background-size:10px 10px;clip-path:polygon(1% 0,99% 0,100% 100%,0 100%)}.ballast:after{content:"";position:absolute;inset:5px 0 auto;height:5px;background:repeating-linear-gradient(90deg,#8b9390 0 4px,transparent 4px 15px);border-top:1px solid #566663}
        .urban{top:207px;height:19px;background:linear-gradient(#8fae8b 0 45%,#c9d0c7 45% 100%);border-top:2px solid #70847b}.urban:after{content:"";position:absolute;inset:5px 0 auto;height:5px;border-top:2px solid #60706d;border-bottom:2px solid #60706d}.catenary{position:absolute;left:0;right:0;top:55px;height:43px;border-top:1px solid #899995;background:repeating-linear-gradient(90deg,transparent 0 145px,#91a09d 145px 148px,transparent 148px 290px)}
        .train{position:absolute;filter:drop-shadow(0 4px 4px #50645e24)}.train img{display:block;width:100%;height:72px;object-fit:contain;object-position:center bottom}.passenger{left:0;bottom:124px;width:clamp(390px,58vw,650px)}.passenger img{height:88px;object-position:left bottom}.cargo{left:50%;bottom:68px;width:clamp(290px,50vw,550px);transform:translateX(-50%)}.vlt{right:0;bottom:12px;width:clamp(230px,38vw,420px)}.vlt img{object-position:right bottom}
        </style></head><body><div class="scene"><div class="horizon"></div><div class="catenary"></div><div class="track slab"></div><div class="track ballast"></div><div class="track urban"></div>
        <div class="train passenger"><img src="data:image/webp;base64,__PASSENGER__" alt="Trem bidirecional de passageiros em via eletrificada sobre laje."></div><div class="train cargo"><img src="data:image/webp;base64,__CARGO__" alt="Locomotiva e vagões em via pesada sobre lastro."></div><div class="train vlt"><img src="data:image/webp;base64,__VLT__" alt="VLT articulado em via urbana integrada."></div></div></body></html>'''
        for name,image in _static_sprites_v3().items():
            scene=scene.replace('__'+name.upper()+'__',image)
        html(scene,height=238,scrolling=False)
