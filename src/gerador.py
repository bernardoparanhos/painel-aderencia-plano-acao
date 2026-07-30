"""Geração dos dados sintéticos da carteira.

Três tabelas — clientes, acoes, acompanhamentos — produzidas a partir do config.yaml
com semente fixa. Mesma semente, mesmos dados, sempre.

A ordem importa e não é acidental: primeiro a carteira, depois a agenda de reuniões,
e só então as ações. Ação nasce em reunião, então cliente com agenda irregular gera
menos ações e as vê envelhecer — o efeito da cobertura sobre os outros indicadores
emerge do modelo em vez de ser forçado por parâmetro. Ver docs/decisoes.md, seção 3.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# Vocabulário fictício. Nenhum nome, aqui, corresponde a cliente real de lugar nenhum.
# --------------------------------------------------------------------------------------

_PREFIXOS = [
    "Aurora", "Bandeirante", "Cordilheira", "Delta", "Estrela", "Farol", "Guaporé",
    "Horizonte", "Ipê", "Jacarandá", "Kairós", "Lumiar", "Marfim", "Norte", "Orion",
    "Pampa", "Quartzo", "Rumo", "Serrana", "Tramontana", "Ubá", "Vertente", "Xisto",
    "Zênite", "Alvorada", "Boreal", "Cristal", "Duna", "Ébano", "Fluvial",
]

_SUFIXOS = {
    "Indústria": ["Metalúrgica", "Indústria", "Manufatura", "Componentes"],
    "Varejo": ["Comércio", "Varejo", "Distribuidora", "Lojas"],
    "Serviços": ["Serviços", "Soluções", "Consultoria Técnica", "Engenharia"],
    "Agronegócio": ["Agropecuária", "Agroindústria", "Cooperativa", "Sementes"],
    "Construção": ["Construtora", "Empreendimentos", "Incorporadora", "Obras"],
    "Saúde": ["Saúde", "Clínicas", "Diagnósticos", "Hospitalar"],
}

_DESCRICOES = {
    "Processo": [
        "Mapear o fluxo de {a} e registrar o procedimento",
        "Padronizar a rotina de {a} com checklist",
        "Eliminar retrabalho na etapa de {a}",
        "Definir responsável único para {a}",
        "Revisar o fluxo de aprovação de {a}",
    ],
    "Indicador": [
        "Definir a fórmula e a fonte do indicador de {a}",
        "Implantar o apontamento diário de {a}",
        "Levar o indicador de {a} para a reunião semanal",
        "Corrigir a base que alimenta o painel de {a}",
        "Estabelecer a meta de {a} para o trimestre",
    ],
    "Comercial": [
        "Estruturar o funil de {a}",
        "Revisar a tabela de preços de {a}",
        "Retomar contato com a carteira inativa de {a}",
        "Definir a meta mensal de {a} por vendedor",
        "Padronizar a proposta comercial de {a}",
    ],
    "Financeiro": [
        "Conciliar as contas de {a}",
        "Implantar o fluxo de caixa semanal de {a}",
        "Revisar a política de prazos de {a}",
        "Separar as despesas de {a} do pessoal do sócio",
        "Levantar o custo real de {a}",
    ],
    "Pessoas": [
        "Descrever o cargo responsável por {a}",
        "Estruturar o treinamento da equipe de {a}",
        "Definir o rito de feedback do time de {a}",
        "Formalizar a escala da equipe de {a}",
        "Contratar a posição em aberto em {a}",
    ],
}

_AREAS = [
    "compras", "expedição", "produção", "faturamento", "atendimento", "estoque",
    "manutenção", "vendas", "pós-venda", "recebimento", "orçamento", "qualidade",
]

_OBSERVACOES_OK = [
    "Pauta revisada integralmente.",
    "Reunião com o sócio presente.",
    "Revisão parcial, faltou o responsável da área.",
    "Pauta revisada; duas ações repactuadas.",
    "Reunião curta, foco nas ações vencidas.",
]

_OBSERVACOES_FALTA = [
    "Reunião não realizada — agenda do cliente.",
    "Reunião cancelada na véspera.",
    "Sem reunião na semana; contato apenas por e-mail.",
    "Cliente em fechamento de mês, reunião adiada.",
]


# --------------------------------------------------------------------------------------
# Auxiliares
# --------------------------------------------------------------------------------------

def _segunda_da_semana(data_corte: dt.date, horizonte: int, semana: int) -> dt.date:
    """Segunda-feira da `semana` (1-indexada), contando para trás a partir do corte."""
    fim = data_corte - dt.timedelta(days=data_corte.weekday())  # segunda da semana do corte
    return fim - dt.timedelta(weeks=horizonte - semana)


def _sorteia_categoria(rng: np.random.Generator, categorias: dict) -> str:
    nomes = list(categorias)
    pesos = np.array([categorias[n]["peso"] for n in nomes], dtype=float)
    return str(rng.choice(nomes, p=pesos / pesos.sum()))


def _sorteia_de_dict(rng: np.random.Generator, pesos: dict) -> str:
    nomes = list(pesos)
    p = np.array([pesos[n] for n in nomes], dtype=float)
    return str(rng.choice(nomes, p=p / p.sum()))


# --------------------------------------------------------------------------------------
# Tabela 1 · clientes
# --------------------------------------------------------------------------------------

def gerar_clientes(cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    n = cfg["cenario"]["n_clientes"]
    horizonte = cfg["cenario"]["horizonte_semanas"]
    corte = cfg["cenario"]["data_corte"]
    carteira = cfg["carteira"]

    prefixos = list(rng.permutation(_PREFIXOS))[:n]
    inicio = _segunda_da_semana(corte, horizonte, 1)

    linhas = []
    for i, prefixo in enumerate(prefixos, start=1):
        segmento = str(rng.choice(carteira["segmentos"]))
        porte = _sorteia_de_dict(rng, carteira["portes"])

        # a maioria já estava na carteira antes do horizonte; uma fração entra no meio
        if rng.random() < carteira["fracao_entrada_tardia"]:
            semana_entrada = int(rng.integers(2, max(3, horizonte // 2)))
            data_entrada = _segunda_da_semana(corte, horizonte, semana_entrada)
        else:
            data_entrada = inicio - dt.timedelta(days=int(rng.integers(30, 900)))

        linhas.append(
            {
                "cliente_id": f"C{i:02d}",
                "nome": f"{prefixo} {rng.choice(_SUFIXOS[segmento])}",
                "segmento": segmento,
                "porte": porte,
                "data_entrada": data_entrada,
                "consultor": str(rng.choice(carteira["consultores"])),
            }
        )

    return pd.DataFrame(linhas)


def gerar_perfis(cfg: dict, clientes: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Traços de comportamento por cliente.

    Não vão para a saída: são a causa oculta dos indicadores, e o painel existe justamente
    para inferi-los a partir do efeito. Se estivessem na planilha, o exercício perderia
    a graça — e, mais importante, deixaria de imitar a situação real, em que a disciplina
    do cliente é o que se quer descobrir, não o que se sabe de antemão.
    """
    n = len(clientes)
    ac = cfg["acompanhamento"]
    ex = cfg["execucao"]

    # disciplina: multiplicador lognormal sobre o lead time. >1 é cliente lento.
    fator_execucao = rng.lognormal(mean=0.0, sigma=ex["variabilidade_entre_clientes"], size=n)

    # agenda irregular e hábito de replanejar são sorteados de forma independente:
    # existe cliente organizado na agenda e caótico no prazo, e vice-versa.
    irregulares = rng.random(n) < ac["fracao_clientes_irregulares"]
    replanejadores = rng.random(n) < ex["fracao_clientes_replanejadores"]

    # Cada cliente tem seu dia fixo de reunião na semana, de segunda a sexta.
    #
    # Não é enfeite: com a reunião de todo mundo caindo no mesmo dia, o tempo em
    # aberto de toda pendência vira múltiplo de 7 mais uma constante, e o aging
    # passa a existir só em degraus — a faixa 0–7 com média exata de 3,0 dias,
    # a de 8–15 com exata de 10,0. Coerente, e obviamente artificial.
    dia_reuniao = rng.integers(0, 5, size=n)

    return pd.DataFrame(
        {
            "cliente_id": clientes["cliente_id"].to_numpy(),
            "fator_execucao": fator_execucao,
            "prob_reuniao": np.where(
                irregulares, ac["prob_reuniao_irregular"], ac["prob_reuniao_regular"]
            ),
            "replanejador": replanejadores,
            "dia_reuniao": dia_reuniao,
        }
    ).set_index("cliente_id")


# --------------------------------------------------------------------------------------
# Tabela 2 · acompanhamentos
# --------------------------------------------------------------------------------------

def gerar_acompanhamentos(
    cfg: dict, clientes: pd.DataFrame, perfis: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    horizonte = cfg["cenario"]["horizonte_semanas"]
    corte = cfg["cenario"]["data_corte"]

    linhas = []
    for _, cli in clientes.iterrows():
        prob = float(perfis.loc[cli["cliente_id"], "prob_reuniao"])
        for semana in range(1, horizonte + 1):
            ref = _segunda_da_semana(corte, horizonte, semana)
            if ref < cli["data_entrada"]:
                continue  # cliente ainda não estava na carteira: não há linha, e não conta
            houve = bool(rng.random() < prob)
            linhas.append(
                {
                    "cliente_id": cli["cliente_id"],
                    "semana": semana,
                    "semana_referencia": ref,
                    "houve_reuniao": houve,
                    "n_acoes_revisadas": 0,  # preenchido depois que as ações existirem
                    "observacao": str(
                        rng.choice(_OBSERVACOES_OK if houve else _OBSERVACOES_FALTA)
                    ),
                }
            )

    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------------------
# Tabela 3 · acoes
# --------------------------------------------------------------------------------------

def gerar_acoes(
    cfg: dict,
    clientes: pd.DataFrame,
    perfis: pd.DataFrame,
    acompanhamentos: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    corte = cfg["cenario"]["data_corte"]
    cats = cfg["categorias"]
    par = cfg["acoes"]
    ex = cfg["execucao"]

    porte_por_cliente = clientes.set_index("cliente_id")["porte"].to_dict()
    reunioes = acompanhamentos[acompanhamentos["houve_reuniao"]]

    linhas = []
    contador = 0

    for _, reuniao in reunioes.iterrows():
        cid = reuniao["cliente_id"]
        porte = porte_por_cliente[cid]
        lam = par["media_acoes_por_reuniao"] * par["fator_porte"][porte]

        for _ in range(int(rng.poisson(lam))):
            contador += 1
            categoria = _sorteia_categoria(rng, cats)
            c = cats[categoria]
            responsavel = _sorteia_de_dict(rng, par["responsaveis"])

            # a ação é aberta na reunião, e cada cliente tem seu dia fixo na semana
            abertura = reuniao["semana_referencia"] + dt.timedelta(
                days=int(perfis.loc[cid, "dia_reuniao"])
            )
            prazo_original = abertura + dt.timedelta(days=int(c["prazo_prometido"]))

            # duração real de execução: lognormal com mediana ajustada por cliente e responsável
            mediana = (
                c["lead_time_base"]
                * float(perfis.loc[cid, "fator_execucao"])
                * par["fator_execucao_responsavel"][responsavel]
            )
            duracao = float(rng.lognormal(mean=np.log(mediana), sigma=c["dispersao"]))
            duracao = max(1.0, duracao)

            destino = rng.random()
            abandonada = destino < par["fracao_abandonadas"]
            cancelada = (
                not abandonada
                and destino < par["fracao_abandonadas"] + par["fracao_canceladas"]
            )

            data_conclusao = None
            if not abandonada and not cancelada:
                candidata = abertura + dt.timedelta(days=int(round(duracao)))
                if candidata <= corte:
                    data_conclusao = candidata

            # ------------------------------------------------------------------
            # reprogramação: enquanto o prazo vigente fica para trás e a ação não
            # fecha, alguém empurra a data na reunião.
            # ------------------------------------------------------------------
            passo_min, passo_max = ex["passo_replanejamento_dias"]
            fator_passo = (
                ex["fator_passo_replanejador"]
                if bool(perfis.loc[cid, "replanejador"])
                else 1.0
            )
            teto = (
                ex["max_reprogramacoes_abandonada"]
                if abandonada
                else ex["max_reprogramacoes"]
            )
            alvo = data_conclusao if data_conclusao is not None else corte
            if cancelada:
                alvo = min(abertura + dt.timedelta(days=int(round(duracao))), corte)

            prazo_atual = prazo_original
            n_repro = 0
            while prazo_atual < alvo and n_repro < teto:
                passo = max(3, int(round(rng.integers(passo_min, passo_max + 1) * fator_passo)))
                prazo_atual += dt.timedelta(days=passo)
                n_repro += 1

            if cancelada:
                status = "Cancelada"
            elif data_conclusao is not None:
                status = "Concluída"
            elif prazo_atual < corte:
                status = "Atrasada"
            else:
                status = "Em andamento"

            linhas.append(
                {
                    "acao_id": f"A{contador:04d}",
                    "cliente_id": cid,
                    "categoria": categoria,
                    "descricao": str(rng.choice(_DESCRICOES[categoria])).format(
                        a=str(rng.choice(_AREAS))
                    ),
                    "responsavel": responsavel,
                    "prioridade": _sorteia_de_dict(rng, par["prioridades"]),
                    "data_abertura": abertura,
                    "prazo_original": prazo_original,
                    "prazo_atual": prazo_atual,
                    "n_reprogramacoes": n_repro,
                    "data_conclusao": data_conclusao,
                    "status": status,
                }
            )

    acoes = pd.DataFrame(linhas)
    return acoes.sort_values(["cliente_id", "data_abertura"]).reset_index(drop=True)


def preencher_acoes_revisadas(
    acompanhamentos: pd.DataFrame, acoes: pd.DataFrame
) -> pd.DataFrame:
    """Numa reunião revisa-se o que estava em aberto naquela semana.

    Sem isto, `n_acoes_revisadas` seria um número solto; com isto, é uma contagem
    verificável contra a tabela de ações — e a coerência entre as duas tabelas é
    o que permite alguém auditar a base.
    """
    acomp = acompanhamentos.copy()
    revisadas = []

    por_cliente = {cid: grupo for cid, grupo in acoes.groupby("cliente_id")}

    for _, linha in acomp.iterrows():
        if not linha["houve_reuniao"]:
            revisadas.append(0)
            continue
        grupo = por_cliente.get(linha["cliente_id"])
        if grupo is None:
            revisadas.append(0)
            continue
        ref = linha["semana_referencia"]
        fim_semana = ref + dt.timedelta(days=6)
        abertas = grupo[
            (grupo["data_abertura"] <= fim_semana)
            & (grupo["status"] != "Cancelada")
            & (
                grupo["data_conclusao"].isna()
                | (grupo["data_conclusao"] > ref)
            )
        ]
        revisadas.append(int(len(abertas)))

    acomp["n_acoes_revisadas"] = revisadas
    return acomp


# --------------------------------------------------------------------------------------
# Ponto de entrada do módulo
# --------------------------------------------------------------------------------------

def gerar_base(cfg: dict) -> dict[str, pd.DataFrame]:
    """Devolve as três tabelas do cenário descrito em `cfg`."""
    rng = np.random.default_rng(cfg["cenario"]["semente"])

    clientes = gerar_clientes(cfg, rng)
    perfis = gerar_perfis(cfg, clientes, rng)
    acompanhamentos = gerar_acompanhamentos(cfg, clientes, perfis, rng)
    acoes = gerar_acoes(cfg, clientes, perfis, acompanhamentos, rng)
    acompanhamentos = preencher_acoes_revisadas(acompanhamentos, acoes)

    return {"clientes": clientes, "acoes": acoes, "acompanhamentos": acompanhamentos}
