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
            "magasin_id, "
            "condition_conservation, creneau_retrait, commentaires, "
            "numero_lot, photo_etiquette_url, "
            "categories(libelle), unites(libelle), "
            "types_limite(libelle), magasins(nom, ville, adresse)"
        )
        .eq("statut_don_id", statut_id)
        .order("date_limite", desc=False)
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

    # ── CARTE DES MAGASINS ─────────────────────────────────
    st.markdown("### 🗺️ Carte des magasins")

    try:
        import folium
        from streamlit_folium import st_folium
        from geopy.geocoders import Nominatim
        from geopy.distance import geodesic

        # Barre de recherche + périmètre
        col_adr, col_km = st.columns([3, 1])
        with col_adr:
            adresse_recherche = st.text_input(
                "📍 Mon adresse",
                placeholder="Ex : 19 Rue Pierre Waguet, Beauvais",
                key="carte_adresse",
            )
        with col_km:
            perimetre_km = st.selectbox(
                "Périmètre",
                options=[5, 10, 20, 50, 100],
                index=1,
                key="carte_perimetre",
                format_func=lambda x: f"{x} km",
            )

        # Charge les magasins avec leurs dons disponibles
        magasins_raw = (
            supabase.table("magasins")
            .select("id, nom, adresse, ville, code_postal")
            .execute()
            .data
        )

        # Géocode les adresses des magasins
        geolocator = Nominatim(user_agent="foodrop_app", timeout=5)

        @st.cache_data(ttl=3600)
        def geocode_adresse(adresse_str):
            try:
                loc = Nominatim(user_agent="foodrop_app", timeout=5).geocode(adresse_str)
                return (loc.latitude, loc.longitude) if loc else None
            except Exception:
                return None

        # Géocode l'adresse de recherche si fournie
        coord_recherche = None
        if adresse_recherche.strip():
            coord_recherche = geocode_adresse(adresse_recherche.strip())
            if not coord_recherche:
                st.warning("⚠️ Adresse introuvable. Essaie d'être plus précis.")

        # Centre de la carte
        if coord_recherche:
            centre = coord_recherche
        else:
            centre = (49.4431, 2.0833)  # Beauvais par défaut

        # Crée la carte
        m = folium.Map(location=centre, zoom_start=11 if coord_recherche else 8,
                       tiles="CartoDB positron")

        # Cercle de périmètre si adresse fournie
        if coord_recherche:
            folium.Circle(
                location=coord_recherche,
                radius=perimetre_km * 1000,
                color="#D4A820",
                fill=True,
                fill_color="#D4A820",
                fill_opacity=0.08,
                weight=2,
            ).add_to(m)
            folium.Marker(
                location=coord_recherche,
                popup="📍 Ma position",
                icon=folium.Icon(color="orange", icon="home", prefix="fa"),
            ).add_to(m)

        # Compte les dons disponibles par magasin
        dons_par_magasin = {}
        for don in tous_les_dons:
            mag_id = don.get("magasin_id")
            if mag_id:
                dons_par_magasin[mag_id] = dons_par_magasin.get(mag_id, 0) + 1

        # Place les marqueurs
        magasins_affiches = 0
        for mag in magasins_raw:
            adresse_mag = f"{mag.get('adresse', '')}, {mag.get('code_postal', '')} {mag.get('ville', '')}"
            coords = geocode_adresse(adresse_mag)
            if not coords:
                continue

            # Filtre par périmètre si adresse fournie
            if coord_recherche:
                dist = geodesic(coord_recherche, coords).km
                if dist > perimetre_km:
                    continue

            nb_dons = dons_par_magasin.get(mag["id"], 0)
            couleur = "green" if nb_dons > 0 else "gray"
            label   = f"🏪 {mag['nom']}<br>📦 {nb_dons} don(s) disponible(s)<br>📍 {mag.get('ville', '')}"

            folium.Marker(
                location=coords,
                popup=folium.Popup(label, max_width=200),
                tooltip=f"{mag['nom']} — {nb_dons} don(s)",
                icon=folium.Icon(color=couleur, icon="shopping-cart", prefix="fa"),
            ).add_to(m)
            magasins_affiches += 1

        st_folium(m, use_container_width=True, height=380, returned_objects=[])

        if coord_recherche:
            st.caption(f"🔍 {magasins_affiches} magasin(s) dans un rayon de {perimetre_km} km")

    except ImportError:
        st.info("📦 Installe `streamlit-folium` et `geopy` pour afficher la carte.")
    except Exception as e:
        st.warning(f"⚠️ Carte indisponible : {e}")

    st.divider()

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

                if not st.session_state.get("entite_id"):
                    st.warning("Session invalide. Reconnecte-toi.")
                    if st.form_submit_button("Fermer"):
                        st.session_state[f"reserver_{don['id']}"] = False
                        st.rerun()
                else:
                    asso_id = st.session_state["entite_id"]

                    col_date, col_creneau = st.columns(2)

                    # Extrait jours et plages du créneau magasin
                    # Format : "Lundi, Mardi · 08h00 - 09h00, 14h00 - 15h00"
                    JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                    JOURS_INDEX   = {j: i for i, j in enumerate(JOURS_SEMAINE)}

                    jours_magasin = []
                    plages_magasin = []
                    if creneau and creneau != "—" and "·" in creneau:
                        partie_jours  = creneau.split("·")[0].strip()
                        partie_plages = creneau.split("·")[1].strip()
                        jours_magasin  = [j.strip() for j in partie_jours.split(",") if j.strip() in JOURS_INDEX]
                        plages_magasin = [p.strip() for p in partie_plages.split(",") if p.strip()]

                    if not jours_magasin:
                        jours_magasin = JOURS_SEMAINE
                    if not plages_magasin:
                        plages_magasin = ["08h00 - 09h00", "14h00 - 15h00"]

                    with col_date:
                        jour_choisi = st.selectbox(
                            "Jour de retrait *",
                            options=jours_magasin,
                            key=f"jour_{don['id']}",
                        )
                        # Calcule la prochaine date correspondant au jour choisi
                        idx_cible = JOURS_INDEX[jour_choisi]
                        aujourd_hui = date.today()
                        delta = (idx_cible - aujourd_hui.weekday()) % 7
                        if delta == 0:
                            delta = 7  # Pas aujourd'hui, la semaine prochaine
                        date_retrait = aujourd_hui + timedelta(days=delta)
                        st.markdown(
                            f"<span style='font-family:Fraunces,serif; font-size:0.82rem; color:#4D8C1F;'>"
                            f"📅 Date : <strong>{date_retrait.strftime('%d/%m/%Y')}</strong></span>",
                            unsafe_allow_html=True,
                        )

                    with col_creneau:
                        creneau_choisi = st.selectbox(
                            "Plage horaire *",
                            options=plages_magasin,
                            key=f"creneau_{don['id']}",
                        )

                    col_valider, col_annuler = st.columns(2)
                    with col_valider:
                        confirmer = st.form_submit_button("✅ Confirmer la réservation", type="primary", use_container_width=True)
                    with col_annuler:
                        annuler = st.form_submit_button("✖ Annuler", use_container_width=True)

                    if confirmer:
                        try:
                            heure_debut = creneau_choisi[:5].replace("h", ":")
                            date_retrait_str = f"{date_retrait} {heure_debut}:00"

                            supabase.table("reservations").insert({
                                "don_id":             don["id"],
                                "association_id":     asso_id,
                                "date_retrait_prevu": date_retrait_str,
                                "statut_retrait_id":  get_statut_retrait_prevu_id(),
                            }).execute()

                            supabase.table("dons").update({
                                "statut_don_id": get_statut_reserve_id(),
                            }).eq("id", don["id"]).execute()

                            st.cache_data.clear()
                            st.session_state[f"reserver_{don['id']}"] = False

                            st.success(
                                f"🎉 Don réservé pour le {date_retrait.strftime('%d/%m/%Y')} "
                                f"entre {creneau_choisi} !"
                            )
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Erreur lors de la réservation : {e}")

                    if annuler:
                        st.session_state[f"reserver_{don['id']}"] = False
                        st.rerun()
