"""Desenha assets/tecnologias.svg: a grade de tecnologias do README.

Existe porque <table> no README ganha borda do CSS do GitHub e ele
descarta atributo style, entao nao da para tirar a linha por CSS. Num
SVG unico a grade fica sem borda nenhuma e com o icone no tamanho que
a gente escolher.

Os icones vem do skillicons.dev, embutidos de uma vez por grupo. Como
cada resposta traz ids proprios, cada grupo recebe um prefixo antes de
entrar no arquivo -- sem isso um <defs> sobrescreveria o outro.

Rode de novo so quando mudar a lista abaixo.
"""

import re
import os
import sys
import urllib.request

LARGURA = 830
ALTURA_ICONE = 36
ROTULO = "#8B949E"   # discreto: o icone e que tem cor
FONTE = "'Segoe UI', Ubuntu, Sans-Serif"

GRUPOS = [
    ("Back-end", "python,django,flask,fastapi,php,nodejs"),
    ("Front-end", "html,css,js,ts,react,tailwind,bootstrap"),
    ("Mobile", "flutter,dart"),
    ("Banco de dados", "postgres,mysql,sqlite,redis"),
    ("DevOps e ferramentas",
     "docker,linux,nginx,git,github,githubactions,bash,vscode,postman"),
]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAIDA = os.path.join(RAIZ, "assets", "tecnologias.svg")


def baixa(icones):
    url = f"https://skillicons.dev/icons?i={icones}&theme=dark"
    req = urllib.request.Request(url, headers={"User-Agent": "readme-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def desmonta(svg, prefixo):
    """Devolve (largura, altura, miolo) com os ids prefixados."""
    vb = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if not vb:
        sys.exit("skillicons devolveu SVG sem viewBox")
    _, _, w, h = (float(v) for v in vb.group(1).split())

    miolo = re.sub(r"^.*?<svg[^>]*>", "", svg, count=1, flags=re.S)
    miolo = re.sub(r"</svg>\s*$", "", miolo, flags=re.S)

    for ident in set(re.findall(r'id="([^"]+)"', miolo)):
        novo = f"{prefixo}_{ident}"
        miolo = miolo.replace(f'id="{ident}"', f'id="{novo}"')
        miolo = miolo.replace(f"url(#{ident})", f"url(#{novo})")
        miolo = miolo.replace(f'href="#{ident}"', f'href="#{novo}"')
    return w, h, miolo


partes = []
y = 8
for i, (nome, icones) in enumerate(GRUPOS):
    w, h, miolo = desmonta(baixa(icones), f"g{i}")
    escala = ALTURA_ICONE / h
    largura_final = w * escala

    sozinho = i == len(GRUPOS) - 1 and len(GRUPOS) % 2 == 1
    if sozinho:
        centro = LARGURA / 2
    else:
        centro = LARGURA / 4 if i % 2 == 0 else LARGURA * 3 / 4

    partes.append(
        f'  <text x="{centro:.0f}" y="{y + 12}" text-anchor="middle" '
        f'fill="{ROTULO}" font-size="10.5" font-weight="600" '
        f'letter-spacing="1.6">{nome.upper()}</text>'
    )
    x = centro - largura_final / 2
    partes.append(
        f'  <g transform="translate({x:.1f} {y + 28}) scale({escala:.5f})">\n'
        f"{miolo.strip()}\n  </g>"
    )

    if i % 2 == 1 or sozinho:
        y += ALTURA_ICONE + 52

altura = y + 4

svg = f"""<svg width="{LARGURA}" height="{altura:.0f}" viewBox="0 0 {LARGURA} {altura:.0f}"
     fill="none" xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink" role="img">
  <style>text {{ font-family: {FONTE}; }}</style>
{chr(10).join(partes)}
</svg>
"""

os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
with open(SAIDA, "w", encoding="utf-8", newline="\n") as f:
    f.write(svg)

print(f"assets/tecnologias.svg  {LARGURA}x{altura:.0f}  {len(svg)} bytes")
for nome, icones in GRUPOS:
    print(f"  {nome:22} {len(icones.split(','))} icones")
