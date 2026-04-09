# 📑 Documentação Técnica: Sistema Juris IA

Este documento detalha o funcionamento, a arquitetura e as funcionalidades do sistema **Juris IA**, uma plataforma de gestão jurídica e automação baseada em Inteligência Artificial.

---

## 1. Visão Geral do Sistema
O **Juris IA** é um ecossistema projetado para automatizar o fluxo de trabalho jurídico. Ele combina a gestão tradicional de processos e clientes com capacidades avançadas de IA, especificamente o **RAG (Retrieval-Augmented Generation)**. O sistema permite que advogados realizem buscas semânticas em documentos de processos, recebam respostas fundamentadas e gerem rascunhos de peças processuais exaustivas.

---

## 2. Estrutura do Projeto
A organização do código segue o padrão de separação entre lógica de negócio (backend) e interface (frontend):

### 2.1. Backend (`/app`)
*   **`api/`**: Contém os roteadores FastAPI. Cada arquivo representa um módulo funcional (ex: `processes.py`, `rag.py`, `google_drive.py`).
*   **`core/`**: Configurações centrais, segurança (JWT), definições do banco de dados e variáveis de ambiente (`settings.py`).
*   **`models/`**: Definição das tabelas SQL via SQLAlchemy (Usuários, Clientes, Processos, Documentos, Chunks de IA, etc).
*   **`services/`**: Camada de lógica pesada e integrações externas (OpenAI, Google Drive, Extrator de Texto).
*   **`auth/`**: Gerenciamento de autenticação local e Google OAuth.
*   **`jobs/`**: Tarefas agendadas, como o `email_scheduler.py` para envios automáticos.

### 2.2. Frontend (`/frontend`)
*   **Arquitetura**: Aplicação baseada em JavaScript Vanilla (ES6), HTML5 e CSS3.
*   **`app.js`**: Lógica principal da Dashboard e controle de acesso.
*   **`process_ai.js`**: Interface interativa de chat e geração de petições via RAG.
*   **`config.js`**: Centraliza a URL base da API para facilitar o deploy.

---

## 3. Funcionalidades Detalhadas

### 3.1. Gestão de Documentos e Integração Google Drive
*   **Localização**: `app/api/documents.py` e `app/services/google_drive_service.py`.
*   **Funcionamento**: Ao fazer o upload de um arquivo, o sistema garante a criação de uma estrutura de pastas no Google Drive do escritório (`Processo_ID_Numero`).
*   **Categorização**: O usuário classifica o documento (ex: Provas, Petições). O sistema move o arquivo para a subpasta correspondente no Drive.
*   **Extração de Texto**: O arquivo é processado pelo `document_extractor.py`, que extrai o conteúdo textual e o salva no banco de dados local para processamento imediato pela IA.

### 3.2. RAG (Busca e Redação com IA)
*   **Localização**: `app/services/rag_service.py` e `app/api/rag.py`.
*   **Indexação**: O texto de um processo é quebrado em "Chunks" (blocos de 1200 caracteres). Cada bloco é transformado em um vetor numérico (Embedding) via modelo `text-embedding-3-small` da OpenAI.
*   **Chat Jurídico**: O usuário faz perguntas sobre o caso. O sistema busca os chunks mais similares (similaridade de cosseno) e envia ao GPT-4o para gerar uma resposta baseada apenas nos fatos do processo.
*   **Geração de Peças**:
    *   **Modo Ataque**: Foca em Petição Inicial, buscando fatos e pedidos.
    *   **Modo Defesa**: Foca em Contestação, buscando teses defensivas e contradições.
    *   **Personalização**: Utiliza o `office_style_guide.json` para aplicar a identidade visual do escritório (cabeçalhos/rodapés).

### 3.3. Automação de E-mail (Flows)
*   **Localização**: `app/api/email_flows.py` e `app/jobs/email_scheduler.py`.
*   **Funcionamento**: Permite criar sequências de e-mails para cobrança de documentos ou atualização de clientes.
*   **Inteligência de Fluxo**: O sistema monitora uploads. Se um documento solicitado é enviado, o fluxo de e-mail associado é interrompido automaticamente para evitar cobranças indevidas.

---

## 4. Funcionamento Interno e Fluxo de Dados

1.  **Entrada de Dados**: O usuário cadastra um cliente e um processo.
2.  **Upload e Texto**: Um PDF é enviado. O sistema extrai o texto, salva no banco e o arquivo original vai para o Google Drive.
3.  **Vetorização**: O usuário clica em "Indexar". O `rag_service` percorre todos os documentos do processo, gera embeddings e salva na tabela `ChunkEmbedding`.
4.  **Consulta**: O usuário envia uma dúvida. A API converte a dúvida em vetor, compara com os embeddings do banco e recupera os 6-10 trechos mais relevantes.
5.  **Inferência**: O GPT-4o recebe a pergunta + trechos recuperados e gera a resposta técnica final.

---

## 5. Uso da IA e Prompts

O sistema utiliza a OpenAI com configurações específicas:
*   **Modelo de Chat**: `gpt-4o` (configurável via `OPENAI_CHAT_MODEL`).
*   **Modelo de Embedding**: `text-embedding-3-small`.
*   **Prompt de Redação**: Localizado em `app/services/openai_service.py`, o prompt instrui a IA a ser "Erudita, formal, persuasiva e prolixa", simulando um Advogado Sênior. Ele exige a substituição de placeholders (como nomes fictícios de templates) pelos dados reais extraídos do contexto RAG.

---

## 6. Fluxo do Usuário (User Experience)

1.  **Login**: Autenticação segura via JWT ou Google.
2.  **Dashboard**: Visão geral de prazos, clientes e processos recentes.
3.  **Processo AI**: 
    *   O usuário seleciona um processo.
    *   Realiza a indexação dos documentos carregados.
    *   Usa o chat para tirar dúvidas rápidas sobre o caso.
    *   Usa o gerador de petições para criar o rascunho de uma Inicial ou Contestação.
4.  **Exportação**: O rascunho gerado é convertido para `.docx` pelo `document_generator_service.py` e baixado pelo usuário.

---

## 7. Estruturas de Dados (Modelos SQL)

*   **`User`**: Dados de acesso e vinculação ao escritório (`office_id`).
*   **`Office`**: Configurações do escritório, incluindo tokens do Google e chaves de IA.
*   **`Process`**: Número do processo, tribunal, tipo de ação e link para pasta do Drive.
*   **`Document`**: Metadados do arquivo e o texto bruto (`content_text`).
*   **`DocumentChunk`**: Segmentos de texto associados a um documento.
*   **`ChunkEmbedding`**: Representação vetorial do chunk (formato JSON/Blob).
*   **`GlobalKnowledge`**: Base de conhecimento compartilhada (doutrinas, modelos de petições) para apoio à IA.

---

## 8. Integrações e Tecnologias

*   **FastAPI**: Engine de alta performance para a API.
*   **SQLAlchemy / Alembic**: Gestão e evolução do banco de dados.
*   **OpenAI API**: Processamento de linguagem natural e busca vetorial.
*   **Google Drive API**: Armazenamento e organização de arquivos.
*   **Google Calendar API**: Sincronização de prazos e reuniões.
*   **Python-Docx**: Geração dinâmica de arquivos Word.
*   **Pydantic Settings**: Gestão segura de variáveis de ambiente.

---
*Documento gerado para análise técnica do sistema Juris IA. Proibida a modificação sem autorização dos desenvolvedores.*
