"""Tema visual e paisagem ferroviária leve, sem imagens externas."""
import streamlit as st
from streamlit.components.v1 import html

STYLE = '''<style>
:root {--ink:#243f48;--accent:#28776f;--line:#dde7e4}
[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#f8faf9 0,#f1f5f3 48rem);color:var(--ink)}
.block-container {max-width:1180px;padding:1.3rem 2rem 4rem}
[data-testid="stSidebar"] {background:#f3f7f5;border-right:1px solid #cadad5}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding:1rem .8rem 2rem}
[data-testid="stSidebar"] .st-key-user_profile_card {padding:1rem;border:1px solid #ffffff24;border-radius:16px;background:linear-gradient(145deg,#173c3e,#285b57);color:#fff;box-shadow:0 10px 28px #0b252528}
[data-testid="stSidebar"] .st-key-user_profile_card h3 {color:#fff!important;margin:.2rem 0 0;padding:0}
[data-testid="stSidebar"] .st-key-user_profile_card [data-testid="stCaptionContainer"] {color:#cde0da}
[data-testid="stSidebar"] h2 {margin-top:1.25rem;color:#173f3d;font-size:1.35rem!important}
.sidebar-eyebrow,.login-eyebrow {font-size:.67rem;letter-spacing:.17em;font-weight:800;color:#79b9ad}
.role-badge {display:inline-flex;padding:.24rem .58rem;border-radius:999px;font-size:.7rem;font-weight:800;letter-spacing:.04em;margin:.2rem 0 .65rem;background:#dceee9;color:#1f665c}
.role-root{background:#f5d993;color:#72520b}.role-test{background:#dce6f6;color:#315b8b}
[data-testid="stSidebar"] .st-key-new_budget_card {background:#fff!important;border:1px solid #ccddd8!important;box-shadow:0 8px 22px #173f3d12!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {background:#fff}
.st-key-login_shell {max-width:720px;margin:8vh auto 0;padding:2rem 2.1rem 1.6rem;border:1px solid #c9ddd7;border-radius:22px;background:#fff;box-shadow:0 22px 55px #173f3d1c}
.st-key-login_shell h1 {font-size:2.25rem;letter-spacing:-.045em;color:#173f3d;padding:.25rem 0}
.st-key-login_shell [data-testid="stTabs"] [role="tablist"] {margin-top:1.2rem}
.st-key-hero {background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.4rem 1.6rem .45rem;box-shadow:0 12px 34px #24463f10}
.st-key-hero h1 {font-size:2.2rem;letter-spacing:-.045em;line-height:1.15;color:var(--ink);padding:.15rem 0 .3rem}
.st-key-hero p {color:#647a7f;font-size:.95rem}
.hero-eyebrow {font-size:.67rem;letter-spacing:.17em;font-weight:750;color:#428077}
h3 {font-size:1.25rem!important;letter-spacing:-.025em;color:var(--ink)}
[data-testid="stCaptionContainer"] {color:#63777d}
[data-testid="stTabs"] [role="tablist"] {gap:.5rem;border:0!important;margin:.6rem 0 1rem;flex-wrap:wrap;height:auto!important}
[data-testid="stTabs"] [data-testid="stTab"] {height:auto!important;min-height:44px;padding:.65rem 1rem;background:#fff;border:1px solid var(--line);border-radius:12px;color:#496168;white-space:normal;transition:background .15s}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {background:#e5f1ed;border-color:#57988d;color:#18564d;box-shadow:inset 0 -2px #57988d}
[data-testid="stTabs"] [data-testid="stTab"]:hover {background:#edf5f2;border-color:#87b3aa}
[data-testid="stTabs"] .react-aria-SelectionIndicator {display:none}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;background:#fff;border-color:#dce7e3!important;box-shadow:0 4px 15px #294d4508}
[data-testid="stExpander"] {border-radius:12px;background:#fff;border-color:var(--line)}
[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);border-radius:14px;padding:.65rem .9rem}
[data-testid="stMetricValue"] {font-size:1.65rem!important;letter-spacing:-.025em;color:#244a4c}
[class*="st-key-result_header_"] {margin-top:1.4rem;padding:.9rem 1.1rem .65rem;border-left:5px solid #28776f;border-radius:4px 14px 14px 4px;background:linear-gradient(90deg,#e5f1ed,#f7faf8)}
[class*="st-key-result_header_"] h2 {margin:0;padding:0!important;font-size:1.7rem!important;letter-spacing:-.035em;color:#173f3d}
[class*="st-key-result_header_"] [data-testid="stCaptionContainer"] {font-size:.92rem;color:#526f6b}
[class*="st-key-result_kpis_"] [data-testid="stMetric"] {min-height:116px;padding:1rem 1.15rem;border:1px solid #a8c9c1!important;border-top:5px solid #28776f!important;background:linear-gradient(145deg,#fff,#edf6f2);box-shadow:0 8px 22px #1c514710}
[class*="st-key-result_kpis_"] [data-testid="stMetricLabel"] {font-size:.78rem;font-weight:800;letter-spacing:.055em;text-transform:uppercase;color:#476b66}
[class*="st-key-result_kpis_"] [data-testid="stMetricValue"] {font-size:1.82rem!important;font-weight:780;color:#153f3c}
.st-key-reference_heading {margin:.7rem 0 1rem;padding:1rem 1.2rem;border:1px solid #6da399;border-left:6px solid #28776f;border-radius:14px;background:linear-gradient(115deg,#dceee9,#f7faf8);box-shadow:0 8px 22px #24463f12}
.st-key-reference_heading h2 {margin:0;padding:0!important;color:#174b45;font-size:1.65rem!important}
.st-key-main_bdi_panel,.st-key-cargo_bdi_panel {border-color:#b8d0ca!important;background:#f8fbfa!important}
.st-key-main_service_toolbar,.st-key-cargo_service_toolbar {padding:.55rem .8rem!important;margin:.35rem 0 .8rem;border-color:#b9d2cc!important;background:linear-gradient(90deg,#f4f9f7,#fff)!important;box-shadow:none!important}
.st-key-main_service_toolbar p,.st-key-cargo_service_toolbar p {margin:0}
.st-key-main_service_toolbar [data-testid="stCaptionContainer"],.st-key-cargo_service_toolbar [data-testid="stCaptionContainer"] {font-size:.78rem}
.st-key-main_service_bulk [role="radiogroup"],.st-key-cargo_service_bulk [role="radiogroup"] {justify-content:flex-end}
.st-key-main_service_bulk button,.st-key-cargo_service_bulk button {min-height:34px!important;padding:.3rem .75rem!important;font-size:.82rem!important}
[data-testid="stDataFrame"] {border:1px solid #d7e4df;border-radius:14px;overflow:hidden;background:#fff;box-shadow:0 6px 18px #294d450a}
[data-testid="stDataFrame"] [role="columnheader"] {background:#244f50!important;color:#fff!important;font-weight:700!important}
[data-testid="stDataFrame"] [role="gridcell"] {border-color:#e5ece9!important}
[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {background:#f4f8f6!important}
[data-testid="stFileUploader"] {padding:.35rem;border-radius:12px;background:#f7faf9}
.source-badge {display:inline-flex;align-items:center;padding:.22rem .52rem;margin-right:.35rem;border-radius:999px;font-size:.71rem;font-weight:800;letter-spacing:.055em;background:#e2f1ed;color:#1f665c}
.source-sinapi{background:#e7eef9;color:#315b8b}.source-siurb{background:#fff0d6;color:#805c19}.source-sicro{background:#eee9f8;color:#654d88}.source-siec{background:#def1e9;color:#216757}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button {min-height:42px;border-radius:10px;font-weight:600;box-shadow:none}
[data-testid="stButton"] button[kind="primary"] {background:#28776f;border-color:#28776f;color:#fff}
[data-testid="stButton"] button[kind="primary"]:hover {background:#1d625b;border-color:#1d625b}
[data-testid="stButton"] button[kind="tertiary"] {min-height:36px;font-size:.85rem;padding:.3rem .55rem;color:#376e66;background:#edf4f1;border:1px solid #dce9e3}
[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] {font-size:.93rem}
button:focus-visible,[role="tab"]:focus-visible {outline:3px solid #76b4a6!important;outline-offset:3px}
.st-key-workspace {margin-top:.6rem}
.st-key-workspace > div:first-child [role="tablist"] {padding:.25rem;border:1px solid #c7dcd6;border-radius:14px;background:#eef5f2}
@media(max-width:640px){.block-container{padding:1rem .75rem 3rem}.st-key-login_shell{margin:2vh auto 0;padding:1.2rem}.st-key-hero{padding:1rem 1rem .2rem}.st-key-hero h1{font-size:1.9rem}[data-testid="stTabs"] [data-testid="stTab"]{padding:.6rem .7rem;flex:1 1 auto}[data-testid="stMetricValue"]{font-size:1.35rem!important}}
</style>'''

SCENE = '''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><style>
body{margin:0;font-family:system-ui,sans-serif;color:#54746b;background:#fff} .scene{position:relative;border-radius:12px;overflow:hidden;background:#f0f6f3}svg{display:block;width:100%;height:164px}
.run{animation:journey 80s linear infinite}.passenger{animation-duration:62s;animation-delay:-20s}.cargo{animation-duration:105s;animation-delay:-48s}.vlt{animation-duration:74s;animation-delay:-9s}
@keyframes journey{from{transform:translateX(-470px)}to{transform:translateX(1120px)}}
#pause{position:absolute;right:110px;top:9px;z-index:2;accent-color:#397b6d}label{position:absolute;right:12px;top:7px;font-size:11px;z-index:2;background:#f0f6f3;padding:2px 5px;border-radius:5px;cursor:pointer}#pause:checked~svg .run{animation-play-state:paused}
@media(prefers-reduced-motion:reduce){.run{animation:none;transform:translateX(210px)}.cargo{transform:translateX(450px)}.vlt{transform:translateX(70px)}}
</style></head><body><div class="scene"><input id="pause" type="checkbox" aria-label="Pausar animação"><label for="pause">Pausar animação</label>
<svg viewBox="0 0 1100 180" role="img" aria-label="Paisagem suave com trem de passageiros, trem de carga e VLT em movimento">
<defs><pattern id="ties" width="18" height="8" patternUnits="userSpaceOnUse"><path d="M4 0v8" stroke="#bacdc4" stroke-width="3"/></pattern><g id="wheel"><circle r="4" fill="#657b7a"/><circle r="1.4" fill="#cedbd5"/></g></defs>
<circle cx="865" cy="39" r="22" fill="#ede8cc"/><path d="M0 67Q130 8 285 59T570 40T860 68T1100 39V180H0Z" fill="#e1ece4"/><path d="M0 95Q155 56 330 80T645 77T1100 80V180H0Z" fill="#d4e4db"/>
<g fill="#becfc7"><rect x="660" y="27" width="22" height="48" rx="3"/><rect x="689" y="40" width="35" height="37" rx="3"/><rect x="730" y="20" width="21" height="60" rx="3"/><rect x="758" y="45" width="45" height="35" rx="3"/></g>
<g stroke="#aabfb5" stroke-width="2"><path d="M0 90H1100M0 131H1100M0 169H1100"/></g><g fill="url(#ties)"><path d="M0 89h1100v5H0zM0 130h1100v5H0zM0 168h1100v5H0z"/></g>
<g class="run passenger"><g fill="#b95f58" stroke="#9e514b" stroke-width="1"><rect x="0" y="65" width="107" height="20" rx="6"/><rect x="112" y="65" width="107" height="20" rx="6"/><path d="M224 65h73q14 0 29 20H224Z"/></g><path d="M5 79h304" stroke="#efdcd4" stroke-width="3"/><g fill="#476676"><path d="M10 69h87v7H10zM122 69h87v7h-87zM234 69h47v7h-47zM289 69h10l9 7h-19z"/></g><g transform="translate(18 86)"><use href="#wheel"/><use href="#wheel" x="73"/><use href="#wheel" x="119"/><use href="#wheel" x="187"/><use href="#wheel" x="226"/><use href="#wheel" x="280"/></g></g>
<g class="run cargo"><g fill="#9caeb0" stroke="#7d9598"><rect x="0" y="106" width="74" height="19" rx="2"/><rect x="80" y="106" width="74" height="19" rx="2"/><rect x="160" y="106" width="74" height="19" rx="2"/><path d="M242 125v-20h45V96h23v29Z" fill="#ad6558"/></g><path d="M290 100h15v8h-15" fill="#476676"/><path d="M0 125h315" stroke="#657b7a" stroke-width="3"/><g transform="translate(12 128)"><use href="#wheel"/><use href="#wheel" x="50"/><use href="#wheel" x="80"/><use href="#wheel" x="130"/><use href="#wheel" x="160"/><use href="#wheel" x="210"/><use href="#wheel" x="247"/><use href="#wheel" x="287"/></g></g>
<g class="run vlt"><path d="M0 164q6-23 23-23h148q14 0 26 23Z" fill="#60998e"/><path d="M22 145h43v10H17zM73 145h42v10H73zM123 145h45l9 10h-54z" fill="#e4f0e9"/><path d="M70 141v23m49-23v23" stroke="#476e69" stroke-width="2"/><path d="M82 141l9-9 13 9" fill="none" stroke="#79948c" stroke-width="2"/><g transform="translate(27 166)"><use href="#wheel"/><use href="#wheel" x="43"/><use href="#wheel" x="91"/><use href="#wheel" x="139"/></g></g>
<g font-family="system-ui" font-size="9" fill="#496b60"><text x="12" y="83">PASSAGEIROS</text><text x="12" y="123">CARGA</text><text x="12" y="160">VLT</text></g>
</svg></div></body></html>'''

def apply_theme():
    st.markdown(STYLE, unsafe_allow_html=True)

def animated_header():
    with st.container(key='hero'):
        st.markdown('<span class="hero-eyebrow">PLANEJE · CONFIGURE · ESTIME</span>', unsafe_allow_html=True)
        st.title('Parametric Rails')
        st.caption('Engenharia de custos ferroviários, com clareza do primeiro parâmetro ao orçamento.')
        html(SCENE, height=176, scrolling=False)
