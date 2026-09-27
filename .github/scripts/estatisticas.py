"""Gera o bloco de estatisticas do README com numeros reais.

Le a API do GitHub com o token em GH_TOKEN e reescreve o trecho do
README entre os marcadores INICIO/FIM. Conta repositorio privado e
contribuicao privada, coisa que os cartoes hospedados por terceiros
nao conseguem: o token deles nao enxerga nada disso.

Roda sem dependencia externa, so biblioteca padrao.
"""

import collections
import json
import os
import re
import sys
import urllib.parse
import urllib.request

USUARIO = "Frizzeraneto0"
RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
README = os.path.abspath(os.path.join(RAIZ, "README.md"))
INICIO = "<!-- ESTATISTICAS:INICIO -->"
FIM = "<!-- ESTATISTICAS:FIM -->"

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("faltou GH_TOKEN")


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


def formata(n):
    """1078 -> 1.078"""
    return f"{n:,}".replace(",", ".")


def dias(n):
    return f"{n} dia" if n == 1 else f"{n} dias"


def badge(rotulo, valor, cor):
    r = urllib.parse.quote(rotulo.replace("-", "--"))
    v = urllib.parse.quote(str(valor).replace("-", "--"))
    return (
        f'<img src="https://img.shields.io/badge/{r}-{v}-{cor}'
        f'?style=for-the-badge&labelColor=1F2937" alt="" />'
    )


def sequencias(semanas):
    """Sequencia atual e maior sequencia, a partir do calendario."""
    grade = [d for s in semanas for d in s["contributionDays"]]
    grade.sort(key=lambda d: d["date"])
    maior = atual = 0
    for d in grade:
        if d["contributionCount"] > 0:
            atual += 1
            maior = max(maior, atual)
        else:
            atual = 0
    # o dia de hoje ainda pode fechar com contribuicao: nao zera por ele
    if grade and grade[-1]["contributionCount"] == 0:
        anterior = 0
        for d in reversed(grade[:-1]):
            if d["contributionCount"] > 0:
                anterior += 1
            else:
                break
        atual = anterior
    return atual, maior


dados = graphql(
    """
{
  user(login: "%s") {
    createdAt
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
    issues { totalCount }
    repositoriesContributedTo(
      includeUserRepositories: true
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]
    ) { totalCount }
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
atual, maior = sequencias(calendario["weeks"])

# commits de todo o historico, inclusive em repositorio privado
commits = api(
    "search/commits?q=" + urllib.parse.quote(f"author:{USUARIO}") + "&per_page=1",
    {"Accept": "application/vnd.github.cloak-preview+json"},
)["total_count"]

bytes_por_lingua = collections.Counter()
estrelas = 0
for repo in dados["repositories"]["nodes"]:
    estrelas += repo["stargazerCount"]
    for aresta in repo["languages"]["edges"]:
        bytes_por_lingua[aresta["node"]["name"]] += aresta["size"]

total_bytes = sum(bytes_por_lingua.values()) or 1
LARGURA = 26
linhas = []
for nome, tamanho in bytes_por_lingua.most_common(8):
    pct = tamanho * 100 / total_bytes
    cheio = round(pct / 100 * LARGURA)
    barra = "█" * cheio + "░" * (LARGURA - cheio)
    linhas.append(f"{nome:<12} {barra} {pct:5.2f}%")

bloco = f"""{INICIO}
<div align="center">

{badge("Contribuições (12 meses)", formata(calendario["totalContributions"]), "6366F1")}
{badge("Commits", formata(commits), "8B5CF6")}
{badge("Pull requests", formata(dados["pullRequests"]["totalCount"]), "EC4899")}
{badge("Repositórios", dados["repositories"]["totalCount"], "6366F1")}
{badge("Sequência atual", dias(atual), "8B5CF6")}
{badge("Maior sequência", dias(maior), "EC4899")}

</div>

**Linguagens**, por bytes de código — incluindo os repositórios privados:

```text
{chr(10).join(linhas)}
```

<sub>Gerado por <a href="../../actions/workflows/estatisticas.yml">.github/workflows/estatisticas.yml</a>, todo dia às 3h30.</sub>
{FIM}"""

texto = open(README, encoding="utf-8").read()
padrao = re.compile(re.escape(INICIO) + ".*?" + re.escape(FIM), re.S)
if not padrao.search(texto):
    sys.exit("marcadores nao encontrados no README")

novo = padrao.sub(lambda _: bloco, texto)
if novo == texto:
    print("sem mudanca")
else:
    open(README, "w", encoding="utf-8", newline="\n").write(novo)
    print("README atualizado")

print(f"  contribuicoes : {formata(calendario['totalContributions'])}")
print(f"  commits       : {formata(commits)}")
print(f"  pull requests : {formata(dados['pullRequests']['totalCount'])}")
print(f"  repositorios  : {dados['repositories']['totalCount']}")
print(f"  sequencias    : atual {atual}, maior {maior}")
print(f"  linguagens    : {len(bytes_por_lingua)} ({formata(total_bytes)} bytes)")
