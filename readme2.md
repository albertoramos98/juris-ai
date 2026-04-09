🧠 Juris AI — Legal Ops & Automação Jurídica

Juris AI é uma plataforma de gestão jurídica inteligente focada em operações legais, controle de prazos, gestão de documentos e automação de comunicação com clientes, servindo como base sólida para futura integração com IA jurídica (RAG).

⚠️ Este projeto não é apenas um MVP visual.
Ele possui backend funcional, regras de negócio reais e arquitetura preparada para escala.

🚀 Visão Geral

O Juris AI resolve problemas comuns em escritórios jurídicos:

Falta de controle de prazos

Documentos espalhados (WhatsApp, e-mail, Drive)

Cobrança manual e repetitiva de clientes

Falta de histórico operacional

Pouca automação no dia a dia jurídico

Com o Juris AI, o escritório ganha:

📁 Organização de documentos por processo

⏰ Gestão de prazos críticos

📧 Cobrança automática de documentos

🔒 Controle de acesso por escritório

☁️ Integração nativa com Google Drive e Google Calendar

🏗️ Arquitetura do Projeto
Stack Principal

Backend

Python 3.14

FastAPI

SQLAlchemy

Alembic

APScheduler

Frontend

HTML + CSS (custom)

JavaScript (ES Modules)

Fetch API

Banco de Dados

SQLite (dev)

Estrutura preparada para PostgreSQL (prod)

Integrações

Google OAuth

Google Drive API

Google Calendar API

SMTP (Gmail)

🔐 Autenticação & Escritórios

Login com Google OAuth

Cada usuário pertence a um Office

Todas as operações são isoladas por escritório

Escritórios podem ser bloqueados administrativamente

Bloqueio reflete automaticamente no frontend

📂 Módulo de Processos
Criar e listar processos

Cada processo pertence a:

Cliente

Escritório

Possui prazos, documentos e automações próprias

Tela de Processos

Funciona como tela de detalhe:

Selecionar processo

Criar prazo

Subir documentos

Ativar cobrança automática

Visualizar status operacional

⏰ Módulo de Prazos
Funcionalidades

Criar prazo por processo

Definir responsável

Marcar como crítico

Concluir prazo

Sincronizar com Google Calendar

Regras importantes

Prazos críticos vencidos:

Apenas o owner do escritório pode concluir

Conclusão registra:

data

usuário responsável

📁 Módulo de Documentos (Google Drive)
Upload de documentos

Upload direto pelo sistema

Arquivos são enviados automaticamente para o Google Drive

Estrutura criada automaticamente:

Processo_{id}_{numero}
├── Inicial
├── Procuração
├── Contrato
├── Docs do Cliente
└── Outros

Registro no banco

Cada documento salva:

Processo

Categoria

Nome do arquivo

MIME type

Link de visualização no Drive

📧 Cobrança Automática de Documentos (Email Flow)
O que é?

Sistema de envio automático e recorrente de e-mails para cobrar documentos pendentes do cliente.

Funciona assim:

Usuário ativa cobrança em um processo

Sistema cria ou reativa um Email Flow

Scheduler roda em background

E-mails são enviados conforme intervalo configurado

Ao subir qualquer documento, o fluxo é automaticamente interrompido

Estados do Email Flow

ATIVO → enviando e-mails

PAUSADO → pausado manualmente

ENCERRADO → finalizado

STOPPED_AUTOMATIC → documento recebido

Esses estados são refletidos em tempo real no frontend.

Controles disponíveis no frontend

▶️ Ativar cobrança

⏸️ Pausar cobrança

⛔ Encerrar cobrança

🕒 Scheduler (Background Jobs)

Implementado com APScheduler

Executa verificação periódica de flows ativos

Respeita:

intervalo de dias

número máximo de tentativas

status do fluxo

Totalmente desacoplado do frontend

🔄 Regras de Negócio Importantes

Documento enviado → para cobrança automaticamente

Escritório bloqueado → nenhuma ação permitida

Processos isolados por escritório

Fluxos nunca “spammam” o cliente

🧠 Preparação para IA (RAG)

O projeto foi pensado desde o início para IA:

Já temos:

Documentos organizados

Prazos estruturados

Histórico operacional

Estados claros de processo

Próximo passo natural:

Tabela de eventos (process_events)

Indexação de documentos

RAG jurídico contextual

IA assistente do processo

▶️ Como rodar o projeto (dev)
# criar venv
python -m venv venv
source venv/bin/activate

# instalar dependências
pip install -r requirements.txt

# rodar migrations
alembic upgrade head

# iniciar backend
uvicorn app.main:app --reload


Frontend:

http://127.0.0.1:5500/frontend/


Backend:

http://127.0.0.1:8000

🧪 Observações de Desenvolvimento

SQLite usado apenas para desenvolvimento

APScheduler deve rodar após migrations

Em produção, usar:

PostgreSQL

Redis (opcional para jobs)

Worker dedicado para scheduler

📌 Status do Projeto

✔️ MVP funcional
✔️ Backend sólido
✔️ Automação real
✔️ Base pronta para IA

🚧 Próximo passo:

Audit trail de processos

Templates dinâmicos

RAG jurídico

✍️ Filosofia do Projeto

Automação não substitui o advogado.
Ela devolve tempo, foco e controle.