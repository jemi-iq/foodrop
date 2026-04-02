# ============================================================
# vues/bienvenue.py — Page de bienvenue après inscription
# ============================================================

import streamlit as st


def show():
    type_u   = st.session_state.get("type_utilisateur")
    prenom   = st.session_state.get("user_prenom", "")

    if type_u == "magasin":
        emoji       = "🏪"
        titre       = f"Bienvenue{' ' + prenom if prenom else ''} !"
        sous_titre  = "Ton compte magasin est créé. Tu peux dès maintenant publier tes premiers dons."
        bouton      = "➕ Créer mon premier don"
        description = "Les associations de ton secteur pourront réserver tes invendus en quelques clics."
        couleur     = "#2A5C1E"
    else:
        emoji       = "🤝"
        titre       = f"Bienvenue{' ' + prenom if prenom else ''} !"
        sous_titre  = "Ton compte association est créé. Tu peux dès maintenant chercher des dons disponibles."
        bouton      = "🔍 Chercher mon premier don"
        description = "Des magasins près de toi publient leurs invendus chaque jour."
        couleur     = "#4D8C1F"

    # Page de bienvenue centrée
    st.markdown(f"""
    <div style="text-align:center; padding:3rem 1rem 2rem;">
      <div style="font-size:4rem; margin-bottom:1rem;">{emoji}</div>
      <h1 style="font-family:'Playfair Display',Georgia,serif; font-weight:700;
                 color:#2A5C1E; font-size:2.5rem; margin:0 0 0.8rem;">{titre}</h1>
      <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:1.1rem;
                line-height:1.7; max-width:480px; margin:0 auto 0.5rem;">{sous_titre}</p>
      <p style="font-family:'Fraunces',serif; color:#8C9A7E; font-size:0.95rem;
                max-width:420px; margin:0 auto 2.5rem;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

    # Boutons centrés
    col_vide1, col_action, col_dashboard, col_vide2 = st.columns([1, 1.5, 1.2, 1])

    with col_action:
        if st.button(bouton, type="primary", use_container_width=True):
            st.session_state.bienvenue = False
            if type_u == "magasin":
                st.session_state.page_cible = "➕ Créer un don"
            else:
                st.session_state.page_cible = "🔍 Chercher un don"
            st.rerun()

    with col_dashboard:
        if st.button("🏠 Aller au dashboard", use_container_width=True):
            st.session_state.bienvenue = False
            st.session_state.page_cible = "🏠 Dashboard"
            st.rerun()
