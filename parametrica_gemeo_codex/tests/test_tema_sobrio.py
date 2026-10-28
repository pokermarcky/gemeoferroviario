import colorsys
import re
from pathlib import Path

from railbudget import elevated_drawing
from railbudget.interface import STYLE

ROOT = Path(__file__).resolve().parents[1]
# Laranja e amarelo vivos retirados a pedido do Marcelo (28/10/2026).
VIVOS = ['#e2712a', '#f4b63f', '#d8742f', '#e0913c', '#d0541f', '#f0a03a', '#c9862a', '#ffe4a8', '#c4421f', '#ffe2b0']


def _saturation(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)[2]


def test_tema_nao_usa_mais_laranja_vivo():
    textos = [STYLE, (ROOT / 'railbudget' / 'elevated_drawing.py').read_text(encoding='utf-8'),
              (ROOT / '.streamlit' / 'config.toml').read_text(encoding='utf-8'),
              (ROOT / 'app.py').read_text(encoding='utf-8'),
              (ROOT / 'railbudget' / 'static_scene_v2.py').read_text(encoding='utf-8')]
    for texto in textos:
        for cor in VIVOS:
            assert cor not in texto.lower()


def test_degrade_mantem_vermelho_e_tons_sobrios():
    grad = re.search(r'--grad:linear-gradient\(([^)]*)\)', STYLE).group(1)
    cores = re.findall(r'#[0-9a-fA-F]{6}', grad)
    assert cores[0] == '#b8322a'
    assert all(_saturation(c) < 0.5 for c in cores[1:])


def test_via_permanente_do_desenho_continua_distinguivel():
    via = [elevated_drawing.RAIL, elevated_drawing.SLEEPER, elevated_drawing.BALLAST, elevated_drawing.CURB]
    assert len(set(via)) == len(via)
    assert _saturation(elevated_drawing.SLEEPER) < 0.5 and _saturation(elevated_drawing.BALLAST) < 0.5
