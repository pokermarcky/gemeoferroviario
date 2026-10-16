from pathlib import Path
from hashlib import sha256
import re
import pandas as pd
import streamlit as st
from railbudget.engine import (Scenario, load_model, calculate, select_groups,
    FOUNDATION_OPTIONS, foundation_diameters, foundation_capacity)
from railbudget.elevated import (calculate_elevated, sensitivity, DECK_FACTORS, PIER_FACTORS,
    GEOTECH_FACTORS, METHOD_FACTORS, EXECUTION_FACTORS)
from railbudget.exporters import make_excel, currency, br, caption
from railbudget.interface import apply_theme
from railbudget.static_scene_v2 import static_header_v2
from railbudget.freight import calculate_freight
from railbudget.underground import calculate_underground
from railbudget.vlt import calculate_vlt, make_vlt_excel
from railbudget.reference_data import (SOURCES, KINDS, parse_reference, apply_reference_bases,
    embedded_inventory, normalized_excel)
from railbudget.auth import (budget_download_limit, can, can_download_budget, is_primary_root,
    primary_root_context, require_user)
from railbudget.budget_store import ensure_budget, update_budget
from railbudget.reference_store import load_reference_bases, save_reference_base
from railbudget.user_workspace import render_user_sidebar

ROOT=Path(__file__).resolve().parent

st.set_page_config(page_title='railparametric | Parametric Rails',page_icon=':material/train:',layout='wide')
apply_theme()
configured_root=primary_root_context()
if configured_root:
    try:ensure_budget(configured_root,'VLT Aeroporto - Castelão','VLT',calculate_vlt())
    except RuntimeError:pass
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
if 'reference_bases' not in st.session_state:
    st.session_state.reference_bases=load_reference_bases()
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

    elevated_parameters={};segment_records=[]
    if not freight and configuration=='Elevado':
        with st.container(border=True,key=key+'_elevated_panel'):
            st.markdown('**2. Parâmetros estruturais do elevado**')
            st.caption('Configure primeiro o trecho predominante. Abra somente os painéis necessários para detalhar soluções ou variações do corredor.')
            geometry=st.columns(4)
            height=geometry[0].number_input('Altura média dos pilares (m)',min_value=3.0,max_value=30.0,
                value=8.0,step=.5,format='%.2f',key=key+'_elevated_height')
            span=geometry[1].number_input('Distância entre pilares (m)',min_value=10.0,max_value=45.0,
                value=20.0,step=1.0,format='%.2f',key=key+'_elevated_span',
                help='Vão médio entre eixos dos apoios. O sistema calcula vãos e apoios inteiros por arredondamento para cima.')
            width_single=geometry[2].number_input('Largura do tabuleiro singelo (m)',min_value=4.0,max_value=12.0,
                value=7.0,step=.10,format='%.2f',key=key+'_elevated_width_single')
            width_double=geometry[3].number_input('Largura do tabuleiro duplo (m)',min_value=8.0,max_value=20.0,
                value=11.0,step=.10,format='%.2f',key=key+'_elevated_width_double')
            active_width=width_single if lines==1 else width_double
            st.caption(f'Largura aplicada neste cenário: **{br(active_width,2)} m** para via '+('singela.' if lines==1 else 'dupla.'))
            with st.expander('Fundações e condição urbana',expanded=False):
                foundation_columns=st.columns(3)
                interference=foundation_columns[0].selectbox('Interferência urbana',['Baixa','Média','Alta'],
                    index=1,key=key+'_elevated_urban_interference',
                    help='Orienta a escolha preliminar; não cria um adicional financeiro sem serviço correspondente na base.')
                foundation=foundation_columns[1].selectbox('Tipo de fundação profunda',list(FOUNDATION_OPTIONS),
                    key=key+'_elevated_foundation_type')
                diameters=foundation_diameters(foundation)
                default_diameter=.80 if foundation=='Hélice contínua' else .41
                diameter=foundation_columns[2].selectbox('Diâmetro da estaca (m)',diameters,
                    index=diameters.index(default_diameter),format_func=lambda value:f'{value:.2f} m'.replace('.',','),
                    key=key+'_elevated_pile_diameter_'+('helice' if foundation=='Hélice contínua' else 'raiz'))
                sizing=st.columns(2)
                foundation_depth=sizing[0].number_input('Profundidade média das estacas (m)',min_value=5.0,max_value=60.0,
                    value=20.0,step=1.0,format='%.2f',key=key+'_elevated_foundation_depth')
                piles=sizing[1].number_input('Estacas por apoio',min_value=2,max_value=16,value=4,step=1,
                    key=key+'_elevated_piles_per_support')
                nominal_capacity=foundation_capacity(foundation,float(diameter))*int(piles)
                st.caption('Capacidade nominal declarada na composição SIEC: '
                    f'**{br(foundation_capacity(foundation,float(diameter)),0)} tf por estaca** · '
                    f'**{br(nominal_capacity,0)} tf por apoio**. Referência inicial: 1.160 tf por apoio.')
                if nominal_capacity<1160:
                    st.warning('A capacidade nominal por apoio ficou abaixo da referência inicial. O valor pode ser simulado, mas exige revisão da quantidade de estacas, das cargas e da geotecnia.')
                if interference=='Alta':
                    st.info('Sugestão preliminar: estaca raiz tende a favorecer acessos restritos e locais sensíveis a vibração. Confirme capacidade e quantidade com sondagens e projeto.')
                else:
                    st.info('Sugestão preliminar: hélice contínua oferece boa produtividade quando há acesso para equipamento. Confirme diâmetro e profundidade por sondagens e cargas de projeto.')
                st.caption('As alternativas e os diâmetros exibidos possuem serviços correspondentes na base SIEC vigente. A escolha é orçamentária preliminar, não um dimensionamento.')
            with st.expander('Dividir o corredor em trechos homogêneos',expanded=False):
                use_segments=st.checkbox('Usar geometrias diferentes ao longo do corredor',
                    key=key+'_elevated_use_segments',help='Permite variar altura, vão e fundação sem duplicar canteiro e administração.')
                if use_segments:
                    editor_key=key+'_elevated_segments_editor'
                    if editor_key not in st.session_state:
                        st.session_state[editor_key]=pd.DataFrame([{'Trecho':'Trecho 1','Extensão (km)':float(km),
                            'Altura (m)':float(height),'Vão (m)':float(span),'Fundação':foundation,
                            'Diâmetro (m)':float(diameter),'Profundidade (m)':float(foundation_depth),
                            'Estacas/apoio':int(piles),'Interferência':interference}])
                    segments=st.data_editor(st.session_state[editor_key],num_rows='dynamic',hide_index=True,
                        width='stretch',key=editor_key+'_widget',column_config={
                            'Trecho':st.column_config.TextColumn('Trecho',width='medium',required=True),
                            'Extensão (km)':st.column_config.NumberColumn('Extensão (km)',min_value=.01,format='%.3f',required=True),
                            'Altura (m)':st.column_config.NumberColumn('Altura (m)',min_value=3.,max_value=30.,format='%.2f',required=True),
                            'Vão (m)':st.column_config.NumberColumn('Vão (m)',min_value=10.,max_value=45.,format='%.2f',required=True),
                            'Fundação':st.column_config.SelectboxColumn('Fundação',options=list(FOUNDATION_OPTIONS),required=True),
                            'Diâmetro (m)':st.column_config.NumberColumn('Diâmetro (m)',min_value=.16,max_value=.90,format='%.2f',required=True),
                            'Profundidade (m)':st.column_config.NumberColumn('Profundidade (m)',min_value=5.,max_value=60.,format='%.2f',required=True),
                            'Estacas/apoio':st.column_config.NumberColumn('Estacas/apoio',min_value=2,max_value=16,step=1,required=True),
                            'Interferência':st.column_config.SelectboxColumn('Interferência',options=['Baixa','Média','Alta'],required=True)})
                    segment_records=segments.to_dict('records')
                    segment_sum=sum(float(row.get('Extensão (km)',0) or 0) for row in segment_records)
                    delta=segment_sum-float(km)
                    message=f'Soma dos trechos: {br(segment_sum,3)} km · corredor: {br(km,3)} km'
                    if abs(delta)<=.001:st.success(message)
                    else:st.warning(message+' · ajuste a diferença de '+br(abs(delta),3)+' km.')
                else:
                    segment_records=[]
                    st.caption('Desativado: o corredor inteiro usará a geometria predominante informada acima.')
            with st.expander('Soluções estruturais e método executivo',expanded=False):
                technical=st.columns(2)
                deck_type=technical[0].selectbox('Tipologia do tabuleiro',list(DECK_FACTORS),key=key+'_elevated_deck_type')
                pier_type=technical[1].selectbox('Tipologia dos pilares',list(PIER_FACTORS),key=key+'_elevated_pier_type')
                geotech=technical[0].selectbox('Condição geotécnica',list(GEOTECH_FACTORS),index=1,key=key+'_elevated_geotech')
                method=technical[1].selectbox('Método executivo',list(METHOD_FACTORS),key=key+'_elevated_method')
                execution=st.selectbox('Condição de execução',list(EXECUTION_FACTORS),key=key+'_elevated_execution')
                factor_summary=(f'Tabuleiro ×{br(DECK_FACTORS[deck_type][0],2)} · Pilares ×{br(PIER_FACTORS[pier_type][0],2)} · '
                    f'Geotecnia ×{br(GEOTECH_FACTORS[geotech][0],2)} · Método ×{br(METHOD_FACTORS[method][0],2)} · '
                    f'Execução ×{br(EXECUTION_FACTORS[execution][0],2)}')
                st.caption('Coeficientes declarados no resultado: '+factor_summary+'.')
            with st.expander('Obras singulares e proteção acústica',expanded=False):
                st.caption('Provisões separadas e editáveis; não são apresentadas como preços SIEC.')
                specials=st.columns(2)
                special_length=specials[0].number_input('Extensão de vãos especiais (m)',min_value=0.,max_value=float(km)*1000,
                    value=0.,step=10.,key=key+'_elevated_special_length')
                special_addition=specials[1].number_input('Adicional dos vãos especiais (%)',min_value=0.,max_value=500.,
                    value=50.,step=5.,key=key+'_elevated_special_addition')
                transitions=specials[0].number_input('Encontros e transições (un)',min_value=0,max_value=1000,value=0,step=1,
                    key=key+'_elevated_transitions')
                transition_cost=specials[1].number_input('Provisão por encontro/transição (R$)',min_value=0.,max_value=1e10,
                    value=2000000.,step=100000.,key=key+'_elevated_transition_cost')
                barrier=st.columns(3)
                barrier_length=barrier[0].number_input('Barreira acústica (m)',min_value=0.,max_value=float(km)*2000,
                    value=0.,step=50.,key=key+'_elevated_barrier_length')
                barrier_height=barrier[1].number_input('Altura da barreira (m)',min_value=.5,max_value=10.,
                    value=3.,step=.5,key=key+'_elevated_barrier_height')
                barrier_cost=barrier[2].number_input('Custo da barreira (R$/m²)',min_value=0.,max_value=1e7,
                    value=2500.,step=100.,key=key+'_elevated_barrier_cost')
            elevated_parameters=dict(elevated_height=float(height),elevated_span=float(span),
                elevated_width_single=float(width_single),elevated_width_double=float(width_double),
                foundation_type=foundation,foundation_depth=float(foundation_depth),
                piles_per_support=int(piles),pile_diameter=float(diameter),urban_interference=interference,
                elevated_segments=tuple(segment_records),deck_type=deck_type,pier_type=pier_type,
                geotechnical_condition=geotech,construction_method=method,execution_constraint=execution,
                special_span_length=float(special_length),special_span_addition=float(special_addition),
                transitions=int(transitions),transition_unit_cost=float(transition_cost),
                noise_barrier_length=float(barrier_length),noise_barrier_height=float(barrier_height),
                noise_barrier_unit_cost=float(barrier_cost))

    service_step='3' if elevated_parameters else '2'
    bdi_step='4' if elevated_parameters else '3'
    st.markdown(f'**{service_step}. Serviços incluídos**')
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
        st.markdown(f'**{bdi_step}. BDI e condições do orçamento**')
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
                profile='siec',bdi=percentage/100,**elevated_parameters)
            result=calculate_freight(p,axle,rules,catalog) if freight else calculate_underground(p,rules,catalog) if subterraneo else calculate_elevated(p,rules,catalog,segment_records or None) if configuration=='Elevado' else calculate(p,rules,catalog)
            if freight:
                result['scenario'].update(locomotives=float(locomotives),wagons=float(wagons))
                result['warnings'].append('Frota fora do total: '+br(locomotives,2)+' locomotiva(s) equivalente(s)/km, '+br(wagons,2)+' vagão(ões) equivalente(s)/km. Pátios, terminais, pontes e passagens em nível também não foram orçados.')
            st.session_state.results[key]=result
            st.session_state[key+'_reference_signature']=reference_signature
            elevated_inputs=tuple(repr(value) for value in elevated_parameters.values()) if elevated_parameters else ()
            st.session_state[key+'_calculated_inputs']=(km,configuration,lines,drainage,fence,amvs,detection,trainsets if not freight else 0,
                elevated_inputs if not freight else (axle,locomotives,wagons))
        except (ValueError,KeyError,ZeroDivisionError) as exc:
            st.session_state.results.pop(key,None);st.error(str(exc))
    rate=percentage/100 if apply_bdi else 0.0
    elevated_inputs=tuple(repr(value) for value in elevated_parameters.values()) if elevated_parameters else ()
    current_inputs=(km,configuration,lines,drainage,fence,amvs,detection,trainsets if not freight else 0,
        elevated_inputs if not freight else (axle,locomotives,wagons))
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


def render_project_save_action(key, result, disabled=False):
    """Grava o cenário recalculado no mesmo projeto que está em edição."""
    context = st.session_state.get("budget_edit_context")
    if not context or context.get("key") != key:
        return
    with st.container(border=True, key=f"save_project_edit_{key}"):
        st.markdown(f"**Atualizar projeto salvo:** {context['name']}")
        if disabled:
            st.caption("Atualize o orçamento antes de salvar as alterações no projeto.")
        if st.button("Salvar alterações no projeto", icon=":material/save:", type="primary",
            key=f"save_project_changes_{key}", use_container_width=True, disabled=disabled):
            try:
                update_budget(current_user, context["id"], name=context["name"], result=result,
                    modality=context["modality"])
                st.session_state.pop("budget_edit_context", None)
                st.toast("Projeto e custos atualizados com sucesso.", icon=":material/check_circle:")
                st.rerun()
            except (RuntimeError, ValueError, LookupError) as exc:
                st.error(str(exc))


def render_vlt_budget():
    st.subheader('Configure seu VLT')
    st.caption('Modelo inicial integralmente referenciado no orçamento do edital do Ramal VLT Aeroporto - Castelão.')
    with st.container(border=True):
        st.markdown('**Traçado híbrido em via dupla**')
        columns=st.columns(2)
        surface_km=columns[0].number_input('Trecho em superfície (km de corredor)',min_value=0.0,
            max_value=1000.0,value=0.90,step=0.10,format='%.3f',key='vlt_surface_km')
        elevated_km=columns[1].number_input('Trecho elevado (km de corredor)',min_value=0.0,
            max_value=1000.0,value=1.70,step=0.10,format='%.3f',key='vlt_elevated_km')
        st.caption('Referência do edital: 0,90 km em superfície + 1,70 km elevado = 2,60 km de corredor e 5,20 km de linha em via dupla.')
        st.caption('Os valores já contêm os BDIs do edital: materiais 16,80%, serviços 24,23% e betuminosos 15,00%.')
    update=st.button('Atualizar orçamento',key='vlt_calculate',type='primary',icon=':material/calculate:')
    inputs=(float(surface_km),float(elevated_km))
    if update or 'vlt' not in st.session_state.results:
        try:
            st.session_state.results['vlt']=calculate_vlt(*inputs)
            st.session_state.vlt_calculated_inputs=inputs
        except ValueError as exc:
            st.session_state.results.pop('vlt',None);st.error(str(exc));return
    stale=st.session_state.get('vlt_calculated_inputs')!=inputs
    if stale:st.info('Você alterou o traçado. Selecione Atualizar orçamento para conferir os novos valores.')
    result=st.session_state.results.get('vlt')
    if not result:return
    st.session_state.display_results['vlt']=result
    if is_primary_root(current_user) and not st.session_state.get('vlt_seed_checked'):
        try:
            ensure_budget(current_user,'VLT Aeroporto - Castelão','VLT',calculate_vlt())
            st.session_state.vlt_seed_checked=True
        except (RuntimeError,PermissionError) as exc:
            st.warning('O orçamento foi calculado, mas o projeto inicial não pôde ser salvo: '+str(exc))
    with st.container(key='result_header_vlt'):
        st.markdown('## Resultado do orçamento VLT')
        st.caption('Orçamento-base do edital, data-base fevereiro/2025, parametrizado por tipo de implantação.')
    with st.container(key='result_kpis_vlt'):
        columns=st.columns(3,gap='medium')
        columns[0].metric('Custo total',currency(result['total']),border=True)
        columns[1].metric('Por km de corredor',currency(result['per_km']),border=True)
        columns[2].metric('Por km de linha',currency(result['per_line_km']),border=True)
    st.caption(f"Corredor: {br(result['scenario']['km'],3)} km · Via dupla: {br(result['scenario']['line_km'],3)} km de linha · Data-base: {result['reference_period']}")
    render_project_save_action('vlt', result, disabled=stale)
    summary=pd.DataFrame([{'Componente':name,'Valor (R$)':value}
        for name,value in result['segments'].items()])
    views=st.columns([1,1.1],gap='large')
    with views[0]:
        st.markdown('**Composição por implantação**')
        display_table(summary,monetary=('Valor (R$)',),height=250)
    with views[1]:
        st.markdown('**Participação no cenário**')
        st.bar_chart(summary,x='Componente',y='Valor (R$)',horizontal=True,color='#60998e',height=250)
    with st.expander('Ver grupos do edital e critérios paramétricos',expanded=False):
        detail=pd.DataFrame([{'EAP':item['eap'],'Grupo do edital':item['label'],
            'Aplicação':item['basis'],'Custo-base (R$)':item['baseline_cost'],
            'Fator':item['quantity'],'Custo no cenário (R$)':item['total']}
            for item in result['items']])
        display_table(detail,monetary=('Custo-base (R$)','Custo no cenário (R$)'),height=520)
    for warning in result['warnings']:st.caption('• '+warning)
    if can_download_budget(current_user,int(st.session_state.get('trial_excel_downloads',0))):
        st.download_button('Baixar orçamento em Excel',make_vlt_excel(result),
            file_name='orcamento_vlt_aeroporto_castelao.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='vlt_excel',icon=':material/download:')


def result_group_label(group,result):
    """Traduz o nome histórico do agrupamento para a solução exibida."""
    label=group.split(' ',1)[1]
    if result['scenario']['configuration']=='Subterrâneo':
        return {'Via permanente':'Túnel e via permanente','Vedação':'Segurança e ventilação',
                'Infraestrutura de cabos':'Canaletas e passa-fios'}.get(label,label)
    return label


def render_elevated_summary(result,key):
    elevated=result.get('elevated')
    if not elevated:return
    scenario=result['scenario']
    with st.container(border=True,key='elevated_result_summary'):
        st.markdown('### Síntese estrutural do elevado')
        st.caption('Quantitativos preliminares derivados da geometria escolhida e vinculados aos serviços SIEC do orçamento.')
        metrics=st.columns(4)
        metrics[0].metric('Vãos / apoios',f"{elevated['spans']} / {elevated['supports']}",border=True)
        metrics[1].metric('Largura do tabuleiro',br(elevated['active_width'],2)+' m',border=True)
        metrics[2].metric('Total de estacas',str(elevated['total_piles']),border=True)
        metrics[3].metric('Capacidade nominal / apoio',br(elevated['nominal_capacity_per_support'],0)+' tf',border=True)
        st.markdown(
            f"**Solução informada:** {scenario['foundation_type']} Ø {br(scenario['pile_diameter'],2)} m · "
            f"{scenario['piles_per_support']} estacas/apoio · profundidade média {br(scenario['foundation_depth'],2)} m · "
            f"extensão total {br(elevated['total_pile_length'],2)} m."
        )
        st.caption(elevated['recommendation'])
        st.markdown(
            '<div class="elevated-scheme"><div class="scheme-rail"></div>'
            '<div class="scheme-deck"></div><div class="scheme-pier p1"></div>'
            '<div class="scheme-pier p2"></div><div class="scheme-pier p3"></div>'
            f'<span class="scheme-span">Vão predominante: {br(scenario["elevated_span"],2)} m</span>'
            f'<span class="scheme-height">Altura: {br(scenario["elevated_height"],2)} m</span></div>',
            unsafe_allow_html=True)
        first_group=next((group for group in result['groups'] if group.startswith('1 ')),None)
        if first_group in result.get('selected_groups',result['groups']):
            structure=pd.DataFrame([{'Componente estrutural':name,'Custo direto (R$)':value}
                for name,value in elevated['components'].items()])
            with st.expander('Ver composição estrutural e memória dos parâmetros',expanded=False):
                display_table(structure,monetary=('Custo direto (R$)',))
                memory=pd.DataFrame([
                    {'Parâmetro':'Altura média dos pilares','Valor aplicado':br(scenario['elevated_height'],2)+' m','Referência SIEC':'8,00 m'},
                    {'Parâmetro':'Distância entre pilares','Valor aplicado':br(scenario['elevated_span'],2)+' m','Referência SIEC':'20,00 m'},
                    {'Parâmetro':'Largura do tabuleiro','Valor aplicado':br(elevated['active_width'],2)+' m','Referência SIEC':'7,00 m singela / 11,00 m dupla'},
                    {'Parâmetro':'Fundação profunda','Valor aplicado':scenario['foundation_type'],'Referência SIEC':'Hélice contínua'},
                    {'Parâmetro':'Estacas por apoio','Valor aplicado':str(scenario['piles_per_support']),'Referência SIEC':'4'},
                    {'Parâmetro':'Profundidade média','Valor aplicado':br(scenario['foundation_depth'],2)+' m','Referência SIEC':'20,00 m'},
                    {'Parâmetro':'Diâmetro','Valor aplicado':br(scenario['pile_diameter'],2)+' m','Referência SIEC':'0,80 m'},
                ])
                display_table(memory)
        summaries=elevated.get('segment_summaries',[])
        if summaries:
            with st.expander('Trechos homogêneos e soluções adotadas',expanded=False):
                segment_frame=pd.DataFrame(summaries)
                display_table(segment_frame,height=min(420,95+40*len(segment_frame)))
                factors=pd.DataFrame([{'Critério':name,'Solução':data['choice'],
                    'Coeficiente':br(data['factor'],2),'Aplicação':data['criterion']}
                    for name,data in elevated.get('technical_factors',{}).items()])
                if not factors.empty:
                    st.markdown('**Coeficientes técnicos declarados**')
                    display_table(factors)
        indicators=elevated.get('indicators',{})
        if indicators:
            with st.expander('Indicadores gerenciais do elevado',expanded=False):
                indicator_rows=[]
                for name,value in indicators.items():
                    shown=(currency(value) if name.startswith('Custo ') else
                        br(value,2)+'%' if name.endswith('(%)') else
                        br(value,2) if isinstance(value,float) else str(value))
                    indicator_rows.append({'Indicador':name,'Resultado':shown})
                display_table(pd.DataFrame(indicator_rows))
        with st.expander('Análise de sensibilidade',expanded=False):
            st.caption('Compara o total quando os principais parâmetros variam ±10%, mantendo as demais premissas.')
            signature=sha256(repr(result['scenario']).encode()).hexdigest()
            sensitivity_key=key+'_elevated_sensitivity'
            if st.button('Calcular sensibilidade',key=key+'_sensitivity_button',icon=':material/analytics:'):
                try:
                    scenario_data=dict(result['scenario'])
                    segment_data=scenario_data.pop('elevated_segments',[]) or None
                    parameter=Scenario(**scenario_data)
                    st.session_state[sensitivity_key]=(signature,sensitivity(result,parameter,rules,catalog,segment_data))
                except (ValueError,KeyError,TypeError) as exc:
                    st.error('Sensibilidade não calculada: '+str(exc))
            cached=st.session_state.get(sensitivity_key)
            if cached and cached[0]==signature:
                sensitivity_frame=pd.DataFrame(cached[1])
                if sensitivity_frame.empty:st.info('A sensibilidade ainda não está disponível para esta combinação de trechos.')
                else:display_table(sensitivity_frame,monetary=('Cenário inferior (R$)','Cenário-base (R$)','Cenário superior (R$)'))


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
    if r['scenario']['configuration']=='Elevado' and modality=='passageiro':
        render_elevated_summary(r,key)
    render_project_save_action(key, r)
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
            st.caption('O novo arquivo substituirá integralmente a versão ativa e permanecerá como a data-base atual.')
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
                    save_reference_base(current_user,parsed)
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
    editing=st.session_state.get('budget_edit_context')
    if editing:
        with st.container(border=True,key='project_edit_banner'):
            st.markdown(f"### Editando: {editing['name']}")
            st.caption(f"Abra a aba {editing['modality']}, ajuste os parâmetros, selecione Atualizar orçamento e depois Salvar alterações no projeto.")
            if st.button('Cancelar edição',key='cancel_project_edit',icon=':material/close:'):
                st.session_state.pop('budget_edit_context',None)
                st.rerun()
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
        render_vlt_budget()

    with shortline:
        pass

with reference_tab:
    with st.container(key='reference_heading'):
        st.markdown('## Bases de referência')
        st.caption('Carregue a versão mais recente de cada fonte e escolha se a tabela contém insumos ou serviços.')
    status=st.columns(2)
    status[0].metric('Tabelas enviadas',len(enabled_bases),border=True)
    status[1].metric('Códigos atualizados',sum(linked_uploads.values()),border=True)
    st.info('Cada fonte e tipo mantém somente a versão mais recente. Uma nova tabela substitui a anterior, permanece ativa após novo acesso e recalcula automaticamente os orçamentos quando houver códigos vinculados.')
    source_tabs=st.tabs(list(SOURCES))
    for source,source_tab in zip(SOURCES,source_tabs):
        with source_tab:
            default_kind='Serviços' if source=='SIEC' else 'Insumos'
            kind=st.segmented_control('Conteúdo da tabela',list(KINDS),default=default_kind,
                key=f'reference_kind_{source}')
            reference_card(source,kind)

render_user_sidebar(current_user)
