# ============================================================
# vues/mes_informations.py — Page "Mes informations"
# ============================================================
# Permet à l'utilisateur connecté de consulter et modifier
# ses informations (magasin ou association).
# Intégration dans app.py :
#   from vues import mes_informations
#   mes_informations.show()
# ============================================================

import streamlit as st
from config import supabase


# ----------------------------------------------------------
# Fonctions de récupération
# ----------------------------------------------------------

def get_infos_magasin(entite_id: str) -> dict:
    res = (
        supabase.table("magasins")
        .select("*")
        .eq("id", entite_id)
        .single()
        .execute()
    )
    return res.data


def get_infos_association(entite_id: str) -> dict:
    res = (
        supabase.table("associations")
        .select("*")
        .eq("id", entite_id)
        .single()
        .execute()
    )
    return res.data


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("👤 Mes informations")
    st.caption("Consulte et modifie les informations de ton compte")

    type_u    = st.session_state.get("type_utilisateur")
    entite_id = st.session_state.get("entite_id")
    user_email = st.session_state.get("user_email", "—")

    if not entite_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    # ── Chargement des infos ───────────────────────────────
    try:
        if type_u == "magasin":
            infos = get_infos_magasin(entite_id)
        else:
            infos = get_infos_association(entite_id)
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        st.stop()

    # ── Info compte ────────────────────────────────────────
    st.markdown("### 🔐 Compte")
    st.markdown(f"""
    <div class="foodrop-card">
      <p style="margin:0; font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.9rem;">
        Email de connexion
      </p>
      <p style="margin:4px 0 0; font-family:'Syne',sans-serif; font-weight:700;
                color:#2A5C1E; font-size:1rem;">{user_email}</p>
      <p style="margin:8px 0 0; font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.85rem;">
        Type de compte : {'🏪 Magasin' if type_u == 'magasin' else '🤝 Association'}
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Formulaire de modification ─────────────────────────
    label = "Magasin" if type_u == "magasin" else "Association"
    st.markdown(f"### 🏢 Informations {label}")

    with st.form(f"form_mes_infos_{type_u}"):

        col1, col2 = st.columns(2)

        with col1:
            nom = st.text_input(
                f"Nom du {label.lower()} *",
                value=infos.get("nom", ""),
            )
            adresse = st.text_input(
                "Adresse",
                value=infos.get("adresse", "") or "",
            )
            ville = st.text_input(
                "Ville",
                value=infos.get("ville", "") or "",
            )

        with col2:
            code_postal = st.text_input(
                "Code postal",
                value=infos.get("code_postal", "") or "",
            )
            contact_nom = st.text_input(
                "Nom du contact",
                value=infos.get("contact_nom", "") or "",
            )
            contact_prenom = st.text_input(
                "Prénom du contact",
                value=infos.get("contact_prenom", "") or "",
            )

        col3, col4 = st.columns(2)
        with col3:
            contact_tel = st.text_input(
                "Téléphone",
                value=infos.get("contact_telephone", "") or "",
            )
        with col4:
            contact_email = st.text_input(
                "Email de contact",
                value=infos.get("contact_email", "") or "",
            )

        st.divider()
        st.markdown("### 🔑 Changer le mot de passe")
        st.caption("Laisse vide si tu ne veux pas changer ton mot de passe.")

        col5, col6 = st.columns(2)
        with col5:
            nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
        with col6:
            confirm_mdp = st.text_input("Confirmer le mot de passe", type="password")

        submitted = st.form_submit_button(
            "💾 Enregistrer les modifications",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        erreurs = []
        if not nom.strip():
            erreurs.append(f"Le nom du {label.lower()} est obligatoire.")
        if nouveau_mdp and len(nouveau_mdp) < 8:
            erreurs.append("Le mot de passe doit faire au moins 8 caractères.")
        if nouveau_mdp and nouveau_mdp != confirm_mdp:
            erreurs.append("Les mots de passe ne correspondent pas.")

        if erreurs:
            for e in erreurs:
                st.error(f"❌ {e}")
        else:
            try:
                # Mise à jour des infos dans la table magasins ou associations
                table = "magasins" if type_u == "magasin" else "associations"
                supabase.table(table).update({
                    "nom":               nom.strip(),
                    "adresse":           adresse.strip() or None,
                    "ville":             ville.strip() or None,
                    "code_postal":       code_postal.strip() or None,
                    "contact_nom":       contact_nom.strip() or None,
                    "contact_prenom":    contact_prenom.strip() or None,
                    "contact_telephone": contact_tel.strip() or None,
                    "contact_email":     contact_email.strip() or None,
                }).eq("id", entite_id).execute()

                # Mise à jour du mot de passe si renseigné
                if nouveau_mdp:
                    supabase.auth.update_user({"password": nouveau_mdp})
                    st.success("✅ Informations et mot de passe mis à jour !")
                else:
                    st.success("✅ Informations mises à jour !")

            except Exception as e:
                st.error(f"❌ Erreur lors de la mise à jour : {e}")
