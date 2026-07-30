"""Imagens do painel, para o README, o site e o LinkedIn.

Quem abre o repositório quase nunca instala dependência. A planilha versionada resolve
metade do problema; a imagem resolve a outra metade, porque aparece antes de qualquer
clique. Por isso os prints são gerados por código junto com o relatório, e não
capturados de tela: nascem sempre coerentes com o número da rodada.

Mesma paleta do Excel — a peça precisa parecer uma peça só.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

TINTA = "#16324F"
GRAFITE = "#3B4A5A"
NEVOA = "#8496A8"
CLARO = "#F2F6FA"
LINHA = "#DAE3EC"
VERDE, VERDE_BG = "#1B7F5A", "#E4F3EC"
AMBAR, AMBAR_BG = "#9A6B08", "#FBF0DA"
VERMELHO, VERMELHO_BG = "#A83232", "#FAE6E6"
ACENTO = "#2E6F9E"

FAMILIA = ["Segoe UI", "DejaVu Sans"]


def _base_rc() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": FAMILIA,
            "axes.edgecolor": LINHA,
            "axes.labelcolor": GRAFITE,
            "text.color": GRAFITE,
            "xtick.color": GRAFITE,
            "ytick.color": GRAFITE,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _faixa(valor, bom, ruim, maior_e_melhor=True):
    if maior_e_melhor:
        if valor >= bom:
            return VERDE, VERDE_BG
        return (AMBAR, AMBAR_BG) if valor >= ruim else (VERMELHO, VERMELHO_BG)
    if valor <= bom:
        return VERDE, VERDE_BG
    return (AMBAR, AMBAR_BG) if valor <= ruim else (VERMELHO, VERMELHO_BG)


def _cartao(fig, x, y, w, h, rotulo, valor, contexto, pergunta, cor, cor_fundo):
    fig.patches.append(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0,rounding_size=0.008",
            transform=fig.transFigure, facecolor=cor_fundo, edgecolor=LINHA, linewidth=0.8,
        )
    )
    fig.patches.append(
        FancyBboxPatch(
            (x, y + h - 0.006), w, 0.006,
            boxstyle="square,pad=0",
            transform=fig.transFigure, facecolor=cor, edgecolor="none",
        )
    )
    pad = 0.014
    fig.text(x + pad, y + h - 0.036, rotulo.upper(), fontsize=8.5, color=NEVOA, weight="bold")
    fig.text(x + pad, y + h - 0.098, valor, fontsize=27, color=cor, weight="bold", va="center")
    fig.text(x + pad, y + h - 0.140, contexto, fontsize=8.5, color=GRAFITE)
    fig.text(
        x + pad, y + 0.020, pergunta, fontsize=8, color=NEVOA, style="italic",
        va="bottom", wrap=True,
    )


def print_painel(res: dict, cfg: dict, periodo: tuple[dt.date, dt.date], destino: Path) -> Path:
    """O painel inteiro em uma imagem: os seis cartões, o aging e a cobertura."""
    _base_rc()
    painel = res["painel"]
    leitura = cfg["leitura"]
    inicio, fim = periodo

    fig = plt.figure(figsize=(14, 8.6), dpi=170)

    fig.text(0.045, 0.945, "Painel de aderência a plano de ação",
             fontsize=23, color=TINTA, weight="bold")
    fig.text(
        0.045, 0.912,
        f"{cfg['cenario']['nome']} · {cfg['cenario']['n_clientes']} clientes · "
        f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y} · {painel['total_acoes']} ações acompanhadas",
        fontsize=10, color=GRAFITE,
    )
    fig.text(
        0.045, 0.890,
        "Dados sintéticos, gerados por código com semente fixa. Nenhum dado de cliente real.",
        fontsize=8.5, color=NEVOA, style="italic",
    )

    pct30 = painel["aging_mais_30_pct"]
    cartoes = [
        ("Aderência ao prazo", f"{painel['aderencia']:.0%}",
         f"{painel['aderencia_denominador']} ações com prazo vencido",
         "O acompanhamento está funcionando ou só registrando?",
         *_faixa(painel["aderencia"], leitura["aderencia_saudavel"], leitura["aderencia_critica"])),
        ("Pendências +30 dias", f"{painel['aging_mais_30']}",
         f"de {painel['pendencias_abertas']} em aberto ({pct30:.0%})",
         "+30 dias não é atraso, é ação abandonada.",
         *_faixa(pct30, 0.15, 0.30, maior_e_melhor=False)),
        ("Taxa de replanejamento", f"{painel['taxa_replanejamento']:.0%}",
         "das ações tiveram o prazo movido",
         "Prazo mal estimado ou execução travada?",
         *_faixa(painel["taxa_replanejamento"], 0.25, 0.45, maior_e_melhor=False)),
        ("Lead time mediano", f"{painel['lead_time_mediano']:.0f} dias",
         "da abertura à conclusão",
         "Quanto tempo prometer na próxima reunião.",
         ACENTO, CLARO),
        ("Cobertura", f"{painel['cobertura']:.0%}",
         "das semanas-cliente com reunião",
         "Dá para ler os números acima como carteira?",
         *_faixa(painel["cobertura"], leitura["cobertura_minima"], 0.55)),
        ("Clientes em risco crítico", f"{painel['clientes_criticos']}",
         f"topo: {painel['cliente_topo_risco'][:26]}",
         "Por quem começar a agenda da semana.",
         *((VERMELHO, VERMELHO_BG) if painel["clientes_criticos"] >= 5
           else (AMBAR, AMBAR_BG) if painel["clientes_criticos"] >= 2 else (VERDE, VERDE_BG))),
    ]

    largura, altura, folga = 0.288, 0.185, 0.017
    for i, cartao in enumerate(cartoes):
        x = 0.045 + (i % 3) * (largura + folga)
        y = 0.640 - (i // 3) * (altura + folga)
        _cartao(fig, x, y, largura, altura, *cartao)

    # ---- aging ----------------------------------------------------------------------
    aging = res["aging_faixas"]
    ax1 = fig.add_axes((0.045, 0.085, 0.42, 0.30))
    cores = [ACENTO, ACENTO, AMBAR, VERMELHO]
    barras = ax1.bar(aging["faixa"], aging["pendencias"], color=cores, width=0.62)
    ax1.bar_label(barras, padding=3, fontsize=9.5, color=GRAFITE, weight="bold")
    ax1.set_title("Pendências em aberto, por faixa de aging",
                  fontsize=11.5, color=TINTA, weight="bold", loc="left", pad=12)
    ax1.spines[["top", "right", "left"]].set_visible(False)
    ax1.tick_params(axis="y", length=0, labelleft=False)
    ax1.tick_params(axis="x", length=0, labelsize=9.5)
    ax1.set_ylim(0, aging["pendencias"].max() * 1.22)
    ax1.grid(False)

    # ---- cobertura ------------------------------------------------------------------
    cob = res["cobertura_semanal"]
    ax2 = fig.add_axes((0.545, 0.085, 0.41, 0.30))
    ax2.plot(cob["semana"], cob["cobertura"], color=ACENTO, linewidth=2.2)
    ax2.fill_between(cob["semana"], 0, cob["cobertura"], color=ACENTO, alpha=0.10)
    ax2.axhline(leitura["cobertura_minima"], color=VERMELHO, linewidth=1.1, linestyle=(0, (4, 3)))
    ax2.text(
        cob["semana"].max(), leitura["cobertura_minima"] - 0.10,
        f"mínimo de leitura {leitura['cobertura_minima']:.0%}",
        fontsize=8, color=VERMELHO, ha="right",
    )
    ax2.set_xlim(cob["semana"].min(), cob["semana"].max())
    ax2.set_title("Cobertura de acompanhamento, semana a semana",
                  fontsize=11.5, color=TINTA, weight="bold", loc="left", pad=12)
    ax2.set_ylim(0, 1.05)
    ax2.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax2.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
    ax2.set_xlabel("semana do período", fontsize=9, color=NEVOA)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.grid(axis="y", color=LINHA, linewidth=0.7)
    ax2.set_axisbelow(True)

    fig.text(
        0.045, 0.028,
        "Aderência medida contra o prazo ORIGINAL, não contra o prazo reprogramado. "
        "Ações canceladas fora dos denominadores.",
        fontsize=8, color=NEVOA, style="italic",
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, bbox_inches=None)
    plt.close(fig)
    return destino


def print_ranking(res: dict, destino: Path) -> Path:
    """A agenda da semana: os dez clientes no topo do risco."""
    _base_rc()
    topo = res["ranking"].head(10).iloc[::-1]

    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=170)
    cores = [
        VERMELHO if c == "Crítico" else AMBAR if c == "Atenção" else VERDE
        for c in topo["classificacao"]
    ]
    barras = ax.barh(topo["nome"], topo["score_risco"], color=cores, height=0.62)
    for barra, (_, linha) in zip(barras, topo.iterrows()):
        ax.text(
            barra.get_width() + 1.4, barra.get_y() + barra.get_height() / 2,
            f"{linha['score_risco']:.0f}   ·   {int(linha['pendencias_vencidas'])} vencidas   ·   "
            f"aging {linha['aging_medio']:.0f}d   ·   {linha['taxa_replanejamento']:.0%} replanejado",
            va="center", fontsize=8.5, color=GRAFITE,
        )

    ax.set_title(
        "A agenda da semana — ranking de risco por cliente",
        fontsize=15, color=TINTA, weight="bold", loc="left", pad=18,
    )
    ax.text(
        0, 1.02,
        "45% pendências vencidas + 35% aging médio + 20% replanejamento, normalizados na carteira. "
        "O score ordena; os números crus ao lado descrevem.",
        transform=ax.transAxes, fontsize=8.5, color=NEVOA, style="italic",
    )
    ax.set_xlim(0, 100)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.tick_params(axis="both", length=0)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=10)
    fig.tight_layout()

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, bbox_inches="tight")
    plt.close(fig)
    return destino


def print_lead_time(res: dict, destino: Path) -> Path:
    """Prometido contra realizado, por categoria. O gráfico que explica a falta de aderência."""
    _base_rc()
    lt = res["lead_time"].sort_values("mediana")

    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=170)
    y = range(len(lt))

    for i, (_, linha) in enumerate(lt.iterrows()):
        ax.plot([linha["p25"], linha["p75"]], [i, i], color=LINHA, linewidth=7, solid_capstyle="round")
        ax.scatter(
            linha["prazo_tipico_prometido"], i, s=95, marker="D", color=VERMELHO, zorder=3,
            label="Prazo prometido na reunião" if i == 0 else None,
        )
        ax.scatter(
            linha["mediana"], i, s=80, facecolor="white", edgecolor=ACENTO, linewidth=2, zorder=3,
            label="Mediana das concluídas (otimista)" if i == 0 else None,
        )
        ax.scatter(
            linha["mediana_com_pendentes"], i, s=95, color=ACENTO, zorder=4,
            label="Mediana incluindo pendentes (limite inferior)" if i == 0 else None,
        )
        dif = linha["diferenca_mediana_menos_prometido"]
        limite = max(linha["p75"], linha["prazo_tipico_prometido"], linha["mediana_com_pendentes"])
        ax.text(
            limite + 1.6, i,
            f"{'+' if dif > 0 else ''}{dif:.0f} dias",
            va="center", fontsize=9, color=VERMELHO if dif > 0 else VERDE, weight="bold",
        )

    ax.set_yticks(list(y))
    ax.set_yticklabels(lt["categoria"], fontsize=10.5)
    ax.set_xlabel("dias entre abertura e conclusão", fontsize=9.5, color=NEVOA)
    ax.set_title(
        "Lead time: o que se promete e o que se entrega",
        fontsize=15, color=TINTA, weight="bold", loc="left", pad=18,
    )
    ax.text(
        0, 1.03,
        "Barra clara = intervalo p25–p75 das concluídas. O círculo vazado só enxerga o que fechou, "
        "e por isso é otimista; o cheio inclui as pendências pelo tempo já decorrido.",
        transform=ax.transAxes, fontsize=8.5, color=NEVOA, style="italic",
    )
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", color=LINHA, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, bbox_inches="tight")
    plt.close(fig)
    return destino


def gerar_prints(
    res: dict, cfg: dict, periodo: tuple[dt.date, dt.date], pasta: Path
) -> list[Path]:
    return [
        print_painel(res, cfg, periodo, pasta / "painel.png"),
        print_ranking(res, pasta / "ranking-de-risco.png"),
        print_lead_time(res, pasta / "lead-time.png"),
    ]
