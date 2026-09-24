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
}
IDENTIFICADOR = re.compile(r"\b[A-Za-z_][A-Za-z_0-9]*\b")
PARAMETRO = re.compile(r"[VP]\d+")


def nome_variavel(nome):
    if PARAMETRO.fullmatch(nome):
        return "Parâmetro " + nome
    return NOMES.get(nome, nome)


def formula_legivel(expressao):
    """Apresenta a memória sem modificar a expressão usada no cálculo."""
    return IDENTIFICADOR.sub(lambda match: nome_variavel(match.group()), expressao).replace("**", "^")
