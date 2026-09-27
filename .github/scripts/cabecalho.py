"""Desenha assets/banner.svg e assets/rodape.svg.

Substitui a onda do capsule-render por algo com cara de terminal:
fundo escuro com grade de pontos, brilho em gradiente e tipografia
monoespaçada. O par abre com "$ whoami" e fecha com "$ exit".

A fonte e a monoespacada do sistema -- SVG servido pelo raw nao carrega
fonte externa, entao pedir JetBrains Mono daria fallback silencioso.

Rode de novo so quando mudar o nome ou a chamada abaixo.
"""

import os

NOME = "Rivadávia Neto"
CHAMADA = "Desenvolvedor Full Stack · Automação · SaaS"
PROMPT = "rivadavia@github:~$"

LARGURA = 830
FUNDO = "#0D1117"
CLARO = "#E6EDF3"
APAGADO = "#7D8590"
GRADE = "#21262D"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(RAIZ, "assets")


def comuns(pref):
    """defs compartilhados: gradiente, grade de pontos e desfoque."""
    return f"""  <defs>
    <linearGradient id="{pref}_g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#6366F1"/>
      <stop offset="0.5" stop-color="#8B5CF6"/>
      <stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <pattern id="{pref}_grade" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.1" fill="{GRADE}"/>
    </pattern>
    <filter id="{pref}_blur" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="46"/>
    </filter>
    <linearGradient id="{pref}_esmaece" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#6366F1" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#8B5CF6" stop-opacity="1"/>
      <stop offset="1" stop-color="#EC4899" stop-opacity="0"/>
    </linearGradient>
  </defs>"""


def cursor(x, y, altura=22, largura=9):
    """Bloco piscando. Comeca visivel: se a animacao nao rodar, aparece."""
    return (f'<rect x="{x}" y="{y}" width="{largura}" height="{altura}" '
            f'fill="#8B5CF6" class="cursor"/>')


ESTILO = f"""  <style>
    text {{ font-family: {MONO}; }}
    .cursor {{ animation: pisca 1.2s steps(1) infinite; }}
    @keyframes pisca {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0.15; }} }}
  </style>"""


# ------------------------------------------------------------- banner

A = 210
banner = f"""<svg width="{LARGURA}" height="{A}" viewBox="0 0 {LARGURA} {A}"
     fill="none" xmlns="http://www.w3.org/2000/svg" role="img">
{comuns("b")}
{ESTILO}
  <rect width="{LARGURA}" height="{A}" rx="14" fill="{FUNDO}"/>
  <rect width="{LARGURA}" height="{A}" rx="14" fill="url(#b_grade)" opacity="0.55"/>

  <g opacity="0.4" filter="url(#b_blur)">
    <ellipse cx="120" cy="40" rx="150" ry="70" fill="#6366F1"/>
    <ellipse cx="470" cy="215" rx="200" ry="80" fill="#8B5CF6"/>
    <ellipse cx="800" cy="30" rx="150" ry="70" fill="#EC4899"/>
  </g>

  <g>
    <circle cx="30" cy="28" r="5" fill="#FF5F56" opacity="0.85"/>
    <circle cx="48" cy="28" r="5" fill="#FFBD2E" opacity="0.85"/>
    <circle cx="66" cy="28" r="5" fill="#27C93F" opacity="0.85"/>
  </g>
  <path d="M0 52h{LARGURA}" stroke="{GRADE}" stroke-width="1"/>

  <text x="40" y="94" font-size="13" fill="{APAGADO}">
    <tspan fill="#8B5CF6">{PROMPT}</tspan> whoami
  </text>

  <text x="40" y="146" font-size="42" font-weight="700" fill="{CLARO}"
        letter-spacing="-1">{NOME}</text>
  {cursor(x=40 + int(len(NOME) * (42 * 0.6 - 1)) + 10, y=124, altura=28, largura=13)}

  <text x="42" y="176" font-size="14" fill="{APAGADO}">
    <tspan fill="#8B5CF6">//</tspan> {CHAMADA}
  </text>

  <rect x="40" y="194" width="{LARGURA - 80}" height="2" rx="1"
        fill="url(#b_esmaece)" opacity="0.8"/>
</svg>
"""

# ------------------------------------------------------------- rodape

R = 108
rodape = f"""<svg width="{LARGURA}" height="{R}" viewBox="0 0 {LARGURA} {R}"
     fill="none" xmlns="http://www.w3.org/2000/svg" role="img">
{comuns("r")}
{ESTILO}
  <rect width="{LARGURA}" height="{R}" rx="14" fill="{FUNDO}"/>
  <rect width="{LARGURA}" height="{R}" rx="14" fill="url(#r_grade)" opacity="0.45"/>

  <g opacity="0.35" filter="url(#r_blur)">
    <ellipse cx="{LARGURA / 2}" cy="{R + 20}" rx="320" ry="70" fill="#8B5CF6"/>
  </g>

  <rect x="40" y="22" width="{LARGURA - 80}" height="2" rx="1"
        fill="url(#r_esmaece)" opacity="0.8"/>

  <text x="{LARGURA / 2}" y="66" text-anchor="middle" font-size="14"
        fill="{APAGADO}">
    <tspan fill="#8B5CF6">{PROMPT}</tspan> exit
  </text>
  {cursor(x=int(LARGURA / 2 + len(PROMPT) * 4.2 + 32), y=52, altura=17, largura=8)}
</svg>
"""

os.makedirs(ASSETS, exist_ok=True)
for nome, conteudo in (("banner.svg", banner), ("rodape.svg", rodape)):
    with open(os.path.join(ASSETS, nome), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(conteudo)
    print(f"assets/{nome}  {len(conteudo)} bytes")
