# Indicadores

Definição, fórmula e pergunta de decisão de cada indicador do painel.

Regra que governa esta lista: **indicador que ninguém usa é enfeite.** Se não for possível
escrever a pergunta de decisão ao lado, o indicador não entra. Os seis abaixo passaram no teste.

Convenções válidas para todo o documento:

- **Data de corte** — último dia do horizonte simulado. Tudo é calculado como se a leitura
  estivesse sendo feita nesse dia, antes da reunião da semana seguinte.
- **Período de referência** — do primeiro ao último dia do horizonte. Aparece escrito na aba
  Resumo, porque número sem período é número sem significado.
- **Ação cancelada** — sai de todos os denominadores. Cancelamento é decisão registrada, não
  falha de execução. Contar cancelamento como descumprimento pune quem limpa a pauta.
- **Ação em aberto / pendência** — ação não concluída e não cancelada na data de corte.

---

## 1. Aderência ao prazo

**O que mede:** a fração de compromissos que foram cumpridos na data em que foram prometidos.

**Fórmula**

```
aderência = ações concluídas até o prazo ORIGINAL
            ÷ ações com prazo ORIGINAL vencido dentro do período
```

- Denominador: ações não canceladas cujo `prazo_original` é anterior ou igual à data de corte.
  Uma ação aberta há três dias com prazo para daqui a duas semanas ainda não deve nada — não entra.
- Numerador: dessas, as que têm `data_conclusao` menor ou igual ao `prazo_original`.
- Uma ação ainda em aberto cujo prazo original já venceu conta no denominador e não no numerador.
  Ela já descumpriu. Esperar a conclusão para contabilizar seria adiar a má notícia.

**Pergunta de decisão:** o acompanhamento está funcionando ou só registrando?

**Por que o prazo original e não o atual.** Medir contra o prazo atual é medir contra um alvo que
se move. Se toda reprogramação redefine a régua, a aderência tende a 100% e o indicador para de
informar qualquer coisa. O prazo atual é usado no controle operacional — saber o que vence esta
semana. O prazo original é usado na medição.

**Faixas de leitura adotadas:** ≥ 70% saudável, 50–70% atenção, < 50% crítico. São faixas de
convenção do painel, não benchmark de mercado — ver [limitacoes.md](limitacoes.md).

---

## 2. Aging de pendências

**O que mede:** há quanto tempo cada pendência em aberto está em aberto.

**Fórmula**

```
dias_em_aberto = data de corte − data de abertura      (apenas ações em aberto)
faixas: 0–7 · 8–15 · 16–30 · +30 dias
```

**Pergunta de decisão:** onde intervir primeiro.

**Por que faixas e não média.** A média de aging mistura a ação aberta ontem com a ação parada há
quatro meses e devolve um número que não descreve nenhuma das duas. A distribuição por faixas
mostra a cauda, e a cauda é o problema. Uma carteira com aging médio de 20 dias pode ser uma
carteira saudável ou uma carteira com 15% das ações abandonadas — só as faixas separam os casos.

**Por que a partir da abertura e não do vencimento.** O que interessa é o tempo que o assunto
está na pauta sem sair dela. Contar a partir do vencimento esconde o prazo folgado: uma ação
aberta há 90 dias com prazo de 85 apareceria como "5 dias de atraso". A coluna
`dias_apos_prazo_original` fica na aba Base para quem quiser a outra leitura.

**Leitura da faixa +30:** pendência de mais de 30 dias não é atraso, é ação abandonada. O painel
destaca essa faixa em vermelho porque a decisão que ela pede é diferente: não é cobrar, é decidir
entre repactuar ou cancelar.

---

## 3. Taxa de replanejamento

**O que mede:** a fração de ações cujo prazo foi movido pelo menos uma vez.

```
taxa = ações com ao menos uma reprogramação ÷ total de ações não canceladas
```

Reportada também como média de reprogramações por ação replanejada, porque uma carteira com
muitas ações movidas uma vez é um problema diferente de uma carteira com poucas ações movidas
quatro vezes.

**Pergunta de decisão:** o prazo está sendo mal estimado na origem ou a execução está travando?

**Como separar os dois casos.** Cruzando com o lead time: se a taxa de replanejamento é alta e o
lead time real é estável, o problema é estimativa — a equipe entrega em um ritmo previsível e
promete outro. Se o lead time também é disperso, o problema é execução. O painel dá as duas
tabelas lado a lado por isso, e a aba Replanejamento quebra por cliente e por categoria para
mostrar se o problema é de todos ou de alguns.

---

## 4. Lead time de conclusão

**O que mede:** quanto tempo uma ação leva, da abertura à conclusão, por categoria.

```
lead_time = data de conclusão − data de abertura      (apenas ações concluídas)
reportado: mediana, p25, p75 e amplitude interquartil, por categoria
```

**Pergunta de decisão:** quanto tempo prometer na próxima reunião, com base em histórico.

**Por que mediana e não média.** A distribuição tem cauda longa à direita — a maioria das ações
fecha em prazo parecido e uma minoria estoura muito. A média é puxada pela cauda e passa a
descrever um caso que quase não acontece. A mediana responde "metade das ações desta categoria
fecha em até X dias", que é a frase que serve para prometer prazo.

**Por que p25 e p75 junto.** A mediana sozinha esconde o risco. Categoria com mediana de 20 dias e
p75 de 25 permite prometer prazo. Mediana de 20 com p75 de 60 não permite — ali o prazo prometido
precisa vir com condição, não com data.

**Viés declarado:** só entram ações concluídas. As ações que nunca fecharam — justamente as piores —
ficam de fora. O lead time real é pior do que o medido. Está em [limitacoes.md](limitacoes.md).

---

## 5. Cobertura de acompanhamento

**O que mede:** em que fração da carteira houve reunião registrada em cada semana.

```
cobertura(semana) = clientes com acompanhamento registrado na semana ÷ clientes ativos na semana
```

Cliente ativo é o que já entrou na carteira até aquela semana. Cliente que entrou em março não
conta como descoberto em janeiro.

**Pergunta de decisão:** os cinco indicadores acima podem ser lidos como verdade da carteira, ou
descrevem só a parte que foi acompanhada?

**Por que este indicador existe.** É o indicador que mede o próprio processo de medição. Aderência
de 80% sobre uma cobertura de 55% não é uma carteira com boa aderência: é uma carteira em que
metade dos clientes não foi acompanhada e a outra metade — provavelmente a mais engajada — vai bem.
Cobertura baixa não invalida os números, invalida a generalização deles.

**Regra de leitura adotada no painel:** abaixo de 70% de cobertura média, o Resumo escreve o aviso
junto do número. O aviso é parte do indicador, não decoração.

---

## 6. Ranking de risco por cliente

**O que mede:** ordena a carteira pela urgência de atenção na próxima semana.

```
score = 45% · pendências vencidas (% das ações do cliente)
      + 35% · aging médio das pendências em aberto
      + 20% · taxa de replanejamento do cliente

cada componente normalizado 0–100 pelo mínimo e máximo observados na carteira
```

**Pergunta de decisão:** por quem começar a agenda da semana.

**Por que os pesos são esses.** Pendência vencida é dívida já vencida — pesa mais. Aging é a
gravidade da dívida, entra em seguida. Replanejamento é sintoma, não dano: pesa menos porque um
cliente que reprograma e entrega é melhor que um cliente que não reprograma e não entrega. Os
pesos são convenção explícita e ficam no `config.yaml` para serem discutidos, não escondidos no
código.

**Por que o score é relativo.** A normalização é feita contra a própria carteira: o pior cliente
tende a 100 mesmo que esteja bem em termos absolutos. O score serve para **ordenar**, nunca para
afirmar "este cliente está em risco 82". Por isso a aba traz, ao lado do score, os três números
crus que o formaram — a leitura honesta é a dos números crus; o score só define a ordem da agenda.

**Classificação:** Crítico ≥ 70 · Atenção 40–69 · Estável < 40.

---

## Indicador que ficou de fora

**Percentual de ações por responsável (cliente × consultoria).** Calculável e interessante de
olhar, mas não passou no teste: não existe decisão que mude em função dele. Vira coluna de apoio
na aba Base, não vira indicador.

## Próximo indicador a construir

**Reincidência de tema.** Fração de ações abertas que tratam de um assunto já tratado em ação
anterior concluída para o mesmo cliente. Responde: a ação foi concluída ou só foi fechada? É o
indicador que separa entrega de encerramento administrativo. Fica de fora desta versão porque
exige um campo de tema padronizado que o gerador atual não modela.
