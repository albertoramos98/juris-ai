# Arquitetura de Inteligência Juris AI ⚖️🧠

Este documento descreve o funcionamento técnico da camada de inteligência do sistema **Juris AI**, detalhando como os dados são processados, armazenados e transformados em peças jurídicas de alta complexidade.

---

## 1. A Tecnologia RAG (Retrieval-Augmented Generation)
Diferente de IAs genéricas (como o ChatGPT padrão), o Juris AI utiliza a arquitetura **RAG**. Isso garante que a IA não "invente" (alucine) fatos, pois ela é obrigada a consultar documentos reais antes de responder.

## 2. A Estrutura de Dois Bancos de Dados

O sistema opera com uma separação clara entre **Fatos** e **Direito**:

### A. Memória de Fatos (Contexto do Processo)
*   **Fonte:** Petições iniciais, documentos do cliente, atas de audiência e transcrições de reuniões.
*   **Funcionamento:** Cada processo possui seu próprio "silo" de dados. Quando um documento é indexado, ele é fragmentado e vetorizado especificamente para aquele ID de processo.
*   **Objetivo:** Garantir que a IA saiba exatamente quem são as partes, quais são os pedidos e quais provas existem no caso atual.

### B. Memória de Direito (Biblioteca Jurídica Global)
*   **Fonte:** Leis, Súmulas, Jurisprudência e Doutrina cadastrada pelo escritório.
*   **Funcionamento:** É uma base de conhecimento compartilhada por todo o escritório.
*   **Objetivo:** Fornecer a fundamentação jurídica necessária para qualquer peça, independentemente do cliente.

---

## 3. O Ciclo de Vida do Dado (Workflow)

### Passo 1: Indexação Vetorial (Embedding)
Ao clicar em "Indexar para IA", o sistema utiliza o modelo `text-embedding-3-small` da OpenAI para transformar textos em **vetores numéricos**. Esses vetores representam o *significado semântico* das palavras.
> *Exemplo: A IA entende que "término do contrato" e "rescisão contratual" possuem vetores próximos, mesmo sendo palavras diferentes.*

### Passo 2: Busca Semântica
Quando uma petição é solicitada, o sistema realiza uma busca em tempo real nos dois bancos:
1.  Recupera os trechos mais relevantes dos **Fatos** do processo.
2.  Recupera as **Leis e Teses** mais adequadas na Biblioteca Global.

### Passo 3: Síntese e Redação (GPT-4o)
O motor de redação utiliza o modelo **GPT-4o (Enterprise Level)**. Enviamos para ele um "Prompt de Contexto" que contém:
*   Os fatos reais recuperados.
*   A fundamentação jurídica encontrada.
*   O guia de estilo e cabeçalho do seu escritório.

O resultado é uma peça jurídica personalizada, fundamentada e pronta para o protocolo.

---

## 4. Segurança e Integridade
*   **Silo de Dados:** Um escritório nunca acessa os dados de outro.
*   **Priorização de Fatos:** O sistema possui algoritmos de "boost" que garantem que os nomes e CPFs dos documentos reais do processo sempre substituam qualquer texto de exemplo ou template.
*   **Processamento em Lote:** Suporte para processos de alta complexidade com milhares de páginas de documentos.

---
**Juris AI** - *Inteligência Artificial aplicada ao Direito de Alta Performance.*
