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
    st.session_state.pop(f"edit_budget_{budget_id}", None)
    st.session_state.pop(f"delete_budget_{budget_id}", None)


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
            st.markdown('<span class="sidebar-eyebrow">PORTFÓLIO</span>', unsafe_allow_html=True)
            st.markdown("## Meus Orçamentos")
            st.caption("Seus estudos ferroviários, organizados em um só lugar.")
        display_results = st.session_state.get("display_results", {})
        available = {key: MODALITY_LABELS[key] for key in MODALITY_LABELS if key in display_results}
        with st.container(border=True, key="new_budget_card"):
            st.markdown("**Novo orçamento**")
            if available:
                modality = st.selectbox("Cenário calculado", list(available),
                    format_func=available.get, key="saved_budget_modality")
                name = st.text_input("Nome do orçamento", placeholder="Ex.: Linha Leste · Estudo inicial",
                    key="saved_budget_name", max_chars=80)
                if st.button("Adicionar aos meus orçamentos", icon=":material/add:", type="primary",
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

        mode=storage_mode(user)
        if mode=="session":
            st.caption("No acesso compartilhado de demonstração, os orçamentos ficam somente nesta sessão.")
        elif mode=="sqlite":
            st.caption("Orçamentos preservados entre logout e login neste servidor.")
        try:
            saved = list_budgets(user.user_id,user)
        except RuntimeError as exc:
            st.error(str(exc))
            saved = []
        st.markdown(f'<div class="saved-count"><b>{len(saved)}</b> projeto(s) salvo(s)</div>',
            unsafe_allow_html=True)
        if not saved:
            with st.container(key="empty_budget_collection"):
                st.markdown(":material/folder_open:")
                st.caption("Nenhum orçamento adicionado ainda.")
        for row in saved[:20]:
            result=row.get("result_json",{})
            if isinstance(result,str):
                try:
                    result=json.loads(result)
                except (TypeError,ValueError):result={}
            scenario=result.get("scenario",{}) if isinstance(result,dict) else {}
            budget_id = str(row.get("id", ""))
            distance = _distance_label(result, scenario)
            per_km = _per_km(result, row, scenario)
            with st.container(border=True, key=f"saved_budget_card_{budget_id}"):
                st.markdown(f'<span class="budget-type">{escape(str(row.get("modality", "Modalidade")))}</span>',
                    unsafe_allow_html=True)
                st.markdown(f"### {escape(str(row.get('name','Orçamento')))}")
                st.caption(f":material/calendar_today: {_date_label(row.get('created_at'))}")
                st.markdown(f'<div class="budget-total-label">CUSTO TOTAL</div>'
                    f'<div class="budget-total">{currency(float(row.get("total",0)))}</div>',
                    unsafe_allow_html=True)
                if per_km is not None:
                    st.markdown(f'<div class="budget-per-km">{currency(float(per_km))} <span>por km</span></div>',
                        unsafe_allow_html=True)
                with st.expander("Ver informações", icon=":material/info:"):
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

                edit_key = f"edit_budget_{budget_id}"
                delete_key = f"delete_budget_{budget_id}"
                action_edit, action_delete = st.columns(2)
                if action_edit.button("Editar", icon=":material/edit:", key=f"edit_action_{budget_id}",
                    use_container_width=True):
                    st.session_state[edit_key] = True
                    st.session_state[delete_key] = False
                    st.rerun()
                if action_delete.button("Excluir", icon=":material/delete:", key=f"delete_action_{budget_id}",
                    use_container_width=True):
                    st.session_state[delete_key] = True
                    st.session_state[edit_key] = False
                    st.rerun()

                if st.session_state.get(edit_key):
                    with st.form(f"edit_form_{budget_id}", border=False):
                        new_name = st.text_input("Nome do projeto", value=row.get("name", ""),
                            max_chars=80, key=f"edit_name_{budget_id}")
                        save_column, cancel_column = st.columns(2)
                        save_edit = save_column.form_submit_button("Salvar", type="primary",
                            icon=":material/check:", use_container_width=True)
                        cancel_edit = cancel_column.form_submit_button("Cancelar",
                            use_container_width=True)
                    if save_edit:
                        try:
                            update_budget(user, budget_id, new_name)
                            _close_budget_actions(budget_id)
                            st.toast("Projeto atualizado.", icon=":material/check_circle:")
                            st.rerun()
                        except (RuntimeError, ValueError, LookupError) as exc:
                            st.error(str(exc))
                    if cancel_edit:
                        _close_budget_actions(budget_id)
                        st.rerun()

                if st.session_state.get(delete_key):
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
