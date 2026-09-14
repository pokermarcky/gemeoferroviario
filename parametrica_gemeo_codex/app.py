from pathlib import Path
import sqlite3
import json
import pandas as pd
import streamlit as st
from railbudget.engine import Scenario, load_model, calculate
from railbudget.exporters import export_all, currency, br, caption

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Gêmeo ferroviário | Codex',page_icon=':material/train:',layout='wide')
st.title('Gêmeo digital ferroviário')
st.caption('Cenários de investimento • Via permanente e serviços complementares • Codex')

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

def form(key,default_double=False):
    with st.form('form_'+key):
        profile=st.selectbox('Modelo de referência',list(rules['profiles']),format_func=lambda k:rules['profiles'][k]['label'],key=key+'_profile')
        km=st.number_input('Extensão do corredor (km)',min_value=0.01,max_value=10000.0,value=1.0,step=0.1,format='%.3f',key=key+'_km')
        configuration=st.selectbox('Configuração',['Superfície','Elevado'],key=key+'_configuration')
        lines=st.selectbox('Via',[1,2],index=int(default_double),format_func=lambda n:'Simples' if n==1 else 'Dupla',key=key+'_lines')
        drainage=st.selectbox('Drenagem',['Normal','Reforçada','Complexa'],index=1,key=key+'_drainage')
        fence=st.selectbox('Vedação da faixa',['Cerca','Muro','Nenhuma'],key=key+'_fence')
        amvs=st.number_input('Quantidade total de AMVs',min_value=0,max_value=100000,value=2 if default_double else 1,step=1,key=key+'_amvs',help='Total no corredor, distribuído entre as linhas. Não é quantidade por km.')
        ducts=st.checkbox('Incluir banco de seis dutos',value=True,key=key+'_ducts')
        topo=st.checkbox('Incluir topografia',value=True,key=key+'_topography')
        months=st.number_input('Prazo da obra (meses; 0 = referência)',min_value=0,max_value=1200,value=0,step=1,key=key+'_months',help='SIEC: 6 meses superfície / 18 elevado. Legado: 12 / 24 meses.')
        bdi=st.number_input('BDI (%)',min_value=0.0,max_value=100.0,value=27.84182802164763,format='%.6f',key=key+'_bdi')
        submit=st.form_submit_button('Calcular Orçamento',type='primary',width='stretch')
    if submit:
        try:
            p=Scenario(km=km,configuration=configuration,lines=lines,drainage=drainage,fence=fence,amvs=int(amvs),ducts=ducts,topography=topo,profile=profile,bdi=bdi/100,months=int(months))
            st.session_state.results[key]=calculate(p,rules,catalog)
            st.session_state.downloads.pop(key,None)
        except (ValueError,KeyError,ZeroDivisionError) as exc:
            st.session_state.results.pop(key,None);st.session_state.downloads.pop(key,None);st.error(str(exc))

def render_result(r,key,compact=False):
    st.caption('Cenário calculado: '+caption(r))
    with st.container(horizontal=not compact):
        st.metric('Total com BDI',currency(r['total']),border=True)
        st.metric('Por km de corredor',currency(r['per_km']),border=True)
        if not compact:st.metric('Por km de linha',currency(r['per_line_km']),border=True)
    if compact:
        st.dataframe(pd.DataFrame([{'Grupo':g,'Custo direto (R$)':v} for g,v in r['groups'].items()]),hide_index=True,column_config={'Custo direto (R$)':st.column_config.NumberColumn(format='%.2f')})
        return
    st.subheader('Composição do investimento')
    st.bar_chart(pd.DataFrame({'Grupo':list(r['groups']),'Custo direto (R$)':list(r['groups'].values())}),x='Grupo',y='Custo direto (R$)',horizontal=True,color='#147D83')
    counts=r['counts'];n=len(r['items'])
    with st.container(horizontal=True):
        for source in ['SIEC','SINAPI','SICRO','Mercado','Provisão']:
            st.metric(source,f"{counts.get(source,0)} itens",f"{br(100*counts.get(source,0)/n,1)}% das linhas",delta_color='off',border=True)
    if counts.get('Provisão'):st.warning('Este cenário contém preços provisórios herdados, identificados separadamente de preços oficiais e anúncios de mercado.')
    st.subheader('EAP orçada')
    columns={'eap':'EAP','group':'Grupo','code':'Código','source':'Fonte','label':'Aplicação','description':'Descrição','unit':'Unidade','quantity':'Quantidade','unit_cost':'Custo unitário (R$)','total':'Custo total (R$)','date':'Data-base'}
    frame=pd.DataFrame(r['items'])[list(columns)].rename(columns=columns)
    st.dataframe(frame,hide_index=True,height=530,column_config={'Quantidade':st.column_config.NumberColumn(format='%.6f'),'Custo unitário (R$)':st.column_config.NumberColumn(format='%.2f'),'Custo total (R$)':st.column_config.NumberColumn(format='%.2f')})
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
    r=st.session_state.results.get('main')
    if r:render_result(r,'main')
    else:
        st.info('Configure o cenário à esquerda e selecione Calcular Orçamento.')
        with st.container(border=True):
            st.subheader('Uma base, seis grupos de serviço')
            st.write('Via permanente, topografia, drenagem, vedação, AMVs e banco de dutos, com memória de cálculo e rastreabilidade dos preços.')
            st.write('O modelo SIEC usa via lastreada e AMV nº 14. O modelo legado reproduz a Parte 2, incluindo elevado em placa e AMV nº 9 provisório.')
            st.caption('Custos por km se referem ao corredor. Uma via dupla contém dois km de linha por km de corredor.')
elif page=='Comparar cenários':
    st.subheader('Compare duas alternativas')
    st.caption('Cada cenário conserva os parâmetros do último cálculo. Altere o formulário e calcule novamente para atualizar a comparação.')
    for col,key in zip(st.columns(2),['A','B']):
        with col:
            st.markdown('### Cenário '+key);form(key,key=='B')
            if key in st.session_state.results:render_result(st.session_state.results[key],key,True)
    a,b=st.session_state.results.get('A'),st.session_state.results.get('B')
    if a and b:
        with st.container(horizontal=True):
            st.metric('Diferença total • B − A',currency(b['total']-a['total']),border=True)
            st.metric('Diferença por km de corredor',currency(b['per_km']-a['per_km']),border=True)
        comp=pd.DataFrame([{'Grupo':g,'Cenário A':a['groups'][g],'Cenário B':b['groups'][g],'Diferença B − A':b['groups'][g]-a['groups'][g]} for g in rules['groups']])
        st.dataframe(comp,hide_index=True);st.bar_chart(comp,x='Grupo',y=['Cenário A','Cenário B'],stack=False,horizontal=True)
        if a['scenario']['profile']!=b['scenario']['profile']:st.warning('Os modelos diferem em geometria, via e AMV. A diferença não representa apenas variação de preço.')
        chosen=st.selectbox('Detalhar e exportar cenário',['A','B'])
        render_result(st.session_state.results[chosen],chosen)
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
