# ============================================================
# vues/gerer_reservations.py — Gérer les réservations (Association)
# ============================================================

import streamlit as st
from datetime import date
from config import supabase

BADGE_BASE = (
    "padding:3px 12px; border-radius:20px; font-size:0.8rem; "
    "font-family:'Syne',sans-serif; font-weight:700; display:inline-block;"
)

STATUT_RETRAIT_STYLES = {
    "prevu":        (f"{BADGE_BASE} background:#E8F0FE; color:#1A3A8C;", "🕐 Prévu"),
    "effectue":     (f"{BADGE_BASE} background:#D6EAD6; color:#1A4A1A;", "✅ Effectué"),
    "non_effectue": (f"{BADGE_BASE} background:#FDECEA; color:#7B2020;", "❌ Non effectué"),
    "annule":       (f"{BADGE_BASE} background:#EBEBEB; color:#555555;", "✖ Annulé"),
}

def badge_retrait(libelle):
    style, label = STATUT_RETRAIT_STYLES.get(libelle, (f"{BADGE_BASE} background:#EBEBEB; color:#555;", libelle))
    return f'<span style="{style}">{label}</span>'

def badge_urgence(date_limite_str):
    if not date_limite_str:
        return ""
    jours = (date.fromisoformat(date_limite_str[:10]) - date.today()).days
    if jours < 0:
        return f'<span style="{BADGE_BASE} background:#FDECEA; color:#7B2020;">⚡ Expiré</span>'
    if jours == 0:
        return f'<span style="{BADGE_BASE} background:#FDECEA; color:#7B2020;">⚡ Expire aujourd\'hui</span>'
    if jours == 1:
        return f'<span style="{BADGE_BASE} background:#D4A820; color:#fff;">⚡ 1 jour restant</span>'
    if jours <= 3:
        return f'<span style="{BADGE_BASE} background:#D4A820; color:#fff;">⚡ {jours} jours restants</span>'
    return f'<span style="{BADGE_BASE} background:#E8F5D6; color:#1A4A10;">✅ {jours} jours restants</span>'


@st.cache_data(ttl=30)
def get_reservations_en_cours(association_id: str):
    res = (
        supabase.table("reservations")
        .select(
            "id, date_reservation, date_retrait_prevu, "
            "statuts_retrait(libelle), "
            "dons(id, produit, quantite, date_limite, creneau_retrait, "
            "condition_conservation, numero_lot, photo_etiquette_url, "
            "categories(libelle), unites(libelle), "
            "magasins(nom, ville, adresse, contact_telephone))"
        )
        .eq("association_id", association_id)
        .execute()
    )
    return [
        r for r in res.data
        if not r.get("date_retrait_reel")
    ]


def get_statut_retrait_id(libelle: str):
    res = supabase.table("statuts_retrait").select("id").eq("libelle", libelle).single().execute()
    return res.data["id"]


def get_statut_don_id(libelle: str):
    res = supabase.table("statuts_don").select("id").eq("libelle", libelle).single().execute()
    return res.data["id"]


def _formulaire_controle(resa_id: str, don: dict, asso_id: str):
    """Formulaire de contrôle à réception affiché inline sous la card."""

    don_id       = don.get("id")
    produit      = don.get("produit", "—")
    num_lot      = don.get("numero_lot") or "—"
    date_lim     = (don.get("date_limite") or "")[:10]
    date_lim_aff = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"

    with st.container(border=True):
        st.markdown(
            f"<p style='font-family:Syne,sans-serif; font-weight:700; color:#2A5C1E; "
            f"font-size:1rem; margin:0;'>✅ Contrôle à réception — {produit}</p>",
            unsafe_allow_html=True,
        )
        st.caption(f"Lot : {num_lot} · DLC : {date_lim_aff}")

        with st.form(key=f"form_controle_{resa_id}"):

            st.markdown("#### 📋 Checklist")
            st.markdown("""
            <style>
              [data-baseweb="radio"] [data-checked="true"] > div:first-child {
                background-color: #D4A820 !important;
                border-color: #D4A820 !important;
              }
            </style>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                produit_conforme = st.radio("Produit conforme", ["✅ Oui", "❌ Non"], horizontal=True, key=f"pc_{resa_id}")
                emballage_intact = st.radio("Emballage intact",  ["✅ Oui", "❌ Non"], horizontal=True, key=f"ei_{resa_id}")
            with col2:
                lot_lisible   = st.radio("Numéro de lot lisible",  ["✅ Oui", "❌ Non"], horizontal=True, key=f"ll_{resa_id}")
                dlc_coherente = st.radio("Date limite cohérente", ["✅ Oui", "❌ Non"], horizontal=True, key=f"dc_{resa_id}")

            st.markdown("#### 🌡️ Températures")
            col3, col4 = st.columns(2)
            with col3:
                temp_produit = st.number_input("Température produit (°C)", min_value=-30.0, max_value=60.0, value=4.0, step=0.5, key=f"tp_{resa_id}")
            with col4:
                temp_camion = st.number_input("Température camion (°C)", min_value=-30.0, max_value=60.0, value=6.0, step=0.5, key=f"tc_{resa_id}")

            st.markdown("#### 🏁 Décision")
            decision = st.radio("Décision finale", ["✅ Accepté", "❌ Refusé"], horizontal=True, key=f"dec_{resa_id}")

            if decision == "❌ Refusé":
                commentaire = st.text_area("Motif du refus * (obligatoire)", key=f"com_{resa_id}", max_chars=500)
            else:
                commentaire = st.text_area("Commentaire (facultatif)", key=f"com_{resa_id}", max_chars=500)

            photo_reception = st.file_uploader("📷 Photo réception (facultatif)", type=["jpg","jpeg","png","webp"], key=f"ph_{resa_id}")

            col_val, col_ann = st.columns(2)
            with col_val:
                valider = st.form_submit_button("✅ Valider le contrôle", use_container_width=True)
            with col_ann:
                fermer = st.form_submit_button("✖ Fermer", use_container_width=True)

        if fermer:
            st.session_state[f"controle_ouvert_{resa_id}"] = False
            st.rerun()

        if valider:
            if decision == "❌ Refusé" and not commentaire.strip():
                st.error("❌ Le motif du refus est obligatoire.")
                return

            decision_db = "accepte" if decision == "✅ Accepté" else "refuse"

            photo_url = None
            if photo_reception:
                try:
                    nom = f"receptions/{resa_id}_{photo_reception.name}"
                    supabase.storage.from_("photos").upload(nom, photo_reception.read())
                    photo_url = supabase.storage.from_("photos").get_public_url(nom)
                except Exception:
                    pass

            try:
                supabase.table("controles_reception").insert({
                    "don_id":                don_id,
                    "association_id":        asso_id,
                    "produit_conforme":      produit_conforme == "✅ Oui",
                    "emballage_intact":      emballage_intact == "✅ Oui",
                    "lot_lisible":           lot_lisible == "✅ Oui",
                    "date_limite_coherente": dlc_coherente == "✅ Oui",
                    "temperature_produit":   temp_produit,
                    "temperature_camion":    temp_camion,
                    "decision":              decision_db,
                    "commentaires":          commentaire.strip() or None,
                    "photo_reception_url":   photo_url,
                }).execute()

                supabase.table("dons").update({
                    "statut_don_id": get_statut_don_id("recupere" if decision_db == "accepte" else "refuse"),
                }).eq("id", don_id).execute()

                supabase.table("reservations").update({
                    "statut_retrait_id": get_statut_retrait_id("effectue" if decision_db == "accepte" else "non_effectue"),
                    "date_retrait_reel": str(date.today()),
                }).eq("id", resa_id).execute()

                st.cache_data.clear()
                st.session_state[f"controle_ouvert_{resa_id}"] = False

                if decision_db == "accepte":
                    st.success("🎉 Don accepté et enregistré !")
                else:
                    st.error(f"Don refusé — Motif : {commentaire.strip()}")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Erreur : {e}")


def show():
    from vues import fiche_tracabilite

    # Si une fiche est ouverte, on l'affiche à la place
    if st.session_state.get("fiche_resa_id"):
        fiche_tracabilite.show(st.session_state["fiche_resa_id"], retour_label="← Retour à mes réservations")
        return

    st.title("📦 Mes réservations")
    st.caption("Gère tes dons réservés et effectue les contrôles à réception")

    asso_id = st.session_state.get("entite_id")
    if not asso_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    _, col_refresh = st.columns([6, 1])
    with col_refresh:
        if st.button("↻", key="refresh_resa"):
            st.cache_data.clear()
            st.rerun()

    try:
        reservations = get_reservations_en_cours(asso_id)
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        st.stop()

    if not reservations:
        st.info("Aucune réservation en cours. Va dans « Chercher un don » pour réserver un lot !")
        return

    st.markdown(
        f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
        f"<strong style='color:#2A5C1E;'>{len(reservations)}</strong> réservation(s) en cours</p>",
        unsafe_allow_html=True,
    )

    for resa in reservations:
        don       = resa.get("dons") or {}
        resa_id   = resa["id"]
        produit   = don.get("produit", "—")
        quantite  = don.get("quantite", "?")
        unite     = (don.get("unites") or {}).get("libelle", "")
        categorie = (don.get("categories") or {}).get("libelle", "—")
        magasin   = don.get("magasins") or {}
        mag_nom   = magasin.get("nom", "—")
        mag_ville = magasin.get("ville", "")
        mag_tel   = magasin.get("contact_telephone") or ""
        date_lim  = (don.get("date_limite") or "")[:10]
        date_lim_aff  = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"
        creneau   = don.get("creneau_retrait") or "—"
        date_prev = (resa.get("date_retrait_prevu") or "")[:10]
        date_prev_aff = date.fromisoformat(date_prev).strftime('%d/%m/%Y') if date_prev else "—"
        statut_ret = (resa.get("statuts_retrait") or {}).get("libelle", "prevu")

        if f"controle_ouvert_{resa_id}" not in st.session_state:
            st.session_state[f"controle_ouvert_{resa_id}"] = False
        if f"annuler_{resa_id}" not in st.session_state:
            st.session_state[f"annuler_{resa_id}"] = False
        if f"retrait_confirme_{resa_id}" not in st.session_state:
            st.session_state[f"retrait_confirme_{resa_id}"] = False

        with st.container(border=True):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(
                    f"<span style='font-family:Syne,sans-serif; font-size:0.78rem; color:#4D8C1F; "
                    f"font-weight:700; text-transform:uppercase; letter-spacing:0.05em;'>"
                    f"{mag_nom}{' · ' + mag_ville if mag_ville else ''}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"### {produit}")
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                    f"📦 {quantite} {unite} · {categorie} · DLC {date_lim_aff}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem;'>"
                    f"🕐 {creneau} · Retrait prévu le {date_prev_aff}"
                    f"{' · 📞 ' + mag_tel if mag_tel else ''}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(badge_retrait(statut_ret), unsafe_allow_html=True)
                urgence = badge_urgence(date_lim)
                if urgence:
                    st.markdown(urgence, unsafe_allow_html=True)

            with col_actions:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                # ── Voir la fiche ───────────────────────
                if st.button("📋 Fiche traçabilité", key=f"btn_fiche_{resa_id}", use_container_width=True):
                    st.session_state["fiche_resa_id"] = resa_id
                    st.rerun()

                # ── Confirmer le retrait ────────────────
                if not st.session_state.get(f"retrait_confirme_{resa_id}"):
                    if st.button("🚚 Confirmer le retrait", key=f"btn_retrait_{resa_id}", use_container_width=True):
                        try:
                            supabase.table("reservations").update({
                                "date_retrait_reel": str(date.today()),
                            }).eq("id", resa_id).execute()
                            st.cache_data.clear()
                            st.session_state[f"retrait_confirme_{resa_id}"] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")

                # ── Contrôle à réception ────────────────
                # Disponible seulement après confirmation du retrait
                if st.session_state.get(f"retrait_confirme_{resa_id}"):
                    label_ctrl = "🔒 Fermer" if st.session_state[f"controle_ouvert_{resa_id}"] else "✅ Contrôle réception"
                    if st.button(label_ctrl, key=f"btn_ctrl_{resa_id}", use_container_width=True, type="primary"):
                        st.session_state[f"controle_ouvert_{resa_id}"] = not st.session_state[f"controle_ouvert_{resa_id}"]
                        st.rerun()

                # ── Annuler ─────────────────────────────
                if not st.session_state.get(f"retrait_confirme_{resa_id}"):
                    if st.button("✖ Annuler", key=f"btn_ann_{resa_id}", use_container_width=True):
                        st.session_state[f"annuler_{resa_id}"] = True
                        st.rerun()

        # Confirmation annulation
        if st.session_state[f"annuler_{resa_id}"]:
            with st.container(border=True):
                st.warning(f"⚠️ Confirmes-tu l'annulation de **{produit}** ?")
                col_oui, col_non = st.columns(2)
                with col_oui:
                    if st.button("Oui, annuler", key=f"conf_ann_{resa_id}", type="primary", use_container_width=True):
                        try:
                            supabase.table("reservations").update({
                                "statut_retrait_id": get_statut_retrait_id("annule"),
                            }).eq("id", resa_id).execute()
                            supabase.table("dons").update({
                                "statut_don_id": get_statut_don_id("disponible"),
                            }).eq("id", don.get("id")).execute()
                            st.cache_data.clear()
                            st.session_state[f"annuler_{resa_id}"] = False
                            st.success("Réservation annulée. Le don est de nouveau disponible.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")
                with col_non:
                    if st.button("Non, garder", key=f"keep_ann_{resa_id}", use_container_width=True):
                        st.session_state[f"annuler_{resa_id}"] = False
                        st.rerun()

        # Formulaire contrôle inline
        if st.session_state[f"controle_ouvert_{resa_id}"]:
            _formulaire_controle(resa_id, don, asso_id)
