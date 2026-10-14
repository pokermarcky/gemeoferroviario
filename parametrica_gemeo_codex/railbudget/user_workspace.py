"""Área lateral do usuário e coleção pessoal de orçamentos."""
from datetime import datetime
from html import escape
import json

import streamlit as st

from railbudget.auth import can, is_primary_root, logout
from railbudget.budget_store import (
    delete_budget, list_budgets, save_budget, storage_mode, update_budget,
)
from railbudget.exporters import currency


ROLE_LABELS = {"root": "Administrador root", "user": "Usuário", "test": "Demonstração"}
MODALITY_LABELS = {"main": "Ferrovia de passageiro", "cargo": "Ferrovia de carga",
    "vlt": "VLT - Veículo leve sobre Trilho"}


def _date_label(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y · %H:%M")
    except (TypeError, ValueError):
        return "Data não informada"


def _distance_label(result, scenario):
    distance = result.get("corridor_km")
    if distance is None:
        distance = scenario.get("km")
    if distance is None:
        return None
    return f"{float(distance):,.2f} km".replace(",", "X").replace(".", ",").replace("X", ".")


def _per_km(result, row, scenario):
    value = result.get("per_km")
    distance = result.get("corridor_km", scenario.get("km"))
    if value is None and distance:
        value = float(row.get("total", 0)) / float(distance)
    return value


def _modality_visual(modality):
    label = str(modality).casefold()
    if "vlt" in label:
        return "VLT", "project-vlt"
    if "carga" in label:
        return "CG", "project-cargo"
    return "PS", "project-passenger"


def _modality_key(modality):
    label = str(modality).casefold()
    if "vlt" in label:
        return "vlt"
    if "carga" in label:
        return "cargo"
    return "main"


def _load_budget_for_editing(row, result):
    """Restaura os parâmetros salvos antes de os controles do orçamento serem recriados."""
    scenario = result.get("scenario", {}) if isinstance(result, dict) else {}
    key = _modality_key(row.get("modality", ""))
    st.session_state["budget_edit_context"] = {
        "id": str(row.get("id", "")),
        "name": str(row.get("name", "Orçamento")),
        "modality": str(row.get("modality", "Modalidade")),
        "key": key,
    }
    st.session_state.setdefault("results", {})[key] = result
    st.session_state.setdefault("display_results", {})[key] = result

    if key == "vlt":
        surface = float(scenario.get("surface_km", 0.90))
        elevated = float(scenario.get("elevated_km", 1.70))
        st.session_state["vlt_surface_km"] = surface
        st.session_state["vlt_elevated_km"] = elevated
        st.session_state["vlt_calculated_inputs"] = (surface, elevated)
        return

    freight = key == "cargo"
    km = float(scenario.get("km", 1.0))
    configuration = "Superfície" if freight else scenario.get("configuration", "Superfície")
    lines = int(scenario.get("lines", 1))
    drainage = scenario.get("drainage", "Reforçada")
    fence = scenario.get("fence", "Cerca")
    amvs = int(scenario.get("amvs", 0 if freight else 1))
    detection = scenario.get("detection", "Circuito de via")
    trainsets = 0 if freight else int(scenario.get("trainsets", 0))
    bdi = float(scenario.get("bdi", 0.0))

    st.session_state[f"{key}_km"] = km
    st.session_state[f"{key}_lines"] = lines
    st.session_state[f"{key}_drainage"] = drainage
    st.session_state[f"{key}_fence"] = fence
    st.session_state[f"{key}_amvs"] = amvs
    st.session_state[f"{key}_detection"] = detection
    st.session_state[f"{key}_aplicar_bdi"] = bdi > 0
    st.session_state[f"{key}_bdi_personalizado"] = bdi * 100 if bdi > 0 else 26.30
    st.session_state[f"{key}_service_bulk"] = None
    if not freight:
        st.session_state[f"{key}_profile"] = "SIEC • lastro / AMV nº 14"
        st.session_state[f"{key}_configuration"] = configuration
        st.session_state[f"{key}_trainsets"] = trainsets
    else:
        axle = int(scenario.get("axle_load", 25))
        locomotives = float(scenario.get("locomotives", 0.0))
        wagons = float(scenario.get("wagons", 0.0))
        st.session_state[f"{key}_axle"] = axle
        st.session_state[f"{key}_locomotives"] = locomotives
        st.session_state[f"{key}_wagons"] = wagons

    scope = result.get("scope_summary", []) if isinstance(result, dict) else []
    selected = {item.get("group"): bool(item.get("selected")) for item in scope}
    fallback = [True, bool(scenario.get("topography", True)), True,
        scenario.get("fence", "Nenhuma") != "Nenhuma", int(scenario.get("amvs", 0)) > 0,
        bool(scenario.get("ducts", False)), bool(scenario.get("overhead", False)),
        bool(scenario.get("signaling", False)), bool(scenario.get("rolling_stock", False))]
    for index, item in enumerate(scope[:8 if freight else 9]):
        st.session_state[f"{key}_grupo_{index}"] = selected.get(item.get("group"), fallback[index])
    if not scope:
        for index, checked in enumerate(fallback[:8 if freight else 9]):
            st.session_state[f"{key}_grupo_{index}"] = checked

    extra = ((int(scenario.get("axle_load", 25)), float(scenario.get("locomotives", 0.0)),
        float(scenario.get("wagons", 0.0))) if freight else ())
    st.session_state[f"{key}_calculated_inputs"] = (
        km, configuration, lines, drainage, fence, amvs, detection, trainsets, extra,
    )


@st.dialog("Informações do projeto", width="small")
def _edit_project_dialog(user, row, result):
    """Editor concentrado, sem alongar ou poluir a barra lateral."""
    budget_id = str(row.get("id", ""))
    scenario = result.get("scenario", {}) if isinstance(result, dict) else {}
    distance = _distance_label(result, scenario)
    per_km = _per_km(result, row, scenario)
    modality = str(row.get("modality", "Modalidade"))
    initials, modality_class = _modality_visual(modality)

    st.markdown(
        '<div class="project-editor-heading">'
        f'<span class="project-mark {modality_class}">{initials}</span>'
        '<div><span>PROJETO SELECIONADO</span>'
        f'<strong>{escape(str(row.get("name", "Orçamento")))}</strong></div></div>',
        unsafe_allow_html=True,
    )
    st.caption(f"{modality} · {_date_label(row.get('created_at'))}")
    metrics = st.columns(2)
    metrics[0].metric("Custo total", currency(float(row.get("total", 0))), border=True)
    metrics[1].metric("Custo por km", currency(float(per_km)) if per_km is not None else "—",
        border=True)

    st.markdown("#### Dados técnicos")
    if distance:
        st.markdown(f"**Extensão do corredor:** {distance}")
    if isinstance(result, dict) and result.get("line_km") is not None:
        line_km = f"{float(result['line_km']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"**Extensão de linha:** {line_km} km")
    if isinstance(result, dict) and result.get("reference_period"):
        st.markdown(f"**Data-base:** {result['reference_period']}")
    if scenario.get("configuration"):
        st.markdown(f"**Implantação:** {scenario['configuration']}")
    if scenario.get("lines"):
        st.markdown(f"**Via:** {'Simples' if int(scenario['lines']) == 1 else 'Dupla'}")
    if scenario.get("bdi") is not None:
        st.markdown(f"**BDI:** {float(scenario['bdi']) * 100:.2f}%".replace(".", ","))

    st.divider()
    if st.button("Editar parâmetros e custos", icon=":material/tune:", type="primary",
        key=f"load_budget_{budget_id}", use_container_width=True,
        on_click=_load_budget_for_editing, args=(row, result)):
        st.rerun()
    st.caption("Os parâmetros serão carregados na modalidade correspondente. Recalcule e salve no mesmo projeto.")

    st.divider()
    st.markdown("#### Alterar nome")
    with st.form(f"edit_form_{budget_id}", border=False):
        new_name = st.text_input("Nome do projeto", value=row.get("name", ""),
            max_chars=80, key=f"edit_name_{budget_id}")
        save_edit = st.form_submit_button("Salvar alteração", type="primary",
            icon=":material/save:", use_container_width=True)
    if save_edit:
        try:
            update_budget(user, budget_id, new_name)
            st.toast("Projeto alterado com sucesso.", icon=":material/check_circle:")
            st.rerun()
        except (RuntimeError, ValueError, LookupError) as exc:
            st.error(str(exc))

    st.divider()
    confirm = st.checkbox("Confirmo que desejo excluir este projeto",
        key=f"confirm_delete_{budget_id}")
    if st.button("Excluir projeto", icon=":material/delete:",
        key=f"delete_action_{budget_id}", use_container_width=True, disabled=not confirm):
        try:
            delete_budget(user, budget_id)
            st.toast("Projeto excluído.", icon=":material/delete:")
            st.rerun()
        except (RuntimeError, LookupError) as exc:
            st.error(str(exc))


def render_user_sidebar(user):
    with st.sidebar:
        with st.container(key="user_profile_card"):
            st.markdown('<span class="sidebar-eyebrow">SEU ESPAÇO</span>', unsafe_allow_html=True)
            st.markdown(f"### {user.name}")
            st.caption(user.email if user.role != "test" else "Acesso para conhecer o sistema")
            st.markdown(f'<span class="role-badge role-{user.role}">{ROLE_LABELS[user.role]}</span>', unsafe_allow_html=True)
            if st.button("Sair", icon=":material/logout:", key="logout", use_container_width=True):
                logout(user)

        if not is_primary_root(user):
            return

        with st.container(key="budget_collection_heading"):
            st.markdown('<span class="sidebar-eyebrow">ÁREA DE PROJETOS</span>', unsafe_allow_html=True)
            st.markdown("## Carteira de Projetos")
            st.caption("Organize e acompanhe seus estudos ferroviários.")
        display_results = st.session_state.get("display_results", {})
        available = {key: MODALITY_LABELS[key] for key in MODALITY_LABELS if key in display_results}
        mode=storage_mode(user)
        try:
            saved = list_budgets(user.user_id,user)
        except RuntimeError as exc:
            st.error(str(exc))
            saved = []

        portfolio_total = sum(float(row.get("total", 0)) for row in saved)
        st.markdown(
            '<div class="portfolio-summary">'
            f'<div><span>PROJETOS</span><strong>{len(saved)}</strong></div>'
            f'<div><span>VALOR DA CARTEIRA</span><strong>{currency(portfolio_total)}</strong></div>'
            '</div>', unsafe_allow_html=True,
        )

        with st.expander("Adicionar projeto", icon=":material/add_circle:"):
            if available:
                modality = st.selectbox("Cenário calculado", list(available),
                    format_func=available.get, key="saved_budget_modality")
                name = st.text_input("Nome do projeto", placeholder="Ex.: Linha Leste · Estudo inicial",
                    key="saved_budget_name", max_chars=80)
                if st.button("Salvar na carteira", icon=":material/bookmark_add:", type="primary",
                    key="save_budget", use_container_width=True):
                    if not name.strip():
                        st.warning("Digite um nome para identificar o orçamento.")
                    elif not can(user, "save_budgets"):
                        st.error("Este perfil não pode salvar orçamentos.")
                    else:
                        try:
                            save_budget(user, name, available[modality], display_results[modality])
                            st.success("Orçamento adicionado.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))
            else:
                st.info("Atualize um orçamento para poder adicioná-lo aqui.")

        if mode=="session":
            st.caption("No acesso compartilhado de demonstração, os orçamentos ficam somente nesta sessão.")
        elif mode=="sqlite":
            st.caption(":material/verified_user: Projetos preservados entre seus acessos.")

        search = st.text_input("Buscar na carteira", placeholder="Buscar projeto ou modalidade",
            key="budget_search", label_visibility="collapsed")
        normalized_search = search.strip().casefold()
        filtered = [row for row in saved if not normalized_search or normalized_search in
            f'{row.get("name", "")} {row.get("modality", "")}'.casefold()]
        st.markdown(f'<div class="saved-count"><span>PROJETOS SALVOS</span><b>{len(filtered)}</b></div>',
            unsafe_allow_html=True)
        if filtered:
            st.caption(":material/touch_app: Clique no nome de um projeto para abrir suas informações.")
        if not saved:
            with st.container(key="empty_budget_collection"):
                st.markdown("### Sua carteira está vazia")
                st.caption("Calcule um cenário e use “Adicionar projeto” para começar.")
        elif not filtered:
            with st.container(key="empty_budget_search"):
                st.markdown("### Nenhum projeto encontrado")
                st.caption("Tente buscar por outro nome ou modalidade.")
        for row in filtered[:20]:
            result=row.get("result_json",{})
            if isinstance(result,str):
                try:
                    result=json.loads(result)
                except (TypeError,ValueError):result={}
            scenario=result.get("scenario",{}) if isinstance(result,dict) else {}
            budget_id = str(row.get("id", ""))
            distance = _distance_label(result, scenario)
            per_km = _per_km(result, row, scenario)
            modality = str(row.get("modality", "Modalidade"))
            modality_initials, modality_class = _modality_visual(modality)
            project_name = str(row.get("name", "Orçamento"))
            with st.container(key=f"saved_budget_card_{budget_id}"):
                st.markdown(
                    '<div class="project-card-heading">'
                    f'<span class="project-mark {modality_class}">{modality_initials}</span>'
                    f'<span class="budget-type">{escape(modality)}</span>'
                    '</div>', unsafe_allow_html=True,
                )
                if st.button(project_name, icon=":material/arrow_forward:",
                    key=f"open_project_{budget_id}", use_container_width=True,
                    help="Abrir informações e opções deste projeto"):
                    _edit_project_dialog(user, row, result)
                st.caption(f":material/calendar_today: {_date_label(row.get('created_at'))}")
                st.markdown(f'<div class="budget-total-label">CUSTO TOTAL</div>'
                    f'<div class="budget-total">{currency(float(row.get("total", 0)))}</div>',
                    unsafe_allow_html=True)
                if per_km is not None:
                    st.markdown(f'<div class="budget-per-km">{currency(float(per_km))} '
                        '<span>por km</span></div>', unsafe_allow_html=True)
