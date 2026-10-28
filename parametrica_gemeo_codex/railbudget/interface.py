"""Tema visual e paisagem ferroviária leve, sem imagens externas."""
import streamlit as st
from streamlit.components.v1 import html

STYLE = '''<style>
:root {--ink:#3b2421;--accent:#b8322a;--line:#f8e9cc}
[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#fefbf4 0,#fcf6ea 48rem);color:var(--ink)}
.block-container {max-width:1180px;padding:1.3rem 2rem 4rem}
[data-testid="stSidebar"] {background:#fcf8ed;border-right:1px solid #ebcdb9}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding:1rem .8rem 2rem}
[data-testid="stSidebar"] .st-key-user_profile_card {padding:1rem;border:1px solid #ffffff24;border-radius:16px;background:linear-gradient(145deg,#7e1f19,#a3483a);color:#fff;box-shadow:0 10px 28px #5c1a1630}
[data-testid="stSidebar"] .st-key-user_profile_card h3 {color:#fff!important;margin:.2rem 0 0;padding:0}
[data-testid="stSidebar"] .st-key-user_profile_card [data-testid="stCaptionContainer"] {color:#f0dcc6}
[data-testid="stSidebar"] h2 {margin-top:1.25rem;color:#5c1a16;font-size:1.35rem!important}
.sidebar-eyebrow,.login-eyebrow {font-size:.67rem;letter-spacing:.17em;font-weight:800;color:#e9cfa8}
.role-badge {display:inline-flex;padding:.24rem .58rem;border-radius:999px;font-size:.7rem;font-weight:800;letter-spacing:.04em;margin:.2rem 0 .65rem;background:#f8ebd2;color:#66241f}
.role-root{background:#ecd9b0;color:#72520b}.role-test{background:#dce6f6;color:#315b8b}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {background:#fff}
[data-testid="stSidebar"] .st-key-budget_collection_heading {margin-top:1.25rem;padding:.25rem .2rem .45rem;border-bottom:1px solid #f6e4c0}
[data-testid="stSidebar"] .st-key-budget_collection_heading h2 {margin:.1rem 0 0!important;padding:0!important;font-size:1.48rem!important;letter-spacing:-.04em}
[data-testid="stSidebar"] .st-key-budget_collection_heading [data-testid="stCaptionContainer"] {font-size:.82rem;line-height:1.35;color:#875f57}
[data-testid="stSidebar"] .portfolio-summary {display:grid;grid-template-columns:.72fr 1.55fr;gap:.45rem;margin:.7rem 0 .65rem}
[data-testid="stSidebar"] .portfolio-summary>div {min-width:0;padding:.66rem .7rem;border:1px solid #ecd0bd;border-radius:12px;background:#fff;box-shadow:0 5px 14px #4018160a}
[data-testid="stSidebar"] .portfolio-summary span {display:block;margin-bottom:.18rem;color:#95685f;font-size:.57rem;font-weight:800;letter-spacing:.09em;white-space:nowrap}
[data-testid="stSidebar"] .portfolio-summary strong {display:block;overflow:hidden;color:#5c1a16;font-size:.9rem;font-weight:800;letter-spacing:-.025em;text-overflow:ellipsis;white-space:nowrap}
[data-testid="stSidebar"] .portfolio-summary>div:first-child strong {font-size:1.15rem;color:#b8322a}
[data-testid="stSidebar"] .st-key-budget_search {margin:.55rem 0 .15rem}
[data-testid="stSidebar"] .st-key-budget_search input {min-height:39px;border-color:#ecd0bd;border-radius:11px;background:#fff;font-size:.82rem}
.saved-count {display:flex;align-items:center;justify-content:space-between;margin:.75rem .2rem .5rem;color:#8c6259;font-size:.62rem;font-weight:800;letter-spacing:.1em}.saved-count b{display:inline-grid;place-items:center;min-width:23px;height:23px;border-radius:999px;background:#f8ebd2;color:#682723;font-size:.7rem;letter-spacing:0}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] {padding:.82rem!important;margin-bottom:.62rem;border:1px solid #edd1bf!important;border-radius:15px!important;background:#fff!important;box-shadow:0 7px 18px #4018160b!important;transition:border-color .15s,box-shadow .15s,transform .15s}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"]:hover {border-color:#d69b73!important;box-shadow:0 10px 24px #40181614!important;transform:translateY(-1px)}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] [data-testid="stCaptionContainer"] {font-size:.73rem;color:#8f645b}
[data-testid="stSidebar"] [class*="st-key-open_project_"] button {min-height:45px!important;margin-top:.32rem;padding:.42rem 0!important;justify-content:space-between;border:0!important;background:transparent!important;color:#411916!important;font-size:1rem!important;font-weight:800!important;text-align:left!important;box-shadow:none!important}
[data-testid="stSidebar"] [class*="st-key-open_project_"] button:hover {color:#b8322a!important;background:#fcf5e7!important}
.project-card-heading {display:flex;align-items:center;gap:.5rem}.project-mark{display:inline-grid;place-items:center;width:29px;height:29px;border-radius:9px;background:#f8ebd2;color:#682723;font-size:.62rem;font-weight:900;letter-spacing:.03em}.project-cargo{background:#eee8dc;color:#775a29}.project-vlt{background:#e5e9f7;color:#455b99}.project-passenger{background:#f8ebd2;color:#682723}
.budget-type {display:inline-flex;padding:.18rem .48rem;border-radius:999px;background:#fcf6e9;color:#76524b;font-size:.61rem;font-weight:800;letter-spacing:.045em;text-transform:uppercase}
.budget-total-label {margin-top:.7rem;font-size:.61rem;font-weight:800;letter-spacing:.12em;color:#90655c}.budget-total {font-size:1.24rem;font-weight:800;letter-spacing:-.035em;color:#5c1a16;line-height:1.15}.budget-per-km {margin:.25rem 0 .55rem;color:#b8322a;font-size:.84rem;font-weight:750}.budget-per-km span{font-weight:500;color:#9b6c63}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] [data-testid="stButton"] button {min-height:36px;font-size:.78rem;padding:.3rem .45rem;border-color:#ecd0bd;background:#fff;color:#6c2924}
[data-testid="stSidebar"] [class*="st-key-saved_budget_card_"] [data-testid="stButton"] button:hover {border-color:#a3746b;background:#fcf5e7;color:#4f1b17}
.project-editor-heading {display:flex;align-items:center;gap:.7rem;margin-bottom:.35rem}.project-editor-heading>div{display:flex;min-width:0;flex-direction:column}.project-editor-heading span:not(.project-mark){color:#95685f;font-size:.62rem;font-weight:800;letter-spacing:.1em}.project-editor-heading strong{overflow:hidden;color:#5c1a16;font-size:1.1rem;text-overflow:ellipsis;white-space:nowrap}
[data-testid="stDialog"] [data-testid="stMetric"] {background:#fdfaf4;border-color:#f8e9cc;box-shadow:none}
[data-testid="stDialog"] [data-testid="stMetricValue"] {font-size:1.15rem!important;color:#5c1a16}
[data-testid="stDialog"] h4 {margin-top:.65rem;padding-bottom:.15rem;color:#5c1a16}
[data-testid="stDialog"] [data-testid="stForm"] {margin-bottom:.4rem}
[data-testid="stDialog"] [class*="st-key-delete_action_"] button:enabled {border-color:#d68c82;background:#fff7f5;color:#9a3e32}
.st-key-project_edit_banner {margin:.6rem 0 .9rem;padding:.9rem 1rem!important;border-color:#a87c73!important;border-left:5px solid #b8322a!important;background:linear-gradient(100deg,#fbf2e0,#fff)!important;box-shadow:0 7px 18px #4018160c!important}
.st-key-project_edit_banner h3 {margin:0!important;padding:0!important;color:#4f1b17;font-size:1.08rem!important}
[class*="st-key-save_project_edit_"] {margin:.75rem 0;padding:.85rem 1rem!important;border-color:#b38b83!important;background:#fdf8ef!important}
[class*="st-key-save_project_edit_"] p {margin-bottom:.25rem}
[data-testid="stSidebar"] .st-key-empty_budget_collection,[data-testid="stSidebar"] .st-key-empty_budget_search {padding:1rem;text-align:center;border:1px dashed #e6c1a8;border-radius:12px;background:#fefbf5;color:#90655c}
[data-testid="stSidebar"] .st-key-empty_budget_collection h3,[data-testid="stSidebar"] .st-key-empty_budget_search h3 {margin:0!important;padding:0!important;font-size:.95rem!important}
.st-key-login_shell {max-width:720px;margin:8vh auto 0;padding:2rem 2.1rem 1.6rem;border:1px solid #ebcebb;border-radius:22px;background:#fff;box-shadow:0 22px 55px #4018161c}
.st-key-login_shell h1 {font-size:2.25rem;letter-spacing:-.045em;color:#5c1a16;padding:.25rem 0}
.st-key-login_shell [data-testid="stTabs"] [role="tablist"] {margin-top:1.2rem}
.st-key-hero {background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.4rem 1.6rem .45rem;box-shadow:0 12px 34px #501e1b10}
.st-key-hero h1 {margin-inline:auto;text-align:center;font-family:"Aptos Display","Segoe UI Variable Display","Segoe UI",Inter,system-ui,sans-serif;font-size:2.35rem;font-weight:720;letter-spacing:-.04em;line-height:1.08;color:var(--ink);padding:.2rem 0 .35rem}
.st-key-hero p {color:#8a6159;font-size:.95rem;text-align:center}
.hero-eyebrow {display:block;text-align:center;font-family:"Aptos","Segoe UI Variable Text","Segoe UI",Inter,system-ui,sans-serif;font-size:.67rem;letter-spacing:.17em;font-weight:750;color:#8a4938}
h3 {font-size:1.25rem!important;letter-spacing:-.025em;color:var(--ink)}
[data-testid="stCaptionContainer"] {color:#896057}
[data-testid="stTabs"] [role="tablist"] {gap:.5rem;border:0!important;margin:.6rem 0 1rem;flex-wrap:wrap;height:auto!important}
[data-testid="stTabs"] [data-testid="stTab"] {height:auto!important;min-height:44px;padding:.65rem 1rem;background:#fff;border:1px solid var(--line);border-radius:12px;color:#85322c;white-space:normal;transition:background .15s}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {background:#faf0dc;border-color:#a8604a;color:#561c18;box-shadow:inset 0 -2px #a8604a}
[data-testid="stTabs"] [data-testid="stTab"]:hover {background:#fcf4e6;border-color:#b38e87}
[data-testid="stTabs"] .react-aria-SelectionIndicator {display:none}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;background:#fff;border-color:#f8e9cb!important;box-shadow:0 4px 15px #58211e08}
[data-testid="stExpander"] {border-radius:12px;background:#fff;border-color:var(--line)}
[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);border-radius:14px;padding:.65rem .9rem}
[data-testid="stMetricValue"] {font-size:1.65rem!important;letter-spacing:-.025em;color:#54201c}
[class*="st-key-result_header_"] {margin-top:1.4rem;padding:.9rem 1.1rem .65rem;border-left:5px solid #b8322a;border-radius:4px 14px 14px 4px;background:linear-gradient(90deg,#faf0dc,#fdfaf4)}
[class*="st-key-result_header_"] h2 {margin:0;padding:0!important;font-size:1.7rem!important;letter-spacing:-.035em;color:#5c1a16}
[class*="st-key-result_header_"] [data-testid="stCaptionContainer"] {font-size:.92rem;color:#76524b}
[class*="st-key-result_kpis_"] [data-testid="stMetric"] {min-height:116px;padding:1rem 1.15rem;border:1px solid #dfb192!important;border-top:5px solid #b8322a!important;background:linear-gradient(145deg,#fff,#fcf5e7);box-shadow:0 8px 22px #521f1b10}
[class*="st-key-result_kpis_"] [data-testid="stMetricLabel"] {font-size:.78rem;font-weight:800;letter-spacing:.055em;text-transform:uppercase;color:#85322d}
[class*="st-key-result_kpis_"] [data-testid="stMetricValue"] {font-size:1.82rem!important;font-weight:780;color:#3f1815}
.st-key-reference_heading {margin:.7rem 0 1rem;padding:1rem 1.2rem;border:1px solid #a3766d;border-left:6px solid #b8322a;border-radius:14px;background:linear-gradient(115deg,#f8ebd2,#fdfaf4);box-shadow:0 8px 22px #501e1b12}
.st-key-reference_heading h2 {margin:0;padding:0!important;color:#4b1a17;font-size:1.65rem!important}
.st-key-main_bdi_panel,.st-key-cargo_bdi_panel {border-color:#e4bea4!important;background:#fefbf5!important}
.st-key-main_elevated_panel {margin:.85rem 0 1rem;padding:1rem 1.1rem!important;border-color:#ae867e!important;border-left:5px solid #b8322a!important;background:linear-gradient(115deg,#fcf5e7,#fff)!important;box-shadow:0 8px 24px #501e1b0d!important}
.st-key-main_elevated_panel [data-testid="stExpander"] {margin-top:.65rem;border-color:#e6c3ab;background:#fff}
.st-key-elevated_result_summary {margin:.85rem 0 1rem;padding:1rem 1.1rem!important;border-color:#c7a28c!important;background:linear-gradient(135deg,#fcf7ed,#fff)!important;box-shadow:0 8px 24px #501e1b0d!important}
.st-key-elevated_result_summary h3 {margin:0;padding:0 0 .15rem!important;color:#4f1b17}
.st-key-elevated_result_summary [data-testid="stMetric"] {background:#fff;border-top:3px solid #a8604a!important}
.st-key-main_service_toolbar,.st-key-cargo_service_toolbar {padding:.55rem .8rem!important;margin:.35rem 0 .8rem;border-color:#e5bfa6!important;background:linear-gradient(90deg,#fdf9f0,#fff)!important;box-shadow:none!important}
.st-key-main_service_toolbar p,.st-key-cargo_service_toolbar p {margin:0}
.st-key-main_service_toolbar [data-testid="stCaptionContainer"],.st-key-cargo_service_toolbar [data-testid="stCaptionContainer"] {font-size:.78rem}
.st-key-main_service_bulk [role="radiogroup"],.st-key-cargo_service_bulk [role="radiogroup"] {justify-content:flex-end}
.st-key-main_service_bulk button,.st-key-cargo_service_bulk button {min-height:34px!important;padding:.3rem .75rem!important;font-size:.82rem!important}
[data-testid="stDataFrame"] {border:1px solid #f7e6c4;border-radius:14px;overflow:hidden;background:#fff;box-shadow:0 6px 18px #58211e0a}
[data-testid="stDataFrame"] [role="columnheader"] {background:#8e2a20!important;color:#fff!important;font-weight:700!important}
[data-testid="stDataFrame"] [role="gridcell"] {border-color:#f9eed8!important}
[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {background:#fdf8ef!important}
[data-testid="stFileUploader"] {padding:.35rem;border-radius:12px;background:#fdfaf4}
.source-badge {display:inline-flex;align-items:center;padding:.22rem .52rem;margin-right:.35rem;border-radius:999px;font-size:.71rem;font-weight:800;letter-spacing:.055em;background:#faefd9;color:#66241f}
.source-sinapi{background:#e7eef9;color:#315b8b}.source-siurb{background:#f6ecdc;color:#805c19}.source-sicro{background:#eee9f8;color:#654d88}.source-siec{background:#f9edd6;color:#672621}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button {min-height:42px;border-radius:10px;font-weight:600;box-shadow:none}
[data-testid="stButton"] button[kind="primary"] {background:#b8322a;border-color:#b8322a;color:#fff}
[data-testid="stButton"] button[kind="primary"]:hover {background:#962620;border-color:#962620}
[data-testid="stButton"] button[kind="tertiary"] {min-height:36px;font-size:.85rem;padding:.3rem .55rem;color:#7c2f29;background:#fbf4e6;border:1px solid #f8eacd}
[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] {font-size:.93rem}
button:focus-visible,[role="tab"]:focus-visible {outline:3px solid #b97a5e!important;outline-offset:3px}
.st-key-workspace {margin-top:.6rem}
.st-key-workspace > div:first-child [role="tablist"] {padding:.25rem;border:1px solid #ebccb8;border-radius:14px;background:#fcf5e7}
/* Tema vermelho e amarelo: degradê vermelho -> terracota -> ocre suave (sóbrio) nos destaques, fundos claros para leitura */
:root {--grad:linear-gradient(90deg,#b8322a,#a0614c 55%,#c9ad80);--grad-soft:linear-gradient(115deg,#f5e9db,#fff8ea)}
[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#f7efe4 0,#fff8ec 22rem,#fffaf3 60rem)}
[data-testid="stHeader"] {background:transparent}
[data-testid="stHeader"]::before {content:"";position:absolute;inset:0 0 auto;height:5px;background:var(--grad)}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#f5eadc 0,#faf4ec 18rem,#fffaf3 100%)}
[data-testid="stSidebar"] .sidebar-eyebrow {color:#b8322a}
[data-testid="stSidebar"] .st-key-user_profile_card {border:1px solid #e2c7b0;border-top:0;background:var(--grad) top/100% 6px no-repeat,linear-gradient(150deg,#fffaf0,#ffe9bf);color:#3b2421;box-shadow:0 10px 26px #b8322a1f}
[data-testid="stSidebar"] .st-key-user_profile_card h3 {color:#5c1a16!important}
[data-testid="stSidebar"] .st-key-user_profile_card [data-testid="stCaptionContainer"] {color:#896057}
[data-testid="stSidebar"] .st-key-user_profile_card .sidebar-eyebrow {color:#b8322a}
[data-testid="stSidebar"] .st-key-user_profile_card a {color:#962620!important}
[data-testid="stSidebar"] .st-key-user_profile_card .role-badge {background:linear-gradient(90deg,#b8322a,#9e4a3a);color:#fff}
[data-testid="stSidebar"] .st-key-user_profile_card .role-test {background:#fff;color:#962620;border:1px solid #c4927a}
[data-testid="stSidebar"] .st-key-user_profile_card button {background:#fff;border:1px solid #d2ad95;color:#962620}
[data-testid="stSidebar"] .st-key-user_profile_card button:hover {background:#f7efe4;border-color:#b8322a;color:#7a2018}
.st-key-hero {border:1px solid transparent;border-top:5px solid transparent;background:linear-gradient(#fff,#fff) padding-box,var(--grad) border-box}
.st-key-hero h1 {background:linear-gradient(90deg,#8e211b,#a3483a 55%,#b8700d);-webkit-background-clip:text;background-clip:text;color:transparent!important}
.hero-eyebrow {color:#a3483a}
[data-testid="stCaptionContainer"] p,[data-testid="stCaptionContainer"] span {color:inherit}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {background:linear-gradient(135deg,#a82a22,#a3483a);border-color:#a82a22;color:#fff}
[data-testid="stButton"] button[kind="primary"]:hover,[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover {background:linear-gradient(135deg,#8e211b,#a8361a);border-color:#8e211b;color:#fff}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {background:linear-gradient(180deg,#faf3e9,#f1e2cf);border-color:#c4927a;color:#7a2018;box-shadow:inset 0 -3px #a3483a}
[class*="st-key-result_header_"],.st-key-reference_heading {background:var(--grad-soft);border-left-color:#b8322a}
[class*="st-key-result_kpis_"] [data-testid="stMetric"] {border-top:1px solid #e6cdb8!important;background:var(--grad) top/100% 5px no-repeat,linear-gradient(145deg,#fff,#fff4df)}
.st-key-elevated_result_summary [data-testid="stMetric"] {border-top:1px solid #e6cdb8!important;background:var(--grad) top/100% 3px no-repeat,#fff}
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
