# 📄 Documentação Técnica e Guia de Operação - Juris AI v1.0

Este documento fornece uma visão exaustiva da arquitetura, funcionamento e diretrizes operacionais do **Juris AI**, um ecossistema de inteligência jurídica projetado para alta performance e escalabilidade.

---

## 1. Visão Geral e Stack Tecnológica

O Juris AI foi construído sob o paradigma de **IA Generativa com RAG** (*Retrieval-Augmented Generation*), garantindo que as respostas da inteligência artificial não sejam baseadas apenas em conhecimento genérico, mas no acervo documental específico do escritório e do processo.

### 🛠 Core Tecnológico
- **Backend:** Python 3.11+ com **FastAPI** (Assíncrono, alta performance).
- **Banco de Dados:** SQLAlchemy com suporte a **SQLite** (local) e **PostgreSQL/pgvector** (produção).
- **Processamento de Linguagem:** OpenAI API (Modelos `gpt-4o` para raciocínio e `text-embedding-3-small` para vetores).
- **Transcrição:** OpenAI Whisper (Processamento de áudio em alta fidelidade).
- **Integrações:** Google Drive API (Armazenamento), Google Calendar API (Agendamento), SMTP (Comunicação).
- **Frontend:** Vanilla JavaScript (ES6+), HTML5 e CSS3 moderno (Arquitetura orientada a componentes puros).

---

## 2. Configuração do Sistema (.env)

O arquivo `.env` é o coração da segurança. Abaixo, o detalhamento de cada variável:

| Variável | Descrição |
| :--- | :--- |
| `DATABASE_URL` | String de conexão. Use `sqlite:///./dev.db` local ou `postgresql://...` para nuvem. |
| `SECRET_KEY` | Chave mestra para criptografia de tokens JWT. |
| `OPENAI_API_KEY` | Sua chave da OpenAI. Fundamental para o RAG e Redação. |
| `SMTP_...` | Conjunto de chaves para o envio de e-mails automáticos (Gmail recomendado). |
| `GOOGLE_CLIENT_ID` | Obtido no Google Cloud Console para integração com Drive e Agenda. |

---

## 3. Arquitetura de Inteligência (RAG)

### 3.1 Extração e Limpeza
O sistema utiliza um motor híbrido de extração:
- **Nativo:** `pypdf` e `python-docx` para uploads diretos.
- **Nuvem:** Integração com Google Drive para converter arquivos legados `.doc` e Google Docs em texto puro de forma automática.
- **Filtro de Ruído:** O extrator ignora binários (imagens/áudios) para evitar que "lixo" contamine os embeddings.

### 3.2 Processamento Vetorial
> **⚠️ OBSERVAÇÃO CRÍTICA:** O treinamento da IA (Indexação) exige que o processo possua ao menos um documento com texto extraível (PDF ou Word). Se o processo estiver vazio, a IA não terá "matéria-prima" para gerar petições ou responder consultas.

Quando você clica em **"Indexar para IA"**:
1. O texto é dividido em blocos de 1200 caracteres (Chunks).
2. Cada bloco possui um "overlap" de 150 caracteres para garantir que o contexto entre parágrafos não seja perdido.
3. Os blocos são enviados para a OpenAI para gerar **vetores numéricos (embeddings)**.
4. Esses vetores são salvos no banco de dados, permitindo buscas semânticas (por significado, não apenas palavras-chave).

---

## 4. Manual de Operação da Plataforma

### 4.1 Gestão de Processos
- **Criação:** Sempre informe o número do processo corretamente. O sistema impedirá duplicidade dentro do mesmo escritório.
- **Timeline:** Cada ação importante (criação de prazo, envio de e-mail, upload de documento) gera um evento automático na timeline, auditando o histórico do caso.

### 4.2 O Cérebro (Chat RAG)
- **Como usar:** No chat do processo, faça perguntas específicas sobre os fatos ("O que a testemunha X disse sobre o acidente?").
- **Fontes:** O sistema retornará a resposta e listará os documentos utilizados, permitindo a conferência imediata.

### 4.3 Ataque & Defesa (Redação de Alta Extensão)
Esta é a funcionalidade mais poderosa do sistema.
- **Calibragem:** Diferente de IAs genéricas, o Juris AI instrui o modelo a ser **prolixo e técnico**.
- **Peças Gigantes:** O sistema busca até 30 fragmentos de contexto simultaneamente para redigir petições que podem ultrapassar 3.000 palavras.
- **Word (.docx):** Sempre gere o rascunho e utilize o botão de exportação. O documento baixado já vem formatado com alinhamento justificado e fontes padrão (Arial 12).

### 4.4 Automação de E-mails (Fluxo de Cobrança)
- **Ativação:** Utilize para cobrar documentos pendentes do cliente.
- **Lógica de Parada:** O sistema é "educado". Se o agendador detectar que o cliente subiu um novo documento no processo, ele pausa o fluxo de cobrança automaticamente.

### 4.5 Reuniões
- **Gravação:** Suporta reuniões longas. O áudio é capturado em pequenos fragmentos para não travar o navegador do advogado.
- **Transcrição:** A transcrição é convertida em documento de texto e indexada no RAG, permitindo perguntar à IA o que foi decidido na reunião meses depois.

---

## 5. Diretrizes de Segurança e Multi-tenancy

O Juris AI foi desenhado para ser **Multi-tenant**:
- **Isolamento:** Cada escritório (*Office*) possui um ID único. Um usuário do Escritório A jamais verá processos ou documentos do Escritório B.
- **Bloqueio de Inadimplência:** O sistema possui um mecanismo de bloqueio automático. Se um escritório for bloqueado (manualmente ou por atraso), todas as funcionalidades custosas (IA, Google Drive, Envio de E-mail) são desativadas instantaneamente.
- **Hierarquia:** 
    - **Owner:** Gestão total, pode criar/remover membros e concluir prazos críticos vencidos.
    - **Membro:** Operação do dia a dia, consulta e redação.

---

## 6. Guia de Manutenção e Troubleshooting

- **Erro `invalid_grant` (Google):** Ocorre quando o token do Google expira. Peça ao administrador para deslogar e logar novamente via Google.
- **Indexação Retornando 0 Chunks:** Verifique se os documentos subidos são PDF/Word com texto selecionável. Imagens puras (fotos) sem OCR não geram texto.
- **E-mails não enviados:** Verifique se o "Senha de App" do Gmail está ativo e se o SMTP_PORT está correto (geralmente 587).

---
*Manual desenvolvido como parte da entrega técnica final do Juris AI - Março de 2026.*
