# ============================================================
# vues/controle_reception.py — Contrôle à réception
# ============================================================
# Permet à une association de remplir la checklist qualité
# lors de la récupération d'un don réservé.
# Intégration dans app.py :
#   from vues import controle_reception
#   controle_reception.show()
# ============================================================

import streamlit as st
from datetime import date
from config import supabase


# ----------------------------------------------------------
# Fonctions de récupération des données
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_associations():
    res = supabase.table("associations").select("id, nom").order("nom").execute()
    return {r["nom"]: r["id"] for r in res.data}


@st.cache_data(ttl=30)
def get_reservations_a_controler(association_id: str):
    """
    Récupère les réservations en statut 'prevu' pour cette association.
    Ce sont les dons réservés mais pas encore contrôlés.
    """
    res = (
        supabase.table("reservations")
        .select(
            "id, date_retrait_prevu, "
            "statuts_retrait(libelle), "
            "dons(id, produit, quantite, date_limite, numero_lot, "
            "condition_conservation, photo_etiquette_url, "
            "categories(libelle), unites(libelle), "
            "magasins(nom, ville))"
        )
        .eq("association_id", association_id)
        .execute()
    )
    # Filtre côté Python : statut retrait = prevu
    return [
        r for r in res.data
        if (r.get("statuts_retrait") or {}).get("libelle") == "prevu"
    ]


def get_statut_retrait_id(libelle: str) -> int:
    res = (
        supabase.table("statuts_retrait")
        .select("id")
        .eq("libelle", libelle)
        .single()
        .execute()
    )
    return res.data["id"]


def get_statut_don_id(libelle: str) -> int:
    res = (
        supabase.table("statuts_don")
        .select("id")
        .eq("libelle", libelle)
        .single()
        .execute()
    )
    return res.data["id"]


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("✅ Contrôle à réception")
    st.caption("Remplis la checklist de conformité lors de la récupération d'un don")

    asso_id = st.session_state.get("entite_id")
    if not asso_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    st.divider()

    # ── Chargement des réservations à contrôler ────────────
    try:
        reservations = get_reservations_a_controler(asso_id)
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        st.stop()

    if not reservations:
        st.info(
            "Aucun don en attente de contrôle pour le moment.  \n"
            "Les dons apparaissent ici une fois réservés via « Chercher un don »."
        )
        return

    st.markdown(
        f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
        f"<strong style='color:#2A5C1E;'>{len(reservations)}</strong> "
        f"don(s) en attente de contrôle</p>",
        unsafe_allow_html=True,
    )

    # ── Une carte par réservation ──────────────────────────
    for resa in reservations:
        don       = resa.get("dons") or {}
        don_id    = don.get("id")
        resa_id   = resa.get("id")
        produit   = don.get("produit", "—")
        quantite  = don.get("quantite", "?")
        unite     = (don.get("unites") or {}).get("libelle", "")
        categorie = (don.get("categories") or {}).get("libelle", "—")
        magasin   = don.get("magasins") or {}
        mag_nom   = magasin.get("nom", "—")
        mag_ville = magasin.get("ville", "")
        date_lim  = (don.get("date_limite") or "")[:10]
        date_lim_aff = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"
        conservation = don.get("condition_conservation") or "—"
        numero_lot   = don.get("numero_lot") or "—"
        photo_url    = don.get("photo_etiquette_url")

        with st.container(border=True):

            # En-tête de la carte
            st.markdown(
                f"<span style='font-family:Syne,sans-serif; font-size:0.78rem; "
                f"color:#4D8C1F; font-weight:700; text-transform:uppercase; "
                f"letter-spacing:0.05em;'>{mag_nom}"
                f"{' · ' + mag_ville if mag_ville else ''}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"### {produit}")
            st.markdown(
                f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                f"📦 {quantite} {unite} · {categorie} · "
                f"DLC {date_lim_aff} · ❄️ {conservation} · "
                f"Lot : {numero_lot}</span>",
                unsafe_allow_html=True,
            )

            # Photo étiquette si dispo
            if photo_url:
                with st.expander("📷 Voir la photo étiquette"):
                    st.image(photo_url, use_container_width=True)

            st.divider()

            # ── CHECKLIST ──────────────────────────────────
            st.markdown("#### 📋 Checklist de conformité")

            col1, col2 = st.columns(2)

            with col1:
                produit_conforme = st.radio(
                    "Produit conforme à la description",
                    options=["✅ Oui", "❌ Non"],
                    horizontal=True,
                    key=f"conforme_{resa_id}",
                )
                emballage_intact = st.radio(
                    "Emballage intact",
                    options=["✅ Oui", "❌ Non"],
                    horizontal=True,
                    key=f"emballage_{resa_id}",
                )

            with col2:
                lot_lisible = st.radio(
                    "Numéro de lot lisible",
                    options=["✅ Oui", "❌ Non"],
                    horizontal=True,
                    key=f"lot_{resa_id}",
                )
                dlc_coherente = st.radio(
                    "Date limite cohérente",
                    options=["✅ Oui", "❌ Non"],
                    horizontal=True,
                    key=f"dlc_{resa_id}",
                )

            st.markdown("#### 🌡️ Températures")
            col3, col4 = st.columns(2)

            with col3:
                temp_produit = st.number_input(
                    "Température produit (°C)",
                    min_value=-30.0,
                    max_value=60.0,
                    value=4.0,
                    step=0.5,
                    key=f"temp_prod_{resa_id}",
                    help="Conforme si < 10°C pour le frais"
                )
                # Indicateur conformité température produit
                if temp_produit < 10:
                    st.markdown(
                        f'<span style="font-family:Syne,sans-serif; font-size:0.8rem; '
                        f'font-weight:700; padding:2px 10px; border-radius:20px; '
                        f'background:#D6EAD6; color:#1A4A1A;">✅ Conforme ({temp_produit}°C)</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<span style="font-family:Syne,sans-serif; font-size:0.8rem; '
                        f'font-weight:700; padding:2px 10px; border-radius:20px; '
                        f'background:#FDECEA; color:#7B2020;">❌ Non conforme ({temp_produit}°C)</span>',
                        unsafe_allow_html=True,
                    )

            with col4:
                temp_camion = st.number_input(
                    "Température camion (°C)",
                    min_value=-30.0,
                    max_value=60.0,
                    value=6.0,
                    step=0.5,
                    key=f"temp_cam_{resa_id}",
                    help="Conforme si < 8°C pour le frais"
                )
                if temp_camion < 8:
                    st.markdown(
                        f'<span style="font-family:Syne,sans-serif; font-size:0.8rem; '
                        f'font-weight:700; padding:2px 10px; border-radius:20px; '
                        f'background:#D6EAD6; color:#1A4A1A;">✅ Conforme ({temp_camion}°C)</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<span style="font-family:Syne,sans-serif; font-size:0.8rem; '
                        f'font-weight:700; padding:2px 10px; border-radius:20px; '
                        f'background:#FDECEA; color:#7B2020;">❌ Non conforme ({temp_camion}°C)</span>',
                        unsafe_allow_html=True,
                    )

            st.divider()

            # ── DÉCISION FINALE ────────────────────────────
            st.markdown("#### 🏁 Décision finale")

            decision = st.radio(
                "Décision",
                options=["✅ Accepté", "❌ Refusé"],
                horizontal=True,
                key=f"decision_{resa_id}",
            )

            # Justification obligatoire si refus
            commentaire = ""
            if decision == "❌ Refusé":
                commentaire = st.text_area(
                    "Motif du refus *  (obligatoire)",
                    placeholder="Ex : Produit avarié, emballage ouvert, température hors norme…",
                    key=f"commentaire_{resa_id}",
                    max_chars=500,
                )

                if not commentaire.strip():
                    st.warning("⚠️ Le motif du refus est obligatoire.")
            else:
                commentaire = st.text_area(
                    "Commentaire (facultatif)",
                    placeholder="Tout s'est bien passé, RAS…",
                    key=f"commentaire_{resa_id}",
                    max_chars=500,
                )

            # Photo réception
            photo_reception = st.file_uploader(
                "📷 Photo à la réception (facultatif)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"photo_{resa_id}",
            )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── BOUTON VALIDER ─────────────────────────────
            if st.button(
                f"✅ Valider le contrôle — {produit}",
                key=f"valider_{resa_id}",
                type="primary",
                use_container_width=True,
            ):
                # Vérification motif refus
                if decision == "❌ Refusé" and not commentaire.strip():
                    st.error("❌ Tu dois indiquer un motif de refus avant de valider.")
                    st.stop()

                decision_db = "accepte" if decision == "✅ Accepté" else "refuse"

                # Upload photo réception si présente
                photo_reception_url = None
                if photo_reception:
                    try:
                        nom_fichier = f"receptions/{resa_id}_{photo_reception.name}"
                        supabase.storage.from_("photos").upload(
                            nom_fichier,
                            photo_reception.read(),
                            {"content-type": photo_reception.type},
                        )
                        photo_reception_url = supabase.storage.from_("photos").get_public_url(nom_fichier)
                    except Exception:
                        pass  # Photo facultative, on continue sans

                try:
                    # 1. Enregistre le contrôle
                    supabase.table("controles_reception").insert({
                        "don_id":              don_id,
                        "association_id":      asso_id,
                        "produit_conforme":    produit_conforme == "✅ Oui",
                        "emballage_intact":    emballage_intact == "✅ Oui",
                        "lot_lisible":         lot_lisible == "✅ Oui",
                        "date_limite_coherente": dlc_coherente == "✅ Oui",
                        "temperature_produit": temp_produit,
                        "temperature_camion":  temp_camion,
                        "decision":            decision_db,
                        "commentaires":        commentaire.strip() or None,
                        "photo_reception_url": photo_reception_url,
                    }).execute()

                    # 2. Met à jour le statut du don
                    nouveau_statut_don = "recupere" if decision_db == "accepte" else "refuse"
                    supabase.table("dons").update({
                        "statut_don_id": get_statut_don_id(nouveau_statut_don),
                    }).eq("id", don_id).execute()

                    # 3. Met à jour le statut de la réservation
                    nouveau_statut_retrait = "effectue" if decision_db == "accepte" else "non_effectue"
                    supabase.table("reservations").update({
                        "statut_retrait_id": get_statut_retrait_id(nouveau_statut_retrait),
                        "date_retrait_reel": str(date.today()),
                    }).eq("id", resa_id).execute()

                    # 4. Rafraîchit
                    st.cache_data.clear()

                    if decision_db == "accepte":
                        st.success(f"🎉 Don accepté et enregistré ! Merci pour ce contrôle.")
                    else:
                        st.error(f"Don refusé et enregistré. Motif : {commentaire.strip()}")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur lors de l'enregistrement : {e}")
