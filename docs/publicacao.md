# Publicação

O que sobe para o GitHub, o que não sobe, e por quê. Este arquivo é nota de projeto — se você
chegou aqui procurando como rodar, o [README](../README.md) é o lugar.

---

## O que sobe

```
README.md                      a peça de comunicação
requirements.txt
config.yaml                    os parâmetros que dão sentido ao "mude e veja reagir"
.gitignore
src/                           os seis arquivos de código
docs/                          indicadores, decisões, limitações, este arquivo
ferramentas/                   o script que extrai o print da planilha
exemplos/
  relatorio_exemplo.xlsx       a saída versionada
  prints/                      as imagens usadas no README, no site e no LinkedIn
```

**`exemplos/` é obrigatório, não é acabamento.** A maioria de quem abre um repositório não instala
dependência nenhuma. A planilha versionada e os prints são o que permite entender o valor do
projeto sem rodar uma linha — e o print precisa aparecer no README **antes** de qualquer instrução
de instalação.

## O que não sobe

| Item | Por quê |
|---|---|
| `saida/` | é gerado. Sobe uma cópia curada em `exemplos/`, não o resultado de cada execução |
| `__pycache__/`, `*.pyc` | ruído de execução |
| `.venv/`, `venv/` | ambiente da máquina, não do projeto |
| `.claude/`, `.vscode/`, `.idea/` | configuração de ferramenta local. Quem clona usa a dele |
| `~$painel_aderencia.xlsx` | arquivo de trava que o Excel cria com a planilha aberta. Sobe por descuido com muita frequência |
| O briefing de concepção | documento de trabalho pessoal. O que dele interessa a terceiros já está no README e em `docs/` |

Tudo isso está no [.gitignore](../.gitignore). Antes do primeiro `push`, vale conferir com
`git status` se algum deles escapou — depois de commitado, tirar dá trabalho.

## Nome do repositório

`painel-aderencia-plano-acao`.

O nome do repositório é o nome do projeto, não o nome de um arquivo. `gerador_kpis.py` como
repositório parece arquivo solto; `painel-aderencia-plano-acao` parece projeto. A diferença é de
percepção, e percepção é metade do que um portfólio faz.

## Ordem de publicação

1. **Rodar antes de subir.** `python src/main.py` e `python src/validacao.py`. Subir com o
   relatório desatualizado em `exemplos/` é o erro mais fácil de cometer, porque nada quebra.
2. **Atualizar `exemplos/`** com a saída da rodada final:
   `copy saida\painel_aderencia.xlsx exemplos\relatorio_exemplo.xlsx`
3. **Atualizar os prints.** As imagens do Python saem sozinhas com o `main.py`. O print da aba
   Resumo sai da própria planilha:
   `powershell -Sta -ExecutionPolicy Bypass -File ferramentas\print_da_planilha.ps1`
4. **Conferir o README renderizado** no GitHub depois do primeiro push — caminho de imagem quebrado
   é o defeito mais comum, e é o primeiro que alguém vê.
5. **LinkedIn:** cadastrar em Projetos, com as competências de mapeamento de processos, indicadores
   de desempenho, análise de dados, melhoria contínua e Excel avançado.
6. **Post:** a tese em uma linha, os dois indicadores mais fáceis de entender (aderência e aging),
   o print, e o que a ferramenta não faz. Fechar com o próximo indicador. Sem jargão e sem stack no
   meio do texto — a stack fica no repositório.

## O print que vai para a arte

O print de referência é o da **aba Resumo capturada da própria planilha**, em
`exemplos/prints/planilha-resumo.png`. É ele que aparece no README.

Sai por `ferramentas/print_da_planilha.ps1`, que abre o arquivo no Excel, recorta o intervalo do
painel e salva em PNG — o mesmo que uma captura de tela, sem barra de fórmulas, sem cabeçalho de
coluna e sempre no mesmo enquadramento. O script precisa de Windows com Excel instalado; sem isso,
uma captura de tela manual da aba Resumo, com as linhas de grade já desligadas pela formatação,
resolve igual.

As outras imagens da pasta são geradas pelo `main.py` com matplotlib e servem de material
complementar para o post e para o site. A planilha continua sendo a entrega; elas são apoio.
