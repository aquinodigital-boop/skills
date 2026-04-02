---
name: n8n-orchestrator
description: "Deploy e gerenciamento do Orquestrador Multi-Agente no N8N. TRIGGER quando: usuario pede para importar workflow N8N, configurar orquestrador, deploy de agentes no N8N, ou gerenciar o workflow multi-agente da Aquinobrasil."
---

# Orquestrador Multi-Agente N8N - Aquinobrasil

Skill para implantar e gerenciar o workflow do Orquestrador Multi-Agente no N8N self-hosted.

## Arquitetura do Workflow

```
Telegram Trigger
    |
Classificador (Claude API)
    |
Parse Classificacao (Code)
    |
Router Categorias (Switch)
    |--- PRECIFICACAO ---> Agente Precificacao (Claude)
    |--- SEO ------------> Agente SEO (Claude)
    |--- CONTEUDO -------> Agente Diretor Criativo (Gemini)
    |--- PLANEJAMENTO ---> Agente Planejamento (Claude)
    |--- OPERACIONAL ----> Agente Operacional (Claude)
    |--- OUTRO (fallback)-> Agente Central (Claude)
    |
Formatar Resposta (Code)
    |
    |--- Responder Telegram
    |--- Log Google Sheets
```

## Deploy Rapido

### Pre-requisitos

1. N8N self-hosted rodando (ex: https://n8n.brnqn.cloud)
2. API Key do N8N (Settings > API > Create API Key)
3. API Key da Anthropic (Claude)
4. API Key do Gemini (opcional, para agente de conteudo)
5. Bot Telegram configurado
6. Google Sheets OAuth2 configurado

### Comando de Deploy

```bash
# Deploy basico (importa o workflow)
./deploy.sh --n8n-url https://n8n.brnqn.cloud --api-key SUA_N8N_API_KEY

# Deploy completo (com chaves e ativacao)
./deploy.sh \
  --n8n-url https://n8n.brnqn.cloud \
  --api-key SUA_N8N_API_KEY \
  --gemini-key SUA_GEMINI_KEY \
  --activate
```

### Configuracao Manual de Credenciais

Apos importar, configure no editor do N8N:

#### 1. Anthropic API Key (Header Auth)

- Tipo: Header Auth
- Nome: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: sua chave API da Anthropic
- Usado nos nodes: Classificador, Precificacao, SEO, Planejamento, Operacional, Central

#### 2. Gemini API Key

- Edite o node "Agente Diretor Criativo"
- Substitua `SUBSTITUA_GEMINI_API_KEY` na URL pela sua chave

#### 3. Telegram Bot

- Tipo: Telegram API
- Nome: `Bot ALERTAS`
- Token: token do seu bot do BotFather

#### 4. Google Sheets OAuth2

- Tipo: Google Sheets OAuth2
- Crie planilha "Orquestrador Log" com aba "Log_Orquestrador"
- Colunas: Timestamp, Demanda, Agente, Area, Energia, Resposta_Resumo, Status

## Categorias de Classificacao

| Categoria     | Agente              | Motor  | Exemplos                                    |
|---------------|---------------------|--------|---------------------------------------------|
| PRECIFICACAO  | Agente Precificacao | Claude | margem, markup, preco, custo                |
| SEO           | Agente SEO          | Claude | palavras-chave, ranking, Google             |
| CONTEUDO      | Diretor Criativo    | Gemini | post, legenda, carrossel, reels             |
| PLANEJAMENTO  | Agente Planejamento | Claude | estrategia, roadmap, cronograma, meta       |
| OPERACIONAL   | Agente Operacional  | Claude | processo, automacao, sistema, ferramenta    |
| OUTRO         | Agente Central      | Claude | qualquer demanda nao classificada           |

## Teste

Mande no Telegram pro bot ALERTAS:

```
qual a margem ideal pra Coral Rende Muito 18L?
```

Resultado esperado: classificacao PRECIFICACAO, resposta com analise de margem e markup.

## Troubleshooting

### Workflow nao responde no Telegram
- Verifique se o workflow esta ativo (toggle verde no N8N)
- Confirme que o webhook do Telegram esta registrado (teste com /start no bot)
- Verifique credencial "Bot ALERTAS"

### Erro 401 na Anthropic
- Verifique a credencial "Anthropic API Key" no N8N
- Header Name deve ser exatamente `x-api-key`
- Confirme que a key tem saldo/creditos

### Erro no Gemini
- Verifique se `SUBSTITUA_GEMINI_API_KEY` foi substituida na URL
- Teste a key direto: `curl "https://generativelanguage.googleapis.com/v1beta/models?key=SUA_KEY"`

### Google Sheets nao loga
- Verifique se a planilha "Orquestrador Log" existe
- Confirme que a aba se chama exatamente "Log_Orquestrador"
- Verifique permissoes do OAuth2

### DNS/SSL issues com N8N
- O subdominio n8n deve estar em "DNS Only" no Cloudflare (nao Proxied)
- Caddy deve estar gerenciando o SSL
- Verifique: `curl -I https://n8n.brnqn.cloud`

## Arquivos

- `workflow-orquestrador.json` - Workflow completo do N8N
- `deploy.sh` - Script de deploy automatizado
- `SKILL.md` - Esta documentacao
