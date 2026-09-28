from pathlib import Path
from hashlib import sha256
import pandas as pd
import streamlit as st
from railbudget.engine import Scenario, load_model, calculate, select_groups
from railbudget.exporters import make_excel, currency, br, caption
from railbudget.interface import apply_theme
from railbudget.realistic_scene import realistic_header
from railbudget.freight import calculate_freight
from railbudget.stations import include_stations, STATION_SIZES, STATION_GROUP
from railbudget.reference_data import (SOURCES, KINDS, parse_reference,
    apply_reference_bases, embedded_inventory)

ROOT=Path(__file__).resolve().parent

st.set_page_config(page_title='railparametric | Parametric Rails',page_icon=':material/train:',layout='wide')
apply_theme()
realistic_header()
@st.cache_data(ttl=300,max_entries=2)
def data(version):return load_model(ROOT)

@st.cache_data(ttl=900,max_entries=8,show_spinner=False)
def excel_orcamento(result,price_catalog):return make_excel(result,{**price_catalog,**result.get('custom_prices',{})})

version=(ROOT/'data/catalog.sqlite').stat().st_mtime_ns,(ROOT/'config/rules.json').stat().st_mtime_ns
rules,base_catalog=data(version)
st.session_state.setdefault('results',{})
st.session_state.setdefault('reference_bases',{})
enabled_bases={slot:base for slot,base in st.session_state.reference_bases.items()
    if st.session_state.get(f'ref_enabled_{slot[0]}_{slot[1]}',True)}
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

def set_all_groups(key,count,selected):
    for i in range(count):
        st.session_state[f'{key}_grupo_{i}']=selected


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
        st.warning('Subterrâneo selecionado. As quantidades e os preços de escavação, revestimento, ventilação, segurança e demais sistemas ainda precisam de uma base técnica própria. Este cenário não gera um total por enquanto.')

    st.markdown('**2. Serviços incluídos**')
    st.caption('Ative somente o que faz parte do seu projeto. As opções aparecem em cada cartão.')
    with st.container(horizontal=True, gap='small'):
        st.button('Incluir todos',key=key+'_selecionar_todas',on_click=set_all_groups,args=(key,8 if freight else len(rules['groups'])+1,True),type='tertiary',icon=':material/done_all:')
        st.button('Limpar seleção',key=key+'_desmarcar_todas',on_click=set_all_groups,args=(key,8 if freight else len(rules['groups'])+1,False),type='tertiary',icon=':material/remove_done:')
    chosen=[]
    enabled={}
    drainage=st.session_state.get(key+'_drainage','Reforçada')
    fence=st.session_state.get(key+'_fence','Cerca')
    amvs=st.session_state.get(key+'_amvs',0 if freight else 1)
    detection=st.session_state.get(key+'_detection','Circuito de via')
    trainsets=st.session_state.get(key+'_trainsets',1)
    stations={}
    for i,g in enumerate(rules['groups'][:8] if freight else rules['groups']):
        if i%3==0:group_columns=st.columns(3)
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
        with st.expander('Estações de passageiros · quantidades e preços',expanded=False):
            include_station_group=st.checkbox('Incluir estações no orçamento',value=True,key=key+'_grupo_9')
            st.caption('Informe quantidade e preço unitário estimado por porte. Sem preço unitário não é possível incluir uma estação no orçamento.')
            station_cols=st.columns(3)
            for i,size in enumerate(STATION_SIZES):
                with station_cols[i]:
                    st.markdown('**'+size+'**')
                    qty=st.number_input('Quantidade · '+size.lower(),min_value=0,max_value=1000,value=0,step=1,key=key+'_station_'+str(i))
                    price=st.number_input('Preço por estação (R$) · '+size.lower(),min_value=0.0,max_value=1e12,value=0.0,step=100000.0,format='%.2f',key=key+'_station_price_'+str(i),disabled=qty==0)
                    stations[size]=(int(qty),float(price))
    with st.expander('3. BDI e condições do orçamento',expanded=False):
        apply_bdi=st.checkbox('Aplicar BDI',value=True,key=key+'_aplicar_bdi',persist_state='session')
        percentage=st.number_input('BDI personalizado (%)',min_value=0.0,max_value=100.0,
            value=27.84182802164763,step=0.5,format='%.6f',
            key=key+'_bdi_personalizado',persist_state='session')
        st.caption('O percentual é aplicado uma única vez ao total e aos subtotais selecionados.')
    missing_price=not freight and any(q and not price for q,price in stations.values())
    if missing_price:st.warning('Informe o preço unitário para cada porte de estação selecionado.')
    if freight:st.caption('O orçamento de carga é atualizado automaticamente ao alterar as premissas.')
    else:calculate_now=st.button('Atualizar orçamento',key=key+'_calculate',type='primary',icon=':material/calculate:',disabled=subterraneo or missing_price)
    if freight or calculate_now:
        try:
            p=Scenario(km=km,configuration=configuration,lines=lines,drainage=drainage,
                fence=fence if enabled[3] else 'Nenhuma',amvs=int(amvs) if enabled[4] else 0,
                ducts=enabled[5],topography=enabled[1],overhead=enabled[6],signaling=enabled[7],
                detection=detection,rolling_stock=False if freight else enabled[8],trainsets=0 if freight else int(trainsets) if enabled[8] else 0,
                profile='siec',bdi=percentage/100)
            result=calculate_freight(p,axle,rules,catalog) if freight else calculate(p,rules,catalog)
            if freight:
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
        st.info('Você alterou o cenário. Selecione Atualizar orçamento para conferir os novos valores.')
    if not freight and include_station_group and STATION_GROUP in st.session_state.results.get(key,{}).get('groups',{}):chosen.append(STATION_GROUP)
    return chosen,rate,subterraneo or missing_price or stale


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


def render_result(r,key,modality='passageiro'):
    st.subheader('Resultado do orçamento')
    if modality=='carga':
        st.info('Infraestrutura de carga com alternativa TR57 ou UIC60 da base SIEC. A verificação estrutural da via, frota, pátios, terminais e obras especiais requer orçamento de projeto.')
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
                        detail=pd.DataFrame(rows)[['code','source','label','unit','quantity','unit_cost','total']].rename(columns={
                            'code':'Código','source':'Fonte','label':'Serviço','unit':'Unidade','quantity':'Quantidade',
                            'unit_cost':'Custo unitário (R$)','total':'Custo total (R$)'})
                        detail['Quantidade']=detail['Quantidade'].map(lambda value:br(value,6))
                        display_table(detail,monetary=('Custo unitário (R$)','Custo total (R$)'))
    if not r['items']:
        st.info('Nenhum serviço incluído no total. Selecione ao menos um grupo com serviços para gerar o orçamento em Excel.')
        return
    used_catalog={item['price_key']:catalog[item['price_key']] for item in r['items'] if item['price_key'] in catalog}
    st.download_button('Baixar orçamento em Excel',excel_orcamento(r,used_catalog),
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


def reference_card(source,kind):
    slot=(source,kind)
    embedded=embedded_inventory(base_catalog).get(slot)
    active=st.session_state.reference_bases.get(slot)
    with st.container(border=True):
        st.markdown(f'<span class="source-badge source-{source.lower()}">{source}</span> **{kind}**',unsafe_allow_html=True)
        if active:
            st.caption(f'Base ativa · {active.period or "data-base não informada"}')
            enabled_key=f'ref_enabled_{source}_{kind}'
            st.session_state.setdefault(enabled_key,True)
            enabled=st.toggle('Usar esta tabela no orçamento',key=enabled_key)
            linked=linked_uploads.get(slot,0) if enabled else 0
            st.markdown(f'**{active.count:,} itens** · {linked:,} vinculados ao orçamento'.replace(',','.'))
            st.caption(active.filename)
            preview=pd.DataFrame(active.records[:6]).rename(columns={'code':'Código','description':'Descrição','unit':'Unidade','price':'Preço','date':'Data-base'})
            with st.expander('Visualizar amostra',expanded=False):
                display_table(preview,monetary=('Preço',))
            if st.button('Restaurar base anterior',key=f'restore_{source}_{kind}',type='tertiary',icon=':material/restore:'):
                del st.session_state.reference_bases[slot]
                st.session_state.pop(f'ref_enabled_{source}_{kind}',None)
                st.session_state.results={}
                st.session_state.referencia_inicial_carregada=False
                st.rerun()
        elif embedded:
            periods=' · '.join(sorted(embedded['periods']))
            st.caption(f'Base embarcada · {periods}')
            st.markdown(f'**{embedded["count"]:,} itens** disponíveis'.replace(',','.'))
        else:
            st.caption('Nenhuma tabela ativa')
            st.markdown('**Aguardando uma base válida**')
        period=st.text_input('Data-base da substituição',placeholder='MM/AAAA',key=f'period_{source}_{kind}')
        upload=st.file_uploader('Substituir tabela atual',type=['csv','xlsx'],key=f'upload_{source}_{kind}',
            help='O arquivo novo substitui a tabela anterior desta fonte e categoria. Colunas mínimas: Código, Descrição, Unidade e Preço.')
        if upload and upload.size>200*1024*1024:
            st.error('Arquivo acima de 200 MB. Divida a tabela antes de enviar.');return
        if upload:
            raw=upload.getvalue();digest=sha256(raw).hexdigest()
            if not active or digest!=active.digest or period.strip()!=active.period:
                try:
                    parsed=parse_reference(raw,upload.name,source,kind,period)
                    st.session_state.reference_bases[slot]=parsed
                    st.session_state[f'ref_enabled_{source}_{kind}']=True
                    st.session_state.results={}
                    st.session_state.referencia_inicial_carregada=False
                    st.success(f'{parsed.count:,} itens validados. A nova base já está ativa.'.replace(',','.'))
                    st.rerun()
                except (ValueError,KeyError,ImportError,UnicodeError,TypeError) as exc:
                    st.error('Tabela não ativada: '+str(exc))


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

with reference_tab:
    st.subheader('Gestão das bases de referência')
    st.caption('Mantenha uma única versão ativa por fonte e categoria. Ao enviar uma tabela válida, ela substitui a versão anterior e os códigos já vinculados passam a usar os novos preços.')
    active_count=len(st.session_state.reference_bases)
    status=st.columns(3)
    status[0].metric('Fontes disponíveis',len(SOURCES),border=True)
    status[1].metric('Tabelas substituídas',active_count,border=True)
    status[2].metric('Códigos atualizados',sum(linked_uploads.values()),border=True)
    st.info('Os uploads ficam ativos nesta sessão do aplicativo. A base embarcada permanece como recuperação segura após reinicializações do Streamlit.')
    for name,panel in zip(KINDS,st.tabs(list(KINDS))):
        with panel:
            st.caption('Envie CSV ou Excel com Código, Descrição, Unidade e Preço. A data-base pode estar no arquivo ou ser informada no cartão.')
            for row_start in range(0,len(SOURCES),2):
                columns=st.columns(2,gap='large')
                for source,column in zip(SOURCES[row_start:row_start+2],columns):
                    with column:reference_card(source,name)
