"""Modelo avançado e auditável para o elevado de passageiros."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import math

from .engine import Scenario, calculate
from .expressions import money


DECK_FACTORS={
    'Vigas pré-moldadas com laje':(1.00,'Solução de referência SIEC.'),
    'Viga U pré-moldada':(1.08,'Coeficiente preliminar sobre o tabuleiro de referência.'),
    'Viga-caixão pré-moldada segmental':(1.12,'Coeficiente preliminar para segmentação, protensão e montagem.'),
    'Viga-caixão moldada no local':(1.20,'Coeficiente preliminar para formas, protensão e concretagem no local.'),
    'Tabuleiro misto aço-concreto':(1.35,'Coeficiente preliminar; exige composição específica em projeto.'),
}
PIER_FACTORS={
    'Pilar único circular':(1.00,'Seção de referência.'),
    'Pilar único retangular':(1.03,'Ajuste preliminar de forma e armadura.'),
    'Pilar-parede':(1.12,'Ajuste preliminar de volume, forma e armadura.'),
    'Pórtico':(1.28,'Ajuste preliminar para pilares e travessa do pórtico.'),
}
GEOTECH_FACTORS={
    'Favorável':(.92,'Menor complexidade relativa de blocos e serviços de fundação.'),
    'Intermediária':(1.00,'Condição de referência.'),
    'Desfavorável':(1.25,'Provisão paramétrica para maior complexidade geotécnica.'),
}
METHOD_FACTORS={
    'Montagem com guindaste':(1.00,'Método de referência.'),
    'Lançadeira de vigas':(1.08,'Provisão para equipamento, montagem e logística.'),
    'Aduelas pré-moldadas':(1.15,'Provisão para aduelas, protensão e montagem segmental.'),
    'Cimbramento e concretagem no local':(1.20,'Provisão para cimbramento, formas e operação local.'),
}
EXECUTION_FACTORS={
    'Frente livre':(1.00,'Sem acréscimo paramétrico.'),
    'Ambiente urbano controlado':(1.08,'Acréscimo sobre mobilização, canteiro e administração.'),
    'Janelas noturnas e interdições':(1.18,'Acréscimo sobre mobilização, canteiro e administração.'),
}

FOUNDATION_LABELS={'Sondagens','Mobilização fundações','Estacas','Armadura das estacas',
    'Escavação de blocos','Blocos e encontros'}
PIER_LABELS={'Pilares e travessas'}
DECK_LABELS={'Aparelhos de apoio','Laje de distribuição','Vigas pré-moldadas','Impermeabilização'}
EXECUTION_LABELS={'Canteiro','Mobilização','Administração local'}
SENSITIVE_ELEVATED_ROWS={12,*range(19,38)}
SENSITIVE_DRAINAGE_ROWS={44,45}
SUPPORT_DEPENDENT_ROWS={12,*range(20,31),44,45}


def default_segment(p):
    return {'Trecho':'Trecho 1','Extensão (km)':float(p.km),'Altura (m)':float(p.elevated_height),
        'Vão (m)':float(p.elevated_span),'Fundação':p.foundation_type,
        'Diâmetro (m)':float(p.pile_diameter),'Profundidade (m)':float(p.foundation_depth),
        'Estacas/apoio':int(p.piles_per_support),'Interferência':p.urban_interference}


def normalize_segments(raw,p):
    rows=list(raw or [default_segment(p)])
    clean=[]
    for index,row in enumerate(rows,1):
        if not isinstance(row,dict):raise ValueError('Cada trecho do elevado deve ser uma linha válida.')
        length=float(row.get('Extensão (km)',0) or 0)
        if length<=0:raise ValueError(f'A extensão do trecho {index} deve ser maior que zero.')
        clean.append({'Trecho':str(row.get('Trecho') or f'Trecho {index}')[:40],
            'Extensão (km)':length,'Altura (m)':float(row.get('Altura (m)',p.elevated_height)),
            'Vão (m)':float(row.get('Vão (m)',p.elevated_span)),
            'Fundação':str(row.get('Fundação',p.foundation_type)),
            'Diâmetro (m)':float(row.get('Diâmetro (m)',p.pile_diameter)),
            'Profundidade (m)':float(row.get('Profundidade (m)',p.foundation_depth)),
            'Estacas/apoio':int(row.get('Estacas/apoio',p.piles_per_support)),
            'Interferência':str(row.get('Interferência',p.urban_interference))})
    total=sum(row['Extensão (km)'] for row in clean)
    if not math.isclose(total,p.km,abs_tol=.001):
        raise ValueError(f'A soma dos trechos ({total:.3f} km) deve ser igual à extensão do corredor ({p.km:.3f} km).')
    return clean


def _row_number(item):
    try:return int(item['id'].rsplit(':',1)[1])
    except (ValueError,IndexError):return None


def _sensitive(item):
    row=_row_number(item)
    return ((item['id'].startswith('vp:Elevado:') and row in SENSITIVE_ELEVATED_ROWS) or
        (item['id'].startswith('p2:3 Drenagem:') and row in SENSITIVE_DRAINAGE_ROWS))


def _distribute_amvs(total,segments):
    allocated=[0]*len(segments)
    for _ in range(total):
        candidates=[i for i,row in enumerate(segments)
            if (allocated[i]+1)*50 < row['Extensão (km)']*1000]
        if not candidates:raise ValueError('Não há trecho com extensão suficiente para distribuir os AMVs informados.')
        chosen=max(candidates,key=lambda i:segments[i]['Extensão (km)']/(allocated[i]+1))
        allocated[chosen]+=1
    return allocated


def _scale(item,factor,criterion):
    if math.isclose(factor,1):return
    item['quantity']*=factor
    item['total']=money(item['quantity']*item['unit_cost'])
    item['quantity_formula']=f"({item['quantity_formula']})*{factor:.6f}"
    item['note']=item['note'].rstrip('.')+'. '+criterion


def _provision(result,identifier,label,total,note,unit='vb',quantity=1.0):
    total=money(total)
    if total<=0:return
    unit_cost=money(total/quantity)
    key='Provisão|Serviços|elevado|'+identifier
    price={'key':key,'code':'PR-ELEV-'+identifier.upper(),'source':'Provisão','kind':'Serviços',
        'description':label,'unit':unit,'price':unit_cost,'date':'Premissa do cenário','provenance':'Premissa paramétrica editável.'}
    result.setdefault('custom_prices',{})[key]=price
    result['items'].append({'id':'elevado:'+identifier,'eap':'','group':'1 Via permanente','label':label,
        'code':price['code'],'source':'Provisão','description':label,'unit':unit,'quantity':quantity,
        'unit_cost':unit_cost,'total':total,'price_key':key,'date':price['date'],
        'quantity_formula':f'{quantity:g} × custo unitário informado','original_formula':'',
        'note':note,'origin':'Regra paramétrica complementar','sheet':'Elevado','row':'Provisão',
        'provenance':price['provenance'],'original_eap':''})


def _recompute(result):
    order=list(result['groups'])
    result['items'].sort(key=lambda item:(order.index(item['group']),item.get('_segment_order',0),item['id']))
    sequence=Counter()
    for item in result['items']:
        group=item['group'].split()[0];sequence[group]+=1
        prefix=('1.1.'+str(result['scenario']['lines'])) if group=='1' else group
        item['eap']=prefix+'.'+str(sequence[group]).zfill(3)
        item.pop('_segment_order',None)
    result['groups']={group:money(sum(item['total'] for item in result['items'] if item['group']==group)) for group in order}
    result['direct']=money(sum(item['total'] for item in result['items']))
    result['bdi_amount']=money(result['direct']*result['scenario']['bdi'])
    result['total']=money(result['direct']+result['bdi_amount'])
    km=result['scenario']['km'];lines=result['scenario']['lines']
    result['per_km']=money(result['total']/km);result['per_line_km']=money(result['total']/(km*lines))
    result['counts']=dict(Counter(item['source'] for item in result['items']))


def _indicators(result,segments):
    elevated=result['elevated'];width=elevated['active_width'];area=result['scenario']['km']*1000*width
    concrete=sum(item['quantity'] for item in result['items'] if item['unit']=='m³' and
        any(word in (item['label']+' '+item['description']).lower() for word in ('concreto','blocos','pilares','laje','vigas')))
    steel=sum(item['quantity'] for item in result['items'] if item['unit']=='kg' and
        any(word in (item['label']+' '+item['description']).lower() for word in ('armadura','aço')))
    components=elevated['components']
    return {'Custo por apoio':money(result['total']/max(elevated['supports'],1)),
        'Custo por vão':money(result['total']/max(elevated['spans'],1)),
        'Custo por m² de tabuleiro':money(result['total']/max(area,1)),
        'Concreto estrutural estimado (m³)':concrete,'Aço estrutural estimado (kg)':steel,
        'Participação das fundações (%)':100*components['Fundações']/result['direct'] if result['direct'] else 0,
        'Trechos homogêneos':len(segments)}


def calculate_elevated(p,rules,catalog,segments=None):
    """Calcula elevado segmentado e aplica coeficientes técnicos declarados."""
    if p.configuration!='Elevado':return calculate(p,rules,catalog)
    choices=[(p.deck_type,DECK_FACTORS,'tipologia do tabuleiro'),(p.pier_type,PIER_FACTORS,'tipologia dos pilares'),
        (p.geotechnical_condition,GEOTECH_FACTORS,'condição geotécnica'),
        (p.construction_method,METHOD_FACTORS,'método executivo'),
        (p.execution_constraint,EXECUTION_FACTORS,'condição de execução')]
    for value,options,label in choices:
        if value not in options:raise ValueError('Valor inválido para '+label+'.')
    nonnegative=[(p.special_span_length,'extensão de vãos especiais'),
        (p.special_span_addition,'adicional dos vãos especiais'),
        (p.transition_unit_cost,'custo dos encontros e transições'),
        (p.noise_barrier_length,'extensão da barreira acústica'),
        (p.noise_barrier_height,'altura da barreira acústica'),
        (p.noise_barrier_unit_cost,'custo da barreira acústica')]
    for value,label in nonnegative:
        if not math.isfinite(value) or value<0:raise ValueError(label.capitalize()+' deve ser não negativa.')
    if p.special_span_length>p.km*1000:raise ValueError('A extensão de vãos especiais não pode superar o corredor.')
    if type(p.transitions) is not int or p.transitions<0:raise ValueError('Quantidade de encontros e transições deve ser inteira e não negativa.')
    clean=normalize_segments(segments if segments is not None else p.elevated_segments,p)
    result=calculate(p,rules,catalog)
    first=clean[0]
    segment_override=(len(clean)>1 or not math.isclose(first['Extensão (km)'],p.km) or
        not math.isclose(first['Altura (m)'],p.elevated_height) or
        not math.isclose(first['Vão (m)'],p.elevated_span) or first['Fundação']!=p.foundation_type or
        not math.isclose(first['Diâmetro (m)'],p.pile_diameter) or
        not math.isclose(first['Profundidade (m)'],p.foundation_depth) or
        first['Estacas/apoio']!=p.piles_per_support or first['Interferência']!=p.urban_interference)
    if segment_override:
        retained=[item for item in result['items'] if not _sensitive(item)]
        replacement=[];mobilizations=set();amvs=_distribute_amvs(p.amvs,clean)
        segment_summaries=[]
        for index,(row,segment_amvs) in enumerate(zip(clean,amvs),1):
            segment_p=replace(p,km=row['Extensão (km)'],amvs=segment_amvs,
                elevated_height=row['Altura (m)'],elevated_span=row['Vão (m)'],
                foundation_type=row['Fundação'],foundation_depth=row['Profundidade (m)'],
                piles_per_support=row['Estacas/apoio'],pile_diameter=row['Diâmetro (m)'],
                urban_interference=row['Interferência'],elevated_segments=())
            partial=calculate(segment_p,rules,catalog)
            for source in partial['items']:
                if not _sensitive(source):continue
                if source['label']=='Mobilização fundações':
                    if source['code'] in mobilizations:continue
                    mobilizations.add(source['code'])
                item=deepcopy(source);item['id']+=f':trecho:{index}'
                item['label']=row['Trecho']+' · '+item['label'];item['_segment_order']=index
                item['note']=f"{row['Trecho']}, {row['Extensão (km)']:.3f} km. "+item['note']
                if index>1 and _row_number(source) in SUPPORT_DEPENDENT_ROWS:
                    factor=partial['elevated']['spans']/partial['elevated']['supports']
                    _scale(item,factor,'O apoio inicial é compartilhado com o trecho anterior e foi contabilizado uma única vez.')
                replacement.append(item)
            supports=partial['elevated']['supports']-(1 if index>1 else 0)
            piles=supports*row['Estacas/apoio']
            segment_summaries.append({**row,'Vãos':partial['elevated']['spans'],
                'Apoios':supports,'Estacas':piles,
                'Extensão de estacas (m)':piles*row['Profundidade (m)'],
                'Capacidade nominal/apoio (tf)':partial['elevated']['nominal_capacity_per_support']})
        result['items']=retained+replacement
        result['elevated']['spans']=sum(row['Vãos'] for row in segment_summaries)
        result['elevated']['supports']=sum(row['Apoios'] for row in segment_summaries)
        result['elevated']['total_piles']=sum(row['Estacas'] for row in segment_summaries)
        result['elevated']['total_pile_length']=sum(row['Extensão de estacas (m)'] for row in segment_summaries)
        result['elevated']['nominal_capacity_per_support']=min(row['Capacidade nominal/apoio (tf)'] for row in segment_summaries)
        result['elevated']['segment_summaries']=segment_summaries
    else:
        result['elevated']['segment_summaries']=[{**clean[0],'Vãos':result['elevated']['spans'],
            'Apoios':result['elevated']['supports'],'Estacas':result['elevated']['total_piles'],
            'Extensão de estacas (m)':result['elevated']['total_pile_length'],
            'Capacidade nominal/apoio (tf)':result['elevated']['nominal_capacity_per_support']}]

    deck_factor,deck_note=DECK_FACTORS[p.deck_type]
    pier_factor,pier_note=PIER_FACTORS[p.pier_type]
    geotech_factor,geotech_note=GEOTECH_FACTORS[p.geotechnical_condition]
    method_factor,method_note=METHOD_FACTORS[p.construction_method]
    execution_factor,execution_note=EXECUTION_FACTORS[p.execution_constraint]
    for item in result['items']:
        plain_label=item['label'].split(' · ')[-1]
        if plain_label in FOUNDATION_LABELS:_scale(item,geotech_factor,geotech_note)
        if plain_label in PIER_LABELS:_scale(item,pier_factor,pier_note)
        if plain_label in DECK_LABELS:_scale(item,deck_factor*method_factor,deck_note+' '+method_note)
        if plain_label in EXECUTION_LABELS:_scale(item,execution_factor,execution_note)
    _recompute(result)
    current_deck=sum(x['total'] for x in result['items'] if x['label'].split(' · ')[-1] in DECK_LABELS)
    current_piers=sum(x['total'] for x in result['items'] if x['label'].split(' · ')[-1] in PIER_LABELS)
    structural_per_m=(current_deck+current_piers)/(p.km*1000)
    _provision(result,'vao_especial','Adicional para vãos especiais',
        p.special_span_length*structural_per_m*p.special_span_addition/100,
        f'Provisão editável: {p.special_span_length:.2f} m com adicional de {p.special_span_addition:.2f}% sobre a referência estrutural por metro.')
    _provision(result,'transicoes','Encontros e transições',p.transitions*p.transition_unit_cost,
        'Quantidade e custo unitário informados pelo usuário.',unit='un',quantity=float(p.transitions) if p.transitions else 1)
    barrier_area=p.noise_barrier_length*p.noise_barrier_height
    _provision(result,'barreira_acustica','Barreira acústica',barrier_area*p.noise_barrier_unit_cost,
        'Provisão fora da SIEC; área e custo unitário editáveis.',unit='m²',quantity=barrier_area if barrier_area else 1)
    _recompute(result)
    result['scenario']['elevated_segments']=clean
    result['elevated']['technical_factors']={
        'Tipologia do tabuleiro':{'choice':p.deck_type,'factor':deck_factor,'criterion':deck_note},
        'Tipologia dos pilares':{'choice':p.pier_type,'factor':pier_factor,'criterion':pier_note},
        'Condição geotécnica':{'choice':p.geotechnical_condition,'factor':geotech_factor,'criterion':geotech_note},
        'Método executivo':{'choice':p.construction_method,'factor':method_factor,'criterion':method_note},
        'Restrição executiva':{'choice':p.execution_constraint,'factor':execution_factor,'criterion':execution_note},
    }
    components={
        'Fundações':money(sum(x['total'] for x in result['items'] if x['label'].split(' · ')[-1] in FOUNDATION_LABELS)),
        'Pilares e travessas':money(sum(x['total'] for x in result['items'] if x['label'].split(' · ')[-1] in PIER_LABELS)),
        'Tabuleiro':money(sum(x['total'] for x in result['items'] if x['label'].split(' · ')[-1] in DECK_LABELS)),
    }
    group1=next(value for group,value in result['groups'].items() if group.startswith('1 '))
    components['Via, proteções e provisões']=money(group1-sum(components.values()))
    result['elevated']['components']=components
    result['elevated']['indicators']=_indicators(result,clean)
    result['warnings'].append('Coeficientes de tipologia, método e condição geotécnica são premissas paramétricas declaradas; substitua-os por composições de projeto quando disponíveis.')
    return result


def sensitivity(result,p,rules,catalog,segments):
    """Sensibilidade central de quatro variáveis, mantendo as demais premissas."""
    base=result['total'];rows=[]
    clean=normalize_segments(segments,p)
    tests=[('Altura dos pilares','elevated_height','Altura (m)',.10),
        ('Distância entre pilares','elevated_span','Vão (m)',.10),
        ('Largura do tabuleiro','elevated_width_single' if p.lines==1 else 'elevated_width_double',None,.10),
        ('Profundidade das estacas','foundation_depth','Profundidade (m)',.10)]
    for label,field,segment_field,variation in tests:
        current=getattr(p,field)
        if len(clean)>1 and segment_field:
            low_segments=[{**row,segment_field:row[segment_field]*(1-variation)} for row in clean]
            high_segments=[{**row,segment_field:row[segment_field]*(1+variation)} for row in clean]
            low=calculate_elevated(p,rules,catalog,low_segments)['total']
            high=calculate_elevated(p,rules,catalog,high_segments)['total']
        else:
            low=calculate_elevated(replace(p,**{field:current*(1-variation)}),rules,catalog,clean if len(clean)>1 else None)['total']
            high=calculate_elevated(replace(p,**{field:current*(1+variation)}),rules,catalog,clean if len(clean)>1 else None)['total']
        rows.append({'Parâmetro':label,'Variação':'±10%','Cenário inferior (R$)':low,
            'Cenário-base (R$)':base,'Cenário superior (R$)':high,
            'Amplitude sobre o total (%)':100*(max(low,high)-min(low,high))/base if base else 0})
    return rows
