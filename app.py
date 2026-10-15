"""
app.py
Application Flask principale : interface de chat du chatbot BankDemo (simulé),
connecté à Ollama et protégé par le filtre de filter.py.
Lab pédagogique : toutes les données sont fictives.
"""

from flask import Flask, render_template, request, redirect, url_for
import ollama
import uuid

from filter import SYSTEM_PROMPT, filtrer_reponse
from dashboard import dashboard_bp

MODELE = 'llama3.2:3b'

app = Flask(__name__)
app.register_blueprint(dashboard_bp)

# Stockage en mémoire de toutes les conversations : { id: {"titre":..., "messages":[...]} }
# NB : non persisté sur disque -> réinitialisé à chaque redémarrage du serveur.
conversations = {}


def generer_reponses(historique_messages):
    """Envoie l'historique au LLM (Ollama). Retourne (réponse brute, réponse filtrée)."""
    dernier_message = historique_messages[-1]['content']
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + historique_messages
    response = ollama.chat(model=MODELE, messages=messages)
    brute = response['message']['content']
    return brute, filtrer_reponse(brute, dernier_message)


def demander_au_bot(historique_messages):
    """Retourne uniquement la réponse filtrée (celle vue par l'utilisateur)."""
    return generer_reponses(historique_messages)[1]


@app.route('/')
def accueil():
    return render_template('index.html', conversations=conversations,
                           conv_id=None, messages=[])


@app.route('/nouvelle')
def nouvelle_conversation():
    conv_id = str(uuid.uuid4())[:8]
    conversations[conv_id] = {"titre": "Nouvelle discussion", "messages": []}
    return redirect(url_for('voir_conversation', conv_id=conv_id))


@app.route('/conversation/<conv_id>')
def voir_conversation(conv_id):
    conv = conversations.get(conv_id, {"titre": "Nouvelle discussion", "messages": []})
    return render_template('index.html', conversations=conversations,
                           conv_id=conv_id, messages=conv["messages"])


@app.route('/conversation/<conv_id>/envoyer', methods=['POST'])
def envoyer_message(conv_id):
    message = request.form['message']
    if conv_id not in conversations:
        conversations[conv_id] = {"titre": "Nouvelle discussion", "messages": []}

    conv = conversations[conv_id]
    conv["messages"].append({'role': 'user', 'content': message})

    if conv["titre"] == "Nouvelle discussion":
        conv["titre"] = message[:40] + ("..." if len(message) > 40 else "")

    reponse = demander_au_bot(conv["messages"])
    conv["messages"].append({'role': 'assistant', 'content': reponse})

    return redirect(url_for('voir_conversation', conv_id=conv_id))


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Point d'entrée API utilisé par redteam.py : le script de Red Team passe par
    le vrai pipeline (filtre + dashboard) au lieu d'appeler Ollama directement.
    Avec {"debug": true}, la réponse brute (avant filtre) est aussi renvoyée,
    pour mesurer ce que le modèle a réellement laissé fuiter (usage lab uniquement).
    """
    data = request.get_json()
    messages = data.get('messages', [])
    brute, filtree = generer_reponses(messages)
    resultat = {"reponse": filtree}
    if data.get('debug'):
        resultat["brute"] = brute
    return resultat


if __name__ == '__main__':
    # Lab local : écoute uniquement sur la machine (127.0.0.1)
    app.run(host='127.0.0.1', port=5000, debug=False)
