# ============================================================
# pages/creer_don.py — Formulaire de création d'un don
# ============================================================

import streamlit as st
from datetime import date, timedelta
from config import supabase


@st.cache_data(ttl=300)
def charger_categories():
    res = supabase.table("categories").select("id, libelle").order("libelle").execute()
    return res.data

@st.cache_data(ttl=300)
def charger_unites():
    res = supabase.table("unites").select("id, libelle").execute()
    return res.data

@st.cache_data(ttl=300)
def charger_types_limite():
    res = supabase.table("types_limite").select("id, libelle").execute()
    return res.data

@st.cache_data(ttl=300)
def charger_statut_disponible():
    res = supabase.table("statuts_don").select("id").eq("libelle", "disponible").execute()
    return res.data[0]["id"] if res.data else None


def show():
    st.title("➕ Créer un don")
    st.caption("Publie un lot d'invendus pour les associations partenaires")

    categories   = charger_categories()
    unites       = charger_unites()
    types_limite = charger_types_limite()

    cat_options  = {c["libelle"]: c["id"] for c in categories}
    unit_options = {u["libelle"]: u["id"] for u in unites}
    tl_options   = {t["libelle"]: t["id"] for t in types_limite}

    with st.form("form_creer_don", clear_on_submit=True):

        st.markdown("### 🥦 Informations produit")

        produit = st.text_input(
            "Libellé produit *",
            placeholder="Ex : Yaourts nature, Pommes Golden, Pain de campagne…",
        )

        col1, col2 = st.columns(2)
        with col1:
            categorie_label = st.selectbox("Catégorie *", options=list(cat_options.keys()))
        with col2:
            condition_conservation = st.selectbox(
                "Conditions de conservation *",
                options=["Ambiant", "Frais (0–4°C)", "Surgelé (< -18°C)"],
            )

        col3, col4 = st.columns(2)
        with col3:
            quantite = st.number_input("Quantité *", min_value=0.1, step=0.5, value=1.0)
        with col4:
            unite_label = st.selectbox("Unité *", options=list(unit_options.keys()))

        numero_lot = st.text_input("Numéro de lot", placeholder="Ex : LOT-2024-0412")

        st.markdown("### 📅 Date limite de consommation")

        col5, col6 = st.columns(2)
        with col5:
            type_limite_label = st.selectbox(
                "Type de date *",
                options=list(tl_options.keys()),
                help="DLC = Date Limite de Consommation. DDM = Date de Durabilité Minimale.",
            )
        with col6:
            date_limite = st.date_input(
                "Date *",
                value=date.today() + timedelta(days=3),
                min_value=date.today(),
            )

        jours_restants = (date_limite - date.today()).days
        if jours_restants <= 2:
            st.warning(f"⚠️ Don urgent — seulement **{jours_restants} jour(s)** avant la date limite.")

        st.markdown("### 🕐 Créneau de retrait")

        creneau_retrait = st.text_input(
            "Créneau proposé *",
            placeholder="Ex : Lundi–Vendredi 8h–10h, Samedi 9h–12h",
        )

        st.markdown("### 📷 Photo & remarques")

        photo_etiquette = st.file_uploader(
            "Photo de l'étiquette (facultatif)",
            type=["jpg", "jpeg", "png"],
            help="Prends en photo l'étiquette du produit pour faciliter le contrôle qualité.",
        )

        commentaires = st.text_area(
            "Commentaires (facultatif)",
            placeholder="Informations complémentaires, état du produit, conditionnement particulier…",
            height=100,
        )

        st.markdown("---")
        soumis = st.form_submit_button("✅ Publier le don", use_container_width=True)

    if soumis:
        erreurs = []
        if not produit.strip():
            erreurs.append("Le libellé produit est obligatoire.")
        if quantite <= 0:
            erreurs.append("La quantité doit être supérieure à 0.")
        if not creneau_retrait.strip():
            erreurs.append("Le créneau de retrait est obligatoire.")

        if erreurs:
            for e in erreurs:
                st.error(f"❌ {e}")
            st.stop()

        photo_url = None
        if photo_etiquette is not None:
            try:
                nom_fichier = f"etiquettes/{date.today().isoformat()}_{photo_etiquette.name}"
                donnees     = photo_etiquette.read()
                supabase.storage.from_("photos").upload(nom_fichier, donnees)
                photo_url = supabase.storage.from_("photos").get_public_url(nom_fichier)
            except Exception as e:
                st.warning(f"⚠️ Photo non uploadée ({e}). Le don sera publié sans photo.")

        nouveau_don = {
            "produit":                produit.strip(),
            "categorie_id":           cat_options[categorie_label],
            "quantite":               quantite,
            "unite_id":               unit_options[unite_label],
            "type_limite_id":         tl_options[type_limite_label],
            "date_limite":            date_limite.isoformat(),
            "numero_lot":             numero_lot.strip() or None,
            "condition_conservation": condition_conservation,
            "creneau_retrait":        creneau_retrait.strip(),
            "photo_etiquette_url":    photo_url,
            "commentaires":           commentaires.strip() or None,
            "statut_don_id":          charger_statut_disponible(),
        }

        try:
            res = supabase.table("dons").insert(nouveau_don).execute()
            if res.data:
                st.success("🎉 Don publié avec succès ! Les associations peuvent maintenant le réserver.")
                st.balloons()
            else:
                st.error("❌ Une erreur est survenue lors de l'enregistrement. Réessaie.")
        except Exception as e:
            st.error(f"❌ Erreur Supabase : {e}")