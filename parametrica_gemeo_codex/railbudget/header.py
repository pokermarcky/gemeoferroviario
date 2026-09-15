"""Cabeçalho com ilustração vetorial animada, sem dependências externas."""
import streamlit as st

TRAIN_HTML = '''
<svg viewBox="0 0 560 190" role="img" aria-label="Trem metropolitano vermelho e prata em movimento sobre via permanente">
<defs>
 <linearGradient id="body" x2="0" y2="1"><stop stop-color="#f2f5f8"/><stop offset=".5" stop-color="#c6ced5"/><stop offset="1" stop-color="#8796a3"/></linearGradient>
 <linearGradient id="sky" x2="1" y2="1"><stop stop-color="#eaf2f6"/><stop offset="1" stop-color="#dce8ed"/></linearGradient>
 <pattern id="ties" width="32" height="28" patternUnits="userSpaceOnUse"><path d="M5 0h10l8 28H9z" fill="#89959b"/></pattern>
</defs>
<rect width="560" height="190" rx="20" fill="url(#sky)"/>
<g fill="#b5c9d2" opacity=".5"><path d="M0 120V76h40v44h15V48h26v72h18V69h44v51h30V40h30v80h25V62h48v58h25V78h33v42h34V48h38v72h29V62h40v58h30V81h55v39z"/></g>
<path d="M0 153H560V190H0z" fill="#b6bfc1"/>
<g class="track"><rect x="-32" y="154" width="624" height="28" fill="url(#ties)"/></g>
<path d="M0 159H560M0 179H560" stroke="#526574" stroke-width="4"/>
<path d="M0 156H560M0 176H560" stroke="#edf4f8" stroke-width="2"/>
<path d="M0 36H560" stroke="#647d8d" stroke-width="1.5"/>
<g class="train">
 <path d="M273 69l17-25 25 23M284 43h18" fill="none" stroke="#526574" stroke-width="3"/>
 <rect x="18" y="71" width="212" height="77" rx="9" fill="url(#body)" stroke="#7a8a96"/>
 <rect x="234" y="71" width="213" height="77" rx="9" fill="url(#body)" stroke="#7a8a96"/>
 <path d="M443 71h37q22 0 30 19l23 43q4 15-12 15h-78z" fill="#db243b"/>
 <path d="M477 80h6q12 0 19 17l10 20h-39z" fill="#163447"/>
 <path d="M481 84h5l15 28h-6z" fill="#688999"/>
 <path d="M20 118h425v14H20z" fill="#dc263d"/>
 <g fill="#233f50" stroke="#8394a1" stroke-width="2">
  <rect x="30" y="83" width="38" height="27" rx="3"/><rect x="113" y="83" width="43" height="27" rx="3"/><rect x="170" y="83" width="43" height="27" rx="3"/>
  <rect x="248" y="83" width="43" height="27" rx="3"/><rect x="336" y="83" width="43" height="27" rx="3"/><rect x="392" y="83" width="43" height="27" rx="3"/>
 </g>
 <g stroke="#738591" fill="#c8d1d8"><rect x="76" y="79" width="28" height="65" rx="2"/><rect x="299" y="79" width="28" height="65" rx="2"/></g>
 <g fill="#294858"><rect x="80" y="84" width="9" height="27"/><rect x="92" y="84" width="8" height="27"/><rect x="303" y="84" width="9" height="27"/><rect x="315" y="84" width="8" height="27"/></g>
 <path d="M90 80v63M313 80v63" stroke="#738591"/>
 <path d="M229 81v60" stroke="#334958" stroke-width="5"/>
 <g fill="#253b49" stroke="#8da0ac" stroke-width="3"><circle cx="54" cy="149" r="10"/><circle cx="192" cy="149" r="10"/><circle cx="267" cy="149" r="10"/><circle cx="457" cy="149" r="10"/></g>
 <path d="M32 140h180M248 140h195" stroke="#687d8b" stroke-width="5"/>
 <rect x="509" y="126" width="12" height="5" rx="2" fill="#fff1b2"/>
 <path d="M518 148h14" stroke="#334958" stroke-width="5"/>
</g>
</svg>
'''
TRAIN_CSS = '''
svg {display:block;width:100%;height:170px;overflow:hidden;}
.track {animation:rails .55s linear infinite;}
.train {animation:travel 4s ease-in-out infinite;}
@keyframes rails {to {transform:translateX(-32px);}}
@keyframes travel {0%,100% {transform:translateX(-8px);} 50% {transform:translate(5px,-1px);}}
@media (prefers-reduced-motion:reduce) {.track,.train {animation:none;}}
'''


def render_header(train_component):
    title, train = st.columns([1.4, 1], vertical_alignment='center')
    with title:
        st.title('Parametric Rails')
        st.caption('Orçamentação paramétrica ferroviária')
        st.caption('Via permanente e serviços complementares')
    with train:
        train_component(key='parametric_rails_header', height=170)
