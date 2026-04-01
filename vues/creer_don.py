# ============================================================
# vues/creer_don.py — Formulaire de création d'un don
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


MOTIFS_DON = [
    "Date courte",
    "Mauvais calibrage",
    "Emballage abîmé (non ouvert)",
    "Surproduction",
    "Retour magasin",
    "Fin de gamme",
    "Autre",
]

PLAGES_HORAIRES = [
    "07h00 - 08h00", "08h00 - 09h00", "09h00 - 10h00",
    "10h00 - 11h00", "11h00 - 12h00", "12h00 - 13h00",
    "14h00 - 15h00", "15h00 - 16h00", "16h00 - 17h00",
    "17h00 - 18h00", "18h00 - 19h00", "19h00 - 20h00",
]


def show():
    st.title("➕ Créer un don")
    st.caption("Publie un lot d'invendus pour les associations partenaires")

    magasin_id = st.session_state.get("entite_id")
    if not magasin_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    categories   = charger_categories()
    unites       = charger_unites()
    types_limite = charger_types_limite()

    cat_options  = {c["libelle"]: c["id"] for c in categories}
    unit_options = {u["libelle"]: u["id"] for u in unites}
    tl_options   = {t["libelle"]: t["id"] for t in types_limite}

    with st.form("form_creer_don", clear_on_submit=True):

        # ── SECTION 1 : Produit ────────────────────────────
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
                options=["Ambiant", "Frais (0–8°C)"],
            )

        col3, col4 = st.columns(2)
        with col3:
            quantite = st.number_input(
                "Quantité *",
                min_value=1,
                step=1,
                value=1,
                format="%d",
            )
        with col4:
            unite_label = st.selectbox("Unité *", options=list(unit_options.keys()))

        numero_lot = st.text_input(
            "Numéro de lot *",
            placeholder="Ex : LOT-2024-0412",
            help="Obligatoire pour la traçabilité des produits.",
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            motif_don = st.selectbox(
                "Motif du don *",
                options=MOTIFS_DON,
            )
        with col_m2:
            motif_detail = st.text_input(
                "Précision (facultatif)",
                placeholder="Ex : angles abîmés, calibre 2…",
            )

        # ── SECTION 2 : Date limite ────────────────────────
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
        st.markdown("### 🕐 Créneaux de retrait")
        st.caption("Sélectionne les jours et les plages horaires disponibles.")

        # Jours — cases à cocher
        jours_options = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        cols_jours = st.columns(7)
        jours_selectionnes = []
        for i, jour in enumerate(jours_options):
            with cols_jours[i]:
                if st.checkbox(jour[:3], key=f"jour_{jour}"):
                    jours_selectionnes.append(jour)

        # Plusieurs plages horaires
        plages_choisies = st.multiselect(
            "Plages horaires *",
            options=PLAGES_HORAIRES,
            default=["08h00 - 09h00"],
            help="Tu peux sélectionner plusieurs plages horaires.",
        )

        # Aperçu créneau
        if jours_selectionnes and plages_choisies:
            creneau_retrait = f"{', '.join(jours_selectionnes)} · {', '.join(plages_choisies)}"
            st.markdown(
                f'<span style="font-family:Fraunces,serif; font-size:0.9rem; color:#2A5C1E;">'
                f'📅 Créneau : <strong>{creneau_retrait}</strong></span>',
                unsafe_allow_html=True,
            )
        else:
            creneau_retrait = ""
            if not jours_selectionnes:
                st.markdown(
                    '<span style="font-family:Fraunces,serif; font-size:0.88rem; color:#C0392B;">'
                    '⚠️ Sélectionne au moins un jour.</span>', unsafe_allow_html=True)
            if not plages_choisies:
                st.markdown(
                    '<span style="font-family:Fraunces,serif; font-size:0.88rem; color:#C0392B;">'
                    '⚠️ Sélectionne au moins une plage horaire.</span>', unsafe_allow_html=True)

        # ── SECTION 4 : Photos & remarques ────────────────
        st.markdown("### 📷 Photos & remarques")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            photo_etiquette = st.file_uploader(
                "Photo de l'étiquette (facultatif)",
                type=["jpg", "jpeg", "png", "webp"],
                key="upload_etiquette",
            )
        with col_p2:
            photo_produit = st.file_uploader(
                "Photo du produit (facultatif)",
                type=["jpg", "jpeg", "png", "webp"],
                key="upload_produit",
            )

        commentaires = st.text_area(
            "Commentaires supplémentaires (facultatif)",
            placeholder="Informations complémentaires, conditionnement particulier…",
            height=80,
        )

        st.markdown("---")
        soumis = st.form_submit_button("✅ Publier le don", use_container_width=True)

    # ── VALIDATION & ENREGISTREMENT ────────────────────────
    if soumis:
        erreurs = []
        if not produit.strip():
            erreurs.append("Le libellé produit est obligatoire.")
        if quantite <= 0:
            erreurs.append("La quantité doit être supérieure à 0.")
        if not numero_lot.strip():
            erreurs.append("Le numéro de lot est obligatoire.")
        if not jours_selectionnes:
            erreurs.append("Sélectionne au moins un jour de retrait.")
        if not plages_choisies:
            erreurs.append("Sélectionne au moins une plage horaire.")

        if erreurs:
            for e in erreurs:
                st.error(f"❌ {e}")
            st.stop()

        # Construction du commentaire complet
        motif_complet = motif_don
        if motif_detail.strip():
            motif_complet += f" — {motif_detail.strip()}"
        commentaire_final = motif_complet
        if commentaires.strip():
            commentaire_final += f"\n{commentaires.strip()}"

        # Upload photos
        def upload_photo(fichier, dossier):
            if fichier is None:
                return None
            try:
                nom = f"{dossier}/{date.today().isoformat()}_{fichier.name}"
                supabase.storage.from_("photos").upload(nom, fichier.read())
                return supabase.storage.from_("photos").get_public_url(nom)
            except Exception as e:
                st.warning(f"⚠️ Photo non uploadée ({e}).")
                return None

        photo_etiquette_url = upload_photo(photo_etiquette, "etiquettes")
        photo_produit_url   = upload_photo(photo_produit, "produits")

        # Stocke les deux URLs séparées par | dans le champ photo_etiquette_url
        if photo_etiquette_url and photo_produit_url:
            photo_finale = f"{photo_etiquette_url}|{photo_produit_url}"
        else:
            photo_finale = photo_etiquette_url or photo_produit_url

        nouveau_don = {
            "magasin_id":             magasin_id,
            "produit":                produit.strip(),
            "categorie_id":           cat_options[categorie_label],
            "quantite":               int(quantite),
            "unite_id":               unit_options[unite_label],
            "type_limite_id":         tl_options[type_limite_label],
            "date_limite":            date_limite.isoformat(),
            "numero_lot":             numero_lot.strip(),
            "condition_conservation": condition_conservation,
            "creneau_retrait":        creneau_retrait,
            "photo_etiquette_url":    photo_finale,
            "commentaires":           commentaire_final,
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
