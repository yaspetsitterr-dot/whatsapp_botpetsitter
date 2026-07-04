# Bot WhatsApp + Gemini

Bot inteligente para WhatsApp Business usando a API oficial da Meta (Cloud API) e o Gemini como cérebro de IA.

## 1. Pegue sua chave do Gemini

1. Acesse https://aistudio.google.com/app/apikey
2. Clique em "Create API Key"
3. Copie a chave gerada

## 2. Rodar localmente (opcional, para testar)

```bash
pip install -r requirements.txt
cp .env.example .env
# edite o .env com seus valores reais
python app.py
```

## 3. Subir para o Render (hospedagem gratuita)

1. Crie uma conta em https://render.com
2. Suba esta pasta para um repositório no GitHub
3. No Render: "New +" → "Web Service" → conecte o repositório
4. Configurações:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
5. Em "Environment", adicione as variáveis:
   - `VERIFY_TOKEN`
   - `WHATSAPP_TOKEN`
   - `PHONE_NUMBER_ID`
   - `GEMINI_API_KEY`
6. Clique em "Deploy"
7. Copie a URL gerada (algo como `https://seu-bot.onrender.com`)

## 4. Configurar o Webhook na Meta

Na tela "Etapa 2. Configuração da produção" > "Configurar webhooks":

- **URL de callback:** `https://seu-bot.onrender.com/webhook`
- **Verificar token:** o mesmo valor que você colocou em `VERIFY_TOKEN`

Clique em "Verificar e salvar". Depois, marque os campos de assinatura (webhook fields), pelo menos `messages`.

## 5. Testar

Envie uma mensagem de WhatsApp para o número de teste (ou número de produção configurado). O bot deve responder automaticamente usando o Gemini.

## Personalização

Edite a variável `SYSTEM_PROMPT` dentro de `app.py` para mudar o comportamento e personalidade do bot.
