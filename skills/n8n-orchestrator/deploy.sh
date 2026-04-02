#!/bin/bash
# ============================================================
# Deploy Script - Orquestrador Multi-Agente N8N
# Aquinobrasil
# ============================================================
#
# Uso:
#   ./deploy.sh --n8n-url https://n8n.brnqn.cloud --api-key SUA_KEY
#
# Opcoes:
#   --n8n-url       URL do N8N (obrigatorio)
#   --api-key       API Key do N8N (obrigatorio)
#   --anthropic-key API Key da Anthropic (opcional, configura depois)
#   --gemini-key    API Key do Gemini (opcional, configura depois)
#   --activate      Ativa o workflow apos importar
#   --help          Mostra ajuda
# ============================================================

set -euo pipefail

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
N8N_URL=""
API_KEY=""
ANTHROPIC_KEY=""
GEMINI_KEY=""
ACTIVATE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_FILE="${SCRIPT_DIR}/workflow-orquestrador.json"

# ---- Parse args ----
while [[ $# -gt 0 ]]; do
  case $1 in
    --n8n-url)    N8N_URL="$2"; shift 2 ;;
    --api-key)    API_KEY="$2"; shift 2 ;;
    --anthropic-key) ANTHROPIC_KEY="$2"; shift 2 ;;
    --gemini-key) GEMINI_KEY="$2"; shift 2 ;;
    --activate)   ACTIVATE=true; shift ;;
    --help)
      head -20 "$0" | tail -15
      exit 0
      ;;
    *) echo -e "${RED}Argumento desconhecido: $1${NC}"; exit 1 ;;
  esac
done

# ---- Validacao ----
if [[ -z "$N8N_URL" ]]; then
  echo -e "${RED}Erro: --n8n-url e obrigatorio${NC}"
  echo "Uso: ./deploy.sh --n8n-url https://n8n.brnqn.cloud --api-key SUA_KEY"
  exit 1
fi

if [[ -z "$API_KEY" ]]; then
  echo -e "${RED}Erro: --api-key e obrigatorio${NC}"
  echo ""
  echo -e "${YELLOW}Para criar uma API Key no N8N:${NC}"
  echo "  1. Acesse ${N8N_URL}/settings/api"
  echo "  2. Clique em 'Create API Key'"
  echo "  3. Copie a chave gerada"
  echo ""
  exit 1
fi

# Remove trailing slash
N8N_URL="${N8N_URL%/}"

if [[ ! -f "$WORKFLOW_FILE" ]]; then
  echo -e "${RED}Erro: workflow JSON nao encontrado em ${WORKFLOW_FILE}${NC}"
  exit 1
fi

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Orquestrador Multi-Agente - Deploy N8N   ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ---- Step 1: Testar conexao ----
echo -e "${YELLOW}[1/5] Testando conexao com N8N...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-N8N-API-KEY: ${API_KEY}" \
  "${N8N_URL}/api/v1/workflows?limit=1" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  echo -e "${GREEN}  Conexao OK (HTTP ${HTTP_CODE})${NC}"
elif [[ "$HTTP_CODE" == "401" ]]; then
  echo -e "${RED}  Erro: API Key invalida (HTTP 401)${NC}"
  exit 1
elif [[ "$HTTP_CODE" == "000" ]]; then
  echo -e "${RED}  Erro: Nao foi possivel conectar em ${N8N_URL}${NC}"
  echo -e "${YELLOW}  Verifique se o N8N esta rodando e acessivel${NC}"
  exit 1
else
  echo -e "${YELLOW}  Aviso: HTTP ${HTTP_CODE} - tentando continuar...${NC}"
fi

# ---- Step 2: Preparar workflow JSON ----
echo -e "${YELLOW}[2/5] Preparando workflow...${NC}"

TEMP_FILE=$(mktemp)
cp "$WORKFLOW_FILE" "$TEMP_FILE"

# Substituir Gemini API Key se fornecida
if [[ -n "$GEMINI_KEY" ]]; then
  sed -i "s/SUBSTITUA_GEMINI_API_KEY/${GEMINI_KEY}/g" "$TEMP_FILE"
  echo -e "${GREEN}  Gemini API Key configurada${NC}"
else
  echo -e "${YELLOW}  Gemini API Key: nao fornecida (configure manualmente depois)${NC}"
fi

echo -e "${GREEN}  Workflow preparado${NC}"

# ---- Step 3: Importar workflow ----
echo -e "${YELLOW}[3/5] Importando workflow no N8N...${NC}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${N8N_URL}/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: ${API_KEY}" \
  -d @"$TEMP_FILE")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

rm -f "$TEMP_FILE"

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
  WORKFLOW_ID=$(echo "$BODY" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  if [[ -z "$WORKFLOW_ID" ]]; then
    # Tenta formato numerico
    WORKFLOW_ID=$(echo "$BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
  fi
  echo -e "${GREEN}  Workflow importado com sucesso! ID: ${WORKFLOW_ID}${NC}"
else
  echo -e "${RED}  Erro ao importar workflow (HTTP ${HTTP_CODE})${NC}"
  echo -e "${RED}  Resposta: ${BODY}${NC}"
  exit 1
fi

# ---- Step 4: Listar credenciais existentes ----
echo -e "${YELLOW}[4/5] Verificando credenciais...${NC}"

CREDS_RESPONSE=$(curl -s \
  -H "X-N8N-API-KEY: ${API_KEY}" \
  "${N8N_URL}/api/v1/credentials" 2>/dev/null || echo "{}")

echo ""
echo -e "${BLUE}  Credenciais necessarias:${NC}"
echo ""

# Check Anthropic
if echo "$CREDS_RESPONSE" | grep -qi "anthropic\|header.*auth"; then
  echo -e "  ${GREEN}[?] Anthropic API Key - pode ja existir (verifique no painel)${NC}"
else
  echo -e "  ${RED}[X] Anthropic API Key - CRIAR no N8N${NC}"
fi
echo -e "      Tipo: Header Auth"
echo -e "      Header Name: x-api-key"
echo -e "      Header Value: sua API key Anthropic"
echo -e "      Nome da credencial: 'Anthropic API Key'"
echo ""

# Check Telegram
if echo "$CREDS_RESPONSE" | grep -qi "telegram\|bot.*alertas"; then
  echo -e "  ${GREEN}[OK] Bot ALERTAS - parece existir${NC}"
else
  echo -e "  ${RED}[X] Bot ALERTAS (Telegram) - CRIAR no N8N${NC}"
fi
echo -e "      Tipo: Telegram API"
echo -e "      Token: token do seu bot ALERTAS"
echo ""

# Check Google Sheets
if echo "$CREDS_RESPONSE" | grep -qi "google.*sheet\|google.*oauth"; then
  echo -e "  ${GREEN}[OK] Google Sheets OAuth2 - parece existir${NC}"
else
  echo -e "  ${RED}[X] Google Sheets OAuth2 - CRIAR no N8N${NC}"
fi
echo -e "      Planilha: 'Orquestrador Log'"
echo -e "      Aba: 'Log_Orquestrador'"
echo -e "      Colunas: Timestamp, Demanda, Agente, Area, Energia, Resposta_Resumo, Status"
echo ""

# Gemini
if [[ -n "$GEMINI_KEY" ]]; then
  echo -e "  ${GREEN}[OK] Gemini API Key - configurada na URL${NC}"
else
  echo -e "  ${YELLOW}[!] Gemini API Key - substituir SUBSTITUA_GEMINI_API_KEY no node 'Agente Diretor Criativo'${NC}"
fi
echo ""

# ---- Step 5: Ativar workflow ----
if [[ "$ACTIVATE" == true && -n "$WORKFLOW_ID" ]]; then
  echo -e "${YELLOW}[5/5] Ativando workflow...${NC}"

  ACTIVATE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PATCH "${N8N_URL}/api/v1/workflows/${WORKFLOW_ID}" \
    -H "Content-Type: application/json" \
    -H "X-N8N-API-KEY: ${API_KEY}" \
    -d '{"active": true}')

  if [[ "$ACTIVATE_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}  Workflow ativado com sucesso!${NC}"
  else
    echo -e "${RED}  Erro ao ativar (HTTP ${ACTIVATE_RESPONSE})${NC}"
    echo -e "${YELLOW}  Ative manualmente no painel: ${N8N_URL}/workflow/${WORKFLOW_ID}${NC}"
  fi
else
  echo -e "${YELLOW}[5/5] Ativacao: pule ou use --activate${NC}"
  if [[ -n "$WORKFLOW_ID" ]]; then
    echo -e "  Para ativar manualmente: ${N8N_URL}/workflow/${WORKFLOW_ID}"
  fi
fi

# ---- Resumo ----
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  Deploy concluido!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "  Workflow ID: ${WORKFLOW_ID:-'N/A'}"
echo -e "  URL: ${N8N_URL}/workflow/${WORKFLOW_ID:-''}"
echo ""
echo -e "${YELLOW}  Proximos passos:${NC}"
echo -e "  1. Abra o workflow no editor: ${N8N_URL}/workflow/${WORKFLOW_ID:-''}"
echo -e "  2. Configure as credenciais nos nodes (veja lista acima)"
echo -e "  3. Crie a planilha 'Orquestrador Log' no Google Sheets"
echo -e "  4. Ative o workflow"
echo -e "  5. Teste mandando mensagem no Telegram:"
echo -e "     'qual a margem ideal pra Coral Rende Muito 18L?'"
echo ""
