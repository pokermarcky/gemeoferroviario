from pathlib import Path
import sqlite3
import json
import pandas as pd
import streamlit as st
from railbudget.engine import Scenario, load_model, calculate, select_groups
from railbudget.exporters import export_all, currency, br, caption
from railbudget.header import render_header, TRAIN_HTML, TRAIN_CSS

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Parametric Rails',page_icon=':material/train:',layout='wide')
train_component = st.components.v2.component("parametric_rails_train", html=TRAIN_HTML, css=TRAIN_CSS)
render_header(train_component)

@st.cache_data(ttl=300,max_entries=2)
def data(version):return load_model(ROOT)

@st.cache_data(ttl=300,max_entries=2)
def base(version):
    with sqlite3.connect(ROOT/'data/catalog.sqlite') as con:return pd.read_sql_query('SELECT * FROM prices ORDER BY source,code',con)

@st.cache_data(ttl=900,max_entries=8,show_spinner=False)
def exports(result,version):return export_all(result,data(version)[1])

version=(ROOT/'data/catalog.sqlite').stat().st_mtime_ns,(ROOT/'config/rules.json').stat().st_mtime_ns
rules,catalog=data(version)
st.session_state.setdefault('results',{})
st.session_state.setdefault('downloads',{})
if not st.session_state.get('referencia_inicial_carregada'):
    st.session_state.results.setdefault('main',calculate(Scenario(),rules,catalog))
    st.session_state.referencia_inicial_carregada=True

def form(key,default_double=False):
    with st.form('form_'+key):
        profile=st.selectbox('Modelo de referência',list(rules['profiles']),format_func=lambda k:rules['profiles'][k]['label'],key=key+'_profile')
        km=st.number_input('Extensão do corredor (km)',min_value=0.01,max_value=10000.0,value=1.0,step=0.1,format='%.3f',key=key+'_km')
        configuration=st.selectbox('Configuração',['Superfície','Elevado'],key=key+'_configuration')
        lines=st.selectbox('Via',[1,2],index=int(default_double),format_func=lambda n:'Simples' if n==1 else 'Dupla',key=key+'_lines')
        drainage=st.selectbox('Drenagem',['Normal','Reforçada','Complexa'],index=1,key=key+'_drainage')
        fence=st.selectbox('Vedação da faixa',['Cerca','Muro','Nenhuma'],key=key+'_fence')
        amvs=st.number_input('Quantidade total de AMVs',min_value=0,max_value=100000,value=2 if default_double else 1,step=1,key=key+'_amvs',help='Total no corredor, distribuído entre as linhas. Não é quantidade por km.')
        overhead=st.checkbox('Incluir rede aérea',value=True,key=key+'_overhead')
        signaling=st.checkbox('Incluir sinalização',value=True,key=key+'_signaling')
        detection=st.selectbox('Detecção de trens',['Circuito de via','Contador de eixos'],key=key+'_detection')
        rolling_stock=st.checkbox('Incluir material rodante',value=True,key=key+'_rolling_stock')
        trainsets=st.number_input('Quantidade de composições de 8 carros',min_value=0,max_value=10000,value=1,step=1,key=key+'_trainsets',help='Custo calculado por composição. O indicador por km rateia a frota pela extensão do corredor.')
        months=st.number_input('Prazo da obra (meses; 0 = referência)',min_value=0,max_value=1200,value=0,step=1,key=key+'_months',help='SIEC: 6 meses superfície / 18 elevado. Legado: 12 / 24 meses.')
        bdi=st.session_state.get(key+'_bdi_personalizado',27.84182802164763)
        submit=st.form_submit_button('Calcular Orçamento',type='primary',width='stretch')
    if submit:
        try:
            p=Scenario(km=km,configuration=configuration,lines=lines,drainage=drainage,fence=fence,amvs=int(amvs),overhead=overhead,signaling=signaling,detection=detection,rolling_stock=rolling_stock,trainsets=int(trainsets),profile=profile,bdi=bdi/100,months=int(months))
            st.session_state.results[key]=calculate(p,rules,catalog)
            st.session_state.downloads.pop(key,None)
        except (ValueError,KeyError,ZeroDivisionError) as exc:
            st.session_state.results.pop(key,None);st.session_state.downloads.pop(key,None);st.error(str(exc))

def set_all_groups(key,count,selected):
    for i in range(count):
        st.session_state[f'{key}_grupo_{i}']=selected


def scope_controls(r,key):
    st.markdown('**Grupos incluídos no total**')
    st.caption('Marque os grupos desejados. O total é atualizado imediatamente, mantendo a geometria do cenário calculado.')
    all_on,all_off=st.columns(2)
    all_on.button('Selecionar todas',key=key+'_selecionar_todas',on_click=set_all_groups,args=(key,len(r['groups']),True),width='stretch')
    all_off.button('Desmarcar todas',key=key+'_desmarcar_todas',on_click=set_all_groups,args=(key,len(r['groups']),False),width='stretch')
    chosen=[]
    columns=st.columns(2)
    for i,g in enumerate(r['groups']):
        with columns[i%2]:
            if st.checkbox(g.split(' ',1)[1],value=True,key=f'{key}_grupo_{i}',persist_state='session'):
                chosen.append(g)
    with st.container(border=True):
        st.subheader('BDI do orçamento')
        apply_bdi=st.checkbox('Aplicar BDI',value=True,key=key+'_aplicar_bdi',persist_state='session')
        percentage=st.number_input('BDI personalizado (%)',min_value=0.0,max_value=100.0,
            value=r['scenario']['bdi']*100,step=0.5,format='%.6f',
            key=key+'_bdi_personalizado',persist_state='session')
        st.caption('Edite o percentual e pressione Enter ou clique fora do campo. Marque Aplicar BDI para incluir o acréscimo no total e nos grupos. Desmarque para consultar os custos sem BDI.')
    rate=percentage/100 if apply_bdi else 0.0
    signature=(tuple(chosen),rate)
    if st.session_state.get(key+'_selecao_anterior')!=signature:
        st.session_state.downloads.pop(key,None)
        st.session_state[key+'_selecao_anterior']=signature
    return select_groups(r,chosen,bdi_rate=rate)


def render_result(r,key,compact=False):
    st.caption('Cenário calculado: '+caption(r))
    with st.container(horizontal=not compact):
        st.metric('Total com BDI' if r['scenario']['bdi'] else 'Total sem BDI',currency(r['total']),border=True)
        st.metric('Por km de corredor',currency(r['per_km']),border=True)
        if not compact:st.metric('Por km de linha',currency(r['per_line_km']),border=True)
    if compact:
        st.dataframe(pd.DataFrame([{'Grupo':g,'Custo direto (R$)':v} for g,v in r['groups'].items()]),hide_index=True,column_config={'Custo direto (R$)':st.column_config.NumberColumn(format='%.2f')})
        return
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
    st.subheader('Rastreabilidade das fontes')
    counts=r['counts'];n=len(r['items'])
    with st.container(horizontal=True):
        for source in ['SIEC','SINAPI','SICRO','Mercado','Provisão']:
            st.metric(source,f"{counts.get(source,0)} itens",f"{br(100*counts.get(source,0)/n if n else 0,1)}% das linhas",delta_color='off',border=True)
    if counts.get('Provisão'):st.warning('Este cenário contém preços provisórios herdados, identificados separadamente de preços oficiais e anúncios de mercado.')
    if not r['items']:
        st.info('Nenhum serviço incluído no total. Selecione ao menos um grupo com serviços para gerar documentos.')
        return
    with st.expander('Memórias, origem dos itens e limites'):
        for warning in r['warnings']:st.write('• '+warning)
        st.caption(f"Prazo: {r['duration']} meses. Regra {r['rule_version']}.")
        st.dataframe(pd.DataFrame(r['items'])[['label','quantity_formula','origin','sheet','row','original_formula','note','provenance']],hide_index=True)
    st.subheader('Documentos do cenário')
    st.caption('Excel com fórmulas e bases utilizadas; Word editável; PDFs equivalentes do orçamento e relatório, gerados sem depender do Microsoft Office.')
    if st.button('Preparar arquivos para download',key=key+'_prepare',icon=':material/download:'):
        with st.spinner('Preparando Excel, Word e PDFs…'):st.session_state.downloads[key]=exports(r,version)
    if key in st.session_state.downloads:
        labels={'orcamento.xlsx':'Excel • orçamento','relatorio.docx':'Word • relatório','orcamento.pdf':'PDF • orçamento','relatorio.pdf':'PDF • relatório'}
        mimes={'xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','pdf':'application/pdf'}
        with st.container(horizontal=True):
            for name,content in st.session_state.downloads[key].items():st.download_button(labels[name],content,file_name=key+'_'+name,mime=mimes[name.split('.')[-1]],key=key+'_'+name,on_click='ignore')

page=st.segmented_control('Área de trabalho',['Orçamento','Comparar cenários','Base de dados','Regras e validação'],default='Orçamento',key='page',selection_mode='single')
if page=='Orçamento':
    with st.sidebar:st.header('Defina o cenário');form('main')
    st.caption('Ao abrir, exibimos o cenário de referência de 1 km. Para mudar suas características, ajuste o formulário e clique em Calcular Orçamento.')
    r=st.session_state.results.get('main')
    if r:render_result(scope_controls(r,'main'),'main')
    else:
        st.info('Configure o cenário à esquerda e selecione Calcular Orçamento.')
        with st.container(border=True):
            st.subheader('Uma base, nove grupos de serviço')
            st.write('Via permanente, topografia, drenagem, vedação, AMVs, infraestrutura de cabos, rede aérea, sinalização e material rodante, com memória de cálculo e rastreabilidade dos preços.')
            st.write('O modelo SIEC usa via lastreada e AMV nº 14. O modelo legado reproduz a Parte 2, incluindo elevado em placa e AMV nº 9 provisório.')
            st.caption('Custos por km se referem ao corredor. Uma via dupla contém dois km de linha por km de corredor.')
elif page=='Comparar cenários':
    st.subheader('Compare duas alternativas')
    st.caption('Cada cenário conserva os parâmetros do último cálculo. Altere o formulário e calcule novamente para atualizar a comparação.')
    effective={}
    for col,key in zip(st.columns(2),['A','B']):
        with col:
            st.markdown('### Cenário '+key);form(key,key=='B')
            if key in st.session_state.results:
                effective[key]=scope_controls(st.session_state.results[key],key)
                render_result(effective[key],key,True)
    a,b=effective.get('A'),effective.get('B')
    if a and b:
        with st.container(horizontal=True):
            st.metric('Diferença total • B − A',currency(b['total']-a['total']),border=True)
            st.metric('Diferença por km de corredor',currency(b['per_km']-a['per_km']),border=True)
        comp=pd.DataFrame([{'Grupo':g,'Cenário A':a['groups'][g],'Cenário B':b['groups'][g],'Diferença B − A':b['groups'][g]-a['groups'][g]} for g in rules['groups']])
        st.dataframe(comp,hide_index=True);st.bar_chart(comp,x='Grupo',y=['Cenário A','Cenário B'],stack=False,horizontal=True)
        if a['scenario']['profile']!=b['scenario']['profile']:st.warning('Os modelos diferem em geometria, via e AMV. A diferença não representa apenas variação de preço.')
        chosen=st.selectbox('Detalhar e exportar cenário',['A','B'])
        render_result(effective[chosen],chosen)
elif page=='Base de dados':
    st.subheader('Referências de preço consolidadas')
    frame=base(version)
    with st.container(horizontal=True):
        st.metric('Referências únicas',f'{len(frame):,}',border=True)
        st.metric('Com preço numérico',f'{frame.price.notna().sum():,}',border=True)
        st.metric('Sem preço',f'{frame.price.isna().sum():,}',border=True)
    st.caption('SIEC junho/2026; provisões declaradas setembro/2026; anúncio consultado em 13/09/2026. Não há tabelas SINAPI/SICRO nos arquivos recebidos. Registros sem preço não são tratados como zero.')
    search=st.text_input('Buscar código ou descrição',key='base_search')
    sources=st.multiselect('Fontes',frame.source.unique().tolist(),default=frame.source.unique().tolist())
    kind=st.selectbox('Disponibilidade',['Todas','Com preço','Sem preço'])
    frame=frame[frame.source.isin(sources)]
    if search:frame=frame[frame.code.str.contains(search,case=False,regex=False)|frame.description.str.contains(search,case=False,regex=False)]
    if kind!='Todas':frame=frame[frame.price.notna() if kind=='Com preço' else frame.price.isna()]
    st.caption(f'{len(frame):,} referências no filtro')
    st.dataframe(frame.rename(columns={'code':'Código','description':'Descrição','unit':'Unidade','price':'Preço unitário','source':'Fonte','date':'Data-base','provenance':'Arquivo / aba / linha'}),hide_index=True,height=600)
else:
    st.subheader('Regras e rastreabilidade')
    st.markdown((ROOT/'docs/MAPEAMENTO.md').read_text(encoding='utf-8'))
    with st.expander('Cobertura de todos os itens originais'):st.dataframe(pd.DataFrame(json.loads((ROOT/'config/coverage.json').read_text(encoding='utf-8'))),hide_index=True)
    with st.expander('Inventário das planilhas de origem'):st.dataframe(pd.DataFrame(json.loads((ROOT/'data/inventory.json').read_text(encoding='utf-8'))),hide_index=True)
    if st.button('Conferir quatro cenários da Parte 2',key='validate'):
        expected={('Elevado',1):53552530.02,('Elevado',2):80467223.28,('Superfície',1):13321596.60,('Superfície',2):20597620.85}
        rows=[]
        for (cfg,lines),value in expected.items():
            got=calculate(Scenario(profile='legacy',configuration=cfg,lines=lines,amvs=lines),rules,catalog)['total']
            rows.append({'Cenário':cfg+' '+str(lines),'Planilha manual':value,'Motor':got,'Diferença':round(got-value,2)})
        st.dataframe(pd.DataFrame(rows),hide_index=True)
        if all(abs(x['Diferença'])<.01 for x in rows):st.success('Os quatro totais coincidem com os orçamentos manuais.')
        else:st.error('Há divergências. Revise as regras e bases antes de utilizar os resultados.')
