# Limitações

O que estes dados **não** permitem afirmar.

Declarar limite é sinal de quem mede. A lista existe para que ninguém — inclusive eu, daqui a seis
meses — leia um número deste projeto como algo que ele não é.

---

## 1. Os dados são sintéticos. Nenhum número descreve empresa real

Toda a base é gerada por código a partir do `config.yaml`. Não há dado de cliente, não há
apontamento real, não há empresa por trás de nenhum dos 26 nomes fictícios.

**Não se pode dizer:** "a aderência média de uma carteira de consultoria é 48%".
**Pode-se dizer:** "com estas premissas de prazo prometido e de tempo real de execução, a aderência
resultante é 48% — e o painel mostra onde isso dói."

O projeto demonstra o **método de medição**, não um diagnóstico de mercado.

## 2. O comportamento modelado é premissa, não medição

A parte mais discutível do projeto está no `config.yaml`, não no cálculo dos indicadores. Que a
categoria Processo leve 23 dias de mediana real contra 21 prometidos, que 7% das ações sejam
abandonadas, que 20% dos clientes concentrem o replanejamento: tudo isso são hipóteses minhas
sobre como o processo se comporta, informadas pela rotina que originou a ideia, e não estimadas
a partir de amostra nenhuma.

Mudar esses parâmetros muda todos os indicadores. Isso é recurso, não defeito — é o que permite
perguntar "e se a reunião fosse quinzenal?". Mas significa que **os valores absolutos do painel
são consequência das premissas**, e as premissas não foram validadas contra realidade.

O que não depende de premissa é a aritmética: dado o mesmo conjunto de ações, os seis indicadores
seriam calculados do mesmo jeito sobre dados reais.

## 3. O projeto não afirma ganho de eficiência

Não há medição antes e depois em operação real. Não existe grupo de controle, não existe carteira
que usou o painel comparada com carteira que não usou.

**Não se pode dizer:** "esta ferramenta aumenta a aderência da carteira".
**Pode-se dizer:** "esta ferramenta torna a aderência visível, e o que não é visível não é
discutido na reunião".

A tese do projeto é sobre **medição**, não sobre resultado.

## 4. Lead time só enxerga o que fechou

A mediana de lead time é calculada sobre ações concluídas. As ações que nunca fecharam — que são
justamente as mais lentas — ficam de fora, e o número sai otimista por construção. No cenário base,
isso é forte a ponto de a mediana aparecer **abaixo** do prazo prometido numa carteira que cumpre
menos da metade dos prazos.

A coluna `mediana_com_pendentes` corrige parcialmente, contando cada pendência pelo tempo já
decorrido. Como esse tempo ainda vai crescer, ela é um **limite inferior** da verdade, não a
verdade. O lead time real é pior que os dois números.

Fazer isso direito exigiria análise de sobrevivência (Kaplan-Meier), que está fora do escopo desta
versão e é honesto dizer que está.

## 5. O score de risco é relativo, e só serve para ordenar

A normalização é min-max contra a própria carteira. O pior cliente tende a 100 mesmo que esteja
bem em termos absolutos; o melhor tende a 0 mesmo estando mal.

**Não se pode dizer:** "o cliente X tem risco 81 de um máximo de 100".
**Pode-se dizer:** "o cliente X é o primeiro da fila esta semana".

Os pesos (45/35/20) são convenção declarada, não resultado de calibração estatística. Estão no
`config.yaml` justamente para poderem ser contestados. Duas carteiras diferentes não têm scores
comparáveis entre si.

## 6. A cobertura mede registro, não qualidade

O indicador de cobertura conta reuniões registradas. Ele não sabe se a reunião durou dez minutos
ou duas horas, se a pauta foi revisada inteira ou se alguém só marcou presença. Uma carteira pode
ter 100% de cobertura e acompanhamento ruim.

O campo `n_acoes_revisadas` dá uma pista de profundidade, mas é gerado por regra, não observado.

## 7. O período é uma janela fechada, sem sazonalidade

O horizonte é de 26 semanas contínuas, sem feriado, sem férias coletivas, sem fechamento de ano.
A geração não modela períodos em que a operação inteira desacelera, e eles existem: dezembro e
janeiro não se parecem com maio.

Como consequência, a série de cobertura oscila em torno de uma média estável, quando na prática
ela tem quedas sazonais previsíveis.

## 8. Cancelamento é tratado como decisão legítima, e isso é gamificável

Ações canceladas saem de todos os denominadores, pelo motivo explicado em
[decisoes.md](decisoes.md#7-cancelamento-sai-do-denominador). O efeito colateral é conhecido: quem
quiser melhorar a aderência sem melhorar a execução pode cancelar em massa as ações que vão
estourar.

O painel mostra o total de cancelamentos ao lado da aderência justamente para que a manobra fique
visível, mas não existe nenhum controle automático contra ela. Em uso real, aderência subindo
junto com cancelamento subindo é sinal de alerta, não de melhora.

## 9. Uma ação, um prazo, um responsável

O modelo não tem dependência entre ações, não tem subtarefa, não tem responsável compartilhado e
não tem esforço estimado. Plano de ação real tem tudo isso.

A simplificação é deliberada — os seis indicadores não precisam desses campos —, mas significa que
o projeto não é um modelo de gestão de projetos. É um modelo do **acompanhamento** de um plano de
ação, que é coisa mais estreita.

## 10. O que o número de reprogramações não distingue

`n_reprogramacoes` conta quantas vezes o prazo se moveu. Não distingue a reprogramação combinada
com antecedência e justificativa da reprogramação anunciada no dia do vencimento. São
comportamentos muito diferentes, com a mesma contagem.

---

## Em uma frase

Este projeto prova que o processo de acompanhamento **pode ser medido**, e mostra quais números
respondem quais decisões. Ele não mede nenhuma carteira real, não valida nenhuma hipótese sobre
comportamento de clientes e não demonstra ganho de eficiência.
