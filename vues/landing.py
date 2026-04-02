# ============================================================
# vues/landing.py — Page d'accueil Foodrop
# ============================================================
# Affichée quand l'utilisateur n'est pas connecté.
# Remplace la page auth.show() comme point d'entrée.
# Intégration dans app.py :
#   from vues import landing
#   landing.show()  ← si pas connecté
# ============================================================

import streamlit as st
from config import supabase


# ----------------------------------------------------------
# KPIs globaux depuis Supabase
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_kpis():
    try:
        # Nombre de dons publiés
        dons = supabase.table("dons").select("id, quantite, statut_don_id").execute().data
        nb_dons = len(dons)

        # Statut récupéré
        statut_rec = (
            supabase.table("statuts_don")
            .select("id")
            .eq("libelle", "recupere")
            .single()
            .execute()
            .data
        )
        id_rec = statut_rec["id"] if statut_rec else None

        # Volume sauvé (somme quantités récupérées)
        recuperes = [d for d in dons if d.get("statut_don_id") == id_rec]
        volume = int(sum(d.get("quantite", 0) for d in recuperes))

        # Nombre de magasins et associations
        nb_mag  = len(supabase.table("magasins").select("id").execute().data)
        nb_asso = len(supabase.table("associations").select("id").execute().data)

        return {
            "nb_dons":  nb_dons,
            "volume":   volume,
            "nb_mag":   nb_mag,
            "nb_asso":  nb_asso,
        }
    except Exception:
        return {"nb_dons": 0, "volume": 0, "nb_mag": 0, "nb_asso": 0}


# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------

def show():
    """Page d'accueil publique — non connecté."""

    # CSS spécifique landing (complète le CSS global de app.py)
    st.markdown("""
    <style>
      /* Cache le header Streamlit et supprime le padding du haut */
      [data-testid="stHeader"] { display: none; }
      [data-testid="stAppViewContainer"] > section:first-child { padding-top: 0 !important; }
      .block-container { padding-top: 0.5rem !important; }

      .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(2.2rem, 5vw, 3.8rem);
        font-weight: 800;
        color: #2A5C1E;
        line-height: 1.15;
        margin: 0;
      }
      .hero-title .accent { color: #A8D455; }

      .hero-sub {
        font-family: 'Fraunces', serif;
        font-size: 1.15rem;
        color: #6B7A5E;
        margin-top: 1rem;
        line-height: 1.7;
        max-width: 540px;
      }

      .btn-primaire {
        display: inline-block;
        background: #2A5C1E;
        color: white !important;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        padding: 0.8rem 2rem;
        border-radius: 50px;
        text-decoration: none;
        transition: background 0.2s;
        cursor: pointer;
      }
      .btn-secondaire {
        display: inline-block;
        background: #D4A820;
        color: white !important;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        padding: 0.8rem 2rem;
        border-radius: 50px;
        text-decoration: none;
        cursor: pointer;
      }
      .btn-outline {
        display: inline-block;
        background: transparent;
        color: #2A5C1E !important;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        padding: 0.75rem 1.8rem;
        border-radius: 50px;
        border: 2px solid #2A5C1E;
        text-decoration: none;
        cursor: pointer;
      }

      .kpi-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem 1rem;
        text-align: center;
        border: 1px solid #E0DDD5;
        box-shadow: 0 2px 12px rgba(42,92,30,0.06);
      }
      .kpi-number {
        font-family: 'Syne', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        color: #2A5C1E;
        margin: 0;
        line-height: 1;
      }
      .kpi-label {
        font-family: 'Fraunces', serif;
        font-size: 0.88rem;
        color: #6B7A5E;
        margin-top: 6px;
      }

      .feature-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #E0DDD5;
        height: 100%;
      }
      .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
      }
      .feature-title {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: #2A5C1E;
        margin: 0 0 0.5rem;
      }
      .feature-desc {
        font-family: 'Fraunces', serif;
        font-size: 0.9rem;
        color: #6B7A5E;
        line-height: 1.6;
        margin: 0;
      }

      .profile-card {
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
      }
      .profile-card.magasin  { background: #2A5C1E; }
      .profile-card.asso     { background: #F4F0E8; border: 2px solid #2A5C1E; }

      .section-title {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.8rem;
        color: #2A5C1E;
        margin-bottom: 0.5rem;
      }
      .section-sub {
        font-family: 'Fraunces', serif;
        color: #6B7A5E;
        font-size: 1rem;
        margin-bottom: 2rem;
      }

      .divider-green {
        border: none;
        border-top: 2px solid #E8F5D6;
        margin: 2.5rem 0;
      }
    </style>
    """, unsafe_allow_html=True)

    # ── NAVBAR : Logo à gauche + boutons à droite ─────────
    import base64, pathlib

    logo_svg = pathlib.Path("assets/logo.svg").read_text()
    logo_b64 = base64.b64encode(logo_svg.encode()).decode()

    hero_bytes = pathlib.Path("assets/hero.png").read_bytes()
    hero_b64   = base64.b64encode(hero_bytes).decode()

    # Vérifie si un bouton navbar a été cliqué via query_params
    params = st.query_params
    if params.get("action"):
        st.session_state.landing_action = params.get("action")
        st.query_params.clear()
        st.rerun()

    # Navbar HTML — les boutons utilisent ?action= pour déclencher la navigation
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding:0.5rem 0 0.8rem; flex-wrap:wrap; gap:1rem;">
      <img src="data:image/svg+xml;base64,{logo_b64}"
           style="height:100px; width:auto;" alt="Foodrop">
      <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end;">
        <a href="?action=inscription_association" class="navbar-btn"
          style="background:#2A5C1E; color:white !important; border:none; border-radius:50px;
                 font-family:'Syne',sans-serif; font-weight:700; font-size:0.88rem;
                 padding:0.6rem 1.2rem; cursor:pointer; white-space:nowrap;
                 text-decoration:none; display:inline-block;">
          🤝 Inscrire mon association
        </a>
        <a href="?action=inscription_magasin" class="navbar-btn"
          style="background:#D4A820; color:white !important; border:none; border-radius:50px;
                 font-family:'Syne',sans-serif; font-weight:700; font-size:0.88rem;
                 padding:0.6rem 1.2rem; cursor:pointer; white-space:nowrap;
                 text-decoration:none; display:inline-block;">
          🏪 Inscrire mon magasin
        </a>
        <a href="?action=connexion" class="navbar-btn-outline"
          style="background:transparent; color:#2A5C1E !important; border:2px solid #2A5C1E;
                 border-radius:50px; font-family:'Syne',sans-serif; font-weight:700;
                 font-size:0.88rem; padding:0.55rem 1.2rem; cursor:pointer; white-space:nowrap;
                 text-decoration:none; display:inline-block;">
          🔑 Me connecter
        </a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
      .navbar-btn { color: white !important; }
      .navbar-btn-outline { color: #2A5C1E !important; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <style>
      .hero-titre {{
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: clamp(2rem, 4vw, 3.2rem) !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        text-shadow: none !important;
      }}
    </style>
    <div style="position:relative; width:100%; border-radius:16px;
                overflow:hidden; margin:0.5rem 0 0;">
      <img src="data:image/png;base64,{hero_b64}"
           style="width:100%; height:440px; object-fit:cover; object-position:center; display:block;">
      <div style="position:absolute; inset:0;
                  background:linear-gradient(90deg, rgba(0,0,0,0.55) 0%,
                  rgba(0,0,0,0.20) 60%, transparent 100%);"></div>
      <div style="position:absolute; top:50%; left:3.5rem; transform:translateY(-50%); max-width:540px;">
        <p class="hero-titre">Rien ne se perd,<br>tout se partage.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='divider-green'>", unsafe_allow_html=True)

    # ── KPIs ───────────────────────────────────────────────
    kpis = get_kpis()

    st.markdown("""
    <p style="font-family:'Playfair Display',Georgia,serif; font-weight:700; font-size:1.8rem;
              color:#2A5C1E; text-align:center; margin-bottom:0.4rem;">Foodrop en chiffres</p>
    <p class="section-sub" style="text-align:center;">Des résultats concrets, mis à jour en temps réel.</p>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, kpis["nb_dons"],  "Dons publiés"),
        (k2, kpis["volume"],   "Unités sauvées"),
        (k3, kpis["nb_mag"],   "Magasins partenaires"),
        (k4, kpis["nb_asso"],  "Associations actives"),
    ]
    for col, val, label in kpi_data:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <p class="kpi-number">{val}</p>
              <p class="kpi-label">{label}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='divider-green'>", unsafe_allow_html=True)

    # ── COMMENT ÇA MARCHE ──────────────────────────────────
    st.markdown("""
    <p style="font-family:'Playfair Display',Georgia,serif; font-weight:700; font-size:1.8rem;
              color:#2A5C1E; text-align:center; margin-bottom:0.4rem;">Comment ça marche ?</p>
    <p class="section-sub" style="text-align:center;">3 étapes simples pour sauver des produits du gaspillage.</p>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    features = [
        (f1, "📦", "Le magasin publie", "En quelques secondes, le magasin publie un lot d'invendus avec les infos produit, la DLC et le créneau de retrait."),
        (f2, "🔍", "L'association réserve", "Les associations voient les dons disponibles en temps réel et réservent le lot qui leur convient, avec le créneau souhaité."),
        (f3, "✅", "Le contrôle valide", "À la récupération, l'association remplit une checklist qualité. Tout est tracé pour garantir la conformité."),
    ]
    for col, icon, titre, desc in features:
        with col:
            st.markdown(f"""
            <div class="feature-card">
              <div class="feature-icon">{icon}</div>
              <p class="feature-title" style="font-family:'Playfair Display',Georgia,serif; font-weight:700;">{titre}</p>
              <p class="feature-desc">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='divider-green'>", unsafe_allow_html=True)

    # ── DEUX PROFILS ───────────────────────────────────────
    st.markdown("""
    <p style="font-family:'Playfair Display',Georgia,serif; font-weight:700; font-size:1.8rem;
              color:#2A5C1E; text-align:center; margin-bottom:0.4rem;">Rejoins Foodrop</p>
    <p class="section-sub" style="text-align:center;">Une plateforme, deux profils.</p>
    """, unsafe_allow_html=True)

    p1, p2 = st.columns(2)

    with p1:
        st.markdown("""
        <div style="background:transparent; border-radius:20px; padding:2rem; text-align:center;
                    border: 2px solid #D4A820;">
          <p style="font-size:2.5rem; margin:0;">🏪</p>
          <p style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.3rem;
                    color:#D4A820; margin:0.75rem 0 0.5rem;">Je suis un magasin</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E;
                    font-size:0.92rem; line-height:1.6; margin-bottom:1.5rem;">
            Publie tes invendus en quelques clics. Réduis ton gaspillage
            et contribue à ta communauté locale.
          </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏪 Inscrire mon magasin →", key="cta_mag2", use_container_width=True, type="primary"):
            st.session_state.landing_action = "inscription_magasin"
            st.rerun()

    with p2:
        st.markdown("""
        <div style="background:#F4F0E8; border-radius:20px; padding:2rem; text-align:center;
                    border: 2px solid #2A5C1E;">
          <p style="font-size:2.5rem; margin:0;">🤝</p>
          <p style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.3rem;
                    color:#2A5C1E; margin:0.75rem 0 0.5rem;">Je suis une association</p>
          <p style="font-family:'Fraunces',serif; color:#6B7A5E;
                    font-size:0.92rem; line-height:1.6; margin-bottom:1.5rem;">
            Accède aux dons disponibles près de toi. Réserve, récupère
            et contrôle la qualité en toute simplicité.
          </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🤝 Inscrire mon association →", key="cta_asso2", use_container_width=True):
            st.session_state.landing_action = "inscription_association"
            st.rerun()

    # ── FOOTER ─────────────────────────────────────────────
    st.markdown(f"""
    <hr class='divider-green'>
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding-bottom:2rem; flex-wrap:wrap; gap:1rem;">
      <img src="data:image/svg+xml;base64,{logo_b64}"
           style="height:48px; width:auto;" alt="Foodrop">
      <p style="font-family:'Fraunces',serif; color:#6B7A5E; font-size:0.85rem; margin:0;">
        Fait avec amour à UniLaSalle Beauvais ❤️
      </p>
    </div>
    """, unsafe_allow_html=True)
