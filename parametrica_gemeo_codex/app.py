from pathlib import Path
from hashlib import sha256
import re
import pandas as pd
import streamlit as st
from railbudget.engine import Scenario, load_model, calculate, select_groups
from railbudget.exporters import make_excel, currency, br, caption
from railbudget.interface import apply_theme
from railbudget.static_scene_v2 import static_header_v2
from railbudget.freight import calculate_freight
from railbudget.underground import calculate_underground
from railbudget.reference_data import (SOURCES, KINDS, parse_reference, apply_reference_bases,
    embedded_inventory, normalized_excel)
from railbudget.auth import budget_download_limit, can, can_download_budget, require_user
from railbudget.user_workspace import render_user_sidebar

ROOT=Path(__file__).resolve().parent

st.set_page_config(page_title='railparametric | Parametric Rails',page_icon=':material/train:',layout='wide')
apply_theme()
current_user=require_user()
static_header_v2()
@st.cache_data(ttl=300,max_entries=2)
def data(version):return load_model(ROOT)

@st.cache_data(ttl=900,max_entries=8,show_spinner=False)
def excel_orcamento(result,price_catalog):return make_excel(result,{**price_catalog,**result.get('custom_prices',{})})

version=(ROOT/'data/catalog.sqlite').stat().st_mtime_ns,(ROOT/'config/rules.json').stat().st_mtime_ns
rules,base_catalog=data(version)
st.session_state.setdefault('results',{})
st.session_state.setdefault('display_results',{})
st.session_state.setdefault('reference_bases',{})
enabled_bases=dict(st.session_state.reference_bases)
reference_signature=tuple(sorted((source,kind,base.digest,base.period)
    for (source,kind),base in enabled_bases.items()))
if st.session_state.get('active_reference_signature') not in (None,reference_signature):
    st.session_state.results={}
    st.session_state.referencia_inicial_carregada=False
st.session_state.active_reference_signature=reference_signature
catalog,linked_uploads=apply_reference_bases(base_catalog,enabled_bases)
if not st.session_state.get('referencia_inicial_carregada'):
    st.session_state.results.setdefault('main',calculate(Scenario(),rules,catalog))
    st.session_state.referencia_inicial_carregada=True


def set_service_selection(key,indices):
    """Aplica uma seleção em lote antes de os checkboxes dos serviços serem criados."""
    action=st.session_state.get(key+'_service_bulk')
    if action not in ('Marcar todas','Desmarcar todas'):return
    checked=action=='Marcar todas'
    for index in indices:st.session_state[f'{key}_grupo_{index}']=checked


def clear_service_selection(key):
    """Volta a seleção rápida ao estado neutro após um ajuste manual."""
    st.session_state[key+'_service_bulk']=None

def budget_controls(key,freight=False):
    st.subheader('Configure sua ferrovia')
    st.caption('Comece pelo traçado. Depois, escolha os serviços e confira o resultado abaixo.')
    with st.container(border=True):
        st.markdown('**1. Traçado e características**')
        general=st.columns(3 if freight else 4)
        with general[0]:
            if freight:st.caption('Base de referência: SIEC • via em lastro / AMV nº 14')
            else:st.selectbox('Modelo de referência',['SIEC • lastro / AMV nº 14'],key=key+'_profile')
        with general[1]:
            km=st.number_input('Extensão do corredor (km)',min_value=0.01,max_value=10000.0,value=1.0,step=0.1,format='%.3f',key=key+'_km')
        with general[2]:
            if freight:st.caption('Implantação: superfície · via em lastro')
            configuration='Superfície' if freight else st.selectbox('Configuração',['Superfície','Elevado','Subterrâneo'],key=key+'_configuration')
        if freight:
            lines=st.selectbox('Via',[1,2],format_func=lambda n:'Simples' if n==1 else 'Dupla',key=key+'_lines')
            axle=st.selectbox('Alternativa de carga por eixo (t/eixo)',[20,25],index=1,key=key+'_axle',help='20 t: TR57; 25 t: UIC60. Alternativas de orçamento, sujeitas a projeto estrutural.')
            st.caption('Via de superfície com trilhos e montagem específicos para a alternativa selecionada. Verifique a capacidade em projeto.')
        else:
            with general[3]:
                lines=st.selectbox('Via',[1,2],format_func=lambda n:'Simples' if n==1 else 'Dupla',key=key+'_lines')

    subterraneo=configuration=='Subterrâneo'
    if subterraneo:
        st.warning('Estimativa subterrânea preliminar por equivalência SIEC. Premissa inicial: um tubo circular de 10,00 m por via. O resultado não substitui projeto geotécnico, estrutural, hidráulico, de ventilação ou de segurança.')

    st.markdown('**2. Serviços incluídos**')
    st.caption('Marque somente os grupos que fazem parte do escopo do projeto.')
    service_indices=list(range(len(rules['groups'][:8] if freight else rules['groups'])))
    with st.container(border=True,key=key+'_service_toolbar'):
        toolbar=st.columns([1.15,2.35],vertical_alignment='center')
        with toolbar[0]:
            st.markdown('**Seleção rápida**')
            st.caption('Aplique a todos e refine abaixo.')
        with toolbar[1]:
            st.segmented_control('Selecionar serviços',['Marcar todas','Desmarcar todas'],
                default=None,key=key+'_service_bulk',label_visibility='collapsed',
                on_change=set_service_selection,args=(key,service_indices))
    chosen=[]
    enabled={}
    drainage=st.session_state.get(key+'_drainage','Reforçada')
    fence=st.session_state.get(key+'_fence','Cerca')
    amvs=st.session_state.get(key+'_amvs',0 if freight else 1)
    detection=st.session_state.get(key+'_detection','Circuito de via')
    trainsets=st.session_state.get(key+'_trainsets',1)
    for i,g in enumerate(rules['groups'][:8] if freight else rules['groups']):
        if i%3==0:group_columns=st.columns(3)
        with group_columns[i%len(group_columns)]:
            with st.container(border=True):
                label=('Banco de dutos' if configuration=='Superfície' else 'Canaletas e passa-fios') if i==5 else ('Túnel e via permanente' if subterraneo and i==0 else 'Segurança e ventilação' if subterraneo and i==3 else g.split(' ',1)[1])
                checkbox_key=f'{key}_grupo_{i}'
                st.session_state.setdefault(checkbox_key,i not in (4,5,6,7) if freight else True)
                enabled[i]=st.checkbox(label,key=checkbox_key,persist_state='session',
                    on_change=clear_service_selection,args=(key,))
                if enabled[i]:
                    if i==0:st.caption('Via '+configuration.lower()+' • '+('simples' if lines==1 else 'dupla'))
                    elif i==1:st.caption('Levantamentos e acompanhamento topográfico.')
                    elif i==2:drainage=st.selectbox('Tipo de drenagem',['Normal','Reforçada','Complexa'],index=['Normal','Reforçada','Complexa'].index(drainage),key=key+'_drainage')
                    elif i==3:
                        if subterraneo:
                            fence='Cerca';st.caption('Provisões iniciais de combate a incêndio, alarme, iluminação e ventilação.')
                        else:fence=st.selectbox('Tipo de vedação',['Cerca','Muro'],index=['Cerca','Muro'].index(fence if fence in ('Cerca','Muro') else 'Cerca'),key=key+'_fence')
                    elif i==4:amvs=st.number_input('Quantidade total de AMVs',min_value=0,max_value=100000,value=int(amvs),step=1,key=key+'_amvs',help='Total no corredor, distribuído entre as linhas.')
                    elif i==5:st.caption('Banco subterrâneo de seis dutos.' if configuration=='Superfície' else 'Canaletas e passa-fios embutidos no tabuleiro elevado.' if configuration=='Elevado' else 'Duas canaletas técnicas longitudinais por tubo.')
                    elif i==6:st.caption('Rede aérea de alimentação e seus suportes.')
                    elif i==7:detection=st.selectbox('Detecção de trens',['Circuito de via','Contador de eixos'],index=['Circuito de via','Contador de eixos'].index(detection),key=key+'_detection')
                    elif i==8:trainsets=st.number_input('Composições de 8 carros',min_value=0,max_value=10000,value=int(trainsets),step=1,key=key+'_trainsets',help='Custo por composição; o indicador por km é um rateio.')
                else:
                    st.caption('Não incluído no total.')
            if enabled[i]:
                chosen.append(g)
    if freight:
        with st.container(border=True):
            st.markdown('**Frota e instalações de carga**')
            fleet=st.columns(2)
            with fleet[0]:locomotives=st.number_input('Locomotivas equivalentes (un/km)',min_value=0.0,max_value=10000.0,value=0.0,step=0.01,format='%.2f',key=key+'_locomotives')
            with fleet[1]:wagons=st.number_input('Vagões equivalentes (un/km)',min_value=0.0,max_value=100000.0,value=0.0,step=0.01,format='%.2f',key=key+'_wagons')
            st.caption('A base SIEC contém custos horários de operação de locomotiva e vagões, mas não preços de aquisição. As quantidades acima ficam registradas como escopo pendente e não entram no total.')
            st.caption('Pátios, terminais, pontes, passagens em nível e interfaces de carga também exigem orçamento próprio.')
    with st.container(border=True,key=key+'_bdi_panel'):
        st.markdown('**3. BDI e condições do orçamento**')
        apply_bdi=st.checkbox('Aplicar BDI',value=True,key=key+'_aplicar_bdi',persist_state='session')
        percentage=st.number_input('BDI personalizado (%)',min_value=0.0,max_value=100.0,
            value=26.30,step=0.10,format='%.2f',
            key=key+'_bdi_personalizado',persist_state='session')
        st.caption('Sugestão inicial: 26,30%. O usuário pode ajustar o percentual; ele é aplicado uma única vez ao total e aos subtotais.')
    calculate_now=st.button('Atualizar orçamento',key=key+'_calculate',type='primary',
        icon=':material/calculate:')
    reference_refresh=st.session_state.get(key+'_reference_signature')!=reference_signature
    if calculate_now or reference_refresh or key not in st.session_state.results:
        try:
            p=Scenario(km=km,configuration=configuration,lines=lines,drainage=drainage,
                fence=fence if enabled[3] else 'Nenhuma',amvs=int(amvs) if enabled[4] else 0,
                ducts=enabled[5],topography=enabled[1],overhead=enabled[6],signaling=enabled[7],
                detection=detection,rolling_stock=False if freight else enabled[8],trainsets=0 if freight else int(trainsets) if enabled[8] else 0,
                profile='siec',bdi=percentage/100)
            result=calculate_freight(p,axle,rules,catalog) if freight else calculate_underground(p,rules,catalog) if subterraneo else calculate(p,rules,catalog)
            if freight:
                result['scenario'].update(locomotives=float(locomotives),wagons=float(wagons))
                result['warnings'].append('Frota fora do total: '+br(locomotives,2)+' locomotiva(s) equivalente(s)/km, '+br(wagons,2)+' vagão(ões) equivalente(s)/km. Pátios, terminais, pontes e passagens em nível também não foram orçados.')
            st.session_state.results[key]=result
            st.session_state[key+'_reference_signature']=reference_signature
            st.session_state[key+'_calculated_inputs']=(km,configuration,lines,drainage,fence,amvs,detection,trainsets if not freight else 0,
                () if not freight else (axle,locomotives,wagons))
        except (ValueError,KeyError,ZeroDivisionError) as exc:
            st.session_state.results.pop(key,None);st.error(str(exc))
    rate=percentage/100 if apply_bdi else 0.0
    current_inputs=(km,configuration,lines,drainage,fence,amvs,detection,trainsets if not freight else 0,
        () if not freight else (axle,locomotives,wagons))
    st.session_state.setdefault(key+'_calculated_inputs',current_inputs)
    stale=key+'_calculated_inputs' in st.session_state and st.session_state[key+'_calculated_inputs']!=current_inputs
    if stale:
        st.info('Você alterou o cenário. Selecione Atualizar orçamento para conferir os novos valores.')
    return chosen,rate,stale


def display_table(frame, monetary=(), height=None):
    """Tabela de leitura com padrão monetário brasileiro e hierarquia visual consistente."""
    shown=frame.copy()
    for column in monetary:
        if column in shown:
            shown[column]=shown[column].map(lambda value: currency(value) if pd.notna(value) else '—')
    options=dict(hide_index=True,width='stretch',row_height=38,
        column_config={column:st.column_config.TextColumn(width='medium') for column in monetary})
    if height is not None:options['height']=height
    st.dataframe(shown,**options)


def result_group_label(group,result):
    """Traduz o nome histórico do agrupamento para a solução exibida."""
    label=group.split(' ',1)[1]
    if result['scenario']['configuration']=='Subterrâneo':
        return {'Via permanente':'Túnel e via permanente','Vedação':'Segurança e ventilação',
                'Infraestrutura de cabos':'Canaletas e passa-fios'}.get(label,label)
    return label


def render_result(r,key,modality='passageiro'):
    st.session_state.display_results[key]=r
    with st.container(key='result_header_'+key):
        st.markdown('## Resultado do orçamento')
        st.caption('Síntese financeira do cenário e do escopo selecionado.')
    if modality=='carga':
        st.info('Infraestrutura de carga com alternativa TR57 ou UIC60 da base SIEC. A verificação estrutural da via, frota, pátios, terminais e obras especiais requer orçamento de projeto.')
    st.caption('Cenário calculado: '+caption(r))
    with st.container(key='result_kpis_'+key):
        result_columns=st.columns(3,gap='medium')
        result_columns[0].metric('Total com BDI' if r['scenario']['bdi'] else 'Total sem BDI',currency(r['total']),border=True)
        result_columns[1].metric('Por km de corredor',currency(r['per_km']),border=True)
        result_columns[2].metric('Por km de linha',currency(r['per_line_km']),border=True)
    financial_caption=f"Custo direto: {currency(r['direct'])} | BDI aplicado: {br(r['scenario']['bdi']*100,6)}% | Acréscimo de BDI: {currency(r['bdi_amount'])}"
    st.caption(financial_caption.replace('$',r'\$'))
    columns={'eap':'EAP','group':'Grupo','code':'Código','source':'Fonte','label':'Aplicação','description':'Descrição','unit':'Unidade','quantity':'Quantidade','unit_cost':'Custo unitário (R$)','total':'Custo total (R$)','date':'Data-base'}
    frame=pd.DataFrame(r['items'])[list(columns)].rename(columns=columns) if r['items'] else pd.DataFrame(columns=columns.values())
    summary_tab,detail_tab=st.tabs(['Resumo geral','Detalhamento por grupo'])
    with summary_tab:
        st.caption('Visão consolidada do total selecionado. Consulte o detalhamento para conferir cada serviço, quantidade, código, fonte e preço.')
        st.subheader('Participação por grupo')
        group_frame=pd.DataFrame([{'Grupo':result_group_label(g,r),'Custo direto (R$)':v} for g,v in r['groups'].items()])
        summary_columns=st.columns([1,1.15],gap='large')
        with summary_columns[0]:
            display_table(group_frame,monetary=('Custo direto (R$)',),height=320)
        with summary_columns[1]:
            st.bar_chart(group_frame,x='Grupo',y='Custo direto (R$)',horizontal=True,color='#60998e',height=320)
    with detail_tab:
        with st.expander('EAP completa · serviços e preços',expanded=False):
            frame['Quantidade']=frame['Quantidade'].map(lambda value:br(value,6))
            display_table(frame,monetary=('Custo unitário (R$)','Custo total (R$)'),height=530)
        st.caption('Cada cartão mostra custo direto, valor com BDI e participação no total. Abra a composição para conferir os itens.')
        for group in r['scope_summary']:
            if not group['selected']:continue
            if modality=='carga' and group['group'].startswith('9 '):continue
            with st.container(border=True):
                st.subheader(result_group_label(group['group'],r))
                if group['group'].startswith('3 '):st.caption('Drenagem '+r['scenario']['drainage'].lower())
                if group['group'].startswith('4 '):st.caption('Segurança e ventilação preliminares' if r['scenario']['configuration']=='Subterrâneo' else 'Vedação: '+r['scenario']['fence'].lower())
                if group['group'].startswith('6 '):st.caption('Banco subterrâneo de seis dutos' if r['scenario']['configuration']=='Superfície' else 'Canaletas e passa-fios embutidos no tabuleiro elevado' if r['scenario']['configuration']=='Elevado' else 'Canaletas técnicas longitudinais do túnel')
                if group['group'].startswith('8 '):st.caption('Detecção: '+r['scenario']['detection'].lower())
                if group['group'].startswith('9 '):st.caption(f"Frota: {r['scenario']['trainsets']} composição(ões) de 8 carros; custo por composição e rateio por km atendido.")
                if not group['direct']:st.info('Sem serviços neste cenário. Verifique os parâmetros do formulário para incluir este grupo.')
                with st.container(horizontal=True):
                    st.metric('Subtotal direto',currency(group['direct']))
                    st.metric('Subtotal com BDI' if r['scenario']['bdi'] else 'Subtotal sem BDI',currency(group['total']))
                    st.metric('Por km com BDI' if r['scenario']['bdi'] else 'Por km sem BDI',currency(group['per_km_with_bdi']))
                    st.metric('Participação no total selecionado',br(group['share'],2)+'%')
                rows=[x for x in r['items'] if x['group']==group['group']]
                if rows:
                    with st.expander('Ver composição e preços de '+result_group_label(group['group'],r),expanded=False):
                        detail=pd.DataFrame(rows)[['code','source','label','unit','quantity','unit_cost','total']].rename(columns={
                            'code':'Código','source':'Fonte','label':'Serviço','unit':'Unidade','quantity':'Quantidade',
                            'unit_cost':'Custo unitário (R$)','total':'Custo total (R$)'})
                        detail['Quantidade']=detail['Quantidade'].map(lambda value:br(value,6))
                        display_table(detail,monetary=('Custo unitário (R$)','Custo total (R$)'))
    if not r['items']:
        st.info('Nenhum serviço incluído no total. Selecione ao menos um grupo com serviços para gerar o orçamento em Excel.')
        return
    used_catalog={item['price_key']:catalog[item['price_key']] for item in r['items'] if item['price_key'] in catalog}
    downloads_used=int(st.session_state.get('trial_excel_downloads',0))
    if can_download_budget(current_user,downloads_used):
        def register_trial_download():
            if budget_download_limit(current_user) is not None:
                st.session_state.trial_excel_downloads=downloads_used+1
        st.download_button('Baixar orçamento em Excel',excel_orcamento(r,used_catalog),
            file_name='orcamento_ferrovia_'+modality+'.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key=key+'_excel',icon=':material/download:',on_click=register_trial_download)
        if budget_download_limit(current_user) is not None:
            st.caption('Demonstração: este é o único download de Excel disponível nesta sessão.')
    elif budget_download_limit(current_user) is not None:
        st.info('O download de demonstração já foi utilizado nesta sessão.')
    else:
        st.info('O perfil de demonstração permite conhecer e calcular, mas não gera a planilha Excel.')

def reference_card(source,kind):
    slot=(source,kind)
    embedded=embedded_inventory(base_catalog).get(slot)
    active=st.session_state.reference_bases.get(slot)
    with st.container(border=True):
        st.markdown(f'<span class="source-badge source-{source.lower()}">{source}</span> **{kind}**',unsafe_allow_html=True)
        if active:
            st.caption(f'Base ativa · {active.period or "data-base não informada"}')
            linked=linked_uploads.get(slot,0)
            st.markdown(f'**{active.count:,} itens** · {linked:,} vinculados ao orçamento'.replace(',','.'))
            st.caption(active.filename)
            if not linked:
                st.warning('A base está ativa para consulta, mas nenhum código com unidade compatível está vinculado ao orçamento atual.')
            preview=pd.DataFrame(active.records[:6]).rename(columns={'code':'Código','description':'Descrição','unit':'Unidade','price':'Preço','date':'Data-base'})
            with st.expander('Visualizar amostra',expanded=False):
                display_table(preview,monetary=('Preço',))
            if can(current_user,'download_excel'):
                st.download_button('Baixar tabela convertida',normalized_excel(active),
                    file_name=f'{source.lower()}_{kind.lower()}_{active.period.replace("/","-") or "normalizada"}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    key=f'normalized_{source}_{kind}',icon=':material/download:')
        elif embedded:
            periods=' · '.join(sorted(embedded['periods']))
            st.caption(f'Base embarcada · {periods}')
            st.markdown(f'**{embedded["count"]:,} itens** disponíveis'.replace(',','.'))
        else:
            st.caption('Nenhuma tabela ativa')
            st.markdown('**Aguardando uma base válida**')
        if not can(current_user,'manage_bases'):
            st.info('Consulta liberada. A substituição da data-base e o upload de planilhas são exclusivos do administrador root.')
            return
        upload=st.file_uploader('Substituir tabela atual',type=['csv','xls','xlsx','xlsm'],key=f'upload_{source}_{kind}',
            help='Aceita CSV, XLS, XLSX e XLSM. O sistema procura automaticamente o cabeçalho em todas as abas e converte Código, Descrição, Unidade e Preço para o padrão interno.')
        if upload and upload.size>200*1024*1024:
            st.error('Arquivo acima de 200 MB. Divida a tabela antes de enviar.');return
        if upload:
            st.caption('O novo arquivo substituirá integralmente a versão ativa nesta sessão.')
            period=st.text_input('Nova data-base',placeholder='MM/AAAA',key=f'period_{source}_{kind}',
                help='Campo obrigatório. Exemplo: 08/2026.')
            if not re.fullmatch(r'(0[1-9]|1[0-2])/\d{4}',period.strip()):
                st.info('Digite a nova data-base no formato MM/AAAA para validar e ativar a tabela.')
                return
            raw=upload.getvalue();digest=sha256(raw).hexdigest()
            if not active or digest!=active.digest or period.strip()!=active.period:
                try:
                    parsed=parse_reference(raw,upload.name,source,kind,period)
                    _,prospective_links=apply_reference_bases(base_catalog,{slot:parsed})
                    matched=prospective_links.get(slot,0)
                    st.session_state.reference_bases[slot]=parsed
                    st.session_state.results={}
                    st.session_state.referencia_inicial_carregada=False
                    st.session_state[f'upload_notice_{source}_{kind}']=(parsed.count,matched)
                    st.rerun()
                except (ValueError,KeyError,ImportError,UnicodeError,TypeError) as exc:
                    st.error('Tabela não ativada: '+str(exc))
        notice=st.session_state.pop(f'upload_notice_{source}_{kind}',None)
        if notice:
            count,matched=notice
            if matched:
                st.success(f'{count:,} itens validados; {matched:,} preço(s) vinculado(s). Os orçamentos foram recalculados automaticamente.'.replace(',','.'))
            else:
                st.warning(f'{count:,} itens validados, mas nenhum código com unidade compatível corresponde aos itens usados no orçamento.'.replace(',','.'))


budgets_tab,reference_tab=st.tabs(['ORÇAMENTOS','BASES DE REFERÊNCIA'],key='workspace')
with budgets_tab:
    st.caption('Escolha uma modalidade para configurar o corredor e revisar o orçamento.')
    passageiro,carga,vlt,shortline=st.tabs([
        'Ferrovia de passageiro','Ferrovia de carga','VLT - Veículo leve sobre Trilho','Shortline'])

    with passageiro:
        chosen,rate,subterraneo=budget_controls('main')
        if not subterraneo:
            r=st.session_state.results.get('main')
            if r:render_result(select_groups(r,chosen,bdi_rate=rate),'main')
            else:st.info('Revise as opções acima e selecione Atualizar orçamento.')

    with carga:
        st.caption('Infraestrutura de superfície com referências SIEC. Frota, pátios e obras especiais exigem orçamento específico.')
        cargo_chosen,cargo_rate,cargo_blocked=budget_controls('cargo',freight=True)
        if not cargo_blocked:
            cargo_result=st.session_state.results.get('cargo')
            if cargo_result:render_result(select_groups(cargo_result,cargo_chosen,bdi_rate=cargo_rate),'cargo',modality='carga')
            else:st.info('Confira as premissas da ferrovia de carga para gerar o orçamento.')

    with vlt:
        pass

    with shortline:
        pass

with reference_tab:
    with st.container(key='reference_heading'):
        st.markdown('## Bases de referência')
        st.caption('Carregue a versão mais recente de cada fonte e escolha se a tabela contém insumos ou serviços.')
    status=st.columns(2)
    status[0].metric('Tabelas enviadas',len(enabled_bases),border=True)
    status[1].metric('Códigos atualizados',sum(linked_uploads.values()),border=True)
    st.info('Cada fonte e tipo mantém somente a versão mais recente nesta sessão. Uma nova tabela substitui a anterior e recalcula automaticamente os orçamentos quando houver códigos vinculados.')
    source_tabs=st.tabs(list(SOURCES))
    for source,source_tab in zip(SOURCES,source_tabs):
        with source_tab:
            default_kind='Serviços' if source=='SIEC' else 'Insumos'
            kind=st.segmented_control('Conteúdo da tabela',list(KINDS),default=default_kind,
                key=f'reference_kind_{source}')
            reference_card(source,kind)

render_user_sidebar(current_user)
