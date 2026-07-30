# Decisões de modelagem

O que foi decidido, e por quê. Documento de projeto, não de instalação: a intenção é que alguém
que discorde de uma decisão consiga discordar do motivo, não adivinhar o motivo.

---

## 1. Por que dados sintéticos

A rotina que originou a ideia é de carteira real. O dado é do cliente, não meu, e não sai de lá.
Sintético resolve dois problemas de uma vez: não expõe nada de ninguém e permite provar o que a
ferramenta faz de verdade, que é **medir um processo de acompanhamento** — não analisar uma
carteira específica.

A contrapartida é dura e está declarada em [limitacoes.md](limitacoes.md): nenhum número deste
projeto descreve uma empresa real. O que o projeto demonstra é o método de cálculo e a leitura de
decisão que cada indicador permite.

## 2. As três tabelas

O modelo é o menor que sustenta os seis indicadores. Cada campo abaixo é usado por pelo menos um
cálculo; campo que não fosse usado por nenhum não entraria.

### `clientes` — uma linha por cliente da carteira

| Campo | Tipo | Observação |
|---|---|---|
| `cliente_id` | texto | `C01`…`C26` |
| `nome` | texto | fictício, gerado por combinação |
| `segmento` | categoria | Indústria, Varejo, Serviços, Agronegócio, Construção, Saúde |
| `porte` | categoria | Pequeno, Médio, Grande — governa o volume de ações |
| `data_entrada` | data | pode ser posterior ao início do horizonte |
| `consultor` | texto | responsável pelo acompanhamento |

### `acoes` — uma linha por ação de plano de ação

| Campo | Tipo | Observação |
|---|---|---|
| `acao_id` | texto | `A0001`… |
| `cliente_id` | texto | chave para `clientes` |
| `categoria` | categoria | Processo, Indicador, Comercial, Financeiro, Pessoas |
| `descricao` | texto | frase curta, coerente com a categoria |
| `responsavel` | categoria | Cliente ou Consultoria |
| `prioridade` | categoria | Alta, Média, Baixa |
| `data_abertura` | data | sempre cai em uma semana com reunião registrada |
| `prazo_original` | data | o prazo prometido na reunião de abertura. **Nunca muda** |
| `prazo_atual` | data | o prazo vigente depois das reprogramações |
| `n_reprogramacoes` | inteiro | quantas vezes o prazo foi movido |
| `data_conclusao` | data ou vazio | vazio para tudo que não foi concluído |
| `status` | categoria | Concluída, Em andamento, Atrasada, Cancelada |

Guardar `prazo_original` e `prazo_atual` em colunas separadas é a decisão estrutural do modelo
inteiro. É o que permite medir aderência contra a promessa e operar contra o prazo vigente ao
mesmo tempo. Um modelo com uma coluna só de prazo não consegue calcular aderência ao prazo —
só consegue calcular aderência ao último prazo, que é quase sempre uma boa notícia falsa.

### `acompanhamentos` — uma linha por cliente por semana

| Campo | Tipo | Observação |
|---|---|---|
| `cliente_id` | texto | chave para `clientes` |
| `semana` | inteiro | 1 … horizonte |
| `semana_referencia` | data | segunda-feira da semana |
| `houve_reuniao` | booleano | base da cobertura |
| `n_acoes_revisadas` | inteiro | 0 quando não houve reunião |
| `observacao` | texto | curto, do tipo que aparece em ata |

A linha existe mesmo quando não houve reunião. Semana sem registro e semana com registro de "não
houve" são coisas diferentes, e o indicador de cobertura depende de saber a diferença. Só não
existe linha para semana anterior à entrada do cliente na carteira.

## 3. Ação nasce em reunião

Os `acompanhamentos` são gerados **antes** das `acoes`, e uma ação só pode ser aberta em uma
semana em que houve reunião com aquele cliente.

Isso não é detalhe de implementação: é o que faz a cobertura ter consequência. Cliente com agenda
irregular gera menos ações, e as ações que ele tem envelhecem mais, porque não há reunião para
cobrá-las. O efeito aparece sozinho nos indicadores, sem nenhum parâmetro que o force. Se a
geração fosse independente, cobertura seria um número decorativo ao lado de indicadores que não
sabem que ela existe.

## 4. Como o atraso é gerado

Não existe um parâmetro "taxa de cumprimento" que sorteia direto se a ação cumpriu o prazo. O
cumprimento é **consequência**, e sai do encontro de duas coisas:

1. **O prazo prometido**, fixo por categoria (`prazo_prometido` no `config.yaml`).
2. **A duração real de execução**, sorteada de uma lognormal com mediana `lead_time_base`,
   multiplicada pelo fator de disciplina do cliente e pelo fator do responsável.

A ação cumpre o prazo se a duração real couber no prazo prometido. Nada mais.

Três motivos para modelar assim:

- **Cauda longa sem gambiarra.** A lognormal já produz o padrão real: a maioria fecha em torno da
  mediana, uma minoria estoura muito. Uma normal daria estouros simétricos, que não existem —
  ninguém entrega 40 dias antes do prazo.
- **Otimismo estrutural fica explícito.** Em quase toda categoria o `lead_time_base` é maior que o
  `prazo_prometido`. Essa diferença — a reunião prometendo mais rápido do que a operação executa —
  é a causa modelada do descumprimento, e é uma tese sobre o processo, não um número mágico.
- **Os indicadores ficam coerentes entre si.** Aderência, lead time e replanejamento saem todos do
  mesmo sorteio. Se cada um fosse sorteado separado, o painel poderia mostrar aderência ruim com
  lead time ótimo, o que não descreve nenhuma operação possível.

**Disciplina por cliente.** Cada cliente recebe um multiplicador lognormal fixo
(`variabilidade_entre_clientes`) aplicado a todas as suas ações. É o que faz alguns clientes serem
consistentemente piores — sem isso, o ranking de risco ordenaria ruído, e ordenar ruído é pior que
não ordenar.

## 5. Como a reprogramação é gerada

A reprogramação é reativa, como na vida real: enquanto o prazo vigente vai ficando para trás e a
ação não fecha, alguém empurra a data na reunião. O laço soma passos de 7 a 21 dias ao
`prazo_atual` até alcançar a data de conclusão — ou a data de corte, para o que ainda está aberto.

**Concentração em poucos clientes.** Uma fração da carteira
(`fracao_clientes_replanejadores`) é marcada como replanejadora e usa passos menores
(`fator_passo_replanejador`). Passo menor significa mais reprogramações para o mesmo atraso, que é
exatamente o comportamento observado: a diferença entre clientes não é o tamanho do atraso, é o
hábito de remarcar de semana em semana em vez de repactuar uma vez.

Isso também garante que a taxa de replanejamento **não** seja proporcional à taxa de atraso. Os
dois indicadores precisam poder discordar — é da discordância entre eles que sai o diagnóstico de
"prazo mal estimado" versus "execução travada".

## 6. Ações abandonadas

`fracao_abandonadas` das ações nunca concluem e nunca são canceladas. Elas ficam com
`data_conclusao` vazia e recebem no máximo uma reprogramação
(`max_reprogramacoes_abandonada`), porque ação abandonada não é remarcada: ela simplesmente para
de ser lida na reunião.

Sem essa fatia, a faixa +30 do aging ficaria quase vazia e o indicador não teria o que revelar. É
o padrão mais incômodo do processo real e o que mais justifica o painel existir — por isso é
modelado de propósito, e não como efeito colateral da cauda da lognormal.

## 7. Cancelamento sai do denominador

Ação cancelada não entra em aderência, aging, replanejamento nem lead time. Ela aparece na aba
Base e na contagem geral, e só.

Cancelar é uma decisão de gestão registrada: a ação deixou de fazer sentido. Contar cancelamento
como descumprimento faria o indicador punir a limpeza de pauta e premiar a pauta inflada de ações
mortas — o incentivo exatamente invertido. A contrapartida é conhecida: se alguém quiser maquiar
aderência, o caminho é cancelar em massa. Por isso o volume de cancelamentos aparece explícito no
Resumo, ao lado da aderência. Indicador que pode ser gamed precisa vir com o contador do gaming ao lado.

## 8. Divergências encontradas na validação manual

O Bloco 3 do roadmap pedia conferir dois ou três casos à mão contra o cálculo do código. O script
`src/validacao.py` recalcula os seis indicadores em Python puro, linha a linha, com `for` e `if`,
sem nenhuma agregação do Pandas — e compara com o resultado da rotina oficial. São implementações
independentes: para as duas concordarem por acaso, o mesmo erro teria que ter sido cometido duas
vezes, do mesmo jeito, em dois estilos de código diferentes. Rodando com a semente 42, as sete
verificações passam.

Três divergências apareceram durante a construção e foram resolvidas assim:

**Ações com prazo original vencido mas ainda em aberto.** A primeira versão excluía essas ações do
denominador da aderência, contando só as já concluídas. Isso inflava o indicador em cerca de sete
pontos — 57% em vez de 50%, no cenário base. Uma ação vencida e em aberto já descumpriu, e omiti-la
é adiar a má notícia até a semana em que ela fecha. Corrigido: o denominador é "prazo original
vencido", independente de status.

**Lead time mostrando categoria entregando antes do prometido.** Numa carteira com 50% de
aderência, a tabela de lead time apontava mediana abaixo do prazo prometido em quase toda
categoria. Não era erro de conta: é viés de sobrevivência, porque a mediana só enxerga ações que
fecharam, e as que mais demoram são exatamente as que ainda não fecharam. Como o número, sozinho,
levava à leitura oposta da verdade, entrou a coluna `mediana_com_pendentes`, que conta cada
pendência pelo tempo já decorrido desde a abertura. Como esse tempo ainda vai crescer, o resultado
é um limite inferior da mediana verdadeira — e é por ele que se promete prazo. Foi a única vez em
que um indicador precisou de uma segunda coluna para não mentir.

**Aging de ação aberta na própria semana de corte.** Ação aberta na sexta e lida no domingo
aparecia com aging 2, o que empurrava a faixa 0–7 para cima e diluía a leitura. Mantido assim:
o aging é tempo em aberto, e dois dias em aberto são dois dias em aberto. A alternativa —
começar a contar só depois do vencimento — foi rejeitada pelo motivo descrito em
[indicadores.md](indicadores.md#2-aging-de-pendências).

## 9. Formato de saída: Excel, não dashboard web

A decisão é sobre o destinatário. A reunião semanal acontece com planilha na tela, não com
navegador aberto em servidor. Um dashboard web exigiria hospedagem, e hospedagem exigiria alguém
mantendo — o que mata a ferramenta em duas semanas. Uma pasta de trabalho vai por e-mail, abre no
celular do sócio e sobrevive sem mim.

Os CSVs da base saem junto para quem quiser levar para Power BI. O que não vai acontecer é o Excel
ser o formato intermediário de um dashboard: ele é a entrega.
