"""Cena animada com material rodante ilustrado em volume e proporções reais."""
import base64
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import html


@st.cache_data(show_spinner=False)
def _sprites():
    root = Path(__file__).resolve().parents[1] / 'assets'
    return {name: base64.b64encode((root / ('train-' + name + '-v1.webp')).read_bytes()).decode('ascii')
            for name in ('passenger', 'cargo', 'vlt')}


def realistic_header():
    with st.container(key='hero'):
        st.markdown('<span class="hero-eyebrow">PLANEJE · CONFIGURE · ESTIME</span>', unsafe_allow_html=True)
        st.title('Parametric Rails')
        st.caption('Engenharia de custos ferroviários, com clareza do primeiro parâmetro ao orçamento.')
        scene = '''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><style>
        body{margin:0;background:#fff;font-family:system-ui,sans-serif}
        .scene{position:relative;height:242px;overflow:hidden;border-radius:12px;background:linear-gradient(#e6eef0 0%,#f3f5ef 37%,#dde4da 38%,#e4e7df 100%)}
        .horizon{position:absolute;inset:35px 0 auto;height:52px;opacity:.22;background:linear-gradient(90deg,transparent 5%,#a7b6b4 5% 9%,transparent 9% 11%,#a7b6b4 11% 18%,transparent 18% 63%,#a7b6b4 63% 65%,transparent 65% 71%,#a7b6b4 71% 79%,transparent 79%);mask-image:linear-gradient(transparent,#000)}
        .rail{position:absolute;left:0;right:0;height:9px;border-top:2px solid #8d9996;border-bottom:1px solid #a6afaa;background:repeating-linear-gradient(90deg,#bec5ba 0 3px,#d9dcd2 3px 12px)}
        .r1{top:111px;opacity:.65}.r2{top:169px;opacity:.8}.r3{top:225px}
        .train{position:absolute;left:0;width:clamp(260px,46vw,510px);animation:travel 76s linear infinite;will-change:transform}
        .train img{display:block;width:100%;height:auto;max-height:76px;object-fit:contain;object-position:bottom}
        .passenger{bottom:128px;animation-duration:72s;animation-delay:-27s}
        .cargo{bottom:70px;width:clamp(290px,50vw,550px);animation-duration:96s;animation-delay:-47s}
        .vlt{bottom:14px;width:clamp(230px,38vw,420px);animation-duration:64s;animation-delay:-38s}
        @keyframes travel{from{transform:translateX(-110%)}to{transform:translateX(105vw)}}
        .control{position:absolute;z-index:2;right:10px;top:9px;display:flex;align-items:center;gap:6px;padding:6px 9px;border-radius:8px;background:#ffffffed;color:#35534f;font-size:11px;cursor:pointer;border:1px solid #dce6e1}
        #pause{accent-color:#28776f;margin:0}.scene:has(#pause:checked) .train{animation-play-state:paused}
        @media(prefers-reduced-motion:reduce){.train{animation:none;transform:translateX(8vw)}.cargo{transform:translateX(40vw)}.vlt{transform:translateX(24vw)}}
        </style></head><body><div class="scene">
        <label class="control"><input id="pause" type="checkbox">Pausar animação</label>
        <div class="horizon"></div><div class="rail r1"></div><div class="rail r2"></div><div class="rail r3"></div>
        <div class="train passenger"><img src="data:image/webp;base64,__PASSENGER__" alt="Trem de passageiros em movimento, com carroceria prata e vermelha."></div>
        <div class="train cargo"><img src="data:image/webp;base64,__CARGO__" alt="Locomotiva de carga com vagões em movimento."></div>
        <div class="train vlt"><img src="data:image/webp;base64,__VLT__" alt="VLT articulado em movimento."></div>
        </div></body></html>'''
        for name, image in _sprites().items():
            scene = scene.replace('__' + name.upper() + '__', image)
        html(scene, height=254, scrolling=False)
