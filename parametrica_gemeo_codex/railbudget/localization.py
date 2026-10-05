"""Rótulos em português para memórias apresentadas ao usuário.

As expressões executáveis e fórmulas do Excel continuam com identificadores
internos; esta camada altera apenas o texto exibido.
"""
import re

NOMES = {
    "km": "extensão do corredor (km)",
    "configuration": "configuração",
    "lines": "quantidade de vias",
    "drainage": "tipo de drenagem",
    "fence": "tipo de vedação",
    "amvs": "quantidade de AMVs",
    "ducts": "incluir dutos",
    "topography": "incluir topografia",
    "overhead": "incluir rede aérea",
    "signaling": "incluir sinalização",
    "detection": "detecção de trens",
    "rolling_stock": "incluir material rodante",
    "trainsets": "quantidade de composições",
    "profile": "modelo de referência",
    "bdi": "taxa de BDI",
    "months": "prazo informado (meses)",
    "duration": "prazo adotado (meses)",
    "envelope": "extensão ocupada por AMV (m)",
    "span": "vão da estrutura (m)",
    "height": "altura da estrutura (m)",
    "L": "extensão do corredor (m)",
    "run": "extensão de via corrida (m)",
    "low_amvs": "AMVs por via (mínimo)",
    "extra": "vias com AMV adicional",
    "sleepers": "quantidade de dormentes",
    "management": "fator de gestão",
    "foundation": "fator de fundações",
    "spans": "quantidade de vãos",
    "supports": "quantidade de apoios",
    "surface_area": "área de superfície (m²)",
    "deck_area": "área do tabuleiro (m²)",
    "ballast": "volume de lastro (m³)",
    "welds": "quantidade de soldas",
    "overhead_supports": "apoios da rede aérea",
    "tension_sections": "trechos de tensionamento",
    "sectioning_points": "pontos de seccionamento",
    "signal_blocks": "blocos de sinalização",
    "signal_points": "pontos de sinalização",
    "interlockings": "setores de intertravamento",
    "double_width_add": "largura adicional da via dupla (m)",
    "double_foundation_factor": "fator de fundações da via dupla",
    "double_management_factor": "fator de gestão da via dupla",
    "overhead_span": "vão dos suportes da rede aérea (m)",
    "tension_length": "comprimento do trecho de tensionamento (m)",
    "sectioning_length": "intervalo de seccionamento (m)",
    "signal_block_length": "comprimento do bloco de sinalização (m)",
    "interlocking_length": "intervalo de intertravamento (m)",
    "ceil": "arredondar para cima",
    "floor": "arredondar para baixo",
    "min": "mínimo",
    "max": "máximo",
    "V5": "extensão do corredor",
    "V6": "extensão ocupada por AMV",
    "V8": "massa linear do trilho TR-57",
    "V15": "espessura do sublastro",
    "V18": "estacas por apoio",
    "V19": "comprimento médio das estacas",
    "V20": "prazo paramétrico",
    "V21": "prazo paramétrico",
    "V22": "horas mensais da administração local",
    "V23": "distância média de transporte do lastro",
    "P5": "extensão do corredor",
    "P7": "extensão ocupada por AMV",
    "P8": "AMVs por via",
    "P9": "largura da plataforma de via simples",
    "P10": "largura da plataforma de via dupla",
    "P11": "largura do tabuleiro de via simples",
    "P12": "largura do tabuleiro de via dupla",
    "P13": "vão estrutural de referência",
    "P14": "estacas por apoio em via simples",
    "P15": "estacas por apoio em via dupla",
    "P16": "comprimento médio das estacas",
    "P17": "volume do bloco em via simples",
    "P18": "volume do bloco em via dupla",
    "P19": "volume do pilar em via simples",
    "P20": "volume do pilar em via dupla",
    "P21": "prazo paramétrico",
    "P22": "prazo paramétrico",
    "P23": "horas mensais de monitoramento",
    "P24": "largura da faixa em via simples",
    "P25": "largura da faixa em via dupla",
    "P29": "espaçamento entre caixas",
    "P30": "quantidade de dutos",
    "P33": "horas previstas de bombeamento",
}
IDENTIFICADOR = re.compile(r"\b[A-Za-z_][A-Za-z_0-9]*\b")
PARAMETRO = re.compile(r"[VP]\d+")


def nome_variavel(nome):
    if nome in NOMES:
        return NOMES[nome]
    if PARAMETRO.fullmatch(nome):
        return "Parâmetro " + nome
    return nome


def formula_legivel(expressao):
    """Apresenta a memória sem modificar a expressão usada no cálculo."""
    return IDENTIFICADOR.sub(lambda match: nome_variavel(match.group()), expressao).replace("**", "^")


UNIDADES = {
    "km": "km", "L": "m", "run": "m", "envelope": "m", "span": "m",
    "height": "m", "duration": "meses", "V5": "m", "V6": "m",
    "V8": "kg/m", "V15": "m", "V18": "un", "V19": "m",
    "V20": "meses", "V21": "meses", "V22": "h/mês", "V23": "km",
    "P5": "m", "P7": "m", "P8": "un/via", "P9": "m", "P10": "m",
    "P11": "m", "P12": "m", "P13": "m", "P14": "un", "P15": "un",
    "P16": "m", "P17": "m³", "P18": "m³", "P19": "m³", "P20": "m³",
    "P21": "meses", "P22": "meses", "P23": "h/mês", "P24": "m",
    "P25": "m", "P29": "m", "P30": "un", "P33": "h",
}


def numero_legivel(valor, casas=6):
    texto=f"{float(valor):,.{casas}f}".rstrip('0').rstrip('.')
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def memoria_quantidade(expressao, contexto, quantidade, unidade):
    """Transforma a expressão técnica em uma memória curta, avaliada e legível."""
    def substituir(match):
        nome=match.group()
        rotulo=nome_variavel(nome)
        if nome not in contexto:return rotulo
        sufixo=(' '+UNIDADES[nome]) if nome in UNIDADES else ''
        return f"{rotulo} ({numero_legivel(contexto[nome])}{sufixo})"
    texto=IDENTIFICADOR.sub(substituir,str(expressao).replace('**','^'))
    texto=texto.replace('*',' × ').replace('/',' ÷ ')
    texto=re.sub(r'\s+',' ',texto).strip()
    return f"{texto} = {numero_legivel(quantidade)} {unidade}"
