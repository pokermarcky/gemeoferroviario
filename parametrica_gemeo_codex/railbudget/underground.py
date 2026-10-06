"""Composição paramétrica preliminar de via subterrânea com referências SIEC."""

from collections import Counter
from dataclasses import asdict, replace
import math

from .engine import calculate, resolve_price
from .expressions import money


def _siec(code):
    return f'SIEC|Serviços|junho/2026|{code}'


def _item(catalog, priority, *, item_id, eap, group, label, code, quantity,
          formula, note, origin='subterraneo'):
    price=resolve_price([_siec(code)],catalog,priority)
    total=money(quantity*price['price'])
    return {
        'id':item_id,'eap':eap,'original_eap':eap,'group':group,'label':label,
        'code':price['code'],'source':price['source'],'description':price['description'],
        'unit':price['unit'],'quantity':quantity,'unit_cost':price['price'],'total':total,
        'price_key':price['key'],'date':price['date'],'quantity_formula':formula,
        'original_formula':formula,'note':note,'origin':origin,'sheet':'Modelo subterrâneo preliminar',
        'row':0,'provenance':price['provenance'],
    }


def calculate_underground(p, rules, catalog):
    """Calcula um túnel preliminar; não reaproveita terraplenagem ou estrutura de superfície."""
    if p.configuration!='Subterrâneo':
        raise ValueError('A composição subterrânea exige a configuração Subterrâneo.')

    # A validação geométrica e dos controles é reaproveitada por uma configuração reconhecida.
    proxy=replace(p,configuration='Elevado',fence='Nenhuma')
    common=calculate(proxy,rules,catalog)
    L=p.km*1000
    tubes=p.lines
    diameter=10.0
    excavation_area=math.pi*diameter**2/4
    perimeter=math.pi*diameter
    excavation=excavation_area*L*tubes
    projected_concrete=perimeter*.10*L*tubes
    final_lining=perimeter*.30*L*tubes
    lining_steel=final_lining*120
    waterproofing=perimeter*L*tubes
    slab_concrete=.75*L*tubes
    slab_mesh=slab_concrete*80
    run=max(0,L*tubes-p.amvs*rules['profiles'][p.profile]['envelope'])
    welds=math.ceil(110*run/950)
    priority=rules['source_priority']
    items=[]

    def add(group,label,code,quantity,formula,note):
        sequence=1+sum(item['group']==group for item in items)
        items.append(_item(catalog,priority,item_id=f'sub:{group.split()[0]}:{sequence:02}',
            eap=f'{group.split()[0]}.3.{sequence:03}',group=group,label=label,code=code,
            quantity=quantity,formula=formula,note=note))

    # Estrutura civil e via sobre laje. Uma via equivale a um tubo circular independente.
    add('1 Via permanente','Escavação da seção do túnel','SIEC-02.01.01.100.14',excavation,
        'π × (10 m)² ÷ 4 × extensão × número de tubos',
        'Equivalência preliminar com o serviço SIEC de escavação de tunnel liner; não define método executivo.')
    add('1 Via permanente','Carga do material escavado','SIEC-02.01.01.110.34',excavation,
        'volume escavado','Carga e descarga livres; destinação ambiental não incluída.')
    add('1 Via permanente','Transporte do material escavado','SIEC-02.01.01.110.30',excavation*20,
        'volume escavado × 20 km','Distância média de transporte adotada: 20 km.')
    add('1 Via permanente','Revestimento primário em concreto projetado','SIEC-02.01.05.110.11',projected_concrete,
        'perímetro do tubo × 0,10 m × extensão × número de tubos',
        'Preço equivalente SIEC de concreto projetado fck 30 MPa; item específico de túnel está sem preço na base.')
    add('1 Via permanente','Revestimento estrutural definitivo','SIEC-02.01.05.110.07',final_lining,
        'perímetro do tubo × 0,30 m × extensão × número de tubos',
        'Concreto estrutural fck 40 MPa; espessura preliminar de 0,30 m.')
    add('1 Via permanente','Armadura do revestimento definitivo','SIEC-02.01.05.300.33',lining_steel,
        'volume do revestimento × 120 kg/m³','Taxa preliminar de armadura: 120 kg/m³.')
    add('1 Via permanente','Impermeabilização do revestimento','SIEC-02.01.12.130.08',waterproofing,
        'perímetro do tubo × extensão × número de tubos','Manta asfáltica de 3 mm como equivalência SIEC.')
    add('1 Via permanente','Laje de apoio da via','SIEC-02.01.05.110.07',slab_concrete,
        '0,75 m³/m × extensão × número de vias','Seção preliminar: 3,00 m de largura por 0,25 m de espessura.')
    add('1 Via permanente','Armadura da laje de apoio','SIEC-11.04.01.100.27',slab_mesh,
        'volume da laje × 80 kg/m³','Taxa preliminar de tela: 80 kg/m³.')
    add('1 Via permanente','Fornecimento de trilhos TR-57','SIEC-03.04.01.100.08',2*run*57/1000*1.02,
        '2 trilhos × extensão útil × 57 kg/m × 1,02','Inclui perda paramétrica de 2%.')
    add('1 Via permanente','Montagem da via sobre estrutura de concreto','SIEC-03.03.04.100.22',run,
        'extensão útil × número de vias','Referência SIEC para bitola de 1.600 mm e fixação elástica.')
    add('1 Via permanente','Soldagem dos trilhos','SIEC-03.03.04.100.30',welds,
        'arredondar para cima (110 × extensão útil ÷ 950)','Quantidade paramétrica coerente com o modelo ferroviário existente.')

    if p.topography:
        add('2 Topografia','Pinos de convergência e nivelamento','SIEC-02.01.00.110.14',math.ceil(L/25)*tubes,
            '1 pino a cada 25 m por tubo','Monitoramento geométrico preliminar; instrumentação geotécnica completa não incluída.')

    channel_factor={'Normal':1,'Reforçada':2,'Complexa':2}[p.drainage]
    add('3 Drenagem','Canaletas longitudinais com grelha','SIEC-02.01.03.540.41',channel_factor*L*tubes,
        f'{channel_factor} canaleta(s) longitudinal(is) × extensão × número de tubos',
        'Dimensionamento hidráulico deverá confirmar a quantidade e a seção.')
    if p.drainage in ('Reforçada','Complexa'):
        add('3 Drenagem','Dreno profundo longitudinal','SIEC-02.01.03.540.25',L*tubes,
            'extensão × número de tubos','Referência SIEC com diâmetro de 0,20 m.')
    if p.drainage=='Complexa':
        add('3 Drenagem','Bombas submersíveis de drenagem','SIEC-02.03.07.110.66',2*math.ceil(p.km)*tubes,
            '2 bombas por km ou fração, por tubo','Redundância preliminar; poços, quadros e alimentação elétrica exigem projeto.')

    if p.fence!='Nenhuma':
        spacing=100
        points=math.ceil(L/spacing)*tubes
        add('4 Vedação','Conjuntos de hidrante','SIEC-02.02.05.300.73',math.ceil(L/200)*tubes,
            '1 conjunto a cada 200 m por tubo','Provisão de combate a incêndio; rede hidráulica e reservação não incluídas.')
        add('4 Vedação','Extintores de pó químico seco','SIEC-02.02.05.230.04',points,
            '1 unidade a cada 100 m por tubo','Distribuição preliminar.')
        add('4 Vedação','Acionadores manuais de alarme','SIEC-02.03.07.400.01',points,
            '1 unidade a cada 100 m por tubo','Central, detectores, cabeamento e integração não incluídos.')
        add('4 Vedação','Iluminação autônoma de emergência','SIEC-02.03.11.210.04',math.ceil(L/50)*tubes,
            '1 bloco a cada 50 m por tubo','Distribuição preliminar, sujeita a estudo luminotécnico e de abandono.')
        add('4 Vedação','Exaustores axiais de referência','SIEC-02.03.01.110.37',points,
            '1 conjunto a cada 100 m por tubo','Somente provisão por equivalência SIEC; não substitui o projeto de ventilação longitudinal do túnel.')

    if p.ducts:
        add('6 Infraestrutura de cabos','Canaletas técnicas com tampa','SIEC-02.01.03.540.43',2*L*tubes,
            '2 canaletas × extensão × número de tubos','Canaletas para segregação preliminar de energia, telecomunicações e controle; cabos não incluídos.')

    # Sistemas comuns são mantidos, mas componentes incompatíveis com túnel são retirados.
    kept_groups={'5 AMVs','7 Rede aérea','8 Sinalização','9 Material rodante'}
    excluded={'a2:7:01','a2:7:02'}
    for item in common['items']:
        if item['group'] not in kept_groups or item['id'] in excluded:
            continue
        copied=dict(item)
        if copied['id']=='a2:7:03':
            copied['label']='Suportes e conjuntos de suspensão da rede aérea'
        items.append(copied)

    order={group:index for index,group in enumerate(rules['groups'])}
    items.sort(key=lambda item:(order[item['group']],item['eap']))
    groups={group:money(sum(item['total'] for item in items if item['group']==group)) for group in rules['groups']}
    direct=money(sum(groups.values()))
    bdi=money(direct*p.bdi)
    total=money(direct+bdi)
    context={
        'km':p.km,'L':L,'lines':p.lines,'tubes':tubes,'tunnel_diameter':diameter,
        'excavation_area':excavation_area,'excavation_volume':excavation,
        'primary_lining_thickness':.10,'final_lining_thickness':.30,
        'haul_distance':20,'bdi':p.bdi,
    }
    warnings=[
        'Estimativa subterrânea preliminar por equivalência SIEC. Não constitui orçamento executivo nem define o método construtivo.',
        'Premissa geométrica: um tubo circular de 10,00 m de diâmetro para cada via; via dupla equivale a dois tubos independentes.',
        'A escavação usa o item SIEC de tunnel liner como referência. A composição SIEC de túnel com frente grampeada e o concreto projetado específico de túnel estão sem preço; foi empregado concreto projetado equivalente disponível.',
        'Não estão incluídos: poços e emboques, estações subterrâneas, passagens de emergência entre tubos, desapropriações, remanejamentos, tratamento de solo, interferências, destinação ambiental, tuneladora, segmentos pré-moldados e contingência geotécnica.',
        'Ventilação, incêndio, iluminação e bombeamento são provisões quantitativas iniciais. Dimensionamento de segurança, hidráulico, elétrico e de evacuação é obrigatório.',
        'O BDI é uma premissa editável; não houve reajuste monetário das datas-base.',
    ]
    if p.amvs:
        warnings.append('AMV nº 14 mantido como referência SIEC. Sua implantação em túnel e a adaptação à via sobre concreto exigem composição específica de projeto.')
    if p.overhead:
        warnings.append('Rede aérea: postes e implantação de postes foram retirados; os suportes foram tratados como fixações à estrutura do túnel. O arranjo elétrico final exige projeto.')
    if p.signaling:
        warnings.append(f'Sinalização paramétrica com detecção por {p.detection.lower()}; interfaces de túnel e centro de controle ainda dependem de projeto.')
    if p.rolling_stock:
        warnings.append(f'Material rodante mantido fora da natureza civil do túnel: {p.trainsets} composição(ões) de 8 carros, conforme a referência já adotada no sistema.')
    return {
        'scenario':asdict(p),'model_label':'SIEC • subterrâneo preliminar','duration':0,
        'items':items,'groups':groups,'direct':direct,'bdi_amount':bdi,'total':total,
        'per_km':money(total/p.km),'per_line_km':money(total/(p.km*p.lines)),
        'counts':dict(Counter(item['source'] for item in items)),'warnings':warnings,
        'rule_version':rules['version'],'derived':[],
        'context':context,
    }
