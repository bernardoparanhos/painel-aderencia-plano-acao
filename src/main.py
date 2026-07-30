"""Ponto de entrada: gera, calcula, exporta.

    python src/main.py

Lê o cenário do config.yaml, gera as três tabelas sintéticas, calcula os seis
indicadores e escreve a pasta de trabalho em saida/. Um comando, um arquivo.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import indicadores as ind  # noqa: E402
from gerador import _segunda_da_semana, gerar_base  # noqa: E402
from relatorio import montar_workbook, salvar_reproduzivel  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------------------

def carregar_config(caminho: Path) -> dict:
    with open(caminho, encoding="utf-8") as arq:
        cfg = yaml.safe_load(arq)

    corte = cfg["cenario"]["data_corte"]
    if isinstance(corte, dt.datetime):
        cfg["cenario"]["data_corte"] = corte.date()
    elif isinstance(corte, str):
        cfg["cenario"]["data_corte"] = dt.date.fromisoformat(corte)

    pesos = cfg["risco"]
    soma = pesos["peso_vencidas"] + pesos["peso_aging"] + pesos["peso_replanejamento"]
    if abs(soma - 1.0) > 1e-9:
        raise ValueError(f"Os pesos do score de risco somam {soma}, e precisam somar 1.")

    return cfg


def _caminho_curto(caminho: Path) -> str:
    """Caminho relativo à raiz quando dá; absoluto quando o usuário apontou para fora."""
    try:
        return str(caminho.relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def calcular_tudo(tabelas: dict, cfg: dict) -> dict:
    """Roda os seis indicadores sobre a base e devolve tudo o que vira aba."""
    corte = cfg["cenario"]["data_corte"]
    clientes, acoes, acomp = tabelas["clientes"], tabelas["acoes"], tabelas["acompanhamentos"]

    base = ind.preparar(acoes, corte)

    return {
        "base_preparada": base,
        "painel": ind.painel_resumo(base, acomp, clientes, cfg),
        "aderencia_cliente": ind.aderencia_por_cliente(base, clientes),
        "aging_faixas": ind.aging_de_pendencias(base),
        "aging_detalhe": ind.aging_detalhado(base, clientes),
        "replanejamento_cliente": ind.replanejamento_por_cliente(base, clientes),
        "replanejamento_categoria": ind.replanejamento_por_categoria(base),
        "lead_time": ind.lead_time_por_categoria(base),
        "cobertura_semanal": ind.cobertura_por_semana(acomp),
        "cobertura_cliente": ind.cobertura_por_cliente(acomp, clientes),
        "ranking": ind.ranking_de_risco(base, clientes, cfg["risco"]),
        "base_achatada": ind.base_achatada(base, clientes, corte),
    }


def exportar_csv(tabelas: dict, res: dict, pasta: Path) -> list[Path]:
    pasta_csv = pasta / "csv"
    pasta_csv.mkdir(parents=True, exist_ok=True)
    escritos = []
    saidas = {
        "clientes": tabelas["clientes"],
        "acoes": tabelas["acoes"],
        "acompanhamentos": tabelas["acompanhamentos"],
        "base_achatada": res["base_achatada"],
        "ranking_de_risco": res["ranking"],
        "cobertura_semanal": res["cobertura_semanal"],
    }
    for nome, df in saidas.items():
        destino = pasta_csv / f"{nome}.csv"
        df.to_csv(destino, index=False, encoding="utf-8-sig", sep=";", decimal=",")
        escritos.append(destino)
    return escritos


def imprimir_resumo(painel: dict, cfg: dict, periodo: tuple[dt.date, dt.date]) -> None:
    """O mesmo painel do Excel, em texto, para quem rodou pelo terminal."""
    inicio, fim = periodo
    largura = 74
    linha = "─" * largura

    print()
    print(f"┌{linha}┐")
    print(f"│ {'PAINEL DE ADERÊNCIA A PLANO DE AÇÃO'.ljust(largura - 1)}│")
    subtitulo = (
        f"{cfg['cenario']['nome']} · {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} · "
        f"{painel['total_acoes']} ações"
    )
    print(f"│ {subtitulo.ljust(largura - 1)}│")
    print(f"├{linha}┤")

    itens = [
        ("Aderência ao prazo", f"{painel['aderencia']:.0%}",
         f"sobre {painel['aderencia_denominador']} ações com prazo vencido"),
        ("Pendências +30 dias", f"{painel['aging_mais_30']}",
         f"de {painel['pendencias_abertas']} em aberto ({painel['aging_mais_30_pct']:.0%})"),
        ("Taxa de replanejamento", f"{painel['taxa_replanejamento']:.0%}",
         "ações com o prazo movido ao menos uma vez"),
        ("Lead time mediano", f"{painel['lead_time_mediano']:.0f} dias",
         "da abertura à conclusão"),
        ("Cobertura", f"{painel['cobertura']:.0%}",
         "das semanas-cliente com reunião registrada"),
        ("Clientes críticos", f"{painel['clientes_criticos']}",
         f"topo: {painel['cliente_topo_risco']}"),
    ]
    for rotulo, valor, contexto in itens:
        print(f"│ {rotulo:<24}{valor:>10}   {contexto[:36]:<36}│")

    print(f"└{linha}┘")
    if not painel["cobertura_suficiente"]:
        print(
            f"  Cobertura abaixo de {cfg['leitura']['cobertura_minima']:.0%}: os números acima "
            "descrevem a parte\n  acompanhada da carteira, não a carteira inteira."
        )
    print()


# --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera a base sintética, calcula os indicadores e escreve o Excel."
    )
    parser.add_argument("--config", default=str(RAIZ / "config.yaml"), help="cenário a usar")
    parser.add_argument("--saida", default=None, help="pasta de saída (padrão: a do config)")
    parser.add_argument("--semente", type=int, default=None, help="sobrescreve a semente")
    parser.add_argument("--sem-prints", action="store_true", help="não gera as imagens do painel")
    parser.add_argument("--sem-csv", action="store_true", help="não exporta os CSVs")
    args = parser.parse_args(argv)

    cfg = carregar_config(Path(args.config))
    if args.semente is not None:
        cfg["cenario"]["semente"] = args.semente

    pasta = (Path(args.saida) if args.saida else RAIZ / cfg["saida"]["pasta"]).resolve()
    pasta.mkdir(parents=True, exist_ok=True)

    corte = cfg["cenario"]["data_corte"]
    periodo = (
        _segunda_da_semana(corte, cfg["cenario"]["horizonte_semanas"], 1),
        corte,
    )

    print(f"  cenário .......... {cfg['cenario']['nome']} (semente {cfg['cenario']['semente']})")
    tabelas = gerar_base(cfg)
    print(
        f"  base gerada ...... {len(tabelas['clientes'])} clientes · "
        f"{len(tabelas['acoes'])} ações · {len(tabelas['acompanhamentos'])} semanas-cliente"
    )

    res = calcular_tudo(tabelas, cfg)
    print("  indicadores ...... 6 calculados")

    destino = pasta / cfg["saida"]["arquivo_excel"]
    salvar_reproduzivel(montar_workbook(res, cfg, periodo), destino, corte)
    print(f"  planilha ......... {_caminho_curto(destino)}")

    if cfg["saida"]["exportar_csv"] and not args.sem_csv:
        escritos = exportar_csv(tabelas, res, pasta)
        print(f"  csv .............. {len(escritos)} arquivos em {pasta.name}/csv")

    if cfg["saida"]["gerar_prints"] and not args.sem_prints:
        from prints import gerar_prints  # importado só aqui: matplotlib é opcional

        imagens = gerar_prints(res, cfg, periodo, RAIZ / cfg["saida"]["pasta_prints"])
        print(f"  prints ........... {len(imagens)} imagens em {cfg['saida']['pasta_prints']}/")

    imprimir_resumo(res["painel"], cfg, periodo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
