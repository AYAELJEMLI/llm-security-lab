"""
dashboard.py
Blueprint Flask affichant le journal des incidents de sécurité
(tentatives d'attaque interceptées par le filtre de filter.py).
"""

from flask import Blueprint, render_template
from filter import incidents

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    total_llm0102 = len([i for i in incidents if i["type"].startswith("LLM01")])
    total_llm07 = len([i for i in incidents if i["type"].startswith("LLM07")])
    return render_template(
        'dashboard.html',
        incidents=list(reversed(incidents)),
        total_llm0102=total_llm0102,
        total_llm07=total_llm07
    )
