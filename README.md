
# CASE - Support e Analytics: Pipeline de Dados e Dashboard

**Autor:** Matheus Rodrigues Silva Maia

**LinkedIn:** https://www.linkedin.com/in/matheusrodriguestech/

## 1. Objetivo do Projeto

Este projeto foi desenvolvido para resolver um desafio técnico de engenharia e análise de dados focado no fluxo de processamento de notas fiscais. O cliente final solicitou uma melhoria específica descrita como:

> "Gostaria que criassem um relatório que exibisse as notas fiscais de material que passaram na tarefa de escrituração com status de sucesso no último mês".
> 
> 

O objetivo não foi apenas escrever a consulta SQL solicitada, mas construir uma **solução analítica ponta a ponta**. Para isso, foi provisionado um ambiente de banco de dados do zero, criado um pipeline de extração automatizado em Python e desenvolvido um Dashboard interativo para exploração de dados (Data Discovery) muito além do escopo inicial.

---

## 2. Arquitetura e Decisões Técnicas

Como o desafio forneceu apenas o diagrama de classes e a modelagem teórica, o primeiro passo foi criar o ambiente de dados para validar a lógica de negócios e as consultas.

### 2.1. Escolha da Infraestrutura (Docker vs. Cloud)

Inicialmente, avaliou-se a possibilidade de provisionar um banco de dados relacional na AWS (como o RDS) utilizando *Terraform* para demonstrar conhecimentos avançados de *Infrastructure as Code* (IaC). No entanto, para o escopo deste desafio, o uso de infraestrutura em nuvem caracterizaria *over-engineering* (complexidade desnecessária e custos não justificados).

Optou-se por utilizar o **Docker (Docker Compose)**. O Docker entrega um ambiente local robusto, 100% reprodutível em qualquer máquina e perfeitamente adequado para simular um servidor PostgreSQL profissional em segundos, mantendo as melhores práticas de mercado.

### 2.2. Correção de Inconsistências na Modelagem

Durante a tradução do diagrama para o script de criação de tabelas (DDL), foi identificada e corrigida uma inconsistência na documentação original do *case*:

* Na tabela `tasks`, a chave estrangeira `task_definition_id` foi documentada com o tipo de dado `character varying`.


* Contudo, na tabela de origem `task_definitions`, a chave primária `id` é do tipo numérico `bigint`.


* **Ação:** O tipo de dado na tabela `tasks` foi corrigido para `BIGINT` no script de inicialização para garantir a integridade referencial (*Foreign Key Constraint*) no banco de dados.

### 2.3. Estrutura do Projeto (Árvore de Arquivos)

Abaixo está a organização dos artefatos construídos:

```text
CASE_SQL_CHALLENGE/
├── docker-compose.yml          # Orquestração do container PostgreSQL
├── init_scripts/               # Scripts executados automaticamente pelo Docker
│   ├── 01_schema.sql           # Criação da estrutura de tabelas e relacionamentos (DDL)
│   └── 02_seed.sql             # Inserção de dados estáticos e edge cases para testes (DML)
└── app/
    ├── .env                    # Variáveis de ambiente (credenciais de banco)
    ├── requirements.txt        # Dependências do Python (Pandas, Streamlit, etc.)
    ├── main.py                 # Pipeline de extração e automação de planilhas Excel
    ├── data_generator_chaos.py # Script gerador de dados sintéticos para simular volume real
    └── dashboard.py            # Aplicação Streamlit com o Dashboard

```

---

## 3. Consulta SQL Principal

O coração do desafio consistia em traduzir regras de negócio para a linguagem relacional. O maior obstáculo técnico foi resolver a cardinalidade de "1 para Muitos" (1:N) entre a Nota Fiscal e seus Itens (Pedidos de Compra), sem violar a regra de unicidade de ID por linha.

![Print do código SQL](/assets/01.png)

**Análise Detalhada da Query:**

* **Agrupmaneto de Itens e a Função `STRING_AGG`:** Se uma nota possui três produtos (itens) com pedidos de compra diferentes, um `JOIN` simples criaria três linhas para a mesma nota fiscal no relatório. Para evitar essa geração de linhas, a query utiliza a cláusula `GROUP BY` no ID da Nota e aplica a função avançada de agregação `STRING_AGG(DISTINCT i.purchase_order, ', ')`. Isso consolida múltiplos pedidos em uma única célula separada por vírgula, mantendo o ID da nota único no relatório.
* **Múltiplos `JOINs`:** Utilizou-se `INNER JOIN` para conectar a tabela fato (`tax_documents`) com as tabelas dimensionais vitais (`tasks`, `cities`), garantindo a rastreabilidade do processo de escrituração e os dados geográficos de fornecedor e tomador. Usou-se `LEFT JOIN` na tabela `items` por precaução defensiva, para que a nota não desaparecesse caso o cadastro de itens estivesse ausente.
* **Filtros Rigorosos (`WHERE`):** A filtragem garante estritamente os requisitos:
* Apenas notas de material (`type = 'MaterialInvoice'`).
* Apenas tarefas da etapa de escrituração (`task_definition_id = 12`).
* Apenas processamentos de sucesso (`status_id = 120`).


* **Filtro Temporal Dinâmico:** Em vez de usar datas *hardcoded*, a query utiliza `DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')`, assegurando que o script seja executado automaticamente em qualquer dia e sempre puxe perfeitamente os limites do mês calendário anterior.

---

## 4. Automação de Relatórios em Python (`main.py`)

Em um cenário corporativo real, gestores não executam consultas SQL diretamente no banco. Pensando nisso, foi desenvolvido o script `main.py`.

O objetivo deste arquivo é demonstrar a capacidade de construir um pipeline básico. Ele se conecta ao banco de dados via SQLAlchemy, executa a query consolidada usando a biblioteca *Pandas* e exporta automaticamente o resultado para uma planilha formatada `.xlsx`, pronta para envio por e-mail ou integração.

---

## 5. Dashboard e Analytics (Streamlit)

Para entregar um valor superior e focado em soluções para a área de negócios, a entrega final evoluiu para uma aplicação web utilizando a biblioteca **Streamlit**. O objetivo foi abandonar o formato estático e entregar uma ferramenta dinâmica para auditoria fiscal e exploração de *insights*.

![Print do Dashboard](/assets/02.png)

### 5.1. Análises Implementadas e Geração de Valor

* **A. Análise de Spend por Fornecedores (Top 10)**
* **Pergunta a ser respondida:** Quem são os fornecedores que concentram a maior parte do nosso volume financeiro aprovado?
* **Insight Gerado:** Identifica a aderência à Lei de Pareto (80/20). Demonstra visualmente a dependência da operação em um grupo seleto de fornecedores, norteando a equipe de compras para focar esforços de negociação e gestão de riscos em parceiros estratégicos essenciais.


* **B. Distribuição Geográfica (Risco Fiscal)**
* **Pergunta a ser respondida:** Qual é a origem predominante (Estado e Cidade) das notas fiscais que estamos processando?
* **Insight Gerado:** Crucial para o planejamento tributário. Monitorar se há alta concentração de operações interestaduais ajuda a prever a complexidade do recolhimento de impostos, como o Diferencial de Alíquota de ICMS, além de otimizar a logística de suprimentos.


* **C. Lead Time (Eficiência Operacional)**
* **Pergunta a ser respondida:** Qual é a velocidade de processamento do time, desde a chegada da tarefa até o seu sucesso?
* **Insight Gerado:** Através do cálculo matemático de diferença entre a data de criação e a de finalização, o histograma revela a constância operacional. Uma cauda longa neste gráfico indica gargalos em processos específicos, demandando atenção da coordenação da equipe.


* **D. Evolução Diária (Volume de Notas por Dia)**
* **Pergunta a ser respondida:** Existe um padrão de sazonalidade ou picos de sobrecarga na escrituração ao longo do mês?
* **Insight Gerado:** Facilita a gestão de pessoas. Se os picos de notas processadas ocorrem em dias específicos (como no fechamento contábil mensal), o gestor pode bloquear folgas da equipe nestas datas críticas, evitando gargalos de aprovação.



### 5.2. Funcionalidades de Interface

O Menu Lateral da aplicação atua como um verdadeiro painel de controle interativo:

* **Filtros Dinâmicos Multi-seleção:** Permite navegar por todo o banco, alterando dinamicamente o Período, o Tipo de Nota, o Tipo de Tarefa (Escrituração, Pagamento, etc) e o Status do Processo (Sucesso, Falha, Duplicada).
* **Exportação "On-the-Fly":** Contém um botão integrado de download que lê instantaneamente o DataFrame filtrado na tela e o disponibiliza para o usuário baixar em formato Excel com um único clique, unindo visualização e extração em um só lugar.

---

## 6. Guia de Execução (Passo a Passo)

Para reproduzir este ecossistema em seu computador, certifique-se de ter o Docker e o Python 3 instalados.

**Passo 1: Subir a Infraestrutura**
No terminal, dentro da pasta raiz do projeto, execute o comando abaixo. O Docker irá baixar o PostgreSQL, inicializar o banco de dados `case_analytics` e executar a criação das tabelas automaticamente através do volume mapeado.

```bash
docker-compose up -d

```

**Passo 2: Instalar Dependências**
Navegue até a pasta da aplicação e instale as bibliotecas Python necessárias.

```bash
cd app
pip install -r requirements.txt

```

**Passo 3: Popular o Banco de Dados com Cenários Complexos**
Para que o Dashboard tenha dados ricos o suficiente para evidenciar os gráficos, rode o gerador de dados sintéticos. Este script suja o banco com notas de sucesso, falhas, serviços e notas com tempo de processamento variado.

```bash
python data_generator_chaos.py

```

**Passo 4: Gerar a Planilha Simples da Requisição Principal**
Se o foco for apenas verificar a funcionalidade solicitada inicialmente no *case* técnico, execute o script base para gerar o Excel na pasta atual.

```bash
python main.py

```

**Passo 5: Iniciar o Dashboard de Analytics**
Por fim, inicie o servidor web local do Streamlit. O seu navegador padrão abrirá automaticamente a interface executiva, permitindo o uso completo dos filtros e a exploração visual.

```bash
python -m streamlit run dashboard.py

```

---