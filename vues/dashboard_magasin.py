# ============================================================
# pages/dashboard_magasin.py — Dashboard côté Magasin
# ============================================================
# Affiche les KPIs, les dons récents et les alertes urgentes.
# Intégration dans app.py :
#   from pages import dashboard_magasin
#   dashboard_magasin.show()
# ============================================================

import streamlit as st
from datetime import date, timedelta
from config import supabase


# ----------------------------------------------------------
# Fonctions de récupération des données
# ----------------------------------------------------------

@st.cache_data(ttl=60)   # Rafraîchi toutes les 60 secondes
def get_stats_magasin(magasin_id: str) -> dict:
    """Calcule les KPIs principaux pour un magasin donné."""

    # Tous les dons du magasin
    tous = (
        supabase.table("dons")
        .select("id, statut_don_id, quantite, date_limite, date_publication")
        .eq("magasin_id", magasin_id)
        .execute()
        .data
    )

    # Récupère les IDs de statuts
    statuts = (
        supabase.table("statuts_don")
        .select("id, libelle")
        .execute()
        .data
    )
    statut_map = {s["libelle"]: s["id"] for s in statuts}

    id_dispo    = statut_map.get("disponible")
    id_reserve  = statut_map.get("reserve")
    id_recupere = statut_map.get("recupere")
    id_refuse   = statut_map.get("refuse")

    dispo    = [d for d in tous if d["statut_don_id"] == id_dispo]
    reserves = [d for d in tous if d["statut_don_id"] == id_reserve]
    recuperes= [d for d in tous if d["statut_don_id"] == id_recupere]
    refuses  = [d for d in tous if d["statut_don_id"] == id_refuse]

    # Volume total récupéré (kg / cartons / etc. — on somme les quantités)
    volume_recupere = sum(d["quantite"] for d in recuperes)

    # Taux de récupération
    termines = len(recuperes) + len(refuses)
    taux = round(len(recuperes) / termines * 100) if termines > 0 else 0

    # Dons urgents (DLC dans ≤ 2 jours, statut disponible)
    aujourd_hui = date.today()
    urgents = [
        d for d in dispo
        if d["date_limite"] and
        (date.fromisoformat(d["date_limite"]) - aujourd_hui).days <= 2
    ]

    return {
        "total":           len(tous),
        "disponibles":     len(dispo),
        "reserves":        len(reserves),
        "recuperes":       len(recuperes),
        "refuses":         len(refuses),
        "volume_recupere": volume_recupere,
        "taux":            taux,
        "urgents":         urgents,
    }


@st.cache_data(ttl=60)
def get_dons_recents(magasin_id: str, limite: int = 8):
    """Récupère les dons les plus récents avec leurs statuts."""
    res = (
        supabase.table("dons")
        .select(
            "id, produit, quantite, date_limite, date_publication, "
            "statut_don_id, creneau_retrait, "
            "categories(libelle), unites(libelle), statuts_don(libelle)"
        )
        .eq("magasin_id", magasin_id)
        .order("date_publication", desc=True)
        .limit(limite)
        .execute()
    )
    return res.data


@st.cache_data(ttl=300)
def get_magasins():
    res = supabase.table("magasins").select("id, nom").order("nom").execute()
    return {row["nom"]: row["id"] for row in res.data}


# ----------------------------------------------------------
# Helpers d'affichage
# ----------------------------------------------------------

STATUT_STYLES = {
    "disponible": ("background:#E8F5D6; color:#1A4A10;", "● Disponible"),
    "reserve":    ("background:#FFF3CD; color:#8C6A1A;", "● Réservé"),
    "recupere":   ("background:#D6EAD6; color:#1A4A1A;", "● Récupéré"),
    "refuse":     ("background:#FDECEA; color:#7B2020;", "● Refusé"),
    "archive":    ("background:#EBEBEB; color:#555555;", "● Archivé"),
}

BADGE_BASE = (
    "padding:3px 12px; border-radius:20px; font-size:0.8rem; "
    "font-family:'Syne',sans-serif; font-weight:700; display:inline-block;"
)

def badge_statut(libelle: str) -> str:
    style, label = STATUT_STYLES.get(libelle, ("background:#E8F5D6; color:#1A4A10;", libelle))
    return f'<span style="{BADGE_BASE} {style}">{label}</span>'

def badge_urgence(date_limite_str: str) -> str:
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


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("🏠 Dashboard Magasin")

    # ── Récupère directement le magasin connecté ───────────
    magasin_id = st.session_state.get("entite_id")

    if not magasin_id:
        st.error("❌ Session invalide. Reconnecte-toi.")
        st.stop()

    # Récupère le nom du magasin pour l'afficher
    try:
        res = supabase.table("magasins").select("nom").eq("id", magasin_id).single().execute()
        magasin_nom = res.data.get("nom", "Mon magasin")
        st.caption(f"Bienvenue — {magasin_nom}")
    except Exception:
        pass

    st.divider()

    # ── Chargement des données ─────────────────────────────
    try:
        stats = get_stats_magasin(magasin_id)
        dons  = get_dons_recents(magasin_id)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {e}")
        st.stop()

    # ── ALERTE URGENCE ─────────────────────────────────────
    if stats["urgents"]:
        nb = len(stats["urgents"])
        noms = ", ".join(d.get("produit", "?") for d in stats["urgents"][:3])
        suite = f" + {nb - 3} autre(s)" if nb > 3 else ""
        st.markdown(
            f"""
            <div style="background:#FFF3CD; border-left:4px solid #D4A820;
                        border-radius:0 12px 12px 0; padding:0.9rem 1.2rem; margin-bottom:1rem;">
              <span style="font-family:'Syne',sans-serif; font-weight:700; color:#8C6A1A; font-size:0.95rem;">
                ⚡ {nb} don(s) urgent(s) — DLC dans ≤ 2 jours
              </span><br>
              <span style="font-family:'Fraunces',serif; color:#8C6A1A; font-size:0.88rem;">
                {noms}{suite}
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── KPIs ───────────────────────────────────────────────
    st.markdown("### 📊 Vue d'ensemble")

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                    color:#2A5C1E; margin:0;">{stats['total']}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">
            Dons publiés
          </p>
        </div>""", unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                    color:#A8D455; margin:0;">{stats['disponibles']}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">
            Disponibles
          </p>
        </div>""", unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                    color:#D4A820; margin:0;">{stats['reserves']}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">
            Réservés
          </p>
        </div>""", unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                    color:#4D8C1F; margin:0;">{stats['recuperes']}</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">
            Récupérés
          </p>
        </div>""", unsafe_allow_html=True)

    with k5:
        couleur_taux = "#2A5C1E" if stats['taux'] >= 70 else "#D4A820" if stats['taux'] >= 40 else "#C0392B"
        st.markdown(f"""
        <div class="foodrop-card" style="text-align:center;">
          <p style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                    color:{couleur_taux}; margin:0;">{stats['taux']}%</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.8rem; margin:4px 0 0;">
            Taux de récupération
          </p>
        </div>""", unsafe_allow_html=True)

    # Barre de progression visuelle
    if stats["total"] > 0:
        st.markdown(f"""
        <div style="margin: 0.5rem 0 1.5rem;">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <span style="font-family:'Fraunces',serif; font-size:0.8rem; color:#6B7A5E;">
              Volume récupéré
            </span>
            <span style="font-family:'Syne',sans-serif; font-weight:700; font-size:0.85rem; color:#2A5C1E;">
              {stats['volume_recupere']:.1f} unités sauvées
            </span>
          </div>
          <div style="background:#E0DDD5; border-radius:20px; height:8px; overflow:hidden;">
            <div style="background: linear-gradient(90deg, #2A5C1E, #A8D455);
                        width:{min(stats['taux'], 100)}%; height:100%; border-radius:20px;
                        transition: width 0.6s ease;">
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── DONS RÉCENTS ───────────────────────────────────────
    st.markdown("### 📦 Dons récents")

    if not dons:
        st.info("Aucun don publié pour l'instant. Crée ton premier don via « Créer un don » !")
        return

    for don in dons:
        statut_libelle = (don.get("statuts_don") or {}).get("libelle", "inconnu")
        categorie      = (don.get("categories") or {}).get("libelle", "—")
        unite          = (don.get("unites") or {}).get("libelle", "")
        date_limite    = don.get("date_limite", "")
        date_pub       = don.get("date_publication", "")[:10] if don.get("date_publication") else "—"

        # Formatage date limite
        if date_limite:
            jours = (date.fromisoformat(date_limite) - date.today()).days
            if jours < 0:
                date_aff = f"⚠️ Expiré le {date.fromisoformat(date_limite).strftime('%d/%m/%Y')}"
            else:
                date_aff = date.fromisoformat(date_limite).strftime('%d/%m/%Y')
        else:
            date_aff = "—"

        with st.container(border=True):
            col_info, col_badges = st.columns([3, 1])

            with col_info:
                st.markdown(
                    f"**{don.get('produit', '—')}**  \n"
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.88rem;'>"
                    f"{don.get('quantite', '?')} {unite} · {categorie} · DLC {date_aff}</span>  \n"
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.82rem;'>"
                    f"🕐 {don.get('creneau_retrait') or '—'} · Publié le {date_pub}</span>",
                    unsafe_allow_html=True,
                )

            with col_badges:
                # Badges rendus chacun dans leur propre st.markdown — jamais imbriqués
                urgence = badge_urgence(date_limite)
                if urgence:
                    st.markdown(urgence, unsafe_allow_html=True)
                st.markdown(badge_statut(statut_libelle), unsafe_allow_html=True)

    st.markdown(
        "<p style='text-align:center; font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem; margin-top:0.5rem;'>"
        "→ Va dans « Gérer les dons » pour modifier ou archiver un don."
        "</p>",
        unsafe_allow_html=True,
    )
