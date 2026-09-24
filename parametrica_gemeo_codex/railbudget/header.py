"""Cabeçalho técnico com ilustração vetorial leve e acessível."""
import streamlit as st

TRAIN_HTML = '''
<svg viewBox="0 0 460 150" role="img" aria-label="Diagrama estilizado de um trem sobre trilhos">
<defs>
 <linearGradient id="card" x2="1" y2="1"><stop stop-color="#163e53"/><stop offset="1" stop-color="#0e2b40"/></linearGradient>
 <linearGradient id="wagon" x2="0" y2="1"><stop stop-color="#dbe8eb"/><stop offset="1" stop-color="#91aeb9"/></linearGradient>
</defs>
<rect width="460" height="150" rx="18" fill="url(#card)"/>
<g fill="none" stroke="#42677a" stroke-width="1" opacity=".48"><path d="M22 27H438M22 50H438M22 73H438M22 96H438M22 119H438"/><path d="M45 15V137M120 15V137M195 15V137M270 15V137M345 15V137M420 15V137"/></g>
<g fill="none" stroke="#7db4bb" stroke-width="2" opacity=".7"><path d="M20 111H440M20 132H440"/></g>
<g class="ties" stroke="#63818d" stroke-width="4"><path d="M0 109l18 27M36 109l18 27M72 109l18 27M108 109l18 27M144 109l18 27M180 109l18 27M216 109l18 27M252 109l18 27M288 109l18 27M324 109l18 27M360 109l18 27M396 109l18 27M432 109l18 27"/></g>
<g class="train">
 <path d="M83 68h220q20 0 28 12l20 30H73V78q0-10 10-10z" fill="url(#wagon)" stroke="#8aabb6" stroke-width="2"/>
 <path d="M75 96h274v12H75z" fill="#16838a"/>
 <path d="M83 78h43v17H83zm52 0h45v17h-45zm54 0h45v17h-45zm54 0h45v17h-45z" fill="#173c51"/>
 <path d="M310 78h14l15 20h-29z" fill="#173c51"/>
 <circle cx="110" cy="111" r="7" fill="#122f40"/><circle cx="285" cy="111" r="7" fill="#122f40"/>
 <path d="M83 68h205" stroke="#f27858" stroke-width="3"/>
</g>
<circle cx="40" cy="34" r="4" fill="#f27858"/><circle cx="420" cy="34" r="4" fill="#63b9b8"/>
</svg>'''
TRAIN_CSS = '''
svg {display:block;width:100%;height:150px;overflow:hidden}
.train {animation:move 5s ease-in-out infinite;transform-origin:center}
@keyframes move {0%,100% {transform:translateX(-5px)} 50% {transform:translateX(6px)}}
@media (prefers-reduced-motion:reduce) {.train {animation:none}}
'''


def render_header(train_component):
    with st.container(key='hero'):
        title, illustration = st.columns([1.8, 1], vertical_alignment='center')
        with title:
            st.markdown('<span class="hero-eyebrow">ENGENHARIA DE CUSTOS · FERROVIAS</span>',unsafe_allow_html=True)
            st.title('Parametric Rails')
            st.markdown('Orçamentos paramétricos para decisões de infraestrutura ferroviária.')
        with illustration:
            train_component(key='parametric_rails_header',height=150)
