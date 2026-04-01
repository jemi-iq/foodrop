# ============================================================
# vues/historique_association.py — Historique des collectes
# ============================================================
# Affiche toutes les réservations passées avec résultats
# des contrôles à réception.
# Intégration dans app.py :
#   from vues import historique_association
#   historique_association.show()
# ============================================================

import streamlit as st
from datetime import date, timedelta
from config import supabase


# ----------------------------------------------------------
# Badges inline
# ----------------------------------------------------------

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

DECISION_STYLES = {
    "accepte": (f"{BADGE_BASE} background:#D6EAD6; color:#1A4A1A;", "✅ Accepté"),
    "refuse":  (f"{BADGE_BASE} background:#FDECEA; color:#7B2020;", "❌ Refusé"),
}

def badge_retrait(libelle):
    style, label = STATUT_RETRAIT_STYLES.get(libelle, (f"{BADGE_BASE} background:#EBEBEB; color:#555;", libelle))
    return f'<span style="{style}">{label}</span>'

def badge_decision(libelle):
    style, label = DECISION_STYLES.get(libelle, (f"{BADGE_BASE} background:#EBEBEB; color:#555;", libelle))
    return f'<span style="{style}">{label}</span>'


# ----------------------------------------------------------
# Données
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_associations():
    res = supabase.table("associations").select("id, nom").order("nom").execute()
    return {r["nom"]: r["id"] for r in res.data}


@st.cache_data(ttl=60)
def get_historique_association(association_id: str):
    res = (
        supabase.table("reservations")
        .select(
            "id, date_reservation, date_retrait_prevu, date_retrait_reel, "
            "statuts_retrait(libelle), "
            "dons(produit, quantite, date_limite, "
            "categories(libelle), unites(libelle), "
            "magasins(nom, ville))"
        )
        .eq("association_id", association_id)
        .order("date_reservation", desc=True)
        .execute()
    )
    return res.data


@st.cache_data(ttl=60)
def get_controles_association(association_id: str):
    """Récupère tous les contrôles pour construire un index don_id → contrôle."""
    res = (
        supabase.table("controles_reception")
        .select("don_id, decision, commentaires, temperature_produit, temperature_camion, date_controle")
        .eq("association_id", association_id)
        .execute()
    )
    # Index par don_id pour accès rapide
    return {r["don_id"]: r for r in res.data}


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("📋 Historique des collectes")
    st.caption("Consulte toutes tes réservations et les résultats des contrôles")

    asso_id = st.session_state.get("entite_id")
    if not asso_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    col_titre, col_refresh = st.columns([6, 1])
    with col_refresh:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↻", key="refresh_histo_asso"):
            st.cache_data.clear()
            st.rerun()
    st.divider()

    # ── Chargement ─────────────────────────────────────────
    try:
        toutes   = get_historique_association(asso_id)
        controles = get_controles_association(asso_id)
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        st.stop()

    if not toutes:
        st.info("Aucune réservation pour l'instant. Va dans « Chercher un don » pour commencer !")
        return

    # ── FILTRES ────────────────────────────────────────────
    st.markdown("### 🎛️ Filtres")
    col1, col2 = st.columns(2)

    statuts_dispo = sorted({
        (r.get("statuts_retrait") or {}).get("libelle", "")
        for r in toutes if (r.get("statuts_retrait") or {}).get("libelle")
    })

    with col1:
        filtre_statut = st.selectbox("Statut retrait", ["Tous"] + statuts_dispo, key="histo_asso_statut")

    with col2:
        filtre_periode = st.selectbox(
            "Période",
            ["Toutes", "7 derniers jours", "30 derniers jours", "3 derniers mois"],
            key="histo_asso_periode",
        )

    # Application des filtres
    reservations = toutes

    if filtre_statut != "Tous":
        reservations = [
            r for r in reservations
            if (r.get("statuts_retrait") or {}).get("libelle") == filtre_statut
        ]

    if filtre_periode != "Toutes":
        jours = {"7 derniers jours": 7, "30 derniers jours": 30, "3 derniers mois": 90}[filtre_periode]
        limite = date.today() - timedelta(days=jours)
        reservations = [
            r for r in reservations
            if r.get("date_reservation") and
            date.fromisoformat(r["date_reservation"][:10]) >= limite
        ]

    st.divider()

    # Mini stats
    nb_total    = len(toutes)
    nb_effectues = sum(1 for r in toutes if (r.get("statuts_retrait") or {}).get("libelle") == "effectue")
    nb_acceptes  = sum(1 for c in controles.values() if c.get("decision") == "accepte")
    taux_collecte = round(nb_effectues / nb_total * 100) if nb_total > 0 else 0
    taux_conformite = round(nb_acceptes / len(controles) * 100) if controles else 0

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#2A5C1E; margin:0;">{nb_total}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">Réservations totales</p>
        </div>""", unsafe_allow_html=True)
    with col_s2:
        couleur = "#2A5C1E" if taux_collecte >= 70 else "#D4A820" if taux_collecte >= 40 else "#C0392B"
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:{couleur}; margin:0;">{taux_collecte}%</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">Taux de collecte</p>
        </div>""", unsafe_allow_html=True)
    with col_s3:
        couleur2 = "#2A5C1E" if taux_conformite >= 70 else "#D4A820" if taux_conformite >= 40 else "#C0392B"
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:{couleur2}; margin:0;">{taux_conformite}%</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">Taux de conformité</p>
        </div>""", unsafe_allow_html=True)

    st.markdown(
        f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:0.5rem 0;'>"
        f"<strong style='color:#2A5C1E;'>{len(reservations)}</strong> réservation(s) affichée(s)</p>",
        unsafe_allow_html=True,
    )

    if not reservations:
        st.warning("Aucune réservation ne correspond à ces filtres.")
        return

    # ── LISTE ──────────────────────────────────────────────
    for resa in reservations:
        don          = resa.get("dons") or {}
        don_id       = don.get("id") if isinstance(don, dict) else None
        produit      = don.get("produit", "—")
        quantite     = don.get("quantite", "?")
        unite        = (don.get("unites") or {}).get("libelle", "")
        categorie    = (don.get("categories") or {}).get("libelle", "—")
        magasin      = don.get("magasins") or {}
        mag_nom      = magasin.get("nom", "—")
        mag_ville    = magasin.get("ville", "")
        date_lim     = (don.get("date_limite") or "")[:10]
        date_lim_aff = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"
        statut_ret   = (resa.get("statuts_retrait") or {}).get("libelle", "—")
        date_resa    = (resa.get("date_reservation") or "")[:10]
        date_resa_aff = date.fromisoformat(date_resa).strftime('%d/%m/%Y') if date_resa else "—"
        date_prev    = (resa.get("date_retrait_prevu") or "")[:10]
        date_prev_aff = date.fromisoformat(date_prev).strftime('%d/%m/%Y') if date_prev else "—"
        date_reel    = (resa.get("date_retrait_reel") or "")[:10]
        date_reel_aff = date.fromisoformat(date_reel).strftime('%d/%m/%Y') if date_reel else "—"

        # Contrôle associé
        controle = controles.get(don_id) if don_id else None

        with st.container(border=True):
            col_info, col_badges = st.columns([3, 1])

            with col_info:
                # Magasin source
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
                    f"📦 {quantite} {unite} · {categorie} · DLC {date_lim_aff}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem;'>"
                    f"📅 Réservé le {date_resa_aff} · Retrait prévu le {date_prev_aff}"
                    f"{' · Récupéré le ' + date_reel_aff if date_reel else ''}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

                # Détails contrôle si disponible
                if controle:
                    with st.expander("🔍 Voir le contrôle à réception"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(
                                f"<span style='font-family:Fraunces,serif; font-size:0.88rem; color:#6B7A5E;'>"
                                f"🌡️ Temp. produit : <strong>{controle.get('temperature_produit', '—')}°C</strong><br>"
                                f"🚛 Temp. camion : <strong>{controle.get('temperature_camion', '—')}°C</strong>"
                                f"</span>",
                                unsafe_allow_html=True,
                            )
                        with c2:
                            date_ctrl = (controle.get("date_controle") or "")[:10]
                            date_ctrl_aff = date.fromisoformat(date_ctrl).strftime('%d/%m/%Y') if date_ctrl else "—"
                            st.markdown(
                                f"<span style='font-family:Fraunces,serif; font-size:0.88rem; color:#6B7A5E;'>"
                                f"📅 Contrôlé le : <strong>{date_ctrl_aff}</strong>"
                                f"</span>",
                                unsafe_allow_html=True,
                            )
                        if controle.get("commentaires"):
                            st.markdown(
                                f"<span style='font-family:Fraunces,serif; font-size:0.85rem; "
                                f"color:#8C6A1A; font-style:italic;'>"
                                f"💬 {controle['commentaires']}</span>",
                                unsafe_allow_html=True,
                            )

            with col_badges:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(badge_retrait(statut_ret), unsafe_allow_html=True)
                if controle:
                    st.markdown(badge_decision(controle.get("decision", "")), unsafe_allow_html=True)
