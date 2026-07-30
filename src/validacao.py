"""Confere os indicadores recalculando tudo em Python puro.

    python src/validacao.py

O roadmap pedia validar dois ou três casos à mão antes de confiar no cálculo. Isto é a
versão disciplinada disso: os seis indicadores recalculados linha a linha, com `for` e
`if`, sem nenhuma agregação do Pandas — e comparados com o que `indicadores.py` devolve.

A graça está em ser uma implementação independente. Se as duas concordam, o erro teria
que ter sido cometido duas vezes, do mesmo jeito, em dois estilos de código diferentes.
Não é prova, mas é muito melhor que conferir o número consigo mesmo.

Divergências que apareceram durante a construção estão registradas em
docs/decisoes.md, seção 8.
"""

from __future__ import annotations

import datetime as dt
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import indicadores as ind  # noqa: E402
from gerador import gerar_base  # noqa: E402
from main import RAIZ, calcular_tudo, carregar_config  # noqa: E402

TOLERANCIA = 1e-9


# --------------------------------------------------------------------------------------
# Recálculo à mão, sobre listas de dicionários
# --------------------------------------------------------------------------------------

def _linhas(df) -> list[dict]:
    return df.to_dict("records")


def _esta_em_aberto(acao: dict) -> bool:
    return acao["status"] != "Cancelada" and acao["data_conclusao"] is None


def aderencia_na_mao(acoes: list[dict], corte: dt.date) -> float:
    denominador = 0
    numerador = 0
    for acao in acoes:
        if acao["status"] == "Cancelada":
            continue
        if acao["prazo_original"] > corte:
            continue
        denominador += 1
        conclusao = acao["data_conclusao"]
        if conclusao is not None and conclusao <= acao["prazo_original"]:
            numerador += 1
    return numerador / denominador


def aging_na_mao(acoes: list[dict], corte: dt.date) -> dict[str, int]:
    faixas = {"0–7 dias": 0, "8–15 dias": 0, "16–30 dias": 0, "+30 dias": 0}
    for acao in acoes:
        if not _esta_em_aberto(acao):
            continue
        dias = (corte - acao["data_abertura"]).days
        if dias <= 7:
            faixas["0–7 dias"] += 1
        elif dias <= 15:
            faixas["8–15 dias"] += 1
        elif dias <= 30:
            faixas["16–30 dias"] += 1
        else:
            faixas["+30 dias"] += 1
    return faixas


def replanejamento_na_mao(acoes: list[dict]) -> float:
    validas = [a for a in acoes if a["status"] != "Cancelada"]
    movidas = [a for a in validas if a["n_reprogramacoes"] >= 1]
    return len(movidas) / len(validas)


def lead_time_na_mao(acoes: list[dict]) -> dict[str, float]:
    por_categoria: dict[str, list[int]] = {}
    for acao in acoes:
        if acao["status"] == "Cancelada" or acao["data_conclusao"] is None:
            continue
        dias = (acao["data_conclusao"] - acao["data_abertura"]).days
        por_categoria.setdefault(acao["categoria"], []).append(dias)
    return {cat: statistics.median(vals) for cat, vals in por_categoria.items()}


def cobertura_na_mao(acompanhamentos: list[dict]) -> float:
    com_reuniao = sum(1 for a in acompanhamentos if a["houve_reuniao"])
    return com_reuniao / len(acompanhamentos)


def risco_na_mao(acoes: list[dict], corte: dt.date, cfg_risco: dict) -> list[tuple[str, float]]:
    """Reproduz o score, inclusive a normalização min-max contra a carteira."""
    por_cliente: dict[str, list[dict]] = {}
    for acao in acoes:
        if acao["status"] == "Cancelada":
            continue
        por_cliente.setdefault(acao["cliente_id"], []).append(acao)

    cruas = {}
    for cid, lista in por_cliente.items():
        abertas = [a for a in lista if _esta_em_aberto(a)]
        vencidas = [a for a in abertas if (corte - a["prazo_original"]).days > 0]
        agings = [(corte - a["data_abertura"]).days for a in abertas]
        movidas = [a for a in lista if a["n_reprogramacoes"] >= 1]
        cruas[cid] = (
            len(vencidas) / len(lista),
            sum(agings) / len(agings) if agings else 0.0,
            len(movidas) / len(lista),
        )

    def normaliza(indice: int) -> dict[str, float]:
        valores = [v[indice] for v in cruas.values()]
        menor, maior = min(valores), max(valores)
        intervalo = maior - menor
        if intervalo == 0:
            return {cid: 0.0 for cid in cruas}
        return {cid: (v[indice] - menor) / intervalo * 100 for cid, v in cruas.items()}

    n_vencidas, n_aging, n_repl = normaliza(0), normaliza(1), normaliza(2)
    scores = {
        cid: round(
            cfg_risco["peso_vencidas"] * n_vencidas[cid]
            + cfg_risco["peso_aging"] * n_aging[cid]
            + cfg_risco["peso_replanejamento"] * n_repl[cid],
            1,
        )
        for cid in cruas
    }
    return sorted(scores.items(), key=lambda par: -par[1])


# --------------------------------------------------------------------------------------

def _comparar(nome: str, na_mao, do_codigo, tolerancia: float = TOLERANCIA) -> bool:
    if isinstance(na_mao, float):
        bate = abs(na_mao - do_codigo) <= tolerancia
        mostrado = f"{na_mao:.6f}  vs  {do_codigo:.6f}"
    else:
        bate = na_mao == do_codigo
        mostrado = f"{na_mao}  vs  {do_codigo}"
    marca = "ok  " if bate else "FALHA"
    print(f"  [{marca}] {nome}")
    if not bate:
        print(f"          à mão vs. código: {mostrado}")
    return bate


def main() -> int:
    cfg = carregar_config(RAIZ / "config.yaml")
    corte = cfg["cenario"]["data_corte"]

    tabelas = gerar_base(cfg)
    res = calcular_tudo(tabelas, cfg)

    acoes = _linhas(tabelas["acoes"])
    for acao in acoes:  # o Pandas devolve NaT; o recálculo à mão trabalha com None
        if acao["data_conclusao"] is not None and str(acao["data_conclusao"]) == "NaT":
            acao["data_conclusao"] = None
    acompanhamentos = _linhas(tabelas["acompanhamentos"])

    print(f"\nValidação do cenário '{cfg['cenario']['nome']}' (semente {cfg['cenario']['semente']})")
    print(f"{len(acoes)} ações · data de corte {corte:%d/%m/%Y}\n")

    resultados = []

    resultados.append(
        _comparar(
            "Aderência ao prazo",
            aderencia_na_mao(acoes, corte),
            res["painel"]["aderencia"],
        )
    )

    faixas_mao = aging_na_mao(acoes, corte)
    faixas_codigo = {
        linha["faixa"]: int(linha["pendencias"])
        for _, linha in res["aging_faixas"].iterrows()
    }
    resultados.append(_comparar("Aging de pendências, por faixa", faixas_mao, faixas_codigo))

    resultados.append(
        _comparar(
            "Taxa de replanejamento",
            replanejamento_na_mao(acoes),
            res["painel"]["taxa_replanejamento"],
        )
    )

    lead_mao = lead_time_na_mao(acoes)
    lead_codigo = {
        linha["categoria"]: float(linha["mediana"])
        for _, linha in res["lead_time"].iterrows()
    }
    resultados.append(
        _comparar(
            "Lead time mediano, por categoria",
            {k: float(v) for k, v in sorted(lead_mao.items())},
            dict(sorted(lead_codigo.items())),
        )
    )

    resultados.append(
        _comparar(
            "Cobertura de acompanhamento",
            cobertura_na_mao(acompanhamentos),
            res["painel"]["cobertura"],
        )
    )

    risco_mao = risco_na_mao(acoes, corte, cfg["risco"])
    risco_codigo = [
        (linha["cliente_id"], float(linha["score_risco"]))
        for _, linha in res["ranking"].iterrows()
    ]
    resultados.append(
        _comparar("Ranking de risco (ordem e score)", risco_mao, risco_codigo)
    )

    # conferência extra: as três tabelas precisam ser coerentes entre si
    resultados.append(
        _comparar(
            "Toda ação nasce em uma semana com reunião",
            True,
            _acoes_nascem_em_reuniao(tabelas),
        )
    )

    falhas = resultados.count(False)
    print()
    if falhas:
        print(f"  {falhas} verificação(ões) falharam.")
        return 1
    print(f"  {len(resultados)} verificações, todas conferem.")
    return 0


def _acoes_nascem_em_reuniao(tabelas: dict) -> bool:
    """A ação é aberta no dia de reunião de uma semana em que houve reunião.

    O dia varia por cliente, então a conferência é feita pela semana: a data de
    abertura é levada de volta à segunda-feira dela e comparada com a agenda.
    """
    semanas_com_reuniao = {
        (linha["cliente_id"], linha["semana_referencia"])
        for _, linha in tabelas["acompanhamentos"].iterrows()
        if linha["houve_reuniao"]
    }
    for _, acao in tabelas["acoes"].iterrows():
        abertura = acao["data_abertura"]
        semana = abertura - dt.timedelta(days=abertura.weekday())
        if (acao["cliente_id"], semana) not in semanas_com_reuniao:
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
