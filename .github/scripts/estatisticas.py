"""Gera os cartoes de estatistica do README.

Desenha tres SVGs em assets/ com os numeros reais lidos da API do
GitHub, usando o token em GH_TOKEN. Conta repositorio privado e
contribuicao privada -- as instancias hospedadas por terceiros nao
conseguem, porque o token delas e do dono da instancia, nao seu.

Roda sem dependencia externa, so biblioteca padrao.
"""

import collections
import hashlib
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request

USUARIO = "Frizzeraneto0"
NOME = "Rivadávia Neto"

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
README = os.path.join(RAIZ, "README.md")
ASSETS = os.path.join(RAIZ, "assets")
INICIO = "<!-- ESTATISTICAS:INICIO -->"
FIM = "<!-- ESTATISTICAS:FIM -->"

FUNDO = "#0D1117"
TITULO = "#8B5CF6"
TEXTO = "#C9D1D9"
APAGADO = "#8B949E"
ACENTO = "#EC4899"
TRILHO = "#21262D"
FONTE = "'Segoe UI', Ubuntu, Sans-Serif"
LAYOUT = "2"  # muda junto com o desenho, para furar o cache

# cores oficiais do GitHub para as linguagens que aparecem por aqui
COR_LINGUAGEM = {
    "Python": "#3572A5", "PHP": "#4F5D95", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#663399", "JavaScript": "#f1e05a",
    "C++": "#f34b7d", "CMake": "#DA3434", "Dart": "#00B4AB",
    "PLpgSQL": "#336790", "Shell": "#89e051", "Dockerfile": "#384d54",
    "C": "#555555", "Java": "#b07219", "Kotlin": "#A97BFF",
    "Ruby": "#701516", "Go": "#00ADD8", "Rust": "#dea584",
    "Swift": "#F05138", "SCSS": "#c6538c", "Vue": "#41b883",
    "Jupyter Notebook": "#DA5B0B", "Makefile": "#427819",
}
RESERVA = ["#8B5CF6", "#EC4899", "#6366F1", "#22D3EE", "#F59E0B",
           "#10B981", "#F43F5E", "#A78BFA"]

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("faltou GH_TOKEN")


# ---------------------------------------------------------------- API

def api(caminho, cabecalhos=None):
    req = urllib.request.Request("https://api.github.com/" + caminho)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    for k, v in (cabecalhos or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def graphql(consulta):
    corpo = json.dumps({"query": consulta}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=corpo)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        resposta = json.load(r)
    if "errors" in resposta:
        sys.exit("GraphQL: %s" % resposta["errors"])
    return resposta["data"]


# ------------------------------------------------------------ desenho

def num(n):
    """1078 -> 1.078"""
    return f"{n:,}".replace(",", ".")


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def estrela(cx, cy, r, cor):
    pontos = []
    for i in range(10):
        raio = r if i % 2 == 0 else r * 0.42
        ang = math.radians(-90 + i * 36)
        pontos.append(f"{cx + raio * math.cos(ang):.2f},"
                      f"{cy + raio * math.sin(ang):.2f}")
    return f'<polygon points="{" ".join(pontos)}" fill="{cor}"/>'


def icone(tipo, x, y, cor):
    """Icone de 14x14 com canto superior esquerdo em (x, y)."""
    cx, cy = x + 7, y + 7
    if tipo == "estrela":
        return estrela(cx, cy, 7, cor)
    if tipo == "commit":
        return (f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="none" '
                f'stroke="{cor}" stroke-width="2"/>'
                f'<path d="M{x} {cy}h3.2M{cx + 3.4} {cy}H{x + 14}" '
                f'stroke="{cor}" stroke-width="2" stroke-linecap="round"/>')
    if tipo == "pr":
        return (f'<circle cx="{x + 3}" cy="{y + 3}" r="2.6" fill="none" '
                f'stroke="{cor}" stroke-width="2"/>'
                f'<circle cx="{x + 3}" cy="{y + 12}" r="2.6" fill="none" '
                f'stroke="{cor}" stroke-width="2"/>'
                f'<circle cx="{x + 12}" cy="{y + 4}" r="2.6" fill="none" '
                f'stroke="{cor}" stroke-width="2"/>'
                f'<path d="M{x + 3} {y + 6}v3M{x + 12} {y + 7}v2" '
                f'stroke="{cor}" stroke-width="2" stroke-linecap="round"/>')
    if tipo == "repo":
        return (f'<rect x="{x + 1}" y="{y + 1}" width="12" height="12" rx="2" '
                f'fill="none" stroke="{cor}" stroke-width="2"/>'
                f'<path d="M{x + 4} {y + 1}v12" stroke="{cor}" '
                f'stroke-width="2"/>')
    if tipo == "calendario":
        return (f'<rect x="{x + 1}" y="{y + 2}" width="12" height="11" rx="2" '
                f'fill="none" stroke="{cor}" stroke-width="2"/>'
                f'<path d="M{x + 1} {y + 6}h12M{x + 4.5} {y}v3M{x + 9.5} {y}v3" '
                f'stroke="{cor}" stroke-width="2" stroke-linecap="round"/>')
    if tipo == "chama":
        return (f'<path d="M{cx} {y}c3 3.5 5.5 5.5 5.5 8.6a5.5 5.5 0 0 1-11 0'
                f'C{cx - 5.5} {y + 5.6} {cx - 2} {y + 4} {cx} {y}z" '
                f'fill="{cor}"/>')
    return ""


def anel(cx, cy, raio, fracao, rotulo, sub, cor):
    volta = 2 * math.pi * raio
    return f"""  <g>
    <circle cx="{cx}" cy="{cy}" r="{raio}" fill="none" stroke="{TRILHO}" stroke-width="6"/>
    <circle cx="{cx}" cy="{cy}" r="{raio}" fill="none" stroke="{cor}" stroke-width="6"
            stroke-linecap="round" stroke-dasharray="{volta:.1f}"
            stroke-dashoffset="{volta * (1 - fracao):.1f}"
            transform="rotate(-90 {cx} {cy})"/>
    <text x="{cx}" y="{cy + 1}" text-anchor="middle" fill="{TEXTO}"
          font-size="20" font-weight="700">{esc(rotulo)}</text>
    <text x="{cx}" y="{cy + 17}" text-anchor="middle" fill="{APAGADO}"
          font-size="10">{esc(sub)}</text>
  </g>"""


def moldura(largura, altura, titulo, miolo):
    cabecalho = ""
    if titulo:
        cabecalho = (f'  <text x="25" y="36" fill="{TITULO}" font-size="17" '
                     f'font-weight="600">{esc(titulo)}</text>\n')
    return f"""<svg width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}"
     fill="none" xmlns="http://www.w3.org/2000/svg" role="img">
  <style>
    text {{ font-family: {FONTE}; }}
  </style>
  <rect width="{largura}" height="{altura}" rx="12" fill="{FUNDO}"/>
{cabecalho}{miolo}
</svg>
"""


# ------------------------------------------------------------- dados

dados = graphql(
    """
{
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    pullRequests { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""
    % USUARIO
)["user"]

calendario = dados["contributionsCollection"]["contributionCalendar"]
grade = sorted((d for s in calendario["weeks"] for d in s["contributionDays"]),
               key=lambda d: d["date"])

maior = corrente = 0
for d in grade:
    corrente = corrente + 1 if d["contributionCount"] > 0 else 0
    maior = max(maior, corrente)
atual = corrente
if grade and grade[-1]["contributionCount"] == 0:
    atual = 0
    for d in reversed(grade[:-1]):
        if d["contributionCount"] == 0:
            break
        atual += 1

ativos = sum(1 for d in grade if d["contributionCount"] > 0)

# intervalo da maior sequencia e data em que a atual comecou
melhor = corrente = 0
fim_maior = comeco_atual = None
for i, d in enumerate(grade):
    if d["contributionCount"] > 0:
        corrente += 1
        if corrente > melhor:
            melhor, fim_maior = corrente, d["date"]
    else:
        corrente = 0
inicio_maior = None
if fim_maior:
    pos = next(i for i, d in enumerate(grade) if d["date"] == fim_maior)
    inicio_maior = grade[pos - maior + 1]["date"]
if atual:
    comeco_atual = grade[len(grade) - atual]["date"]

commits = api(
    "search/commits?q=" + urllib.parse.quote(f"author:{USUARIO}") + "&per_page=1",
    {"Accept": "application/vnd.github.cloak-preview+json"},
)["total_count"]

por_lingua = collections.Counter()
estrelas = 0
for repo in dados["repositories"]["nodes"]:
    estrelas += repo["stargazerCount"]
    for aresta in repo["languages"]["edges"]:
        por_lingua[aresta["node"]["name"]] += aresta["size"]

total_bytes = sum(por_lingua.values()) or 1
repos = dados["repositories"]["totalCount"]
prs = dados["pullRequests"]["totalCount"]
contribuicoes = calendario["totalContributions"]


# ---------------------------------------------------- cartao 1: geral

linhas = [
    ("estrela", "Estrelas recebidas", num(estrelas)),
    ("commit", "Commits", num(commits)),
    ("pr", "Pull requests", num(prs)),
    ("repo", "Repositórios", num(repos)),
    ("calendario", "Contribuições (12 meses)", num(contribuicoes)),
]
miolo = []
y = 66
for i, (tipo, rotulo, valor) in enumerate(linhas):
    miolo.append(
        f'  <g>\n'
        f'    {icone(tipo, 25, y - 11, ACENTO)}\n'
        f'    <text x="49" y="{y}" fill="{TEXTO}" font-size="14" '
        f'font-weight="600">{esc(rotulo)}</text>\n'
        f'    <text x="330" y="{y}" fill="{TEXTO}" font-size="14" '
        f'font-weight="700" text-anchor="end">{valor}</text>\n'
        f'  </g>'
    )
    y += 25
miolo.append(anel(398, 112, 38, ativos / max(len(grade), 1),
                  str(ativos), "dias ativos", TITULO))

with open(os.path.join(ASSETS, "estatisticas.svg"), "w",
          encoding="utf-8", newline="\n") as f:
    f.write(moldura(470, 195, f"Estatísticas de {NOME}", "\n".join(miolo)))


# ----------------------------------------------- cartao 2: linguagens

principais = por_lingua.most_common(8)
miolo = []
x, barra_y, barra_l = 25, 56, 300
for i, (nome, tamanho) in enumerate(principais):
    fatia = tamanho / total_bytes * barra_l
    cor = COR_LINGUAGEM.get(nome, RESERVA[i % len(RESERVA)])
    ponta = ' rx="4"' if i == 0 else ""
    miolo.append(f'  <rect x="{x:.1f}" y="{barra_y}" width="{max(fatia, 1):.1f}" '
                 f'height="9" fill="{cor}"{ponta}/>')
    x += fatia

y = 92
for i, (nome, tamanho) in enumerate(principais):
    coluna = i % 2
    if coluna == 0 and i:
        y += 22
    cx = 25 + coluna * 160
    cor = COR_LINGUAGEM.get(nome, RESERVA[i % len(RESERVA)])
    pct = tamanho / total_bytes * 100
    miolo.append(
        f'  <g>\n'
        f'    <circle cx="{cx + 5}" cy="{y - 4}" r="5" fill="{cor}"/>\n'
        f'    <text x="{cx + 16}" y="{y}" fill="{TEXTO}" font-size="12">'
        f'{esc(nome)} {pct:.2f}%</text>\n'
        f'  </g>'
    )

with open(os.path.join(ASSETS, "linguagens.svg"), "w",
          encoding="utf-8", newline="\n") as f:
    f.write(moldura(350, 195, "Linguagens mais usadas", "\n".join(miolo)))


# ------------------------------------------------ cartao 3: sequencia

L, A = 830, 130
painel = L / 3
miolo = [
    f'  <path d="M{painel:.0f} 26v78M{painel * 2:.0f} 26v78" '
    f'stroke="{TRILHO}" stroke-width="1"/>'
]


def bloco(centro, valor, rotulo, sub, destaque=False):
    cor = ACENTO if destaque else TEXTO
    return (
        f'  <g>\n'
        f'    <text x="{centro:.0f}" y="62" text-anchor="middle" fill="{TEXTO}"'
        f' font-size="30" font-weight="700">{esc(valor)}</text>\n'
        f'    <text x="{centro:.0f}" y="86" text-anchor="middle" fill="{cor}"'
        f' font-size="13" font-weight="600">{esc(rotulo)}</text>\n'
        f'    <text x="{centro:.0f}" y="104" text-anchor="middle" '
        f'fill="{APAGADO}" font-size="10">{esc(sub)}</text>\n'
        f'  </g>'
    )


def br(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


miolo.append(bloco(painel / 2, num(contribuicoes), "Contribuições",
                   "últimos 12 meses"))
miolo.append(f'  {icone("chama", int(painel * 1.5) - 7, 20, ACENTO)}')
miolo.append(bloco(painel * 1.5, str(atual), "Sequência atual",
                   f"desde {br(comeco_atual)}" if comeco_atual else "sem sequência",
                   destaque=True))
miolo.append(bloco(painel * 2.5, str(maior), "Maior sequência",
                   f"{br(inicio_maior)} a {br(fim_maior)}" if fim_maior else "—"))

with open(os.path.join(ASSETS, "sequencia.svg"), "w",
          encoding="utf-8", newline="\n") as f:
    f.write(moldura(L, A, "", "\n".join(miolo)))


# -------------------------------------------------------- bloco final

assinatura = hashlib.sha1(
    f"{estrelas}|{commits}|{prs}|{repos}|{contribuicoes}|{atual}|{maior}|"
    f"{ativos}|{principais}|{LAYOUT}".encode()
).hexdigest()[:8]
base = f"https://raw.githubusercontent.com/{USUARIO}/{USUARIO}/main/assets"

bloco_readme = f"""{INICIO}
<div align="center">

<img src="{base}/estatisticas.svg?v={assinatura}" alt="Estatísticas do GitHub" />
<img src="{base}/linguagens.svg?v={assinatura}" alt="Linguagens mais usadas" />

<img src="{base}/sequencia.svg?v={assinatura}" alt="Sequência de contribuições" />

</div>
{FIM}"""

texto = open(README, encoding="utf-8").read()
padrao = re.compile(re.escape(INICIO) + ".*?" + re.escape(FIM), re.S)
if not padrao.search(texto):
    sys.exit("marcadores nao encontrados no README")
novo = padrao.sub(lambda _: bloco_readme, texto)
if novo != texto:
    open(README, "w", encoding="utf-8", newline="\n").write(novo)

print(f"cartoes gerados (assinatura {assinatura})")
print(f"  estrelas      : {estrelas}")
print(f"  commits       : {num(commits)}")
print(f"  pull requests : {num(prs)}")
print(f"  repositorios  : {repos}")
print(f"  contribuicoes : {num(contribuicoes)}  ({ativos} dias ativos)")
print(f"  sequencias    : atual {atual}, maior {maior}")
print(f"  linguagens    : {len(por_lingua)} ({num(total_bytes)} bytes)")
