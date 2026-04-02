# ============================================================
# vues/fiche_tracabilite.py — Fiche de traçabilité complète
# ============================================================
# Affichée en overlay depuis gerer_reservations et historique_association
# Usage : fiche_tracabilite.show(resa_id)
# ============================================================

import streamlit as st
from datetime import date
from config import supabase


BADGE_BASE = (
    "padding:3px 12px; border-radius:20px; font-size:0.8rem; "
    "font-family:'Syne',sans-serif; font-weight:700; display:inline-block;"
)


@st.cache_data(ttl=60)
def get_fiche(resa_id: str):
    """Charge toutes les données de traçabilité pour une réservation."""
    # Réservation + don + magasin
    resa = (
        supabase.table("reservations")
        .select(
            "id, date_reservation, date_retrait_prevu, date_retrait_reel, "
            "statuts_retrait(libelle), "
            "dons(id, produit, quantite, date_limite, numero_lot, creneau_retrait, "
            "condition_conservation, commentaires, photo_etiquette_url, "
            "categories(libelle), unites(libelle), types_limite(libelle), "
            "magasins(nom, adresse, ville, code_postal, contact_telephone, contact_email))"
        )
        .eq("id", resa_id)
        .single()
        .execute()
    )

    # Contrôle à réception lié au don
    don_id = (resa.data.get("dons") or {}).get("id")
    controle = None
    if don_id:
        res_ctrl = (
            supabase.table("controles_reception")
            .select("*")
            .eq("don_id", don_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        controle = res_ctrl.data[0] if res_ctrl.data else None

    return resa.data, controle


def show(resa_id: str, retour_label: str = "← Retour"):
    """Affiche la fiche de traçabilité complète."""

    # Bouton retour
    if st.button(retour_label, key="retour_fiche"):
        st.session_state["fiche_resa_id"] = None
        st.rerun()

    try:
        resa, controle = get_fiche(resa_id)
    except Exception as e:
        st.error(f"❌ Impossible de charger la fiche : {e}")
        return

    don     = resa.get("dons") or {}
    magasin = don.get("magasins") or {}

    # Dates
    date_lim  = (don.get("date_limite") or "")[:10]
    date_resa = (resa.get("date_reservation") or "")[:10]
    date_prev = (resa.get("date_retrait_prevu") or "")[:10]
    date_reel = (resa.get("date_retrait_reel") or "")[:10]

    def fmt(d): return date.fromisoformat(d).strftime('%d/%m/%Y') if d else "—"

    def info_card(label, valeur):
        st.markdown(
            f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.82rem; margin:0 0 2px;'>{label}</p>"
            f"<p style='font-family:Fraunces,serif; color:#1A2A10; font-size:0.95rem; font-weight:600; margin:0 0 1rem;'>{valeur}</p>",
            unsafe_allow_html=True,
        )

    # En-tête
    st.markdown(f"""
    <div style="border-left:4px solid #2A5C1E; padding:0.5rem 0 0.5rem 1rem; margin-bottom:1.5rem;">
      <p style="font-family:'Syne',sans-serif; font-size:0.78rem; color:#4D8C1F;
                font-weight:700; text-transform:uppercase; letter-spacing:0.08em; margin:0;">
        Fiche de traçabilité
      </p>
      <h2 style="font-family:'Playfair Display',Georgia,serif; color:#2A5C1E;
                 margin:0.2rem 0 0; font-size:1.8rem;">{don.get('produit', '—')}</h2>
    </div>
    """, unsafe_allow_html=True)

    # ── SECTION 1 : Infos produit ──────────────────────────
    st.markdown("### 🥦 Informations produit")
    col1, col2, col3 = st.columns(3)
    with col1:
        info_card("Catégorie", (don.get("categories") or {}).get("libelle", "—"))
        info_card("Conservation", don.get("condition_conservation") or "—")
    with col2:
        unite = (don.get("unites") or {}).get("libelle", "")
        info_card("Quantité", f"{don.get('quantite', '?')} {unite}")
        type_lim = (don.get("types_limite") or {}).get("libelle", "DLC")
        info_card(type_lim, fmt(date_lim))
    with col3:
        info_card("Numéro de lot", don.get("numero_lot") or "—")

    # Motif / commentaires
    if don.get("commentaires"):
        st.markdown(
            f"<div style='background:#F4F0E8; border-radius:12px; padding:0.8rem 1rem; margin-top:0.5rem;'>"
            f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:0;'>"
            f"💬 {don.get('commentaires')}</p></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── SECTION 2 : Magasin & retrait ─────────────────────
    st.markdown("### 🏪 Magasin & retrait")
    col4, col5 = st.columns(2)
    with col4:
        st.markdown(
            f"<p style='font-family:Fraunces,serif; color:#2A5C1E; font-weight:700; margin:0;'>{magasin.get('nom', '—')}</p>"
            f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:0;'>"
            f"{magasin.get('adresse', '')} {magasin.get('code_postal', '')} {magasin.get('ville', '')}</p>"
            f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin-top:4px;'>"
            f"📞 {magasin.get('contact_telephone') or '—'}</p>",
            unsafe_allow_html=True,
        )
    with col5:
        info_card("Créneau de retrait", don.get("creneau_retrait") or "—")
        info_card("Retrait prévu le", fmt(date_prev))
        if date_reel:
            info_card("Retrait effectué le", fmt(date_reel))

    st.divider()

    # ── SECTION 3 : Photos ─────────────────────────────────
    photos_raw = don.get("photo_etiquette_url")
    if photos_raw:
        st.markdown("### 📷 Photos")
        urls = photos_raw.split("|")
        cols_photos = st.columns(len(urls))
        labels = ["Étiquette", "Produit", "Réception"]
        for i, url in enumerate(urls):
            with cols_photos[i]:
                st.image(url, caption=labels[i] if i < len(labels) else f"Photo {i+1}", use_container_width=True)

        if controle and controle.get("photo_reception_url"):
            st.image(controle["photo_reception_url"], caption="Photo réception", use_container_width=True)

        st.divider()

    # ── SECTION 4 : Contrôle à réception ──────────────────
    st.markdown("### ✅ Contrôle à réception")

    if not controle:
        st.info("Aucun contrôle à réception enregistré pour ce don.")
    else:
        # Décision
        decision = controle.get("decision", "—")
        if decision == "accepte":
            st.success("✅ Don **accepté**")
        else:
            st.error(f"❌ Don **refusé** — {controle.get('commentaires') or 'sans motif'}")

        # Checklist
        st.markdown("**Checklist**")
        checks = [
            ("Produit conforme",       controle.get("produit_conforme")),
            ("Emballage intact",       controle.get("emballage_intact")),
            ("Numéro de lot lisible",  controle.get("lot_lisible")),
            ("Date limite cohérente",  controle.get("date_limite_coherente")),
        ]
        col_c1, col_c2 = st.columns(2)
        for i, (label, val) in enumerate(checks):
            col = col_c1 if i % 2 == 0 else col_c2
            with col:
                icone = "✅" if val else "❌"
                st.markdown(
                    f"<p style='font-family:Fraunces,serif; font-size:0.9rem; margin:4px 0;'>"
                    f"{icone} {label}</p>",
                    unsafe_allow_html=True,
                )

        # Températures
        st.markdown("**Températures**")
        col_t1, col_t2 = st.columns(2)
        temp_prod = controle.get("temperature_produit")
        temp_cam  = controle.get("temperature_camion")
        with col_t1:
            conforme = temp_prod is not None and temp_prod < 10
            badge = f'<span style="{BADGE_BASE} background:{"#D6EAD6; color:#1A4A1A" if conforme else "#FDECEA; color:#7B2020"};">{"✅" if conforme else "❌"} Produit : {temp_prod}°C</span>'
            st.markdown(f"<p style='font-family:Fraunces,serif; font-size:0.85rem;'>Température produit</p>{badge}", unsafe_allow_html=True)
        with col_t2:
            conforme = temp_cam is not None and temp_cam < 8
            badge = f'<span style="{BADGE_BASE} background:{"#D6EAD6; color:#1A4A1A" if conforme else "#FDECEA; color:#7B2020"};">{"✅" if conforme else "❌"} Camion : {temp_cam}°C</span>'
            st.markdown(f"<p style='font-family:Fraunces,serif; font-size:0.85rem;'>Température camion</p>{badge}", unsafe_allow_html=True)

        if controle.get("commentaires") and decision != "refuse":
            st.markdown(
                f"<div style='background:#F4F0E8; border-radius:12px; padding:0.8rem 1rem; margin-top:0.5rem;'>"
                f"<p style='font-family:Fraunces,serif; color:#6B7A5E; font-size:0.9rem; margin:0;'>"
                f"💬 {controle.get('commentaires')}</p></div>",
                unsafe_allow_html=True,
            )
