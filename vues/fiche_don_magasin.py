# ============================================================
# vues/fiche_don_magasin.py — Fiche détail d'un don (Magasin)
# ============================================================
# Affichée depuis gerer_dons et historique_magasin.
# Inclut toutes les infos de traçabilité + formulaire de modif.
# Usage : fiche_don_magasin.show(don_id, retour_label)
# ============================================================

import streamlit as st
from datetime import date
from config import supabase


BADGE_BASE = (
    "padding:3px 12px; border-radius:20px; font-size:0.8rem; "
    "font-family:'Syne',sans-serif; font-weight:700; display:inline-block;"
)

MOTIFS_DON = [
    "Date courte", "Mauvais calibrage", "Emballage abîmé (non ouvert)",
    "Surproduction", "Retour magasin", "Fin de gamme", "Autre",
]

PLAGES_HORAIRES = [
    "07h00 - 08h00", "08h00 - 09h00", "09h00 - 10h00",
    "10h00 - 11h00", "11h00 - 12h00", "12h00 - 13h00",
    "14h00 - 15h00", "15h00 - 16h00", "16h00 - 17h00",
    "17h00 - 18h00", "18h00 - 19h00", "19h00 - 20h00",
]


@st.cache_data(ttl=60)
def get_fiche_don(don_id: str):
    don = (
        supabase.table("dons")
        .select(
            "id, produit, quantite, date_limite, numero_lot, creneau_retrait, "
            "condition_conservation, commentaires, photo_etiquette_url, "
            "date_publication, "
            "categories(id, libelle), unites(id, libelle), "
            "types_limite(libelle), statuts_don(libelle), "
            "reservations(id, date_retrait_prevu, date_retrait_reel, "
            "associations(nom, contact_email, contact_telephone))"
        )
        .eq("id", don_id)
        .single()
        .execute()
    )
    # Contrôle chargé séparément (lié à don_id, pas à reservations)
    ctrl = (
        supabase.table("controles_reception")
        .select("*")
        .eq("don_id", don_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    controle = ctrl.data[0] if ctrl.data else None
    return don.data, controle


@st.cache_data(ttl=300)
def get_categories():
    res = supabase.table("categories").select("id, libelle").order("libelle").execute()
    return {c["libelle"]: c["id"] for c in res.data}

@st.cache_data(ttl=300)
def get_unites():
    res = supabase.table("unites").select("id, libelle").execute()
    return {u["libelle"]: u["id"] for u in res.data}


def show(don_id: str, retour_label: str = "← Retour", modifiable: bool = True):

    if st.button(retour_label, key="retour_fiche_mag"):
        st.session_state["fiche_don_id"] = None
        st.rerun()

    try:
        don, controle = get_fiche_don(don_id)
    except Exception as e:
        st.error(f"❌ Impossible de charger la fiche : {e}")
        return

    statut_lib  = (don.get("statuts_don") or {}).get("libelle", "—")
    categorie   = (don.get("categories") or {}).get("libelle", "—")
    unite       = (don.get("unites") or {}).get("libelle", "")
    type_lim    = (don.get("types_limite") or {}).get("libelle", "DLC")
    date_lim    = (don.get("date_limite") or "")[:10]
    date_pub    = (don.get("date_publication") or "")[:10]
    reservations = don.get("reservations") or []
    resa        = reservations[0] if reservations else None
    asso        = (resa.get("associations") or {}) if resa else {}

    def fmt(d): return date.fromisoformat(d).strftime('%d/%m/%Y') if d else "—"

    def info_card(label, valeur):
        st.markdown(
            f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.82rem; margin:0 0 2px;'>{label}</p>"
            f"<p style='font-family:Fraunces,serif; color:#1A2A10; font-size:0.95rem; font-weight:600; margin:0 0 1rem;'>{valeur}</p>",
            unsafe_allow_html=True,
        )

    # Badges statut
    STATUT_STYLES = {
        "disponible": (f"{BADGE_BASE} background:#E8F5D6; color:#1A4A10;", "● Disponible"),
        "reserve":    (f"{BADGE_BASE} background:#FFF3CD; color:#8C6A1A;", "● Réservé"),
        "recupere":   (f"{BADGE_BASE} background:#D6EAD6; color:#1A4A1A;", "● Récupéré"),
        "refuse":     (f"{BADGE_BASE} background:#FDECEA; color:#7B2020;", "● Refusé"),
        "archive":    (f"{BADGE_BASE} background:#EBEBEB; color:#555555;", "● Archivé"),
    }
    style_statut, label_statut = STATUT_STYLES.get(statut_lib, (f"{BADGE_BASE} background:#EBEBEB; color:#555;", statut_lib))

    # En-tête
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                border-left:4px solid #2A5C1E; padding:0.5rem 0 0.5rem 1rem; margin-bottom:1.5rem;">
      <div>
        <p style="font-family:'Syne',sans-serif; font-size:0.78rem; color:#4D8C1F;
                  font-weight:700; text-transform:uppercase; letter-spacing:0.08em; margin:0;">
          Fiche don
        </p>
        <h2 style="font-family:'Playfair Display',Georgia,serif; color:#2A5C1E;
                   margin:0.2rem 0 0; font-size:1.8rem;">{don.get('produit', '—')}</h2>
      </div>
      <span style="{style_statut}">{label_statut}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── SECTION 1 : Infos produit ──────────────────────────
    st.markdown("### 🥦 Informations produit")
    col1, col2, col3 = st.columns(3)
    with col1:
        info_card("Catégorie", categorie)
        info_card("Conservation", don.get("condition_conservation") or "—")
    with col2:
        info_card("Quantité", f"{don.get('quantite', '?')} {unite}")
        info_card(type_lim, fmt(date_lim))
    with col3:
        info_card("Numéro de lot", don.get("numero_lot") or "—")
        info_card("Publié le", fmt(date_pub))

    if don.get("commentaires"):
        st.markdown(
            f"<div style='background:#F4F0E8; border-radius:12px; padding:0.8rem 1rem; margin-top:0.5rem;'>"
            f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:0;'>"
            f"💬 {don.get('commentaires')}</p></div>",
            unsafe_allow_html=True,
        )

    # ── SECTION 2 : Photos ─────────────────────────────────
    photos_raw = don.get("photo_etiquette_url")
    if photos_raw:
        st.divider()
        st.markdown("### 📷 Photos")
        urls = photos_raw.split("|")
        cols_photos = st.columns(len(urls))
        labels = ["Étiquette", "Produit"]
        for i, url in enumerate(urls):
            with cols_photos[i]:
                st.image(url, caption=labels[i] if i < len(labels) else f"Photo {i+1}", use_container_width=True)

    # ── SECTION 3 : Réservation & association ─────────────
    if resa:
        st.divider()
        st.markdown("### 🤝 Réservation")
        col4, col5 = st.columns(2)
        with col4:
            st.markdown(
                f"<p style='font-family:Fraunces,serif; color:#2A5C1E; font-weight:700; margin:0;'>"
                f"{asso.get('nom', '—')}</p>"
                f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:4px 0 0;'>"
                f"📞 {asso.get('contact_telephone') or '—'}</p>"
                f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:2px 0 0;'>"
                f"✉️ {asso.get('contact_email') or '—'}</p>",
                unsafe_allow_html=True,
            )
        with col5:
            date_prev = (resa.get("date_retrait_prevu") or "")[:10]
            date_reel = (resa.get("date_retrait_reel") or "")[:10]
            info_card("Retrait prévu le", fmt(date_prev))
            if date_reel:
                info_card("Retrait effectué le", fmt(date_reel))

    # ── SECTION 4 : Contrôle à réception ──────────────────
    if controle:
        st.divider()
        st.markdown("### ✅ Contrôle à réception")
        decision = controle.get("decision", "—")
        if decision == "accepte":
            st.success("✅ Don **accepté**")
        else:
            st.error(f"❌ Don **refusé** — {controle.get('commentaires') or 'sans motif'}")

        col_c1, col_c2 = st.columns(2)
        checks = [
            ("Produit conforme",      controle.get("produit_conforme")),
            ("Emballage intact",      controle.get("emballage_intact")),
            ("Numéro de lot lisible", controle.get("lot_lisible")),
            ("Date limite cohérente", controle.get("date_limite_coherente")),
        ]
        for i, (label, val) in enumerate(checks):
            col = col_c1 if i % 2 == 0 else col_c2
            with col:
                st.markdown(
                    f"<p style='font-family:Fraunces,serif; font-size:0.9rem; margin:4px 0;'>"
                    f"{'✅' if val else '❌'} {label}</p>",
                    unsafe_allow_html=True,
                )

        col_t1, col_t2 = st.columns(2)
        temp_prod = controle.get("temperature_produit")
        temp_cam  = controle.get("temperature_camion")
        with col_t1:
            ok = temp_prod is not None and temp_prod < 10
            st.markdown(
                f"<p style='font-family:Fraunces,serif; font-size:0.85rem;'>Température produit</p>"
                f'<span style="{BADGE_BASE} background:{"#D6EAD6; color:#1A4A1A" if ok else "#FDECEA; color:#7B2020"};">'
                f"{'✅' if ok else '❌'} {temp_prod}°C</span>",
                unsafe_allow_html=True,
            )
        with col_t2:
            ok = temp_cam is not None and temp_cam < 8
            st.markdown(
                f"<p style='font-family:Fraunces,serif; font-size:0.85rem;'>Température camion</p>"
                f'<span style="{BADGE_BASE} background:{"#D6EAD6; color:#1A4A1A" if ok else "#FDECEA; color:#7B2020"};">'
                f"{'✅' if ok else '❌'} {temp_cam}°C</span>",
                unsafe_allow_html=True,
            )
        if controle.get("photo_reception_url"):
            st.image(controle["photo_reception_url"], caption="Photo réception", use_container_width=True)

    # ── SECTION 5 : Modifier le don ────────────────────────
    if modifiable and statut_lib == "disponible":
        st.divider()
        st.markdown("### ✏️ Modifier le don")

        categories = get_categories()
        unites     = get_unites()

        with st.form("form_modif_fiche"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                nouvelle_quantite = st.number_input(
                    "Quantité", min_value=1, step=1,
                    value=int(don.get("quantite", 1)), format="%d"
                )
                nouveau_lot = st.text_input(
                    "Numéro de lot", value=don.get("numero_lot") or ""
                )
            with col_m2:
                nouvelle_dlc = st.date_input(
                    "Date limite",
                    value=date.fromisoformat(date_lim) if date_lim else date.today(),
                    min_value=date.today()
                )
                nouvelles_plages = st.multiselect(
                    "Plages horaires",
                    options=PLAGES_HORAIRES,
                    default=[p for p in PLAGES_HORAIRES if p in (don.get("creneau_retrait") or "")],
                )

            nouveau_commentaire = st.text_area(
                "Commentaires", value=don.get("commentaires") or "", height=80
            )

            sauvegarder = st.form_submit_button("💾 Sauvegarder les modifications", use_container_width=True)

        if sauvegarder:
            try:
                supabase.table("dons").update({
                    "quantite":        int(nouvelle_quantite),
                    "numero_lot":      nouveau_lot.strip() or None,
                    "date_limite":     nouvelle_dlc.isoformat(),
                    "creneau_retrait": ", ".join(nouvelles_plages) if nouvelles_plages else None,
                    "commentaires":    nouveau_commentaire.strip() or None,
                }).eq("id", don_id).execute()
                st.cache_data.clear()
                st.success("✅ Don mis à jour !")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
