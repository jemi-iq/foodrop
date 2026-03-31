# ============================================================
# vues/gerer_dons.py — Gérer les dons (côté Magasin)
# ============================================================
# Permet au magasin de consulter, filtrer et modifier
# le statut de ses dons en cours.
# Intégration dans app.py :
#   from vues import gerer_dons
#   gerer_dons.show()
# ============================================================

import streamlit as st
from datetime import date
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
    style, label = STATUT_STYLES.get(libelle, (f"{BADGE_BASE} background:#E8F5D6; color:#1A4A10;", libelle))
    return f'<span style="{style}">{label}</span>'

def badge_urgence(date_limite_str):
    if not date_limite_str:
        return ""
    jours = (date.fromisoformat(date_limite_str) - date.today()).days
    if jours < 0:
        return f'<span style="{BADGE_BASE} background:#FDECEA; color:#7B2020;">⚡ Expiré</span>'
    if jours <= 2:
        return f'<span style="{BADGE_BASE} background:#D4A820; color:#fff;">⚡ Urgent</span>'
    return ""


# ----------------------------------------------------------
# Fonctions Supabase
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_magasins():
    res = supabase.table("magasins").select("id, nom").order("nom").execute()
    return {r["nom"]: r["id"] for r in res.data}


@st.cache_data(ttl=30)
def get_dons_magasin(magasin_id: str):
    res = (
        supabase.table("dons")
        .select(
            "id, produit, quantite, date_limite, date_publication, "
            "creneau_retrait, commentaires, condition_conservation, "
            "categories(libelle), unites(libelle), statuts_don(libelle)"
        )
        .eq("magasin_id", magasin_id)
        .order("date_publication", desc=True)
        .execute()
    )
    return res.data


def get_tous_statuts():
    res = supabase.table("statuts_don").select("id, libelle").execute()
    return {r["libelle"]: r["id"] for r in res.data}


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("📦 Gérer les dons")
    st.caption("Consulte, filtre et mets à jour tes dons publiés")

    # ── Sélecteur magasin ──────────────────────────────────
    try:
        magasins = get_magasins()
    except Exception as e:
        st.error(f"❌ Connexion Supabase impossible : {e}")
        st.stop()

    if not magasins:
        st.warning("Aucun magasin trouvé dans la base.")
        st.stop()

    col_select, col_refresh = st.columns([6, 1])
    with col_select:
        magasin_nom = st.selectbox(
            "Magasin",
            options=list(magasins.keys()),
            key="gerer_magasin_select",
        )
    with col_refresh:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↻", key="refresh_gerer"):
            st.cache_data.clear()
            st.rerun()

    magasin_id = magasins[magasin_nom]

    st.divider()

    # ── Chargement ─────────────────────────────────────────
    try:
        tous_les_dons = get_dons_magasin(magasin_id)
    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        st.stop()

    if not tous_les_dons:
        st.info("Aucun don publié pour ce magasin. Va dans « Créer un don » pour commencer !")
        return

    # ── FILTRES ────────────────────────────────────────────
    st.markdown("### 🎛️ Filtres")
    col1, col2, col3 = st.columns(3)

    statuts_disponibles = list({
        (d.get("statuts_don") or {}).get("libelle", "")
        for d in tous_les_dons
        if (d.get("statuts_don") or {}).get("libelle")
    })
    statuts_disponibles.sort()

    with col1:
        filtre_statut = st.selectbox(
            "Statut",
            options=["Tous"] + statuts_disponibles,
            key="filtre_statut_gerer",
        )
    with col2:
        filtre_urgence = st.checkbox("⚡ Urgents seulement", key="filtre_urg_gerer")
    with col3:
        filtre_texte = st.text_input("🔎 Recherche", placeholder="Nom du produit…", key="filtre_txt_gerer")

    # Application des filtres
    dons = tous_les_dons

    if filtre_statut != "Tous":
        dons = [d for d in dons if (d.get("statuts_don") or {}).get("libelle") == filtre_statut]

    if filtre_urgence:
        dons = [
            d for d in dons
            if d.get("date_limite") and
            (date.fromisoformat(d["date_limite"][:10]) - date.today()).days <= 2
            and (d.get("statuts_don") or {}).get("libelle") == "disponible"
        ]

    if filtre_texte.strip():
        terme = filtre_texte.strip().lower()
        dons = [d for d in dons if terme in (d.get("produit") or "").lower()]

    st.divider()

    # Compteur
    st.markdown(
        f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
        f"<strong style='color:#2A5C1E;'>{len(dons)}</strong> don(s) affiché(s) "
        f"sur {len(tous_les_dons)} au total</p>",
        unsafe_allow_html=True,
    )

    if not dons:
        st.warning("Aucun don ne correspond à ces filtres.")
        return

    # ── LISTE DES DONS ─────────────────────────────────────
    try:
        statuts_map = get_tous_statuts()
    except Exception as e:
        st.error(f"❌ Impossible de charger les statuts : {e}")
        st.stop()

    for don in dons:
        statut_libelle = (don.get("statuts_don") or {}).get("libelle", "inconnu")
        categorie      = (don.get("categories") or {}).get("libelle", "—")
        unite          = (don.get("unites") or {}).get("libelle", "")
        date_lim       = (don.get("date_limite") or "")[:10]
        date_pub       = (don.get("date_publication") or "")[:10]
        date_lim_aff   = date.fromisoformat(date_lim).strftime('%d/%m/%Y') if date_lim else "—"
        date_pub_aff   = date.fromisoformat(date_pub).strftime('%d/%m/%Y') if date_pub else "—"

        with st.container(border=True):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(f"### {don.get('produit', '—')}")
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                    f"📦 {don.get('quantite','?')} {unite} · {categorie} · "
                    f"DLC {date_lim_aff} · ❄️ {don.get('condition_conservation') or '—'}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.85rem;'>"
                    f"🕐 {don.get('creneau_retrait') or '—'} · Publié le {date_pub_aff}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

                # Badges statut + urgence sur des st.markdown séparés
                col_b1, col_b2 = st.columns([1, 3])
                with col_b1:
                    st.markdown(badge_statut(statut_libelle), unsafe_allow_html=True)
                with col_b2:
                    urgence = badge_urgence(date_lim)
                    if urgence:
                        st.markdown(urgence, unsafe_allow_html=True)

            with col_actions:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                # ── Modifier le statut ──────────────────
                # On ne propose que les transitions logiques
                transitions = {
                    "disponible": ["reserve", "archive"],
                    "reserve":    ["disponible", "recupere", "archive"],
                    "recupere":   ["archive"],
                    "refuse":     ["archive"],
                    "archive":    [],
                }
                options_transition = transitions.get(statut_libelle, [])

                if options_transition:
                    labels = {
                        "disponible": "● Disponible",
                        "reserve":    "● Réservé",
                        "recupere":   "● Récupéré",
                        "refuse":     "● Refusé",
                        "archive":    "● Archiver",
                    }
                    nouveau_statut = st.selectbox(
                        "Changer le statut",
                        options=["— Choisir —"] + options_transition,
                        format_func=lambda x: labels.get(x, x) if x != "— Choisir —" else "— Choisir —",
                        key=f"statut_select_{don['id']}",
                    )

                    if nouveau_statut != "— Choisir —":
                        if st.button(
                            "✅ Appliquer",
                            key=f"appliquer_{don['id']}",
                            use_container_width=True,
                            type="primary",
                        ):
                            try:
                                supabase.table("dons").update({
                                    "statut_don_id": statuts_map[nouveau_statut],
                                }).eq("id", don["id"]).execute()
                                st.cache_data.clear()
                                st.success(f"✅ Statut mis à jour → {labels[nouveau_statut]}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erreur : {e}")
                else:
                    st.markdown(
                        "<p style='font-family:Fraunces,serif; color:#6B7A5E; "
                        "font-size:0.82rem; font-style:italic;'>Aucune action disponible</p>",
                        unsafe_allow_html=True,
                    )
