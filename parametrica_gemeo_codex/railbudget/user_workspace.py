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


def _close_budget_actions(budget_id):
    st.session_state.pop(f"delete_budget_{budget_id}", None)


def _modality_visual(modality):
    label = str(modality).casefold()
    if "vlt" in label:
        return "VLT", "project-vlt"
    if "carga" in label:
        return "CG", "project-cargo"
    return "PS", "project-passenger"


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
            st.caption(":material/touch_app: Clique em um projeto para abrir seus dados e editar.")
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
                with st.expander(project_name, icon=":material/train:"):
                    st.markdown(
                        '<div class="project-card-heading">'
                        f'<span class="project-mark {modality_class}">{modality_initials}</span>'
                        f'<span class="budget-type">{escape(modality)}</span>'
                        '</div>', unsafe_allow_html=True,
                    )
                    st.caption(f":material/calendar_today: {_date_label(row.get('created_at'))}")
                    st.markdown(f'<div class="budget-total-label">CUSTO TOTAL</div>'
                        f'<div class="budget-total">{currency(float(row.get("total",0)))}</div>',
                        unsafe_allow_html=True)
                    if per_km is not None:
                        st.markdown(
                            f'<div class="budget-per-km">{currency(float(per_km))} '
                            '<span>por km</span></div>', unsafe_allow_html=True,
                        )
                    st.markdown('<div class="project-section-title">DADOS DO PROJETO</div>',
                        unsafe_allow_html=True)
                    if distance:
                        st.markdown(f"**Extensão do corredor:** {distance}")
                    if isinstance(result,dict) and result.get("line_km") is not None:
                        line_km=f"{float(result['line_km']):,.2f}".replace(",","X").replace(".",",").replace("X",".")
                        st.markdown(f"**Extensão de linha:** {line_km} km")
                    if isinstance(result,dict) and result.get("reference_period"):
                        st.markdown(f"**Data-base:** {result['reference_period']}")
                    if scenario.get("configuration"):
                        st.markdown(f"**Implantação:** {scenario['configuration']}")
                    if scenario.get("lines"):
                        st.markdown(f"**Via:** {'Simples' if int(scenario['lines'])==1 else 'Dupla'}")
                    if scenario.get("bdi") is not None:
                        st.markdown(f"**BDI:** {float(scenario['bdi'])*100:.2f}%".replace(".",","))
                    st.markdown('<div class="project-section-title">EDITAR PROJETO</div>',
                        unsafe_allow_html=True)
                    with st.form(f"edit_form_{budget_id}", border=False):
                        new_name = st.text_input("Nome do projeto", value=row.get("name", ""),
                            max_chars=80, key=f"edit_name_{budget_id}")
                        save_edit = st.form_submit_button("Salvar alterações", type="primary",
                            icon=":material/check:", use_container_width=True)
                    if save_edit:
                        try:
                            update_budget(user, budget_id, new_name)
                            _close_budget_actions(budget_id)
                            st.toast("Projeto atualizado.", icon=":material/check_circle:")
                            st.rerun()
                        except (RuntimeError, ValueError, LookupError) as exc:
                            st.error(str(exc))
                    delete_key = f"delete_budget_{budget_id}"
                    if not st.session_state.get(delete_key):
                        if st.button("Excluir projeto", icon=":material/delete:",
                            key=f"delete_action_{budget_id}", use_container_width=True):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        with st.container(key=f"delete_confirmation_{budget_id}"):
                            st.warning("Excluir este projeto? Esta ação não poderá ser desfeita.")
                            confirm_column, cancel_column = st.columns(2)
                            confirm = confirm_column.button("Sim, excluir", icon=":material/delete_forever:",
                                key=f"confirm_delete_{budget_id}", use_container_width=True)
                            cancel = cancel_column.button("Cancelar", key=f"cancel_delete_{budget_id}",
                                use_container_width=True)
                        if confirm:
                            try:
                                delete_budget(user, budget_id)
                                _close_budget_actions(budget_id)
                                st.toast("Projeto excluído.", icon=":material/delete:")
                                st.rerun()
                            except (RuntimeError, LookupError) as exc:
                                st.error(str(exc))
                        if cancel:
                            _close_budget_actions(budget_id)
                            st.rerun()
