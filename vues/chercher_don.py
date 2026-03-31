# ============================================================
# vues/chercher_don.py — Page "Chercher un don" (Association)
# ============================================================
# Affiche la liste des dons disponibles avec filtres,
# et permet à une association de réserver un don.
# Intégration dans app.py :
#   from vues import chercher_don
#   chercher_don.show()
# ============================================================

import streamlit as st
from datetime import date, timedelta
from config import supabase

# ----------------------------------------------------------
# Constantes de style — badges inline (leçon apprise !)
# ----------------------------------------------------------

BADGE_BASE = (
    "padding:3px 12px; border-radius:20px; font-size:0.8rem; "
    "font-family:'Syne',sans-serif; font-weight:700; display:inline-block;"
)

def badge_urgence(date_limite_str: str) -> str:
    if not date_limite_str:
        return ""
    jours = (date.fromisoformat(date_limite_str) - date.today()).days
    if jours < 0:
        return f'<span style="{BADGE_BASE} background:#FDECEA; color:#7B2020;">⚡ Expiré</span>'
    if jours == 0:
        return f'<span style="{BADGE_BASE} background:#D4A820; color:#fff;">⚡ Aujourd\'hui</span>'
    if jours == 1:
        return f'<span style="{BADGE_BASE} background:#D4A820; color:#fff;">⚡ Demain</span>'
    if jours <= 2:
        return f'<span style="{BADGE_BASE} background:#D4A820; color:#fff;">⚡ Urgent</span>'
    return f'<span style="{BADGE_BASE} background:#E8F5D6; color:#1A4A10;">● Disponible</span>'


# ----------------------------------------------------------
# Fonctions de récupération des données
# ----------------------------------------------------------

@st.cache_data(ttl=30)   # Court TTL : les dons changent vite
def get_dons_disponibles():
    """Récupère tous les dons avec statut 'disponible'."""
    # Récupère l'ID du statut disponible
    statut = (
        supabase.table("statuts_don")
        .select("id")
        .eq("libelle", "disponible")
        .single()
        .execute()
    )
    statut_id = statut.data["id"]

    res = (
        supabase.table("dons")
        .select(
            "id, produit, quantite, date_limite, date_publication, "
            "condition_conservation, creneau_retrait, commentaires, "
            "numero_lot, photo_etiquette_url, "
            "categories(libelle), unites(libelle), "
            "types_limite(libelle), magasins(nom, ville, adresse)"
        )
        .eq("statut_don_id", statut_id)
        .order("date_limite", desc=False)   # Les plus urgents en premier
        .execute()
    )
    return res.data


@st.cache_data(ttl=300)
def get_categories():
    res = supabase.table("categories").select("libelle").order("libelle").execute()
    return ["Toutes"] + [r["libelle"] for r in res.data]


@st.cache_data(ttl=300)
def get_associations():
    res = supabase.table("associations").select("id, nom").order("nom").execute()
    return {r["nom"]: r["id"] for r in res.data}


def get_statut_reserve_id():
    res = (
        supabase.table("statuts_don")
        .select("id")
        .eq("libelle", "reserve")
        .single()
        .execute()
    )
    return res.data["id"]


def get_statut_retrait_prevu_id():
    res = (
        supabase.table("statuts_retrait")
        .select("id")
        .eq("libelle", "prevu")
        .single()
        .execute()
    )
    return res.data["id"]


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    st.title("🔍 Chercher un don")
    st.caption("Parcours les dons disponibles et réserve un lot pour ton association")

    # ── Chargement ─────────────────────────────────────────
    try:
        tous_les_dons = get_dons_disponibles()
        categories    = get_categories()
        associations  = get_associations()
    except Exception as e:
        st.error(f"❌ Erreur de connexion : {e}")
        st.stop()

    if not tous_les_dons:
        st.info("Aucun don disponible pour le moment. Reviens bientôt !")
        return

    # ── FILTRES ────────────────────────────────────────────
    st.markdown("### 🎛️ Filtres")
    col1, col2, col3 = st.columns(3)

    with col1:
        filtre_categorie = st.selectbox("Catégorie", options=categories, key="filtre_cat")

    with col2:
        filtre_urgence = st.checkbox("⚡ Urgents seulement (DLC ≤ 2 jours)", key="filtre_urg")

    with col3:
        filtre_texte = st.text_input("🔎 Recherche libre", placeholder="Ex : pain, yaourt…", key="filtre_txt")

    st.divider()

    # ── Application des filtres ────────────────────────────
    dons_filtres = tous_les_dons

    if filtre_categorie != "Toutes":
        dons_filtres = [
            d for d in dons_filtres
            if (d.get("categories") or {}).get("libelle") == filtre_categorie
        ]

    if filtre_urgence:
        dons_filtres = [
            d for d in dons_filtres
            if d.get("date_limite") and
            (date.fromisoformat(d["date_limite"]) - date.today()).days <= 2
        ]

    if filtre_texte.strip():
        terme = filtre_texte.strip().lower()
        dons_filtres = [
            d for d in dons_filtres
            if terme in (d.get("produit") or "").lower()
            or terme in (d.get("commentaires") or "").lower()
        ]

    # Compteur de résultats
    nb = len(dons_filtres)
    st.markdown(
        f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin-bottom:1rem;'>"
        f"<strong style='color:#2A5C1E;'>{nb}</strong> don(s) disponible(s)</p>",
        unsafe_allow_html=True,
    )

    if nb == 0:
        st.warning("Aucun don ne correspond à ces filtres.")
        return

    # ── LISTE DES DONS ─────────────────────────────────────
    for don in dons_filtres:

        categorie  = (don.get("categories") or {}).get("libelle", "—")
        unite      = (don.get("unites") or {}).get("libelle", "")
        type_lim   = (don.get("types_limite") or {}).get("libelle", "Date")
        magasin    = don.get("magasins") or {}
        mag_nom    = magasin.get("nom", "—")
        mag_ville  = magasin.get("ville", "")
        mag_adr    = magasin.get("adresse", "")
        date_lim   = (don.get("date_limite") or "")[:10]  # Sécurisé contre les timestamps complets
        creneau    = don.get("creneau_retrait") or "—"
        conservation = don.get("condition_conservation") or "—"

        # Formatage date limite
        if date_lim:
            jours = (date.fromisoformat(date_lim) - date.today()).days
            date_aff = date.fromisoformat(date_lim).strftime('%d/%m/%Y')
            if jours < 0:
                date_aff = f"⚠️ Expiré ({date_aff})"
        else:
            date_aff = "—"

        with st.container(border=True):
            col_info, col_action = st.columns([3, 1])

            with col_info:
                # En-tête : magasin + badge urgence
                mag_ligne = f"**{mag_nom}**"
                if mag_ville:
                    mag_ligne += f" · {mag_ville}"
                st.markdown(
                    f"<span style='font-family:Syne,sans-serif; font-size:0.78rem; "
                    f"color:#4D8C1F; font-weight:700; text-transform:uppercase; "
                    f"letter-spacing:0.05em;'>{mag_nom}{' · ' + mag_ville if mag_ville else ''}</span>",
                    unsafe_allow_html=True,
                )

                # Titre produit
                st.markdown(f"### {don.get('produit', '—')}")

                # Détails
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                    f"🏷️ {categorie} &nbsp;·&nbsp; "
                    f"📦 {don.get('quantite', '?')} {unite} &nbsp;·&nbsp; "
                    f"❄️ {conservation}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem;'>"
                    f"📅 {type_lim} : <strong>{date_aff}</strong> &nbsp;·&nbsp; "
                    f"🕐 Retrait : {creneau}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

                if don.get("commentaires"):
                    st.markdown(
                        f"<span style='font-family:Fraunces,serif; color:#8C6A1A; "
                        f"font-size:0.85rem; font-style:italic;'>"
                        f"💬 {don['commentaires']}</span>",
                        unsafe_allow_html=True,
                    )

                # Badge urgence séparé
                urgence = badge_urgence(date_lim)
                if urgence:
                    st.markdown(urgence, unsafe_allow_html=True)

            with col_action:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                # Photo étiquette si disponible
                if don.get("photo_etiquette_url"):
                    st.image(don["photo_etiquette_url"], caption="Étiquette", use_container_width=True)

                # Bouton réserver — ouvre un formulaire inline
                if st.button("🤝 Réserver", key=f"btn_{don['id']}", use_container_width=True, type="primary"):
                    st.session_state[f"reserver_{don['id']}"] = True

        # ── Formulaire de réservation (sous la carte) ──────
        if st.session_state.get(f"reserver_{don['id']}"):
            with st.form(key=f"form_resa_{don['id']}"):
                st.markdown(
                    f"<p style='font-family:Syne,sans-serif; font-weight:700; "
                    f"color:#2A5C1E; margin:0;'>Réserver : {don.get('produit')}</p>",
                    unsafe_allow_html=True,
                )

                if not associations:
                    st.warning("Aucune association trouvée. Crée d'abord une association dans Supabase.")
                    if st.form_submit_button("Fermer"):
                        st.session_state[f"reserver_{don['id']}"] = False
                        st.rerun()
                else:
                    asso_nom = st.selectbox(
                        "Ton association *",
                        options=list(associations.keys()),
                        key=f"asso_{don['id']}",
                    )

                    date_retrait = st.date_input(
                        "Date de retrait prévue *",
                        value=date.today() + timedelta(days=1),
                        min_value=date.today(),
                        key=f"date_{don['id']}",
                    )

                    col_valider, col_annuler = st.columns(2)
                    with col_valider:
                        confirmer = st.form_submit_button("✅ Confirmer la réservation", type="primary", use_container_width=True)
                    with col_annuler:
                        annuler = st.form_submit_button("✖ Annuler", use_container_width=True)

                    if confirmer:
                        try:
                            # 1. Crée la réservation
                            supabase.table("reservations").insert({
                                "don_id":           don["id"],
                                "association_id":   associations[asso_nom],
                                "date_retrait_prevu": str(date_retrait),
                                "statut_retrait_id": get_statut_retrait_prevu_id(),
                            }).execute()

                            # 2. Met à jour le statut du don → réservé
                            supabase.table("dons").update({
                                "statut_don_id": get_statut_reserve_id(),
                            }).eq("id", don["id"]).execute()

                            # 3. Nettoie le cache et ferme le formulaire
                            st.cache_data.clear()
                            st.session_state[f"reserver_{don['id']}"] = False

                            st.success(f"🎉 Don réservé par **{asso_nom}** pour le {date_retrait.strftime('%d/%m/%Y')} !")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Erreur lors de la réservation : {e}")

                    if annuler:
                        st.session_state[f"reserver_{don['id']}"] = False
                        st.rerun()
