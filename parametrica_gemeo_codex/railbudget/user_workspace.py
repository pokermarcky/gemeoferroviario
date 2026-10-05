"""Área lateral do usuário e coleção pessoal de orçamentos."""
from datetime import datetime

import streamlit as st

from railbudget.auth import can, logout
from railbudget.budget_store import list_budgets, persistent_storage_enabled, save_budget
from railbudget.exporters import currency


ROLE_LABELS = {"root": "Administrador root", "user": "Usuário", "test": "Demonstração"}
MODALITY_LABELS = {"main": "Ferrovia de passageiro", "cargo": "Ferrovia de carga"}


def _date_label(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y · %H:%M")
    except (TypeError, ValueError):
        return "Data não informada"


def render_user_sidebar(user):
    with st.sidebar:
        with st.container(key="user_profile_card"):
            st.markdown('<span class="sidebar-eyebrow">SEU ESPAÇO</span>', unsafe_allow_html=True)
            st.markdown(f"### {user.name}")
            st.caption(user.email if user.role != "test" else "Acesso para conhecer o sistema")
            st.markdown(f'<span class="role-badge role-{user.role}">{ROLE_LABELS[user.role]}</span>', unsafe_allow_html=True)
            if st.button("Sair", icon=":material/logout:", key="logout", use_container_width=True):
                logout(user)

        st.markdown("## Meus Orçamentos")
        st.caption("Nomeie e guarde os cenários associados ao seu acesso.")
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

        if not persistent_storage_enabled():
            st.caption("Armazenamento temporário nesta implantação. A persistência permanente será ativada na conexão segura da base.")
        try:
            saved = list_budgets(user.user_id)
        except RuntimeError as exc:
            st.error(str(exc))
            saved = []
        st.markdown(f"**Salvos · {len(saved)}**")
        if not saved:
            st.caption("Nenhum orçamento adicionado ainda.")
        for row in saved[:20]:
            with st.container(border=True):
                st.markdown(f"**{row.get('name', 'Orçamento')}**")
                st.caption(f"{row.get('modality', 'Modalidade')} · {_date_label(row.get('created_at'))}")
                st.markdown(currency(float(row.get("total", 0))))
