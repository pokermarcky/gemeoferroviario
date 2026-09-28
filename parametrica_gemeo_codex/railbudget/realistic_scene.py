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
        .scene{position:relative;height:226px;overflow:hidden;border-radius:14px;background:linear-gradient(#e7eff0 0%,#f4f6f1 37%,#dfe6dc 38%,#e8ebe3 100%)}
        .horizon{position:absolute;inset:35px 0 auto;height:52px;opacity:.22;background:linear-gradient(90deg,transparent 5%,#a7b6b4 5% 9%,transparent 9% 11%,#a7b6b4 11% 18%,transparent 18% 63%,#a7b6b4 63% 65%,transparent 65% 71%,#a7b6b4 71% 79%,transparent 79%);mask-image:linear-gradient(transparent,#000)}
        .rail{position:absolute;left:0;right:0;height:9px;border-top:2px solid #8d9996;border-bottom:1px solid #a6afaa;background:repeating-linear-gradient(90deg,#bec5ba 0 3px,#d9dcd2 3px 12px);animation:railFlow 1.3s linear infinite}
        .r1{top:99px;opacity:.65}.r2{top:155px;opacity:.8}.r3{top:211px}
        .train{position:absolute;width:clamp(260px,46vw,510px);animation:glide 5.2s ease-in-out infinite alternate;will-change:transform;filter:drop-shadow(0 5px 5px #50645e28)}
        .train img{display:block;width:100%;height:auto;max-height:76px;object-fit:contain;object-position:bottom}
        .passenger{left:16%;bottom:124px;animation-duration:5.8s}
        .cargo{left:29%;bottom:68px;width:clamp(290px,50vw,550px);animation-duration:7.2s;animation-delay:-2.4s}
        .vlt{left:52%;bottom:12px;width:clamp(230px,38vw,420px);animation-duration:4.9s;animation-delay:-1.6s}
        @keyframes glide{from{transform:translateX(-13px)}to{transform:translateX(13px)}}
        @keyframes railFlow{to{background-position:12px 0}}
        .control{position:absolute;z-index:2;right:10px;top:9px;display:flex;align-items:center;gap:6px;padding:7px 10px;border-radius:999px;background:#fffffff2;color:#35534f;font-size:11px;font-weight:650;cursor:pointer;border:1px solid #d7e3df;box-shadow:0 4px 12px #35534f14}
        #pause{accent-color:#28776f;margin:0}.scene:has(#pause:checked) .train,.scene:has(#pause:checked) .rail{animation-play-state:paused}
        @media(prefers-reduced-motion:reduce){.train,.rail{animation:none}}
        </style></head><body><div class="scene">
        <label class="control"><input id="pause" type="checkbox">Pausar animação</label>
        <div class="horizon"></div><div class="rail r1"></div><div class="rail r2"></div><div class="rail r3"></div>
        <div class="train passenger"><img src="data:image/webp;base64,__PASSENGER__" alt="Trem de passageiros em movimento, com carroceria prata e vermelha."></div>
        <div class="train cargo"><img src="data:image/webp;base64,__CARGO__" alt="Locomotiva de carga com vagões em movimento."></div>
        <div class="train vlt"><img src="data:image/webp;base64,__VLT__" alt="VLT articulado em movimento."></div>
        </div></body></html>'''
        for name, image in _sprites().items():
            scene = scene.replace('__' + name.upper() + '__', image)
        html(scene, height=238, scrolling=False)
