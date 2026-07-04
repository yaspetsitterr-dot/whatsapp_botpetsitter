import os
import requests
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# ==============================
# CONFIGURAÇÕES (via variáveis de ambiente)
# ==============================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "meu_token_secreto")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")          # Token do WhatsApp (Meta)
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")        # Phone Number ID (Meta)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")          # Chave da API do Gemini

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# ==============================
# PROMPT DO SEU BOT (personalize aqui!)
# ==============================
SYSTEM_PROMPT = (
    "Você é o assistente virtual da Yas Pet Sitter, simpático e prestativo. "
    "Responda de forma curta, amigável e objetiva, como se fosse uma "
    "conversa de WhatsApp. Ajude com dúvidas sobre serviços, preços e agendamentos. "
    "Use emojis com moderação, e apenas estes dois: 💜 e 🐾. Não use nenhum outro emoji."
)

# Guarda o histórico de conversa por número de telefone (simples, em memória)
conversas = {}


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """Endpoint que a Meta chama para confirmar o webhook."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403


@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    """Endpoint que recebe as mensagens enviadas pelos clientes no WhatsApp."""
    data = request.get_json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "statuses" in value:
            print(f"[LOG] Status de entrega recebido: {value['statuses']}")

        if "messages" not in value:
            # Pode ser um evento de status (mensagem lida, entregue, etc.)
            return jsonify({"status": "ok"}), 200

        mensagem = value["messages"][0]
        numero_cliente = mensagem["from"]
        texto_recebido = mensagem.get("text", {}).get("body", "")

        print(f"[LOG] Mensagem recebida de {numero_cliente}: {texto_recebido}")

        if texto_recebido:
            resposta = gerar_resposta_ia(numero_cliente, texto_recebido)
            print(f"[LOG] Resposta gerada pela IA: {resposta}")
            resultado_envio = enviar_mensagem_whatsapp(numero_cliente, resposta)
            print(f"[LOG] Resultado do envio: {resultado_envio}")

    except (KeyError, IndexError) as e:
        print("Aviso: payload sem mensagem processável:", e)

    return jsonify({"status": "ok"}), 200


def gerar_resposta_ia(numero_cliente, texto_usuario):
    """Chama o Gemini para gerar a resposta, mantendo um histórico simples."""
    if numero_cliente not in conversas:
        conversas[numero_cliente] = model.start_chat(history=[
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Entendido! Vou ajudar os clientes dessa forma."]},
        ])

    chat = conversas[numero_cliente]
    resposta = chat.send_message(texto_usuario)
    return resposta.text


def enviar_mensagem_whatsapp(numero_destino, texto):
    """Envia uma mensagem de texto de volta pelo WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto},
    }
    resp = requests.post(url, headers=headers, json=payload)
    print(f"[LOG] Status do envio: {resp.status_code} | Resposta: {resp.text}")
    return resp.json()


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Endpoint usado pela página web de chat (sem depender do WhatsApp)."""
    data = request.get_json(silent=True) or {}
    mensagem_usuario = (data.get("message") or "").strip()
    session_id = data.get("session_id") or "anonimo"

    if not mensagem_usuario:
        return jsonify({"reply": "Pode escrever sua mensagem? 🐾"}), 200

    try:
        resposta = gerar_resposta_ia(session_id, mensagem_usuario)
        return jsonify({"reply": resposta}), 200
    except Exception as e:
        print("[LOG] Erro no /api/chat:", e)
        return jsonify({"reply": "Ops, tive um probleminha aqui. Tenta de novo em instantes!"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
