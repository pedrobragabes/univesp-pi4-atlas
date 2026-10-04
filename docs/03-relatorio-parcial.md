# Relatório parcial técnico — Atlas / PI IV

Execução de laboratório em 4 de outubro de 2026. Este documento registra o experimento sintético reproduzível disponível no repositório. A modalidade da matrícula, equipe, parceiro, problema extensionista e datas de entrega devem ser confirmados no AVA; o documento não comprova essas etapas.

## Identificação, contexto e problema

Projeto: Atlas, laboratório territorial de dados. Repositório: [univesp-pi4-atlas](https://github.com/pedrobragabes/univesp-pi4-atlas). O objetivo técnico é testar aquisição, validação, transformação, classificação, avaliação e comunicação de um conjunto controlado, antes de qualquer adaptação para dados autorizados de um parceiro.

A pergunta demonstrativa é se as características de um serviço fictício permitem classificar a pressão mensal em Baixo, Moderado ou Alto. Os nomes dos 12 territórios e as 288 observações são fictícios. A pergunta definitiva e a necessidade da comunidade permanecem pendentes de levantamento real.

## Fonte e governança dos dados

`scripts/generate_demo_data.py` gera 24 meses por território, entre janeiro de 2024 e dezembro de 2025, com semente 42. A origem obrigatória é `SINTETICO_DEMONSTRACAO`. A execução atual não coleta dados pessoais, endereços, observações de campo ou registros de terceiros.

O dicionário e os limiares do alvo estão em [Método e dados](01-metodo-e-dados.md). O validador rejeita ausência de campos/nulos, cabeçalhos duplicados, território vazio, números inválidos ou infinitos, contagens fracionárias, faixas inválidas, classes/origem desconhecidas, competências fora do formato ISO, dia diferente do primeiro do mês e registros fora de 2024–2025. A combinação território/competência deve ser única.

Hash SHA-256 dos bytes da entrada nesta execução: `6f66e58f0b1464d444883913120fc682dc2c850cc82f64d7fc2505119d559b12`. O hash identifica o arquivo usado; não comprova autenticidade de uma futura fonte real. Dados externos continuam exigindo origem, licença ou consentimento, minimização, anonimização, período e contrato de qualidade próprios. A licença MIT do código não autoriza conjuntos de terceiros.

## Objetivos e critérios de sucesso técnico

| Requisito | Decisão e implementação | Verificação | Resultado |
|---|---|---|---|
| Proveniência declarada | Somente origem sintética no contrato atual | Fonte não declarada rejeitada | Aprovado no laboratório |
| Qualidade antes de treinar | Contrato de campos, datas, unicidade e números | Entradas inválidas não publicam artefatos | Aprovado |
| Avaliação temporal | Treino 2024; teste 2025; nenhum outro ano aceito | 144 + 144 = 288 registros; três classes em ambos | Aprovado |
| Comparação com referência | Random Forest e `DummyClassifier(most_frequent)` no mesmo recorte | Acurácia superior à referência e F1 macro > 0,70 | Aprovado na base sintética |
| Reprodução | Semente fixa, hash, versões e classes registrados | Duas execuções produzem métricas, agregações e previsões idênticas | Aprovado no mesmo ambiente |
| Modelo exportado utilizável | `model.joblib` produzido pelo próprio pipeline | Recarregar reproduz as 144 previsões de teste | Aprovado |
| Comunicação fiel | Aviso sintético no painel/API; barras com escala 0–100% | Rotas, cabeçalhos e doze barras verificadas | Aprovado nos testes locais |

## Pipeline executado e ambiente

1. Gerar ou ler o CSV bruto sintético, sem substituir sua origem por uma declaração de campo.
2. Validar o contrato e derivar o mês da competência.
3. Separar 2024 para treino e 2025 para avaliação antes de ajustar o modelo.
4. Codificar território com `OneHotEncoder(handle_unknown="ignore")` e manter as variáveis numéricas.
5. Treinar Random Forest com 160 árvores, profundidade máxima 9, mínimo de duas amostras por folha, balanceamento de classes e `random_state=42`; treinar também a linha de base.
6. Exportar `metrics.json`, `territories.json`, `predictions.csv` e `model.joblib`; apresentar painel Flask e `/api/resumo`.

Ambiente local verificado: Windows, Python 3.14.7, pandas 3.0.6, scikit-learn 1.9.1 e joblib 1.6.0. `requirements.txt` fixa as dependências diretas; `metrics.json` registra as versões efetivamente usadas. Dependências transitivas e diferenças de plataforma podem afetar futuras reproduções, portanto a igualdade atual não é uma garantia entre versões distintas.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\generate_demo_data.py
.\.venv\Scripts\python.exe -m atlas.pipeline
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q atlas scripts tests
```

## Análise preliminar reproduzível

| Classe | Treino 2024 | Teste 2025 | F1 no teste |
|---|---:|---:|---:|
| Baixo | 42 | 34 | 0,7632 |
| Moderado | 66 | 72 | 0,7556 |
| Alto | 36 | 38 | 0,7792 |
| Total | 144 | 144 | — |

| Medida | Random Forest | Linha de base |
|---|---:|---:|
| Acurácia | 0,7639 | 0,5000 |
| F1 macro | 0,7660 | 0,2222 |

A matriz de confusão usa linhas para classes reais do gerador e colunas para as previstas:

| Real / Prevista | Baixo | Moderado | Alto |
|---|---:|---:|---:|
| Baixo | 29 | 5 | 0 |
| Moderado | 12 | 51 | 9 |
| Alto | 1 | 7 | 30 |

O período de teste possui 50% de classe Moderado; acertar sempre essa classe já alcança 50% de acurácia. O F1 macro e o relatório por classe complementam a comparação. As três classes estão presentes nos dois períodos.

O alvo é calculado a partir das próprias características de entrada. O resultado mede aprendizagem da regra sintética e não valida desempenho em territórios reais. A separação temporal evita o uso de observações de 2025 no treino, mas os mesmos territórios aparecem nos dois períodos. Não se mediu generalização para áreas novas, impacto social, causalidade ou incerteza fora dessa amostra. A coluna `confianca` contém a maior probabilidade estimada pelo modelo; ela não foi calibrada nem constitui garantia de acerto.

## Evidências, limites e plano de ação

Onze testes automatizados aprovados incluem contratos inválidos, origem, separação temporal, classes, reprodução, recarga do modelo, painel e API. A suíte usa arquivos temporários sintéticos; o gerador possui estado aleatório local e não altera o gerador global do processo. A CI executa geração, pipeline, testes, verificação de dependências, auditoria e CodeQL; a varredura de segredos foi incorporada ao fluxo de revisão. Resultados de CI devem ser conferidos na PR integrada, sem presumir execução a partir da configuração.

| Próximo passo acadêmico | Evidência necessária | Prazo do AVA | Situação |
|---|---|---|---|
| Confirmar modalidade, grupo e calendário | Registro da oferta e equipe | A confirmar no AVA | Pendente |
| Definir parceiro e pergunta | Levantamento consentido e critérios acordados | A confirmar | Pendente |
| Definir fonte real autorizada | Licença/consentimento, dicionário e contrato específico | A confirmar | Pendente |
| Adaptar análise e recorte de avaliação | Pipeline próprio e relatório com limites da fonte | A confirmar | Depende da fonte |
| Realizar devolutiva e validação | Registros reais, resultados e consentimentos | A confirmar | Pendente |
| Concluir relatório final e vídeo | Documentos e apresentação conforme AVA | A confirmar | Pendente |

O relatório parcial técnico está preenchido e o laboratório é executável. A entrega extensionista final permanece pendente das evidências acima. Nenhuma organização parceira, entrevista, autorização ou melhoria operacional foi inventada.

## Referências técnicas

- [pandas — leitura de CSV](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html): interface usada para carregar a tabela.
- [scikit-learn — RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html): parâmetros do classificador implementado.
- [scikit-learn — DummyClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html): estratégia de referência.
- [scikit-learn — métricas e avaliação](https://scikit-learn.org/stable/modules/model_evaluation.html): definição das métricas de classificação usadas.
