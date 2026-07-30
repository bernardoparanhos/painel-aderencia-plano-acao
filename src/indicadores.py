"""Cálculo dos seis indicadores.

Uma função por indicador, com o nome do indicador. Cada uma recebe as tabelas e
devolve um DataFrame pronto para virar aba — nenhuma delas formata, imprime ou
escreve arquivo. A definição de cada cálculo, com a pergunta de decisão que ele
responde, está em docs/indicadores.md; aqui fica só a aritmética.

Duas convenções valem para o arquivo inteiro:
  · ação cancelada sai de todos os denominadores;
  · pendência é ação não concluída e não cancelada na data de corte.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

FAIXAS_AGING = [(0, 7, "0–7 dias"), (8, 15, "8–15 dias"), (16, 30, "16–30 dias"), (31, None, "+30 dias")]
ROTULOS_AGING = [f[2] for f in FAIXAS_AGING]


# --------------------------------------------------------------------------------------
# Preparo comum
# --------------------------------------------------------------------------------------

def preparar(acoes: pd.DataFrame, corte: dt.date) -> pd.DataFrame:
    """Acrescenta as colunas derivadas que mais de um indicador usa.

    Fica isolado aqui para que dois indicadores nunca discordem sobre o que é uma
    pendência ou sobre como se conta um dia. Divergência de definição entre abas é
    o jeito mais rápido de um painel perder a confiança de quem lê.
    """
    df = acoes.copy()
    dias = lambda serie: (pd.to_datetime(corte) - pd.to_datetime(serie)).dt.days

    df["cancelada"] = df["status"] == "Cancelada"
    df["concluida"] = df["data_conclusao"].notna()
    df["em_aberto"] = ~df["cancelada"] & ~df["concluida"]

    df["dias_em_aberto"] = np.where(df["em_aberto"], dias(df["data_abertura"]), np.nan)
    df["dias_apos_prazo_original"] = np.where(
        df["em_aberto"], dias(df["prazo_original"]), np.nan
    )
    df["prazo_original_vencido"] = ~df["cancelada"] & (
        pd.to_datetime(df["prazo_original"]) <= pd.to_datetime(corte)
    )
    df["cumpriu_prazo"] = df["concluida"] & (
        pd.to_datetime(df["data_conclusao"]) <= pd.to_datetime(df["prazo_original"])
    )
    df["lead_time"] = np.where(
        df["concluida"],
        (pd.to_datetime(df["data_conclusao"]) - pd.to_datetime(df["data_abertura"])).dt.days,
        np.nan,
    )
    df["replanejada"] = ~df["cancelada"] & (df["n_reprogramacoes"] >= 1)
    df["faixa_aging"] = pd.cut(
        df["dias_em_aberto"],
        bins=[-0.5, 7.5, 15.5, 30.5, np.inf],
        labels=ROTULOS_AGING,
    )
    return df


# --------------------------------------------------------------------------------------
# 1 · Aderência ao prazo
# --------------------------------------------------------------------------------------

def aderencia_ao_prazo(base: pd.DataFrame) -> float:
    """Fração das ações com prazo original vencido que foram concluídas até esse prazo."""
    venciveis = base[base["prazo_original_vencido"]]
    if venciveis.empty:
        return float("nan")
    return float(venciveis["cumpriu_prazo"].mean())


def aderencia_por_cliente(base: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Mesma conta, quebrada por cliente, da pior aderência para a melhor."""
    venciveis = base[base["prazo_original_vencido"]]
    agg = venciveis.groupby("cliente_id").agg(
        acoes_com_prazo_vencido=("acao_id", "count"),
        concluidas_no_prazo=("cumpriu_prazo", "sum"),
        pendencias_vencidas=("em_aberto", "sum"),
    )
    agg["aderencia"] = agg["concluidas_no_prazo"] / agg["acoes_com_prazo_vencido"]

    out = (
        clientes.set_index("cliente_id")[["nome", "segmento", "porte", "consultor"]]
        .join(agg, how="left")
        .reset_index()
    )
    out["classificacao"] = pd.cut(
        out["aderencia"],
        bins=[-0.01, 0.4999, 0.6999, 1.01],
        labels=["Crítico", "Atenção", "Saudável"],
    )
    return out.sort_values("aderencia", na_position="last").reset_index(drop=True)


# --------------------------------------------------------------------------------------
# 2 · Aging de pendências
# --------------------------------------------------------------------------------------

def aging_de_pendencias(base: pd.DataFrame) -> pd.DataFrame:
    """Distribuição das pendências em aberto por faixa de dias."""
    abertas = base[base["em_aberto"]]
    contagem = abertas["faixa_aging"].value_counts().reindex(ROTULOS_AGING, fill_value=0)
    total = int(contagem.sum())

    dias_medios = (
        abertas.groupby("faixa_aging", observed=False)["dias_em_aberto"].mean()
        .reindex(ROTULOS_AGING)
    )
    alta = (
        abertas[abertas["prioridade"] == "Alta"]["faixa_aging"]
        .value_counts().reindex(ROTULOS_AGING, fill_value=0)
    )

    return pd.DataFrame(
        {
            "faixa": ROTULOS_AGING,
            "pendencias": contagem.to_numpy(),
            "percentual": contagem.to_numpy() / total if total else np.nan,
            "dias_em_aberto_medio": dias_medios.to_numpy().round(1),
            "das_quais_prioridade_alta": alta.to_numpy(),
            "leitura": [
                "Dentro do ciclo de acompanhamento",
                "Merece cobrança na próxima reunião",
                "Fora do ciclo: repactuar prazo",
                "Ação abandonada: repactuar ou cancelar",
            ],
        }
    )


def aging_detalhado(base: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """As pendências em aberto, uma por linha, das mais antigas para as mais recentes."""
    abertas = base[base["em_aberto"]].copy()
    nomes = clientes.set_index("cliente_id")["nome"]
    abertas["cliente"] = abertas["cliente_id"].map(nomes)
    colunas = [
        "cliente", "acao_id", "categoria", "descricao", "responsavel", "prioridade",
        "data_abertura", "prazo_original", "prazo_atual", "n_reprogramacoes",
        "dias_em_aberto", "dias_apos_prazo_original", "faixa_aging", "status",
    ]
    return (
        abertas[colunas]
        .sort_values("dias_em_aberto", ascending=False)
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------------------------
# 3 · Taxa de replanejamento
# --------------------------------------------------------------------------------------

def taxa_de_replanejamento(base: pd.DataFrame) -> float:
    validas = base[~base["cancelada"]]
    if validas.empty:
        return float("nan")
    return float(validas["replanejada"].mean())


def replanejamento_por_cliente(base: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    validas = base[~base["cancelada"]]
    agg = validas.groupby("cliente_id").agg(
        acoes=("acao_id", "count"),
        acoes_replanejadas=("replanejada", "sum"),
        reprogramacoes_totais=("n_reprogramacoes", "sum"),
    )
    agg["taxa_replanejamento"] = agg["acoes_replanejadas"] / agg["acoes"]
    # média calculada só sobre as replanejadas: distingue "muitas movidas uma vez"
    # de "poucas movidas quatro vezes", que são problemas diferentes
    agg["repro_por_acao_replanejada"] = (
        agg["reprogramacoes_totais"] / agg["acoes_replanejadas"].replace(0, np.nan)
    ).round(2)

    nomes = clientes.set_index("cliente_id")["nome"]
    out = agg.join(nomes).reset_index()
    out = out[
        ["cliente_id", "nome", "acoes", "acoes_replanejadas", "taxa_replanejamento",
         "reprogramacoes_totais", "repro_por_acao_replanejada"]
    ]
    return out.sort_values("taxa_replanejamento", ascending=False).reset_index(drop=True)


def replanejamento_por_categoria(base: pd.DataFrame) -> pd.DataFrame:
    validas = base[~base["cancelada"]]
    agg = validas.groupby("categoria").agg(
        acoes=("acao_id", "count"),
        acoes_replanejadas=("replanejada", "sum"),
        reprogramacoes_totais=("n_reprogramacoes", "sum"),
    )
    agg["taxa_replanejamento"] = agg["acoes_replanejadas"] / agg["acoes"]
    return agg.reset_index().sort_values("taxa_replanejamento", ascending=False)


# --------------------------------------------------------------------------------------
# 4 · Lead time de conclusão
# --------------------------------------------------------------------------------------

def lead_time_por_categoria(base: pd.DataFrame) -> pd.DataFrame:
    """Mediana e dispersão dos dias entre abertura e conclusão, por categoria.

    Mediana, não média: a distribuição tem cauda longa à direita e a média descreve
    um caso que quase não acontece. p25 e p75 vêm junto porque mediana sozinha
    esconde o risco de prometer prazo.
    """
    concluidas = base[base["concluida"] & ~base["cancelada"]]
    agg = concluidas.groupby("categoria")["lead_time"].agg(
        acoes_concluidas="count",
        p25=lambda s: s.quantile(0.25),
        mediana="median",
        p75=lambda s: s.quantile(0.75),
        maximo="max",
    )
    agg["amplitude_p25_p75"] = agg["p75"] - agg["p25"]

    # Correção do viés de sobrevivência.
    #
    # A mediana acima só enxerga ações que fecharam — e as que mais demoram são
    # justamente as que ainda não fecharam. Sozinha, ela chega a mostrar categoria
    # entregando ANTES do prometido numa carteira com aderência ruim, o que é leitura
    # falsa. A coluna abaixo inclui as pendências pelo tempo que já se passou desde a
    # abertura: como esse tempo ainda vai crescer, o resultado é um limite INFERIOR
    # da mediana verdadeira. É o número honesto para prometer prazo.
    validas = base[~base["cancelada"]].copy()
    validas["tempo_censurado"] = np.where(
        validas["concluida"], validas["lead_time"], validas["dias_em_aberto"]
    )
    agg["mediana_com_pendentes"] = validas.groupby("categoria")["tempo_censurado"].median()

    # o dado que fecha a leitura: o prazo que se costuma prometer nesta categoria
    prazos = (
        base.assign(
            prazo_prometido=(
                pd.to_datetime(base["prazo_original"]) - pd.to_datetime(base["data_abertura"])
            ).dt.days
        )
        .groupby("categoria")["prazo_prometido"]
        .median()
    )
    agg["prazo_tipico_prometido"] = prazos

    # Mediana de um número par de observações cai no meio: 19,5 dias é resultado
    # legítimo. Guardar 19,5 e exibir "20" faria a planilha mostrar 20 − 21 = −2,
    # que é aritmética errada na cara de quem lê. Uma casa decimal em todas as
    # colunas de dias resolve, e as contas fecham exatamente como aparecem.
    colunas_dias = ["p25", "mediana", "p75", "mediana_com_pendentes", "prazo_tipico_prometido"]
    agg[colunas_dias] = agg[colunas_dias].round(1)
    agg["amplitude_p25_p75"] = (agg["p75"] - agg["p25"]).round(1)
    agg["diferenca_mediana_menos_prometido"] = (
        agg["mediana_com_pendentes"] - agg["prazo_tipico_prometido"]
    ).round(1)

    ordem = [
        "acoes_concluidas", "p25", "mediana", "p75", "maximo", "amplitude_p25_p75",
        "mediana_com_pendentes", "prazo_tipico_prometido",
        "diferenca_mediana_menos_prometido",
    ]
    return (
        agg[ordem].reset_index()
        .sort_values("mediana_com_pendentes", ascending=False)
        .reset_index(drop=True)
    )


def lead_time_mediano(base: pd.DataFrame) -> float:
    concluidas = base[base["concluida"] & ~base["cancelada"]]
    return float(concluidas["lead_time"].median()) if not concluidas.empty else float("nan")


# --------------------------------------------------------------------------------------
# 5 · Cobertura de acompanhamento
# --------------------------------------------------------------------------------------

def cobertura_por_semana(acompanhamentos: pd.DataFrame) -> pd.DataFrame:
    """Clientes com reunião registrada ÷ clientes ativos, semana a semana."""
    agg = acompanhamentos.groupby(["semana", "semana_referencia"]).agg(
        clientes_ativos=("cliente_id", "count"),
        clientes_com_reuniao=("houve_reuniao", "sum"),
        acoes_revisadas=("n_acoes_revisadas", "sum"),
    ).reset_index()
    agg["cobertura"] = agg["clientes_com_reuniao"] / agg["clientes_ativos"]
    return agg


def cobertura_media(acompanhamentos: pd.DataFrame) -> float:
    return float(acompanhamentos["houve_reuniao"].mean())


def cobertura_por_cliente(
    acompanhamentos: pd.DataFrame, clientes: pd.DataFrame
) -> pd.DataFrame:
    agg = acompanhamentos.groupby("cliente_id").agg(
        semanas_na_carteira=("semana", "count"),
        semanas_com_reuniao=("houve_reuniao", "sum"),
    )
    agg["cobertura"] = agg["semanas_com_reuniao"] / agg["semanas_na_carteira"]

    ultima = (
        acompanhamentos[acompanhamentos["houve_reuniao"]]
        .groupby("cliente_id")["semana_referencia"].max()
        .rename("ultima_reuniao")
    )
    nomes = clientes.set_index("cliente_id")["nome"]
    out = agg.join(ultima).join(nomes).reset_index()
    return out.sort_values("cobertura").reset_index(drop=True)


# --------------------------------------------------------------------------------------
# 6 · Ranking de risco por cliente
# --------------------------------------------------------------------------------------

def _normaliza(serie: pd.Series) -> pd.Series:
    """Min-max 0–100 contra a própria carteira. Score relativo, e declarado como tal."""
    s = serie.astype(float).fillna(0.0)
    span = s.max() - s.min()
    if span == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.min()) / span * 100


def ranking_de_risco(
    base: pd.DataFrame, clientes: pd.DataFrame, cfg_risco: dict
) -> pd.DataFrame:
    validas = base[~base["cancelada"]]

    agg = validas.groupby("cliente_id").agg(
        acoes=("acao_id", "count"),
        pendencias_abertas=("em_aberto", "sum"),
        acoes_replanejadas=("replanejada", "sum"),
    )
    vencidas = (
        validas[validas["em_aberto"] & (validas["dias_apos_prazo_original"] > 0)]
        .groupby("cliente_id")["acao_id"].count()
        .rename("pendencias_vencidas")
    )
    aging = (
        validas[validas["em_aberto"]]
        .groupby("cliente_id")["dias_em_aberto"].mean()
        .rename("aging_medio")
    )

    df = agg.join(vencidas).join(aging).fillna({"pendencias_vencidas": 0, "aging_medio": 0})
    df["pct_vencidas"] = df["pendencias_vencidas"] / df["acoes"]
    df["taxa_replanejamento"] = df["acoes_replanejadas"] / df["acoes"]

    df["score_risco"] = (
        cfg_risco["peso_vencidas"] * _normaliza(df["pct_vencidas"])
        + cfg_risco["peso_aging"] * _normaliza(df["aging_medio"])
        + cfg_risco["peso_replanejamento"] * _normaliza(df["taxa_replanejamento"])
    ).round(1)

    df["classificacao"] = pd.cut(
        df["score_risco"],
        bins=[-0.01, cfg_risco["limite_atencao"] - 0.01, cfg_risco["limite_critico"] - 0.01, 100.01],
        labels=["Estável", "Atenção", "Crítico"],
    )

    nomes = clientes.set_index("cliente_id")[["nome", "consultor"]]
    out = df.join(nomes).reset_index()
    out["aging_medio"] = out["aging_medio"].round(1)
    out = out[
        ["cliente_id", "nome", "consultor", "score_risco", "classificacao",
         "pendencias_vencidas", "pct_vencidas", "aging_medio", "taxa_replanejamento",
         "pendencias_abertas", "acoes"]
    ]
    return out.sort_values("score_risco", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------------------
# Painel: os seis números de leitura única
# --------------------------------------------------------------------------------------

def painel_resumo(
    base: pd.DataFrame,
    acompanhamentos: pd.DataFrame,
    clientes: pd.DataFrame,
    cfg: dict,
) -> dict:
    """Os seis indicadores da carteira, mais o contexto que impede leitura errada."""
    leitura = cfg["leitura"]
    aging = aging_de_pendencias(base)
    cobertura = cobertura_media(acompanhamentos)
    ader = aderencia_ao_prazo(base)
    risco = ranking_de_risco(base, clientes, cfg["risco"])
    abertas = int(base["em_aberto"].sum())
    mais30 = int(aging.loc[aging["faixa"] == "+30 dias", "pendencias"].iloc[0])

    return {
        "aderencia": ader,
        "aderencia_denominador": int(base["prazo_original_vencido"].sum()),
        "aging_mais_30": mais30,
        "aging_mais_30_pct": (mais30 / abertas) if abertas else float("nan"),
        "pendencias_abertas": abertas,
        "taxa_replanejamento": taxa_de_replanejamento(base),
        "lead_time_mediano": lead_time_mediano(base),
        "cobertura": cobertura,
        "cobertura_suficiente": cobertura >= leitura["cobertura_minima"],
        "clientes_criticos": int((risco["classificacao"] == "Crítico").sum()),
        "cliente_topo_risco": risco.iloc[0]["nome"] if not risco.empty else "—",
        "total_acoes": int(len(base)),
        "canceladas": int(base["cancelada"].sum()),
        "concluidas": int(base["concluida"].sum()),
    }


def base_achatada(
    base: pd.DataFrame, clientes: pd.DataFrame, corte: dt.date
) -> pd.DataFrame:
    """Tabela única, pronta para Power BI ou tabela dinâmica."""
    cols_cli = ["nome", "segmento", "porte", "consultor"]
    out = base.merge(
        clientes.set_index("cliente_id")[cols_cli], left_on="cliente_id", right_index=True
    )
    out = out.rename(columns={"nome": "cliente"})
    out["data_referencia"] = corte
    ordem = [
        "acao_id", "cliente_id", "cliente", "segmento", "porte", "consultor",
        "categoria", "descricao", "responsavel", "prioridade", "status",
        "data_abertura", "prazo_original", "prazo_atual", "data_conclusao",
        "n_reprogramacoes", "replanejada", "cumpriu_prazo", "lead_time",
        "dias_em_aberto", "dias_apos_prazo_original", "faixa_aging",
        "em_aberto", "data_referencia",
    ]
    return out[ordem].sort_values(["cliente_id", "data_abertura"]).reset_index(drop=True)
