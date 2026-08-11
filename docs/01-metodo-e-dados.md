# Método e dados

## Pergunta demonstrativa

É possível classificar o nível mensal de pressão sobre um serviço territorial fictício a partir de volume de chamados, tempo de resposta, cobertura, população e condições ambientais?

A pergunta serve para validar o pipeline. A pergunta definitiva deverá nascer do levantamento com o parceiro do semestre.

## Origem e finalidade

O arquivo `data/raw/demonstracao_territorial.csv` é gerado por `scripts/generate_demo_data.py` com semente 42. Todos os registros declaram a origem `SINTETICO_DEMONSTRACAO`. Qualquer outra origem é rejeitada nesta versão para impedir que uma base desconhecida seja tratada como validada.

| Campo | Tipo | Significado | Regra principal |
|---|---|---|---|
| `competencia` | data | primeiro dia do mês observado | data ISO válida |
| `territorio` | texto | nome fictício da área | obrigatório |
| `populacao_estimada` | inteiro | população simulada | não negativa |
| `chamados` | inteiro | solicitações simuladas no mês | não negativo |
| `tempo_medio_h` | decimal | resposta média simulada em horas | não negativa |
| `chuva_mm` | decimal | precipitação mensal simulada | não negativa |
| `temperatura_c` | decimal | temperatura média simulada | entre -20 e 60 |
| `cobertura_servico_pct` | decimal | cobertura simulada do serviço | entre 0 e 100 |
| `nivel_pressao` | categoria | alvo Baixo, Moderado ou Alto | conjunto fechado |
| `origem` | texto | proveniência declarada | somente demonstração sintética |

## Construção do alvo

O nível de pressão combina chamados normalizados pela população, tempo de resposta e falta de cobertura. Limiares fixos separam as classes: abaixo de 1,65 é `Baixo`; de 1,65 até menos de 2,05 é `Moderado`; a partir de 2,05 é `Alto`.

Como o alvo é derivado das próprias variáveis, existe uma relação aprendível por construção. Isso é adequado para um teste técnico controlado, mas não prova validade externa nem relação causal.

## Treino e avaliação

- treino: todas as 144 observações de 2024;
- teste: todas as 144 observações de 2025;
- preparação: codificação one-hot do território e passagem das variáveis numéricas;
- modelo: Random Forest com semente fixa e balanceamento de classes;
- referência: classificador que sempre escolhe a classe mais frequente do treino;
- métricas: acurácia, F1 macro, matriz de confusão e relatório por classe.

A separação temporal evita treinar com observações futuras. Os mesmos territórios aparecem nos dois períodos; portanto, o teste mede generalização no tempo para áreas já conhecidas, não generalização para novos territórios.

## Resultado de referência

| Medida | Resultado |
|---|---:|
| acurácia do modelo | 0,7639 |
| F1 macro | 0,7660 |
| acurácia da linha de base | 0,5000 |
| registros de teste | 144 |

Os artefatos completos ficam em `artifacts/metrics.json` e `artifacts/predictions.csv`.

## Limitações e ética

- não há pessoas, endereços nem territórios reais;
- a base não mede representatividade ou impacto social;
- a classificação não deve priorizar atendimento ou distribuir recursos;
- o desempenho pode cair drasticamente em uma fonte real;
- uma futura base real exigirá licença ou consentimento, minimização, anonimização, análise de viés e nova validação;
- correlação ou capacidade preditiva não implica causalidade.

## Adaptação para o semestre

Com parceiro e fonte definidos, deve-se criar um contrato de dados próprio, preservar uma camada bruta imutável, documentar licença e período, definir a divisão de avaliação antes do treino e registrar a devolutiva do público. Se o volume ou a qualidade forem insuficientes, a decisão correta é priorizar análise descritiva, e não forçar aprendizagem de máquina.
