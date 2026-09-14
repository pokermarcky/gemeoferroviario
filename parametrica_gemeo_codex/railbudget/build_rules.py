"""Estrutura as memórias já extraídas; uso de manutenção, sem interface alternativa."""
import json
import re
import sqlite3
from pathlib import Path

def build(root):
    root=Path(root)
    s=json.loads((root/'data/snapshots.json').read_text(encoding='utf-8'))
    with sqlite3.connect(root/'data/catalog.sqlite') as con:
        keys={r[0]:r[1] for r in con.execute('SELECT code,key FROM prices')}
    def formula(value, prefix):
        return re.sub(r"'Premissas(?: Parte 2)?'!\$?B\$?(\d+)",lambda m:prefix+m[1],str(value).lstrip('='))
    config={'version':'1.0.0','source_priority':['SIEC','SINAPI','SICRO','Mercado','Provisão'],
            'profiles':{'siec':{'label':'SIEC • lastro / AMV nº 14','envelope':50,'surface_months':6,'elevated_months':18,'span':20,'height':8},
                        'legacy':{'label':'Legado Parte 2 • elevado em placa / AMV nº 9','envelope':40,'surface_months':12,'elevated_months':24,'span':30,'height':9}},
            'groups':['1 Via permanente','2 Topografia','3 Drenagem','4 Vedação','5 AMVs','6 Banco de dutos'],
            'constants':{'double_width_add':4,'double_foundation_factor':1.5,'double_management_factor':1.25},
            'parameters':{},'derived':[], 'rules':[]}
    for origin,tab,prefix in [('vp','Premissas','V'),('p2','Premissas Parte 2','P')]:
        for i,row in enumerate(s[origin][tab]['values'],1):
            if i>=5 and len(row)>1 and isinstance(row[1],(int,float)):
                config['parameters'][prefix+str(i)]=row[1]
    # Ordered context definitions, with model-specific values injected by the engine.
    config['derived']=[
        ['L','km*1000'],['run','L*lines-amvs*envelope'],
        ['low_amvs','floor(amvs/lines)'],['extra','amvs-low_amvs*lines'],
        ['sleepers','(lines-extra)*ceil((L-low_amvs*envelope)/0.6)+extra*ceil((L-(low_amvs+1)*envelope)/0.6)'],
        ['management','1+(lines-1)*(double_management_factor-1)'],
        ['foundation','1+(lines-1)*(double_foundation_factor-1)'],
        ['spans','ceil(L/span)'],['supports','spans+1'],
        ['surface_area','L*(6+double_width_add*(lines-1))+amvs*envelope*2'],
        ['deck_area','L*(7+double_width_add*(lines-1))+amvs*envelope*2'],
        ['ballast','(2.175*run-sleepers*2.8*0.28*0.2+3.5*amvs*envelope-300*amvs*0.28*0.2)*1.1'],
        ['welds','ceil(110*run/950)'],
        ['V5','L'],['V6','envelope'],['P5','L'],['P7','envelope'],['P8','amvs/lines'],
        ['P13','span'],['P21','duration'],['P22','duration'],['V20','duration'],['V21','duration']]
    coverage=[]
    for config_name,tab in [('Superfície','Superfície'),('Elevado','Elevado')]:
        sh=s['vp'][tab]
        for n,row in enumerate(sh['formulas'],1):
            if len(row)<12 or not isinstance(row[3],str) or not row[3].startswith('SIEC-'):continue
            val=sh['values'][n-1]; eap,group,label,code=row[:4]
            excluded=label=='Topografia' or group=='02 Drenagem' or label in ('Canaletas de cabos','Passa-fios','Conexões')
            coverage.append({'origin':'vp','sheet':tab,'row':n,'eap':eap,'label':label,'destination':'Substituído pelo grupo geral correspondente' if excluded else 'Perfil SIEC'})
            if excluded:continue
            expr=formula(row[8],'V'); q=val[8]
            g='5 AMVs' if group=='07 AMV' else '1 Via permanente'
            if group=='07 AMV':expr=f'({expr})*amvs'
            elif label in ('Canteiro','Administração local'):expr=f'({expr})*management'
            elif label=='Sondagens':expr='1' if n==11 else ('ceil(L/100)*12' if config_name=='Superfície' else 'supports*20')
            elif label in ('Mobilização','Mobilização fundações'):pass
            elif group=='06 Superestrutura ferroviária':
                if label=='Trilhos':expr='2*run*57/1000*1.02'
                elif label=='Dormentes':expr='sleepers'
                elif label=='Fixações':expr='sleepers*'+('2' if code.endswith('100.17') else '4')
                elif label=='Lastro':expr='ballast'
                elif label=='Transporte do lastro':expr='ballast*V23'
                elif label in ('Montagem','Regularização','Geometria final'):expr='run'
                elif label in ('Soldagem','Controle de soldas'):expr='welds'
            elif config_name=='Superfície':
                if label=='Plataforma':expr='surface_area'
                elif label=='Sublastro':expr='surface_area*V15'
                else:expr=f'{q}*km*(1+(lines-1)*double_width_add/6)'
            elif label=='Estacas':expr='supports*V18*V19*foundation'
            elif label=='Armadura das estacas':expr='supports*V18*V19*0.502655*90*foundation'
            elif label in ('Escavação de blocos','Blocos e encontros','Pilares e travessas'):expr=f'{q}*supports/51*foundation'
            elif label=='Aparelhos de apoio':expr='spans*160*foundation'
            elif label=='Laje de distribuição':expr=f'{q}*deck_area/7100'
            elif label=='Vigas pré-moldadas':expr=f'{q}*km*(1+(lines-1)*double_width_add/7)'
            elif label=='Impermeabilização':expr='deck_area'
            elif label in ('Contratrilhos de segurança','Montagem dos contratrilhos'):expr=f'({expr})*lines'
            r={'id':'vp:'+tab+':'+str(n),'profile':'siec','configuration':config_name,'group':g,'variant':'vp',
               'eap':eap,'label':label,'candidates':[keys[code]],'quantity':expr,'unit':val[7],
               'origin':'vp','sheet':tab,'row':n,'original_quantity':q,'original_total':val[10],
               'original_formula':row[8],'note':row[11]}
            config['rules'].append(r)
    for tab in [x for x in s['p2'] if x[:1] in '123456' and x[1:2]==' ']:
        sh=s['p2'][tab]
        for n,row in enumerate(sh['formulas'],1):
            if len(row)<12 or not isinstance(row[3],str) or row[3] not in keys:continue
            val=sh['values'][n-1];eap,variant,label,code=row[:4]
            group=tab
            expr=formula(row[8],'P')
            profile='legacy' if group.startswith(('1 ','5 ')) else 'both'
            cfg=None
            if group.startswith('1 '):cfg='Elevado' if variant.startswith('1.1.') else 'Superfície'
            if group.startswith('5 '):expr=f'({expr})*amvs'
            # Static reference quantities become explicit densities, not frozen totals.
            elif 'P5' not in expr and 'P21' not in expr and 'P22' not in expr:
                if val[7] not in ('vb',) and not group.startswith('2 '): expr=f'({expr})*km'
            # Discrete assets remain whole; original 1 km reference is preserved.
            if group=='3 Drenagem' and val[7]=='un':expr=f'ceil({expr})'
            if variant=='3.E' and 'Descidas' in label:expr='supports*height'
            # P2 sleeper counts need distribution by line when the total AMV count is odd.
            if group.startswith('1 ') and ('ceil' in expr.lower() or 'ROUNDUP' in expr) and 'P26' in expr:
                qty=val[8];expr='sleepers' if 'dormente' in label.lower() or 'Transporte' in label else '2*sleepers'
            coverage.append({'origin':'p2','sheet':tab,'row':n,'eap':eap,'label':label,'destination':'Perfil legado' if profile=='legacy' else 'Complemento compartilhado'})
            config['rules'].append({'id':'p2:'+tab+':'+str(n),'profile':profile,'configuration':cfg,'group':group,
                'variant':variant,'eap':eap,'label':label,'candidates':[keys[code]],'quantity':expr,'unit':val[7],
                'origin':'p2','sheet':tab,'row':n,'original_quantity':val[8],'original_total':val[10],
                'original_formula':row[8],'note':row[11]})
    (root/'config').mkdir(exist_ok=True)
    (root/'config/rules.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'config/coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    return config
