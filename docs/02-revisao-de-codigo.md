# Revisão de código

Revisão realizada sobre a fundação técnica do Atlas antes da publicação.

## Escopo verificado

- geração e proveniência dos dados;
- regras de qualidade;
- separação de treino e teste;
- comparação com linha de base;
- serialização de artefatos;
- rotas, cabeçalhos e renderização do painel;
- acessibilidade e comportamento responsivo;
- testes e workflow de integração contínua.

## Achados corrigidos

### R1 — conjunto com uma única classe

**Severidade:** alta.

Os limiares iniciais classificavam todas as 288 linhas como `Alto`. Modelo e baseline atingiam 100%, tornando a avaliação inválida. Os limiares foram recalibrados para faixas fixas e o teste passou a exigir que os dois períodos contenham as três classes e que o modelo supere a referência.

### R2 — vazamento temporal na avaliação

**Severidade:** alta.

A divisão aleatória misturava meses de 2024 e 2025. Ela foi substituída por treino integral em 2024 e teste integral em 2025. As quantidades de cada período são verificadas automaticamente.

### R3 — estilo embutido incompatível com a CSP

**Severidade:** média.

As barras usavam atributo `style`, mas a política de segurança permite estilos apenas do próprio domínio. O gráfico passou a usar o elemento semântico `progress`, estilizado no CSS externo. Um teste impede a reintrodução de `style=` na página.

### R4 — dependência direta implícita

**Severidade:** baixa.

O pipeline importa `joblib`, inicialmente disponível apenas como dependência transitiva do scikit-learn. A biblioteca foi declarada explicitamente e fixada no arquivo de requisitos.

## Riscos aceitos e declarados

- o alvo é sintético e derivado das entradas; as métricas não representam desempenho real;
- os mesmos territórios aparecem em treino e teste, embora em períodos diferentes;
- o servidor de desenvolvimento Flask é apenas local; uma implantação futura requer servidor WSGI e configuração operacional;
- os artefatos JSON são lidos do disco a cada requisição, escolha simples e suficiente para 12 territórios;
- não existe evidência de parceiro ou impacto extensionista nesta fase técnica.

## Evidências

- 3 testes automatizados aprovados;
- `pip check` sem dependências quebradas;
- pipeline reproduzível com 288 registros;
- acurácia 0,7639 contra baseline 0,5000;
- cabeçalhos CSP, `nosniff`, negação de frames e política de referência;
- dados e avisos metodológicos visíveis no painel e na API.
- inspeção visual em 1280 px e 390 px, com 12 indicadores renderizados e sem rolagem horizontal.

## Parecer

A fundação está adequada para publicação como protótipo acadêmico e demonstração técnica. Ela ainda não constitui a entrega extensionista final: parceiro, dados autorizados, validação com usuários e documentos exigidos pelo AVA deverão ser acrescentados no semestre correspondente.
