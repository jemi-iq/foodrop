# ============================================================
# vues/auth.py — Authentification Foodrop
# ============================================================
# Gère la connexion et l'inscription (Magasin ou Association)
# via Supabase Auth.
# Intégration dans app.py :
#   from vues import auth
#   auth.show()  ← appelé si aucune session active
# ============================================================

import streamlit as st
from config import supabase


# ----------------------------------------------------------
# Helpers session
# ----------------------------------------------------------

def get_session():
    """Retourne la session active ou None."""
    try:
        session = supabase.auth.get_session()
        return session
    except Exception:
        return None


def get_profile(user_id: str) -> dict | None:
    """Récupère le profil (type + entite_id) de l'utilisateur connecté."""
    try:
        res = (
            supabase.table("profiles")
            .select("type_utilisateur, entite_id")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None


def deconnecter():
    """Déconnecte l'utilisateur et nettoie la session."""
    supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ----------------------------------------------------------
# Formulaire de CONNEXION
# ----------------------------------------------------------

def _form_connexion():
    st.markdown("### 🔑 Connexion")

    with st.form("form_connexion"):
        email = st.text_input("Email", placeholder="ton@email.com")
        mdp   = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter", type="primary", use_container_width=True)

    if submit:
        if not email.strip() or not mdp.strip():
            st.error("❌ Email et mot de passe obligatoires.")
            return

        try:
            res = supabase.auth.sign_in_with_password({
                "email": email.strip(),
                "password": mdp.strip(),
            })

            if res.user:
                # Charge le profil pour connaître le type
                profile = get_profile(res.user.id)
                if not profile:
                    st.error("❌ Profil introuvable. Contacte l'administrateur.")
                    return

                # Stocke en session
                st.session_state.user_id   = res.user.id
                st.session_state.user_email = res.user.email
                st.session_state.type_utilisateur = profile["type_utilisateur"]
                st.session_state.entite_id = profile["entite_id"]
                st.session_state.connecte  = True

                st.success("✅ Connexion réussie !")
                st.rerun()

        except Exception as e:
            msg = str(e)
            if "Invalid login" in msg or "invalid_credentials" in msg:
                st.error("❌ Email ou mot de passe incorrect.")
            else:
                st.error(f"❌ Erreur : {msg}")


# ----------------------------------------------------------
# Formulaire d'inscription MAGASIN
# ----------------------------------------------------------

def _form_inscription_magasin():
    st.markdown("### 🏪 Inscription Magasin")

    with st.form("form_inscription_magasin", clear_on_submit=False):

        st.markdown("#### Informations du magasin")
        col1, col2 = st.columns(2)
        with col1:
            nom_magasin = st.text_input("Nom du magasin *", placeholder="Ex : Biocoop Oberkampf")
            adresse     = st.text_input("Adresse *", placeholder="12 rue de la Paix")
            ville       = st.text_input("Ville *", placeholder="Paris")
        with col2:
            code_postal = st.text_input("Code postal *", placeholder="75011")
            siret       = st.text_input("SIRET", placeholder="123 456 789 00012")

        st.markdown("#### Contact")
        col3, col4 = st.columns(2)
        with col3:
            contact_nom    = st.text_input("Nom *", placeholder="Dupont")
            contact_prenom = st.text_input("Prénom *", placeholder="Marie")
        with col4:
            contact_tel    = st.text_input("Téléphone *", placeholder="06 12 34 56 78")
            contact_email  = st.text_input("Email de connexion *", placeholder="marie@biocoop.fr")

        st.markdown("#### Sécurité")
        mdp       = st.text_input("Mot de passe *", type="password",
                                   help="8 caractères minimum, avec au moins un chiffre ou caractère spécial")
        mdp_conf  = st.text_input("Confirmer le mot de passe *", type="password")

        rgpd = st.checkbox("J'accepte que mes données soient utilisées dans le cadre de Foodrop *")

        submit = st.form_submit_button("✅ Créer mon compte magasin", type="primary", use_container_width=True)

    if submit:
        # Validations
        erreurs = []
        if not nom_magasin.strip(): erreurs.append("Nom du magasin obligatoire.")
        if not adresse.strip():     erreurs.append("Adresse obligatoire.")
        if not ville.strip():       erreurs.append("Ville obligatoire.")
        if not code_postal.strip(): erreurs.append("Code postal obligatoire.")
        if not contact_nom.strip(): erreurs.append("Nom du contact obligatoire.")
        if not contact_prenom.strip(): erreurs.append("Prénom du contact obligatoire.")
        if not contact_tel.strip(): erreurs.append("Téléphone obligatoire.")
        if not contact_email.strip(): erreurs.append("Email obligatoire.")
        if len(mdp) < 8:            erreurs.append("Mot de passe trop court (8 caractères min).")
        if mdp != mdp_conf:         erreurs.append("Les mots de passe ne correspondent pas.")
        if not rgpd:                erreurs.append("Tu dois accepter les conditions RGPD.")

        if erreurs:
            for e in erreurs:
                st.error(f"❌ {e}")
            return

        try:
            # 1. Crée le compte Supabase Auth
            res_auth = supabase.auth.sign_up({
                "email":    contact_email.strip(),
                "password": mdp.strip(),
            })

            if not res_auth.user:
                st.error("❌ Erreur lors de la création du compte.")
                return

            user_id = res_auth.user.id

            # 2. Insère dans la table magasins
            res_mag = supabase.table("magasins").insert({
                "nom":               nom_magasin.strip(),
                "adresse":           adresse.strip(),
                "ville":             ville.strip(),
                "code_postal":       code_postal.strip(),
                "contact_nom":       contact_nom.strip(),
                "contact_prenom":    contact_prenom.strip(),
                "contact_telephone": contact_tel.strip(),
                "contact_email":     contact_email.strip(),
            }).execute()

            magasin_id = res_mag.data[0]["id"]

            # 3. Crée le profil de liaison
            supabase.table("profiles").insert({
                "id":               user_id,
                "type_utilisateur": "magasin",
                "entite_id":        magasin_id,
            }).execute()

            # 4. Connecte et redirige vers la bienvenue
            st.session_state.user_id          = user_id
            st.session_state.user_email       = contact_email.strip()
            st.session_state.user_prenom      = contact_prenom.strip()
            st.session_state.type_utilisateur = "magasin"
            st.session_state.entite_id        = magasin_id
            st.session_state.connecte         = True
            st.session_state.bienvenue        = True
            st.rerun()

        except Exception as e:
            msg = str(e)
            if "already registered" in msg or "already exists" in msg:
                st.error("❌ Cet email est déjà utilisé. Connecte-toi plutôt.")
            else:
                st.error(f"❌ Erreur : {msg}")


# ----------------------------------------------------------
# Formulaire d'inscription ASSOCIATION
# ----------------------------------------------------------

def _form_inscription_association():
    st.markdown("### 🤝 Inscription Association")

    with st.form("form_inscription_association", clear_on_submit=False):

        st.markdown("#### Informations de l'association")
        col1, col2 = st.columns(2)
        with col1:
            nom_asso    = st.text_input("Nom de l'association *", placeholder="Ex : Banque Alimentaire")
            adresse     = st.text_input("Adresse *", placeholder="5 avenue de la République")
            ville       = st.text_input("Ville *", placeholder="Paris")
        with col2:
            code_postal = st.text_input("Code postal *", placeholder="75011")
            rna         = st.text_input("Numéro RNA", placeholder="W751234567",
                                        help="Numéro d'enregistrement national des associations")

        st.markdown("#### Contact")
        col3, col4 = st.columns(2)
        with col3:
            contact_nom    = st.text_input("Nom *", placeholder="Martin")
            contact_prenom = st.text_input("Prénom *", placeholder="Pierre")
        with col4:
            contact_tel    = st.text_input("Téléphone *", placeholder="06 98 76 54 32")
            contact_email  = st.text_input("Email de connexion *", placeholder="pierre@asso.fr")

        st.markdown("#### Sécurité")
        mdp      = st.text_input("Mot de passe *", type="password",
                                  help="8 caractères minimum, avec au moins un chiffre ou caractère spécial")
        mdp_conf = st.text_input("Confirmer le mot de passe *", type="password")

        rgpd = st.checkbox("J'accepte que mes données soient utilisées dans le cadre de Foodrop *")

        submit = st.form_submit_button("✅ Créer mon compte association", type="primary", use_container_width=True)

    if submit:
        erreurs = []
        if not nom_asso.strip():       erreurs.append("Nom de l'association obligatoire.")
        if not adresse.strip():        erreurs.append("Adresse obligatoire.")
        if not ville.strip():          erreurs.append("Ville obligatoire.")
        if not code_postal.strip():    erreurs.append("Code postal obligatoire.")
        if not contact_nom.strip():    erreurs.append("Nom du contact obligatoire.")
        if not contact_prenom.strip(): erreurs.append("Prénom du contact obligatoire.")
        if not contact_tel.strip():    erreurs.append("Téléphone obligatoire.")
        if not contact_email.strip():  erreurs.append("Email obligatoire.")
        if len(mdp) < 8:               erreurs.append("Mot de passe trop court (8 caractères min).")
        if mdp != mdp_conf:            erreurs.append("Les mots de passe ne correspondent pas.")
        if not rgpd:                   erreurs.append("Tu dois accepter les conditions RGPD.")

        if erreurs:
            for e in erreurs:
                st.error(f"❌ {e}")
            return

        try:
            # 1. Crée le compte Auth
            res_auth = supabase.auth.sign_up({
                "email":    contact_email.strip(),
                "password": mdp.strip(),
            })

            if not res_auth.user:
                st.error("❌ Erreur lors de la création du compte.")
                return

            user_id = res_auth.user.id

            # 2. Insère dans la table associations
            res_asso = supabase.table("associations").insert({
                "nom":               nom_asso.strip(),
                "adresse":           adresse.strip(),
                "ville":             ville.strip(),
                "code_postal":       code_postal.strip(),
                "contact_nom":       contact_nom.strip(),
                "contact_prenom":    contact_prenom.strip(),
                "contact_telephone": contact_tel.strip(),
                "contact_email":     contact_email.strip(),
            }).execute()

            asso_id = res_asso.data[0]["id"]

            # 3. Crée le profil de liaison
            supabase.table("profiles").insert({
                "id":               user_id,
                "type_utilisateur": "association",
                "entite_id":        asso_id,
            }).execute()

            # 4. Connecte et redirige vers la bienvenue
            st.session_state.user_id          = user_id
            st.session_state.user_email       = contact_email.strip()
            st.session_state.user_prenom      = contact_prenom.strip()
            st.session_state.type_utilisateur = "association"
            st.session_state.entite_id        = asso_id
            st.session_state.connecte         = True
            st.session_state.bienvenue        = True
            st.rerun()

        except Exception as e:
            msg = str(e)
            if "already registered" in msg or "already exists" in msg:
                st.error("❌ Cet email est déjà utilisé. Connecte-toi plutôt.")
            else:
                st.error(f"❌ Erreur : {msg}")


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show(onglet_actif: str = "connexion"):
    """Affiche le bon formulaire selon l'action choisie depuis la landing."""

    # Bouton retour vers la landing
    if st.button("← Retour à l'accueil", key="retour_landing"):
        st.session_state.landing_action = None
        st.rerun()

    # Logo centré
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0 1rem;">
      <span style="font-family:'Syne',sans-serif; font-size:3rem; font-weight:800; color:#2A5C1E;">
        food<span style="color:#A8D455;">rop</span>
      </span>
      <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:1rem; margin-top:4px;">
        Rien ne se gaspille, tout se partage.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Affiche directement le bon formulaire
    if onglet_actif == "inscription_magasin":
        _form_inscription_magasin()
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤝 Inscrire mon association", key="switch_asso", use_container_width=True):
                st.session_state.landing_action = "inscription_association"
                st.rerun()
        with col2:
            if st.button("🔑 Me connecter", key="switch_login_mag", use_container_width=True):
                st.session_state.landing_action = "connexion"
                st.rerun()

    elif onglet_actif == "inscription_association":
        _form_inscription_association()
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏪 Inscrire mon magasin", key="switch_mag", use_container_width=True):
                st.session_state.landing_action = "inscription_magasin"
                st.rerun()
        with col2:
            if st.button("🔑 Me connecter", key="switch_login_asso", use_container_width=True):
                st.session_state.landing_action = "connexion"
                st.rerun()

    else:  # connexion par défaut
        _form_connexion()
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏪 Inscrire mon magasin", key="switch_mag2", use_container_width=True):
                st.session_state.landing_action = "inscription_magasin"
                st.rerun()
        with col2:
            if st.button("🤝 Inscrire mon association", key="switch_asso2", use_container_width=True):
                st.session_state.landing_action = "inscription_association"
                st.rerun()
