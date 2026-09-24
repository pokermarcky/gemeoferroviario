from pathlib import Path
from io import BytesIO
import pandas as pd
import streamlit as st
from railbudget.engine import Scenario, load_model, calculate, select_groups
from railbudget.exporters import make_excel, currency, br, caption
from railbudget.header import render_header, TRAIN_HTML, TRAIN_CSS
from railbudget.stations import include_stations, STATION_SIZES, STATION_GROUP

ROOT=Path(__file__).resolve().parent

st.set_page_config(page_title='railparametric | Parametric Rails',page_icon=':material/train:',layout='wide')
st.markdown('''<style>
div[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#f4f8fa 0,#ffffff 360px)}
div[data-testid="stTabs"] [role="tablist"] {gap:.4rem;flex-wrap:wrap;border-bottom:0!important;margin:.8rem 0}
div[data-testid="stTabs"] [data-testid="stTab"] {border:1px solid #cbdbe0;border-radius:10px;background:#fff;
  padding:.55rem .9rem;color:#244253;font-weight:600;box-shadow:0 2px 8px #1838490c}
div[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {border-color:#147d83;
  background:#e8f5f3;color:#07585d;box-shadow:inset 0 0 0 1px #147d83}
div[data-testid="stTabs"] .react-aria-SelectionIndicator {display:none}
div[data-testid="stMetric"] {border-radius:12px}
@media(max-width:640px) {div[data-testid="stTabs"] [data-testid="stTab"] {padding:.4rem .55rem;font-size:.88rem}}
</style>''',unsafe_allow_html=True)
train_component = st.components.v2.component("parametric_rails_train", html=TRAIN_HTML, css=TRAIN_CSS)
render_header(train_component)

@st.cache_data(ttl=300,max_entries=2)
def data(version):return load_model(ROOT)

@st.cache_data(ttl=900,max_entries=8,show_spinner=False)
def excel_orcamento(result,version):return make_excel(result,{**data(version)[1],**result.get('custom_prices',{})})

version=(ROOT/'data/catalog.sqlite').stat().st_mtime_ns,(ROOT/'config/rules.json').stat().st_mtime_ns
rules,catalog=data(version)
st.session_state.setdefault('results',{})
if not st.session_state.get('referencia_inicial_carregada'):
    st.session_state.results.setdefault('main',calculate(Scenario(),rules,catalog))
    st.session_state.referencia_inicial_carregada=True

def set_all_groups(key,count,selected):
    for i in range(count):
        st.session_state[f'{key}_grupo_{i}']=selected


def budget_controls(key,freight=False):
    st.subheader('Configure o cenário')
    st.caption('Defina o corredor e selecione apenas os serviços que fazem parte do escopo.')
    with st.container(border=True):
        st.markdown('**Características gerais**')
        general=st.columns(3 if freight else 4)
        with general[0]:
            if freight:st.caption('Base de referência: SIEC • via em lastro / AMV nº 14')
            else:st.selectbox('Modelo de referência',['SIEC • lastro / AMV nº 14'],key=key+'_profile')
        with general[1]:
            km=st.number_input('Extensão do corredor (km)',min_value=0.01,max_value=10000.0,value=1.0,step=0.1,format='%.3f',key=key+'_km')
        with general[2]:
            configuration='Superfície' if freight else st.selectbox('Configuração',['Superfície','Elevado','Subterrâneo'],key=key+'_configuration')
        if freight:
            lines=st.selectbox('Via',[1,2],format_func=lambda n:'Simples' if n==1 else 'Dupla',key=key+'_lines')
            axle=st.number_input('Carga por eixo de projeto (t/eixo)',min_value=10.0,max_value=40.0,value=25.0,step=1.0,key=key+'_axle',help='Premissa para análise futura; não redimensiona os itens SIEC nesta versão.')
            st.caption('Estimativa inicial da infraestrutura de superfície. O dimensionamento para a carga por eixo deve ser conferido em projeto.')
        else:
            with general[3]:
                lines=st.selectbox('Via',[1,2],format_func=lambda n:'Simples' if n==1 else 'Dupla',key=key+'_lines')

    subterraneo=configuration=='Subterrâneo'
    if subterraneo:
        st.warning('Subterrâneo selecionado. As quantidades e os preços de escavação, revestimento, ventilação, segurança e demais sistemas ainda precisam de uma base técnica própria. Este cenário não gera um total por enquanto.')

    st.markdown('**O que incluir no orçamento**')
    st.caption('Marque um grupo para exibir suas opções. Desmarcar o grupo remove seu custo do total.')
    all_on,all_off,spacer=st.columns([1,1,5])
    all_on.button('Selecionar todas',key=key+'_selecionar_todas',on_click=set_all_groups,args=(key,8 if freight else len(rules['groups'])+1,True),type='tertiary')
    all_off.button('Desmarcar todas',key=key+'_desmarcar_todas',on_click=set_all_groups,args=(key,8 if freight else len(rules['groups'])+1,False),type='tertiary')
    chosen=[]
    enabled={}
    drainage=st.session_state.get(key+'_drainage','Reforçada')
    fence=st.session_state.get(key+'_fence','Cerca')
    amvs=st.session_state.get(key+'_amvs',0 if freight else 1)
    detection=st.session_state.get(key+'_detection','Circuito de via')
    trainsets=st.session_state.get(key+'_trainsets',1)
    stations={}
    group_columns=st.columns(3)
    for i,g in enumerate(rules['groups'][:8] if freight else rules['groups']):
        with group_columns[i%len(group_columns)]:
            with st.container(border=True):
                label=('Banco de dutos' if configuration=='Superfície' else 'Canaletas e passa-fios') if i==5 else g.split(' ',1)[1]
                enabled[i]=st.checkbox(label,value=(i not in (4,5,6,7) if freight else True),key=f'{key}_grupo_{i}',persist_state='session')
                if enabled[i]:
                    if i==0:st.caption('Via '+configuration.lower()+' • '+('simples' if lines==1 else 'dupla'))
                    elif i==1:st.caption('Levantamentos e acompanhamento topográfico.')
                    elif i==2:drainage=st.selectbox('Tipo de drenagem',['Normal','Reforçada','Complexa'],index=['Normal','Reforçada','Complexa'].index(drainage),key=key+'_drainage')
                    elif i==3:fence=st.selectbox('Tipo de vedação',['Cerca','Muro'],index=['Cerca','Muro'].index(fence if fence in ('Cerca','Muro') else 'Cerca'),key=key+'_fence')
                    elif i==4:amvs=st.number_input('Quantidade total de AMVs',min_value=0,max_value=100000,value=int(amvs),step=1,key=key+'_amvs',help='Total no corredor, distribuído entre as linhas.')
                    elif i==5:st.caption('Banco subterrâneo de seis dutos.' if configuration=='Superfície' else 'Canaletas e passa-fios embutidos no tabuleiro elevado.' if configuration=='Elevado' else 'Necessita projeto de instalações do túnel.')
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
            with fleet[0]:locomotives=st.number_input('Locomotivas (un)',min_value=0,max_value=10000,value=0,step=1,key=key+'_locomotives')
            with fleet[1]:wagons=st.number_input('Vagões de carga (un)',min_value=0,max_value=100000,value=0,step=1,key=key+'_wagons')
            st.caption('A base SIEC contém custos horários de operação de locomotiva e vagões, mas não preços de aquisição. As quantidades acima ficam registradas como escopo pendente e não entram no total.')
            st.caption('Pátios, terminais, pontes, passagens em nível e interfaces de carga também exigem orçamento próprio.')
    else:
        with st.container(border=True):
            st.markdown('**Estações de passageiros**')
            include_station_group=st.checkbox('Incluir estações no orçamento',value=True,key=key+'_grupo_9')
            st.caption('Informe quantidade e preço unitário estimado por porte. Sem preço unitário não é possível incluir uma estação no orçamento.')
            station_cols=st.columns(3)
            for i,size in enumerate(STATION_SIZES):
                with station_cols[i]:
                    st.markdown('**'+size+'**')
                    qty=st.number_input('Quantidade de estações '+size.lower(),min_value=0,max_value=1000,value=0,step=1,key=key+'_station_'+str(i))
                    price=st.number_input('Preço unitário (R$) • '+size.lower(),min_value=0.0,max_value=1e12,value=0.0,step=100000.0,format='%.2f',key=key+'_station_price_'+str(i),disabled=qty==0)
                    stations[size]=(int(qty),float(price))
    with st.container(border=True):
        st.subheader('BDI do orçamento')
        apply_bdi=st.checkbox('Aplicar BDI',value=True,key=key+'_aplicar_bdi',persist_state='session')
        percentage=st.number_input('BDI personalizado (%)',min_value=0.0,max_value=100.0,
            value=27.84182802164763,step=0.5,format='%.6f',
            key=key+'_bdi_personalizado',persist_state='session')
        st.caption('O percentual é aplicado uma única vez ao total e aos subtotais selecionados.')
    missing_price=not freight and any(q and not price for q,price in stations.values())
    if missing_price:st.warning('Informe o preço unitário para cada porte de estação selecionado.')
    calculate_now=st.button('Calcular orçamento',key=key+'_calculate',type='primary',icon=':material/calculate:',width='stretch',disabled=subterraneo or missing_price)
    if calculate_now:
        try:
            p=Scenario(km=km,configuration=configuration,lines=lines,drainage=drainage,
                fence=fence if enabled[3] else 'Nenhuma',amvs=int(amvs) if enabled[4] else 0,
                ducts=enabled[5],topography=enabled[1],overhead=enabled[6],signaling=enabled[7],
                detection=detection,rolling_stock=False if freight else enabled[8],trainsets=0 if freight else int(trainsets) if enabled[8] else 0,
                profile='siec',bdi=percentage/100)
            result=calculate(p,rules,catalog)
            if freight:
                result['model_label']='SIEC • carga (infraestrutura preliminar)'
                result['groups'].pop('9 Material rodante')
                result['warnings'].append(f'Carga por eixo informada: {axle} t/eixo; não redimensiona a superestrutura de passageiros adotada como referência. Validar trilho, dormentes, lastro e plataforma em projeto.')
                result['warnings'].append(f'Frota fora do total: {locomotives} locomotiva(s), {wagons} vagão(ões). Pátios, terminais, pontes e passagens em nível também não foram orçados.')
            else:result=include_stations(result,stations)
            st.session_state.results[key]=result
            st.session_state[key+'_calculated_inputs']=(km,configuration,lines,drainage,fence,amvs,detection,trainsets if not freight else 0,
                tuple(stations.items()) if not freight else (axle,locomotives,wagons))
        except (ValueError,KeyError,ZeroDivisionError) as exc:
            st.session_state.results.pop(key,None);st.error(str(exc))
    rate=percentage/100 if apply_bdi else 0.0
    current_inputs=(km,configuration,lines,drainage,fence,amvs,detection,trainsets if not freight else 0,
        tuple(stations.items()) if not freight else (axle,locomotives,wagons))
    if not freight:st.session_state.setdefault(key+'_calculated_inputs',current_inputs)
    stale=key+'_calculated_inputs' in st.session_state and st.session_state[key+'_calculated_inputs']!=current_inputs
    if stale and not subterraneo:
        st.info('Parâmetros alterados. Clique em Calcular orçamento para atualizar os valores.')
    if not freight and include_station_group and STATION_GROUP in st.session_state.results.get(key,{}).get('groups',{}):chosen.append(STATION_GROUP)
    return chosen,rate,subterraneo or missing_price or stale


def render_result(r,key,modality='passageiro'):
    if modality=='carga':
        st.warning('Estimativa preliminar da infraestrutura com itens SIEC. A carga por eixo ainda não redimensiona a via; frota, pátios, terminais e obras especiais estão fora deste total.')
    st.caption('Cenário calculado: '+caption(r))
    with st.container(horizontal=True):
        st.metric('Total com BDI' if r['scenario']['bdi'] else 'Total sem BDI',currency(r['total']),border=True)
        st.metric('Por km de corredor',currency(r['per_km']),border=True)
        st.metric('Por km de linha',currency(r['per_line_km']),border=True)
    st.caption(f"Custo direto: {currency(r['direct'])} | BDI aplicado: {br(r['scenario']['bdi']*100,6)}% | Acréscimo de BDI: {currency(r['bdi_amount'])}")
    columns={'eap':'EAP','group':'Grupo','code':'Código','source':'Fonte','label':'Aplicação','description':'Descrição','unit':'Unidade','quantity':'Quantidade','unit_cost':'Custo unitário (R$)','total':'Custo total (R$)','date':'Data-base'}
    frame=pd.DataFrame(r['items'])[list(columns)].rename(columns=columns) if r['items'] else pd.DataFrame(columns=columns.values())
    summary_tab,detail_tab=st.tabs(['Resumo geral','Detalhamento por grupo'])
    with summary_tab:
        st.caption('Visão consolidada do total selecionado. Consulte o detalhamento para conferir cada serviço, quantidade, código, fonte e preço.')
        st.subheader('Participação por grupo')
        group_frame=pd.DataFrame([{'Grupo':g.split(' ',1)[1],'Custo direto (R$)':v} for g,v in r['groups'].items()])
        st.dataframe(group_frame,hide_index=True,column_config={'Custo direto (R$)':st.column_config.NumberColumn(format='%.2f')})
        st.bar_chart(group_frame,x='Grupo',y='Custo direto (R$)',horizontal=True,color='#147D83')
        st.subheader('EAP orçada')
        st.dataframe(frame,hide_index=True,height=530,column_config={'Quantidade':st.column_config.NumberColumn(format='%.6f'),'Custo unitário (R$)':st.column_config.NumberColumn(format='%.2f'),'Custo total (R$)':st.column_config.NumberColumn(format='%.2f')})
    with detail_tab:
        st.caption('Cada cartão mostra custo direto, valor com o BDI escolhido e participação no total. Abra a composição somente quando quiser conferir as linhas de preço.')
        for group in r['scope_summary']:
            if modality=='carga' and group['group'].startswith('9 '):continue
            with st.container(border=True):
                st.subheader(group['group'].split(' ',1)[1])
                if group['group'].startswith('3 '):st.caption('Drenagem '+r['scenario']['drainage'].lower())
                if group['group'].startswith('4 '):st.caption('Vedação: '+r['scenario']['fence'].lower())
                if group['group'].startswith('6 '):st.caption('Banco subterrâneo de seis dutos' if r['scenario']['configuration']=='Superfície' else 'Canaletas e passa-fios embutidos no tabuleiro elevado')
                if group['group'].startswith('8 '):st.caption('Detecção: '+r['scenario']['detection'].lower())
                if group['group'].startswith('9 '):st.caption(f"Frota: {r['scenario']['trainsets']} composição(ões) de 8 carros; custo por composição e rateio por km atendido.")
                if not group['selected']:st.caption('Fora do total selecionado. Valores abaixo são a referência deste grupo no cenário completo.')
                if not group['direct']:st.info('Sem serviços neste cenário. Verifique os parâmetros do formulário para incluir este grupo.')
                with st.container(horizontal=True):
                    st.metric('Subtotal direto',currency(group['direct']))
                    st.metric('Subtotal com BDI' if r['scenario']['bdi'] else 'Subtotal sem BDI',currency(group['total']))
                    st.metric('Por km com BDI' if r['scenario']['bdi'] else 'Por km sem BDI',currency(group['per_km_with_bdi']))
                    st.metric('Participação no total selecionado',br(group['share'],2)+'%')
                rows=[x for x in r['items'] if x['group']==group['group']]
                if rows:
                    with st.expander('Ver composição e preços de '+group['group'].split(' ',1)[1],expanded=False):
                        st.dataframe(pd.DataFrame(rows)[['code','source','label','unit','quantity','unit_cost','total']].rename(columns={
                            'code':'Código','source':'Fonte','label':'Serviço','unit':'Unidade','quantity':'Quantidade',
                            'unit_cost':'Custo unitário (R$)','total':'Custo total (R$)'}),hide_index=True)
    if not r['items']:
        st.info('Nenhum serviço incluído no total. Selecione ao menos um grupo com serviços para gerar o orçamento em Excel.')
        return
    st.download_button('Baixar orçamento em Excel',excel_orcamento(r,version),
        file_name='orcamento_ferrovia_'+modality+'.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key=key+'_excel',icon=':material/download:')

def modalidade_pendente(nome,escopo,dados):
    st.subheader(nome)
    st.write(escopo)
    with st.container(border=True):
        st.info('Orçamento paramétrico em preparação. Ainda não há quantitativos e preços calibrados para esta modalidade.')
        st.markdown('**Bases necessárias para o cálculo**')
        for item in dados:st.write('• '+item)


def preview_reference(upload):
    if not upload:return
    if upload.size>20*1024*1024:
        st.error('Arquivo acima de 20 MB. Divida a tabela antes de enviar.');return
    raw=upload.getvalue()
    try:
        if upload.name.lower().endswith('.csv'):
            try:frame=pd.read_csv(BytesIO(raw),sep=None,engine='python',nrows=25,dtype=str,encoding='utf-8-sig')
            except UnicodeDecodeError:frame=pd.read_csv(BytesIO(raw),sep=None,engine='python',nrows=25,dtype=str,encoding='latin-1')
        else:frame=pd.read_excel(BytesIO(raw),nrows=25,dtype=str,engine='openpyxl')
        if frame.empty:st.warning('Nenhuma linha identificada neste arquivo.');return
        st.success(f'{upload.name}: {len(frame.columns)} colunas identificadas.')
        with st.expander('Prévia das primeiras linhas de '+upload.name):st.dataframe(frame.head(8),hide_index=True)
    except (ValueError,KeyError,ImportError,UnicodeError,TypeError) as exc:
        st.error('Não foi possível ler a tabela: '+str(exc))


st.header('ORÇAMENTOS')
st.caption('Selecione a modalidade. Os valores apresentados correspondem aos itens efetivamente incluídos no escopo.')
passageiro,carga,vlt,shortline=st.tabs([
    'Ferrovia de passageiro','Ferrovia de carga','VLT - Veículo leve sobre Trilho','Shortline'])

with passageiro:
    chosen,rate,subterraneo=budget_controls('main')
    if not subterraneo:
        r=st.session_state.results.get('main')
        if r:render_result(select_groups(r,chosen,bdi_rate=rate),'main')
        else:st.info('Revise as opções acima e selecione Calcular orçamento.')

with carga:
    st.caption('Via em superfície • infraestrutura preliminar com referências SIEC. Frota, pátios e obras especiais dependem de orçamento específico.')
    cargo_chosen,cargo_rate,cargo_blocked=budget_controls('cargo',freight=True)
    if not cargo_blocked:
        cargo_result=st.session_state.results.get('cargo')
        if cargo_result:render_result(select_groups(cargo_result,cargo_chosen,bdi_rate=cargo_rate),'cargo',modality='carga')
        else:st.info('Configure a ferrovia de carga e selecione Calcular orçamento.')

with vlt:
    modalidade_pendente('VLT - Veículo leve sobre Trilho',
        'A via urbana, as paradas, a alimentação elétrica e a frota exigem quantitativos e referências próprios.',[
        'Traçado, tipo de via implantada e interferências urbanas.',
        'Paradas, energia, sinalização e acessibilidade com custos de referência.',
        'Quantidade e especificação dos veículos leves sobre trilhos.'])

with shortline:
    modalidade_pendente('Shortline',
        'A estimativa depende de definir se a linha será implantada, reabilitada ou ampliada e qual tráfego atenderá.',[
        'Inventário da via existente, carga por eixo e velocidade de projeto.',
        'Extensão, dormentes, trilhos, lastro, AMVs e intervenções em pontes.',
        'Pátios, sinalização e frota incluídos no escopo.'])

st.divider()
with st.expander('Tabelas de referência · SINAPI / SIURB / SICRO',expanded=False):
    st.caption('Envie tabelas em CSV ou Excel para conferir sua estrutura. Os arquivos ficam nesta sessão; preços só serão usados nos orçamentos após mapeamento de códigos, unidades e data-base.')
    for name,panel in zip(('Insumos','Serviços'),st.tabs(['Insumos','Serviços'])):
        with panel:
            for source,column in zip(('SINAPI','SIURB','SICRO'),st.columns(3)):
                with column:
                    upload=st.file_uploader(source+' • '+name,type=['csv','xlsx'],key='upload_'+source+'_'+name)
                    preview_reference(upload)
