# ============================================================
# vues/historique_magasin.py — Historique des dons (Magasin)
# ============================================================
# Affiche tous les dons passés avec filtres par statut et date.
# Intégration dans app.py :
#   from vues import historique_magasin
#   historique_magasin.show()
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

STATUT_STYLES = {
    "disponible": (f"{BADGE_BASE} background:#E8F5D6; color:#1A4A10;", "● Disponible"),
    "reserve":    (f"{BADGE_BASE} background:#FFF3CD; color:#8C6A1A;", "● Réservé"),
    "recupere":   (f"{BADGE_BASE} background:#D6EAD6; color:#1A4A1A;", "● Récupéré"),
    "refuse":     (f"{BADGE_BASE} background:#FDECEA; color:#7B2020;", "● Refusé"),
    "archive":    (f"{BADGE_BASE} background:#EBEBEB; color:#555555;", "● Archivé"),
}

def badge_statut(libelle):
    style, label = STATUT_STYLES.get(libelle, (f"{BADGE_BASE} background:#EBEBEB; color:#555;", libelle))
    return f'<span style="{style}">{label}</span>'


# ----------------------------------------------------------
# Données
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_magasins():
    res = supabase.table("magasins").select("id, nom").order("nom").execute()
    return {r["nom"]: r["id"] for r in res.data}


@st.cache_data(ttl=60)
def get_historique_magasin(magasin_id: str):
    res = (
        supabase.table("dons")
        .select(
            "id, produit, quantite, date_limite, date_publication, "
            "condition_conservation, creneau_retrait, "
            "categories(libelle), unites(libelle), statuts_don(libelle), "
            "reservations(date_reservation, date_retrait_reel, "
            "statuts_retrait(libelle), associations(nom))"
        )
        .eq("magasin_id", magasin_id)
        .order("date_publication", desc=True)
        .execute()
    )
    return res.data


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("📋 Historique des dons")
    st.caption("Consulte tous tes dons publiés et leur parcours")

    magasin_id = st.session_state.get("entite_id")
    if not magasin_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    col_titre, col_refresh = st.columns([6, 1])
    with col_refresh:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↻", key="refresh_histo_mag"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # ── Chargement ─────────────────────────────────────────
    try:
        tous = get_historique_magasin(magasin_id)
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        st.stop()

    if not tous:
        st.info("Aucun don publié pour l'instant.")
        return

    # ── FILTRES ────────────────────────────────────────────
    st.markdown("### 🎛️ Filtres")
    col1, col2, col3 = st.columns(3)

    statuts_dispo = sorted({
        (d.get("statuts_don") or {}).get("libelle", "")
        for d in tous if (d.get("statuts_don") or {}).get("libelle")
    })

    with col1:
        filtre_statut = st.selectbox("Statut", ["Tous"] + statuts_dispo, key="histo_mag_statut")

    with col2:
        filtre_periode = st.selectbox(
            "Période",
            ["Toutes", "7 derniers jours", "30 derniers jours", "3 derniers mois"],
            key="histo_mag_periode",
        )

    with col3:
        filtre_texte = st.text_input("🔎 Recherche", placeholder="Nom du produit…", key="histo_mag_txt")

    # Application des filtres
    dons = tous

    if filtre_statut != "Tous":
        dons = [d for d in dons if (d.get("statuts_don") or {}).get("libelle") == filtre_statut]

    if filtre_periode != "Toutes":
        jours = {"7 derniers jours": 7, "30 derniers jours": 30, "3 derniers mois": 90}[filtre_periode]
        limite = date.today() - timedelta(days=jours)
        dons = [
            d for d in dons
            if d.get("date_publication") and
            date.fromisoformat(d["date_publication"][:10]) >= limite
        ]

    if filtre_texte.strip():
        terme = filtre_texte.strip().lower()
        dons = [d for d in dons if terme in (d.get("produit") or "").lower()]

    st.divider()

    # Compteur + mini stats
    nb_total     = len(tous)
    nb_recuperes = sum(1 for d in tous if (d.get("statuts_don") or {}).get("libelle") == "recupere")
    taux         = round(nb_recuperes / nb_total * 100) if nb_total > 0 else 0

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#2A5C1E; margin:0;">{nb_total}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">Dons publiés au total</p>
        </div>""", unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#4D8C1F; margin:0;">{nb_recuperes}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">Dons récupérés</p>
        </div>""", unsafe_allow_html=True)
    with col_s3:
        couleur = "#2A5C1E" if taux >= 70 else "#D4A820" if taux >= 40 else "#C0392B"
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:{couleur}; margin:0;">{taux}%</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">Taux de récupération</p>
        </div>""", unsafe_allow_html=True)

    st.markdown(
        f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:0.5rem 0;'>"
        f"<strong style='color:#2A5C1E;'>{len(dons)}</strong> don(s) affiché(s)</p>",
        unsafe_allow_html=True,
    )

    if not dons:
        st.warning("Aucun don ne correspond à ces filtres.")
        return

    # ── LISTE ──────────────────────────────────────────────
    for don in dons:
        statut_lib = (don.get("statuts_don") or {}).get("libelle", "—")
        categorie  = (don.get("categories") or {}).get("libelle", "—")
        unite      = (don.get("unites") or {}).get("libelle", "")
        date_lim   = (don.get("date_limite") or "")[:10]
        date_pub   = (don.get("date_publication") or "")[:10]
        date_lim_aff = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"
        date_pub_aff = date.fromisoformat(date_pub).strftime('%d/%m/%Y') if date_pub else "—"

        # Infos réservation si elle existe
        reservations = don.get("reservations") or []
        resa = reservations[0] if reservations else None
        asso_nom = (resa.get("associations") or {}).get("nom", "—") if resa else None
        date_retrait = (resa.get("date_retrait_reel") or "")[:10] if resa else None
        date_retrait_aff = date.fromisoformat(date_retrait).strftime('%d/%m/%Y') if date_retrait else "—"

        with st.container(border=True):
            col_info, col_badge = st.columns([4, 1])

            with col_info:
                st.markdown(f"### {don.get('produit', '—')}")
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                    f"📦 {don.get('quantite','?')} {unite} · {categorie} · DLC {date_lim_aff}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem;'>"
                    f"📅 Publié le {date_pub_aff}"
                    f"{' · 🤝 Réservé par : ' + asso_nom if asso_nom else ''}"
                    f"{' · ✅ Récupéré le : ' + date_retrait_aff if date_retrait else ''}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

            with col_badge:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(badge_statut(statut_lib), unsafe_allow_html=True)
