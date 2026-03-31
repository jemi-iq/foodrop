# ============================================================
# vues/dashboard_association.py — Dashboard côté Association
# ============================================================
# Affiche les KPIs, les réservations en cours et l'historique
# récent des collectes.
# Intégration dans app.py :
#   from vues import dashboard_association
#   dashboard_association.show()
# ============================================================

import streamlit as st
from datetime import date
from config import supabase


# ----------------------------------------------------------
# Style badges inline (même convention que les autres pages)
# ----------------------------------------------------------

BADGE_BASE = (
    "padding:3px 12px; border-radius:20px; font-size:0.8rem; "
    "font-family:'Syne',sans-serif; font-weight:700; display:inline-block;"
)

STATUT_DON_STYLES = {
    "disponible": (f"{BADGE_BASE} background:#E8F5D6; color:#1A4A10;", "● Disponible"),
    "reserve":    (f"{BADGE_BASE} background:#FFF3CD; color:#8C6A1A;", "● Réservé"),
    "recupere":   (f"{BADGE_BASE} background:#D6EAD6; color:#1A4A1A;", "● Récupéré"),
    "refuse":     (f"{BADGE_BASE} background:#FDECEA; color:#7B2020;", "● Refusé"),
}

STATUT_RETRAIT_STYLES = {
    "prevu":        (f"{BADGE_BASE} background:#E8F0FE; color:#1A3A8C;", "🕐 Prévu"),
    "effectue":     (f"{BADGE_BASE} background:#D6EAD6; color:#1A4A1A;", "✅ Effectué"),
    "non_effectue": (f"{BADGE_BASE} background:#FDECEA; color:#7B2020;", "❌ Non effectué"),
    "annule":       (f"{BADGE_BASE} background:#EBEBEB; color:#555555;", "✖ Annulé"),
}

def badge_don(libelle):
    style, label = STATUT_DON_STYLES.get(libelle, (f"{BADGE_BASE} background:#E8F5D6; color:#1A4A10;", libelle))
    return f'<span style="{style}">{label}</span>'

def badge_retrait(libelle):
    style, label = STATUT_RETRAIT_STYLES.get(libelle, (f"{BADGE_BASE} background:#EBEBEB; color:#555;", libelle))
    return f'<span style="{style}">{label}</span>'


# ----------------------------------------------------------
# Fonctions de récupération des données
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_associations():
    res = supabase.table("associations").select("id, nom, ville").order("nom").execute()
    return {r["nom"]: r["id"] for r in res.data}


@st.cache_data(ttl=60)
def get_stats_association(association_id: str) -> dict:
    """Calcule les KPIs pour une association donnée."""

    # Toutes les réservations de cette association
    reservations = (
        supabase.table("reservations")
        .select("id, statut_retrait_id, statuts_retrait(libelle), dons(quantite, statut_don_id, statuts_don(libelle))")
        .eq("association_id", association_id)
        .execute()
        .data
    )

    total_resa     = len(reservations)
    en_cours       = [r for r in reservations if (r.get("statuts_retrait") or {}).get("libelle") == "prevu"]
    effectues      = [r for r in reservations if (r.get("statuts_retrait") or {}).get("libelle") == "effectue"]
    non_effectues  = [r for r in reservations if (r.get("statuts_retrait") or {}).get("libelle") in ("non_effectue", "annule")]

    # Volume total collecté (somme des quantités des dons récupérés)
    volume = sum(
        (r.get("dons") or {}).get("quantite", 0)
        for r in effectues
    )

    # Taux de collecte
    termines = len(effectues) + len(non_effectues)
    taux = round(len(effectues) / termines * 100) if termines > 0 else 0

    # Contrôles réception (pour taux de conformité)
    controles = (
        supabase.table("controles_reception")
        .select("decision")
        .eq("association_id", association_id)
        .execute()
        .data
    )
    acceptes = [c for c in controles if c.get("decision") == "accepte"]
    taux_conformite = round(len(acceptes) / len(controles) * 100) if controles else 0

    return {
        "total_resa":      total_resa,
        "en_cours":        len(en_cours),
        "effectues":       len(effectues),
        "volume":          volume,
        "taux":            taux,
        "taux_conformite": taux_conformite,
        "nb_controles":    len(controles),
    }


@st.cache_data(ttl=60)
def get_reservations_recentes(association_id: str, limite: int = 8):
    """Récupère les réservations récentes avec détails du don."""
    res = (
        supabase.table("reservations")
        .select(
            "id, date_reservation, date_retrait_prevu, date_retrait_reel, "
            "statuts_retrait(libelle), "
            "dons(produit, quantite, date_limite, "
            "categories(libelle), unites(libelle), statuts_don(libelle), "
            "magasins(nom, ville))"
        )
        .eq("association_id", association_id)
        .order("date_reservation", desc=True)
        .limit(limite)
        .execute()
    )
    return res.data


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("🏠 Dashboard Association")

    # ── Sélecteur association ──────────────────────────────
    try:
        associations = get_associations()
    except Exception as e:
        st.error(f"❌ Connexion Supabase impossible : {e}")
        st.stop()

    if not associations:
        st.warning("Aucune association trouvée. Crée d'abord une association dans Supabase → Table Editor → associations.")
        st.stop()

    col_select, col_refresh = st.columns([6, 1])
    with col_select:
        asso_nom = st.selectbox(
            "Association affichée",
            options=list(associations.keys()),
            key="dashboard_asso_select",
        )
    with col_refresh:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↻", key="refresh_asso"):
            st.cache_data.clear()
            st.rerun()

    asso_id = associations[asso_nom]

    st.divider()

    # ── Chargement données ─────────────────────────────────
    try:
        stats = get_stats_association(asso_id)
        reservations = get_reservations_recentes(asso_id)
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        st.stop()

    # ── KPIs ───────────────────────────────────────────────
    st.markdown("### 📊 Vue d'ensemble")

    k1, k2, k3, k4, k5 = st.columns(5)

    kpis = [
        (k1, stats["total_resa"],      "#2A5C1E", "Réservations totales"),
        (k2, stats["en_cours"],         "#D4A820", "En cours"),
        (k3, stats["effectues"],        "#4D8C1F", "Collectes effectuées"),
        (k4, f"{stats['volume']:.0f}",  "#2A5C1E", "Unités collectées"),
        (k5, f"{stats['taux']}%",       "#2A5C1E" if stats['taux'] >= 70 else "#D4A820" if stats['taux'] >= 40 else "#C0392B", "Taux de collecte"),
    ]

    for col, valeur, couleur, label in kpis:
        with col:
            st.markdown(f"""
            <div class="foodrop-card" style="text-align:center;">
              <p style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                        color:{couleur}; margin:0;">{valeur}</p>
              <p style="font-family:'Fraunces',serif; color:#6B7A5E;
                        font-size:0.8rem; margin:4px 0 0;">{label}</p>
            </div>""", unsafe_allow_html=True)

    # Barre de progression + conformité
    col_prog, col_conf = st.columns(2)

    with col_prog:
        st.markdown(f"""
        <div style="margin:0.5rem 0 1rem;">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <span style="font-family:'Fraunces',serif; font-size:0.82rem; color:#6B7A5E;">
              Taux de collecte
            </span>
            <span style="font-family:'Syne',sans-serif; font-weight:700;
                         font-size:0.85rem; color:#2A5C1E;">{stats['taux']}%</span>
          </div>
          <div style="background:#E0DDD5; border-radius:20px; height:8px; overflow:hidden;">
            <div style="background:linear-gradient(90deg,#2A5C1E,#A8D455);
                        width:{min(stats['taux'],100)}%; height:100%; border-radius:20px;">
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_conf:
        if stats["nb_controles"] > 0:
            st.markdown(f"""
            <div style="margin:0.5rem 0 1rem;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="font-family:'Fraunces',serif; font-size:0.82rem; color:#6B7A5E;">
                  Taux de conformité ({stats['nb_controles']} contrôles)
                </span>
                <span style="font-family:'Syne',sans-serif; font-weight:700;
                             font-size:0.85rem; color:#2A5C1E;">{stats['taux_conformite']}%</span>
              </div>
              <div style="background:#E0DDD5; border-radius:20px; height:8px; overflow:hidden;">
                <div style="background:linear-gradient(90deg,#4D8C1F,#A8D455);
                            width:{min(stats['taux_conformite'],100)}%; height:100%; border-radius:20px;">
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(
                "<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem;"
                " margin-top:0.8rem;'>Aucun contrôle réception enregistré pour l'instant.</p>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── RÉSERVATIONS RÉCENTES ──────────────────────────────
    st.markdown("### 📦 Réservations récentes")

    if not reservations:
        st.info("Aucune réservation pour l'instant. Va dans « Chercher un don » pour réserver ton premier lot !")
        return

    for resa in reservations:
        don            = resa.get("dons") or {}
        produit        = don.get("produit", "—")
        quantite       = don.get("quantite", "?")
        unite          = (don.get("unites") or {}).get("libelle", "")
        categorie      = (don.get("categories") or {}).get("libelle", "—")
        statut_don_lib = (don.get("statuts_don") or {}).get("libelle", "—")
        magasin        = don.get("magasins") or {}
        mag_nom        = magasin.get("nom", "—")
        mag_ville      = magasin.get("ville", "")
        date_lim       = don.get("date_limite", "")
        statut_ret_lib = (resa.get("statuts_retrait") or {}).get("libelle", "—")

        # Dates — on prend seulement les 10 premiers caractères (YYYY-MM-DD)
        # car Supabase peut renvoyer un timestamp complet (ex: 2026-03-31T00:22:10.655046)
        date_resa = resa.get("date_reservation", "")[:10] if resa.get("date_reservation") else "—"
        date_prev = (resa.get("date_retrait_prevu") or "")[:10]
        date_lim  = (don.get("date_limite") or "")[:10]
        date_prev_aff = date.fromisoformat(date_prev).strftime('%d/%m/%Y') if date_prev else "—"
        date_lim_aff  = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"

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
                # Produit
                st.markdown(f"### {produit}")
                # Détails
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                    f"📦 {quantite} {unite} · {categorie} · DLC {date_lim_aff}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem;'>"
                    f"📅 Réservé le {date_resa} · Retrait prévu le {date_prev_aff}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

            with col_badges:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(badge_don(statut_don_lib), unsafe_allow_html=True)
                st.markdown(badge_retrait(statut_ret_lib), unsafe_allow_html=True)

    st.markdown(
        "<p style='text-align:center; font-family:Fraunces,serif; color:#6B7A5E; "
        "font-size:0.85rem; margin-top:0.5rem;'>"
        "→ Va dans « Contrôle réception » pour valider une collecte."
        "</p>",
        unsafe_allow_html=True,
    )
