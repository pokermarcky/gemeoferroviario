"""Tema visual e paisagem ferroviária leve, sem imagens externas."""
import streamlit as st
from streamlit.components.v1 import html

STYLE = '''<style>
/* Paleta RailParametric — verde sálvia claro, elegante e acessível. */
:root {--ink:#38584f;--accent:#6d9f8f;--line:#d9e8e1}
[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#f7fbf8 0,#eef6f1 48rem);color:var(--ink)}
.block-container {max-width:1180px;padding:1.3rem 2rem 4rem}
[data-testid="stSidebar"] {background:#f1f8f4;border-right:1px solid #d3e3dc}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding:1rem .8rem 2rem}
[data-testid="stSidebar"] .st-key-user_profile_card {padding:1rem;border:1px solid #ffffff24;border-radius:16px;background:linear-gradient(145deg,#4a7469,#6b978a);color:#fff;box-shadow:0 10px 28px #0b252528}
[data-testid="stSidebar"] .st-key-user_profile_card h3 {color:#fff!important;margin:.2rem 0 0;padding:0}
[data-testid="stSidebar"] .st-key-user_profile_card [data-testid="stCaptionContainer"] {color:#dcebe5}
[data-testid="stSidebar"] h2 {margin-top:1.25rem;color:#315a50;font-size:1.35rem!important}
.sidebar-eyebrow,.login-eyebrow {font-size:.67rem;letter-spacing:.17em;font-weight:800;color:#a7d0c2}
.role-badge {display:inline-flex;padding:.24rem .58rem;border-radius:999px;font-size:.7rem;font-weight:800;letter-spacing:.04em;margin:.2rem 0 .65rem;background:#e4f2ec;color:#4e7f72}
.role-root{background:#f5d993;color:#72520b}.role-test{background:#dce6f6;color:#315b8b}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {background:#fff}
[data-testid="stSidebar"] .st-key-budget_collection_heading {margin-top:1.25rem;padding:.25rem .2rem .45rem;border-bottom:1px solid #dbe8e3}
[data-testid="stSidebar"] .st-key-budget_collection_heading h2 {margin:.1rem 0 0!important;padding:0!important;font-size:1.48rem!important;letter-spacing:-.04em}
[data-testid="stSidebar"] .st-key-budget_collection_heading [data-testid="stCaptionContainer"] {font-size:.82rem;line-height:1.35;color:#68837b}
[data-testid="stSidebar"] .portfolio-summary {display:grid;grid-template-columns:.72fr 1.55fr;gap:.45rem;margin:.7rem 0 .65rem}
[data-testid="stSidebar"] .portfolio-summary>div {min-width:0;padding:.66rem .7rem;border:1px solid #d6e7e0;border-radius:12px;background:#fff;box-shadow:0 5px 14px #315a500a}
[data-testid="stSidebar"] .portfolio-summary span {display:block;margin-bottom:.18rem;color:#728a83;font-size:.57rem;font-weight:800;letter-spacing:.09em;white-space:nowrap}
[data-testid="stSidebar"] .portfolio-summary strong {display:block;overflow:hidden;color:#315a50;font-size:.9rem;font-weight:800;letter-spacing:-.025em;text-overflow:ellipsis;white-space:nowrap}
[data-testid="stSidebar"] .portfolio-summary>div:first-child strong {font-size:1.15rem;color:#6d9f8f}
[data-testid="stSidebar"] .st-key-budget_search {margin:.55rem 0 .15rem}
[data-testid="stSidebar"] .st-key-budget_search input {min-height:39px;border-color:#d6e7e0;border-radius:11px;background:#fff;font-size:.82rem}
.saved-count {display:flex;align-items:center;justify-content:space-between;margin:.75rem .2rem .5rem;color:#6f8780;font-size:.62rem;font-weight:800;letter-spacing:.1em}.saved-count b{display:inline-grid;place-items:center;min-width:23px;height:23px;border-radius:999px;background:#e4f2ec;color:#56887a;font-size:.7rem;letter-spacing:0}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] {padding:.82rem!important;margin-bottom:.62rem;border:1px solid #d9e7e1!important;border-radius:15px!important;background:#fff!important;box-shadow:0 7px 18px #315a500b!important;transition:border-color .15s,box-shadow .15s,transform .15s}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"]:hover {border-color:#9fc7b9!important;box-shadow:0 10px 24px #315a5014!important;transform:translateY(-1px)}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] [data-testid="stCaptionContainer"] {font-size:.73rem;color:#718984}
[data-testid="stSidebar"] [class*="st-key-open_project_"] button {min-height:45px!important;margin-top:.32rem;padding:.42rem 0!important;justify-content:space-between;border:0!important;background:transparent!important;color:#315c52!important;font-size:1rem!important;font-weight:800!important;text-align:left!important;box-shadow:none!important}
[data-testid="stSidebar"] [class*="st-key-open_project_"] button:hover {color:#6d9f8f!important;background:#eff8f3!important}
.project-card-heading {display:flex;align-items:center;gap:.5rem}.project-mark{display:inline-grid;place-items:center;width:29px;height:29px;border-radius:9px;background:#e4f2ec;color:#56887a;font-size:.62rem;font-weight:900;letter-spacing:.03em}.project-cargo{background:#eee8dc;color:#775a29}.project-vlt{background:#e5e9f7;color:#455b99}.project-passenger{background:#e4f2ec;color:#56887a}
.budget-type {display:inline-flex;padding:.18rem .48rem;border-radius:999px;background:#f0f5f3;color:#526f69;font-size:.61rem;font-weight:800;letter-spacing:.045em;text-transform:uppercase}
.budget-total-label {margin-top:.7rem;font-size:.61rem;font-weight:800;letter-spacing:.12em;color:#6b817d}.budget-total {font-size:1.24rem;font-weight:800;letter-spacing:-.035em;color:#315a50;line-height:1.15}.budget-per-km {margin:.25rem 0 .55rem;color:#6d9f8f;font-size:.84rem;font-weight:750}.budget-per-km span{font-weight:500;color:#758985}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] [data-testid="stButton"] button {min-height:36px;font-size:.78rem;padding:.3rem .45rem;border-color:#d6e7e0;background:#fff;color:#315f59}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] [data-testid="stButton"] button:hover {border-color:#6ba397;background:#eff8f3;color:#3f7164}
.project-editor-heading {display:flex;align-items:center;gap:.7rem;margin-bottom:.35rem}.project-editor-heading>div{display:flex;min-width:0;flex-direction:column}.project-editor-heading span:not(.project-mark){color:#728a83;font-size:.62rem;font-weight:800;letter-spacing:.1em}.project-editor-heading strong{overflow:hidden;color:#315a50;font-size:1.1rem;text-overflow:ellipsis;white-space:nowrap}
[data-testid="stDialog"] [data-testid="stMetric"] {background:#f7faf9;border-color:#dce8e4;box-shadow:none}
[data-testid="stDialog"] [data-testid="stMetricValue"] {font-size:1.15rem!important;color:#315a50}
[data-testid="stDialog"] h4 {margin-top:.65rem;padding-bottom:.15rem;color:#315a50}
[data-testid="stDialog"] [data-testid="stForm"] {margin-bottom:.4rem}
[data-testid="stDialog"] [class*="st-key-delete_action_"] button:enabled {border-color:#d68c82;background:#fff7f5;color:#9a3e32}
.st-key-project_edit_banner {margin:.6rem 0 .9rem;padding:.9rem 1rem!important;border-color:#93bfaf!important;border-left:5px solid #6d9f8f!important;background:linear-gradient(100deg,#eaf5f0,#fff)!important;box-shadow:0 7px 18px #315a500c!important}
.st-key-project_edit_banner h3 {margin:0!important;padding:0!important;color:#3f7164;font-size:1.08rem!important}
[class*="st-key-save_project_edit_"] {margin:.75rem 0;padding:.85rem 1rem!important;border-color:#a1cabb!important;background:#f3faf6!important}
[class*="st-key-save_project_edit_"] p {margin-bottom:.25rem}
[data-testid="stSidebar"] .st-key-empty_budget_collection,[data-testid="stSidebar"] .st-key-empty_budget_search {padding:1rem;text-align:center;border:1px dashed #c9ded6;border-radius:12px;background:#f8fcfa;color:#6b817d}
[data-testid="stSidebar"] .st-key-empty_budget_collection h3,[data-testid="stSidebar"] .st-key-empty_budget_search h3 {margin:0!important;padding:0!important;font-size:.95rem!important}
.st-key-login_shell {max-width:720px;margin:8vh auto 0;padding:2rem 2.1rem 1.6rem;border:1px solid #d6e8e0;border-radius:22px;background:#fff;box-shadow:0 22px 55px #315a501c}
.st-key-login_shell h1 {font-size:2.25rem;letter-spacing:-.045em;color:#315a50;padding:.25rem 0}
.st-key-login_shell [data-testid="stTabs"] [role="tablist"] {margin-top:1.2rem}
.st-key-hero {background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.4rem 1.6rem .45rem;box-shadow:0 12px 34px #24463f10}
.st-key-hero h1 {margin-inline:auto;text-align:center;font-family:"Aptos Display","Segoe UI Variable Display","Segoe UI",Inter,system-ui,sans-serif;font-size:2.35rem;font-weight:720;letter-spacing:-.04em;line-height:1.08;color:var(--ink);padding:.2rem 0 .35rem}
.st-key-hero p {color:#6c847d;font-size:.95rem;text-align:center}
.hero-eyebrow {display:block;text-align:center;font-family:"Aptos","Segoe UI Variable Text","Segoe UI",Inter,system-ui,sans-serif;font-size:.67rem;letter-spacing:.17em;font-weight:750;color:#6d9f90}
h3 {font-size:1.25rem!important;letter-spacing:-.025em;color:var(--ink)}
[data-testid="stCaptionContainer"] {color:#6b827c}
[data-testid="stTabs"] [role="tablist"] {gap:.5rem;border:0!important;margin:.6rem 0 1rem;flex-wrap:wrap;height:auto!important}
[data-testid="stTabs"] [data-testid="stTab"] {height:auto!important;min-height:44px;padding:.65rem 1rem;background:#fff;border:1px solid var(--line);border-radius:12px;color:#536d66;white-space:normal;transition:background .15s}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {background:#e6f3ed;border-color:#7ead9e;color:#3f7164;box-shadow:inset 0 -2px #7ead9e}
[data-testid="stTabs"] [data-testid="stTab"]:hover {background:#edf5f2;border-color:#a6ccbe}
[data-testid="stTabs"] .react-aria-SelectionIndicator {display:none}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;background:#fff;border-color:#deeae5!important;box-shadow:0 4px 15px #294d4508}
[data-testid="stExpander"] {border-radius:12px;background:#fff;border-color:var(--line)}
[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);border-radius:14px;padding:.65rem .9rem}
[data-testid="stMetricValue"] {font-size:1.65rem!important;letter-spacing:-.025em;color:#3a6259}
[class*="st-key-result_header_"] {margin-top:1.4rem;padding:.9rem 1.1rem .65rem;border-left:5px solid #6d9f8f;border-radius:4px 14px 14px 4px;background:linear-gradient(90deg,#e6f3ed,#f7faf8)}
[class*="st-key-result_header_"] h2 {margin:0;padding:0!important;font-size:1.7rem!important;letter-spacing:-.035em;color:#315a50}
[class*="st-key-result_header_"] [data-testid="stCaptionContainer"] {font-size:.92rem;color:#617e76}
[class*="st-key-result_kpis_"] [data-testid="stMetric"] {min-height:116px;padding:1rem 1.15rem;border:1px solid #a8c9c1!important;border-top:5px solid #6d9f8f!important;background:linear-gradient(145deg,#fff,#edf6f2);box-shadow:0 8px 22px #1c514710}
[class*="st-key-result_kpis_"] [data-testid="stMetricLabel"] {font-size:.78rem;font-weight:800;letter-spacing:.055em;text-transform:uppercase;color:#58796f}
[class*="st-key-result_kpis_"] [data-testid="stMetricValue"] {font-size:1.82rem!important;font-weight:780;color:#315a50}
.st-key-reference_heading {margin:.7rem 0 1rem;padding:1rem 1.2rem;border:1px solid #8ab8a9;border-left:6px solid #6d9f8f;border-radius:14px;background:linear-gradient(115deg,#e4f2ec,#f7faf8);box-shadow:0 8px 22px #24463f12}
.st-key-reference_heading h2 {margin:0;padding:0!important;color:#3f6c60;font-size:1.65rem!important}
.st-key-main_bdi_panel,.st-key-cargo_bdi_panel {border-color:#c9ded6!important;background:#f8fcfa!important}
.st-key-main_elevated_panel {margin:.85rem 0 1rem;padding:1rem 1.1rem!important;border-color:#9fc7b9!important;border-left:5px solid #6d9f8f!important;background:linear-gradient(115deg,#eff8f3,#fff)!important;box-shadow:0 8px 24px #24463f0d!important}
.st-key-main_elevated_panel [data-testid="stExpander"] {margin-top:.65rem;border-color:#bdd4ce;background:#fff}
.st-key-elevated_result_summary {margin:.85rem 0 1rem;padding:1rem 1.1rem!important;border-color:#a8ccbf!important;background:linear-gradient(135deg,#f1f8f6,#fff)!important;box-shadow:0 8px 24px #24463f0d!important}
.st-key-elevated_result_summary h3 {margin:0;padding:0 0 .15rem!important;color:#3f7164}
.st-key-elevated_result_summary [data-testid="stMetric"] {background:#fff;border-top:3px solid #82ad9f!important}
.elevated-scheme {position:relative;height:112px;margin:.75rem 0 .35rem;border:1px solid #dfece7;border-radius:12px;overflow:hidden;background:linear-gradient(#f7fbfa 0 72%,#eaf2ee 72%)}
.scheme-rail {position:absolute;left:6%;right:6%;top:24px;height:4px;background:#607b73;box-shadow:0 7px #9db4ad}
.scheme-deck {position:absolute;left:5%;right:5%;top:36px;height:13px;border-radius:3px;background:linear-gradient(180deg,#86a99f,#6e9187)}
.scheme-pier {position:absolute;top:49px;bottom:12px;width:9px;border-radius:0 0 3px 3px;background:#9eb9b1}.scheme-pier:after{content:"";position:absolute;left:-9px;bottom:-5px;width:27px;height:6px;border-radius:2px;background:#7f9c93}
.scheme-pier.p1{left:16%}.scheme-pier.p2{left:50%}.scheme-pier.p3{right:16%}
.scheme-span,.scheme-height {position:absolute;color:#577870;font-size:.68rem;font-weight:700}.scheme-span{left:25%;top:60px}.scheme-height{right:3%;bottom:7px}
.st-key-main_service_toolbar,.st-key-cargo_service_toolbar {padding:.55rem .8rem!important;margin:.35rem 0 .8rem;border-color:#cbded7!important;background:linear-gradient(90deg,#f4faf7,#fff)!important;box-shadow:none!important}
.st-key-main_service_toolbar p,.st-key-cargo_service_toolbar p {margin:0}
.st-key-main_service_toolbar [data-testid="stCaptionContainer"],.st-key-cargo_service_toolbar [data-testid="stCaptionContainer"] {font-size:.78rem}
.st-key-main_service_bulk [role="radiogroup"],.st-key-cargo_service_bulk [role="radiogroup"] {justify-content:flex-end}
.st-key-main_service_bulk button,.st-key-cargo_service_bulk button {min-height:34px!important;padding:.3rem .75rem!important;font-size:.82rem!important}
[data-testid="stDataFrame"] {border:1px solid #deeae5;border-radius:14px;overflow:hidden;background:#fff;box-shadow:0 6px 18px #294d450a}
[data-testid="stDataFrame"] [role="columnheader"] {background:#5c8377!important;color:#fff!important;font-weight:700!important}
[data-testid="stDataFrame"] [role="gridcell"] {border-color:#e7f0ec!important}
[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {background:#f5faf7!important}
[data-testid="stFileUploader"] {padding:.35rem;border-radius:12px;background:#f7faf9}
.source-badge {display:inline-flex;align-items:center;padding:.22rem .52rem;margin-right:.35rem;border-radius:999px;font-size:.71rem;font-weight:800;letter-spacing:.055em;background:#e8f4ee;color:#4e7f72}
.source-sinapi{background:#e7eef9;color:#315b8b}.source-siurb{background:#fff0d6;color:#805c19}.source-sicro{background:#eee9f8;color:#654d88}.source-siec{background:#e5f3ed;color:#4c806f}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button {min-height:42px;border-radius:10px;font-weight:600;box-shadow:none}
[data-testid="stButton"] button[kind="primary"] {background:#6d9f8f;border-color:#6d9f8f;color:#fff}
[data-testid="stButton"] button[kind="primary"]:hover {background:#4f7f74;border-color:#4f7f74}
[data-testid="stButton"] button[kind="tertiary"] {min-height:36px;font-size:.85rem;padding:.3rem .55rem;color:#5e8b7f;background:#f0f7f3;border:1px solid #e1eee8}
[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] {font-size:.93rem}
button:focus-visible,[role="tab"]:focus-visible {outline:3px solid #98c4b5!important;outline-offset:3px}
.st-key-workspace {margin-top:.6rem}
.st-key-workspace > div:first-child [role="tablist"] {padding:.25rem;border:1px solid #d3e5de;border-radius:14px;background:#f1f8f4}
@media(max-width:640px){.block-container{padding:1rem .75rem 3rem}.st-key-login_shell{margin:2vh auto 0;padding:1.2rem}.st-key-hero{padding:1rem 1rem .2rem}.st-key-hero h1{font-size:1.9rem}[data-testid="stTabs"] [data-testid="stTab"]{padding:.6rem .7rem;flex:1 1 auto}[data-testid="stMetricValue"]{font-size:1.35rem!important}}
</style>'''

SCENE = '''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><style>
body{margin:0;font-family:system-ui,sans-serif;color:#66867b;background:#fff} .scene{position:relative;border-radius:12px;overflow:hidden;background:#f3f9f6}svg{display:block;width:100%;height:164px}
.run{animation:journey 80s linear infinite}.passenger{animation-duration:62s;animation-delay:-20s}.cargo{animation-duration:105s;animation-delay:-48s}.vlt{animation-duration:74s;animation-delay:-9s}
@keyframes journey{from{transform:translateX(-470px)}to{transform:translateX(1120px)}}
#pause{position:absolute;right:110px;top:9px;z-index:2;accent-color:#629687}label{position:absolute;right:12px;top:7px;font-size:11px;z-index:2;background:#f3f9f6;padding:2px 5px;border-radius:5px;cursor:pointer}#pause:checked~svg .run{animation-play-state:paused}
@media(prefers-reduced-motion:reduce){.run{animation:none;transform:translateX(210px)}.cargo{transform:translateX(450px)}.vlt{transform:translateX(70px)}}
</style></head><body><div class="scene"><input id="pause" type="checkbox" aria-label="Pausar animação"><label for="pause">Pausar animação</label>
<svg viewBox="0 0 1100 180" role="img" aria-label="Paisagem suave com trem de passageiros, trem de carga e VLT em movimento">
<defs><pattern id="ties" width="18" height="8" patternUnits="userSpaceOnUse"><path d="M4 0v8" stroke="#cadbd4" stroke-width="3"/></pattern><g id="wheel"><circle r="4" fill="#718881"/><circle r="1.4" fill="#d8e5df"/></g></defs>
<circle cx="865" cy="39" r="22" fill="#ede8cc"/><path d="M0 67Q130 8 285 59T570 40T860 68T1100 39V180H0Z" fill="#e8f1ec"/><path d="M0 95Q155 56 330 80T645 77T1100 80V180H0Z" fill="#deebe4"/>
<g fill="#ccddd5"><rect x="660" y="27" width="22" height="48" rx="3"/><rect x="689" y="40" width="35" height="37" rx="3"/><rect x="730" y="20" width="21" height="60" rx="3"/><rect x="758" y="45" width="45" height="35" rx="3"/></g>
<g stroke="#b9cec5" stroke-width="2"><path d="M0 90H1100M0 131H1100M0 169H1100"/></g><g fill="url(#ties)"><path d="M0 89h1100v5H0zM0 130h1100v5H0zM0 168h1100v5H0z"/></g>
<g class="run passenger"><g fill="#b95f58" stroke="#9e514b" stroke-width="1"><rect x="0" y="65" width="107" height="20" rx="6"/><rect x="112" y="65" width="107" height="20" rx="6"/><path d="M224 65h73q14 0 29 20H224Z"/></g><path d="M5 79h304" stroke="#efdcd4" stroke-width="3"/><g fill="#5e7a72"><path d="M10 69h87v7H10zM122 69h87v7h-87zM234 69h47v7h-47zM289 69h10l9 7h-19z"/></g><g transform="translate(18 86)"><use href="#wheel"/><use href="#wheel" x="73"/><use href="#wheel" x="119"/><use href="#wheel" x="187"/><use href="#wheel" x="226"/><use href="#wheel" x="280"/></g></g>
<g class="run cargo"><g fill="#a8bbb4" stroke="#88a097"><rect x="0" y="106" width="74" height="19" rx="2"/><rect x="80" y="106" width="74" height="19" rx="2"/><rect x="160" y="106" width="74" height="19" rx="2"/><path d="M242 125v-20h45V96h23v29Z" fill="#ad6558"/></g><path d="M290 100h15v8h-15" fill="#5e7a72"/><path d="M0 125h315" stroke="#718881" stroke-width="3"/><g transform="translate(12 128)"><use href="#wheel"/><use href="#wheel" x="50"/><use href="#wheel" x="80"/><use href="#wheel" x="130"/><use href="#wheel" x="160"/><use href="#wheel" x="210"/><use href="#wheel" x="247"/><use href="#wheel" x="287"/></g></g>
<g class="run vlt"><path d="M0 164q6-23 23-23h148q14 0 26 23Z" fill="#82ad9f"/><path d="M22 145h43v10H17zM73 145h42v10H73zM123 145h45l9 10h-54z" fill="#eaf4ef"/><path d="M70 141v23m49-23v23" stroke="#5f8a7e" stroke-width="2"/><path d="M82 141l9-9 13 9" fill="none" stroke="#88a59b" stroke-width="2"/><g transform="translate(27 166)"><use href="#wheel"/><use href="#wheel" x="43"/><use href="#wheel" x="91"/><use href="#wheel" x="139"/></g></g>
<g font-family="system-ui" font-size="9" fill="#61897c"><text x="12" y="83">PASSAGEIROS</text><text x="12" y="123">CARGA</text><text x="12" y="160">VLT</text></g>
</svg></div></body></html>'''

def apply_theme():
    st.markdown(STYLE, unsafe_allow_html=True)

def animated_header():
    with st.container(key='hero'):
        st.markdown('<span class="hero-eyebrow">PLANEJE · CONFIGURE · ESTIME</span>', unsafe_allow_html=True)
        st.title('Parametric Rails')
        st.caption('Engenharia de custos ferroviários, com clareza do primeiro parâmetro ao orçamento.')
        html(SCENE, height=176, scrolling=False)
