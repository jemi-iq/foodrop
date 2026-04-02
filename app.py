# ============================================================
# app.py — Point d'entrée principal de Foodrop
# ============================================================

import streamlit as st

st.set_page_config(
    page_title="Foodrop",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Fraunces:ital,wght@0,300;0,600;1,300;1,600&display=swap');
  :root {
    --foret:#2A5C1E; --herbe:#4D8C1F; --lime:#A8D455;
    --ble:#D4A820; --marron:#8C6A1A; --ivoire:#F4F0E8;
    --texte:#1A2A10; --gris:#6B7A5E;
  }
  .stApp { background-color: var(--ivoire); }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] { background-color: var(--foret) !important; }
  [data-testid="stSidebar"] * { color: white !important; }

  /* Navigation sans radio buttons, effet grossissement */
  [data-testid="stSidebar"] .stRadio > div { gap: 0 !important; }
  [data-testid="stSidebar"] .stRadio label {
    font-family:'Syne',sans-serif; font-size:0.95rem; padding:8px 12px;
    cursor:pointer; border-radius:8px;
    transition: font-size 0.15s, background 0.15s; display:block; width:100%;
  }
  [data-testid="stSidebar"] .stRadio label:hover {
    font-size:1.05rem; background:rgba(255,255,255,0.1);
  }
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
    display: none !important;
  }

  /* ── Titres ── */
  h1, h2, h3 { font-family:'Syne',sans-serif !important; color:var(--foret) !important; }

  /* ── Tous les boutons normaux → forêt ── */
  .stButton > button {
    background-color: var(--foret) !important; color: white !important;
    border: none !important; border-radius: 50px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    padding: 0.5rem 1.5rem !important; transition: background 0.2s !important;
  }
  .stButton > button:hover { background-color: var(--herbe) !important; }
  .stButton > button p { color: white !important; }

  /* ── Boutons dans formulaires (form_submit_button) → forêt ── */
  .stFormSubmitButton > button {
    background-color: var(--foret) !important; color: white !important;
    border: none !important; border-radius: 50px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    padding: 0.5rem 1.5rem !important; transition: background 0.2s !important;
    width: 100% !important;
  }
  .stFormSubmitButton > button:hover { background-color: var(--herbe) !important; }
  .stFormSubmitButton > button p { color: white !important; }

  /* Boutons type="primary" → blé */
  .stButton > button[kind="primary"],
  .stFormSubmitButton > button[kind="primary"] {
    background-color: var(--ble) !important; color: white !important;
  }
  .stButton > button[kind="primary"]:hover,
  .stFormSubmitButton > button[kind="primary"]:hover {
    background-color: var(--marron) !important;
  }

  /* Bouton Se déconnecter sidebar → blé */
  [data-testid="stSidebar"] .stButton > button {
    background-color: var(--ble) !important; color: white !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    background-color: var(--marron) !important;
  }

  /* ── Checkboxes cochées → blé ── */
  [data-baseweb="checkbox"] [data-checked="true"] > div:first-child {
    background-color: var(--ble) !important; border-color: var(--ble) !important;
  }
  input[type="checkbox"]:checked { accent-color: var(--ble) !important; }

  /* ── Multiselect tags → blé ── */
  [data-baseweb="tag"] { background-color: var(--ble) !important; }
  [data-baseweb="tag"] span { color: white !important; }

  /* ── Divers ── */
  .foodrop-card { background:white; border-radius:16px; padding:1.2rem; margin-bottom:1rem; border:1px solid #E0DDD5; box-shadow:0 2px 8px rgba(42,92,30,0.06); }
  p, li, label { font-family:'Fraunces',serif; color:var(--texte); }
</style>
""", unsafe_allow_html=True)

from vues import auth
from vues import landing
from vues import bienvenue
from vues import creer_don
from vues import dashboard_magasin
from vues import chercher_don
from vues import dashboard_association
from vues import controle_reception
from vues import gerer_dons
from vues import gerer_reservations
from vues import historique_magasin
from vues import historique_association
from vues import mes_informations

if "connecte" not in st.session_state:
    st.session_state.connecte         = False
    st.session_state.user_id          = None
    st.session_state.user_email       = None
    st.session_state.type_utilisateur = None
    st.session_state.entite_id        = None
    st.session_state.bienvenue        = False
    st.session_state.page_cible       = None
    st.session_state.fiche_resa_id    = None
    st.session_state.fiche_don_id     = None

if "landing_action" not in st.session_state:
    st.session_state.landing_action = None

if not st.session_state.connecte:
    if st.session_state.landing_action is None:
        landing.show()
        st.stop()
    else:
        auth.show(onglet_actif=st.session_state.landing_action)
        st.stop()

# ── Page de bienvenue après inscription ────────────────────
if st.session_state.get("bienvenue"):
    bienvenue.show()
    st.stop()

type_u = st.session_state.type_utilisateur

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0 0.5rem;">
      <span style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:white;">
        food<span style="color:#A8D455;">rop</span>
      </span>
    </div>
    <hr style="border-color:rgba(255,255,255,0.2); margin-bottom:0.5rem;">
    """, unsafe_allow_html=True)

    from config import supabase as _sb
    entite_id = st.session_state.get("entite_id")
    nom_entite = ""
    try:
        if type_u == "magasin":
            res = _sb.table("magasins").select("nom").eq("id", entite_id).single().execute()
        else:
            res = _sb.table("associations").select("nom").eq("id", entite_id).single().execute()
        nom_entite = res.data.get("nom", "") if res.data else ""
    except Exception:
        nom_entite = st.session_state.get("user_email", "")

    st.markdown(
        f"<div style='text-align:center; padding:1rem 0 0.8rem; display:flex; flex-direction:column; align-items:center; justify-content:center;'>"
        f"<p style='font-size:0.88rem; color:rgba(255,255,255,0.75); font-family:Syne,sans-serif; font-weight:700; margin:0;'>Bienvenue</p>"
        f"<p style='font-size:0.88rem; color:white; font-family:Syne,sans-serif; font-weight:700; margin:0;'>"
        f"{'🏪' if type_u == 'magasin' else '🤝'} {nom_entite}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:rgba(255,255,255,0.2); margin-bottom:0.5rem;'>", unsafe_allow_html=True)

    if type_u == "magasin":
        pages_mag = ["🏠 Dashboard","➕ Créer un don","📦 Gérer les dons","📋 Historique","👤 Mes informations"]
        idx = pages_mag.index(st.session_state.page_cible) if st.session_state.get("page_cible") in pages_mag else 0
        st.session_state.page_cible = None
        page = st.radio("Navigation", pages_mag, index=idx)
    else:
        pages_asso = ["🏠 Dashboard","🔍 Chercher un don","📦 Mes réservations","📋 Historique","👤 Mes informations"]
        idx = pages_asso.index(st.session_state.page_cible) if st.session_state.get("page_cible") in pages_asso else 0
        st.session_state.page_cible = None
        page = st.radio("Navigation", pages_asso, index=idx)

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem; color:rgba(255,255,255,0.4); text-align:center;'>FAQ · Mentions légales</p>", unsafe_allow_html=True)
    if st.button("🚪 Se déconnecter", use_container_width=True):
        auth.deconnecter()

if type_u == "magasin":
    if page == "🏠 Dashboard":           dashboard_magasin.show()
    elif page == "➕ Créer un don":       creer_don.show()
    elif page == "📦 Gérer les dons":     gerer_dons.show()
    elif page == "📋 Historique":         historique_magasin.show()
    elif page == "👤 Mes informations":   mes_informations.show()

elif type_u == "association":
    if page == "🏠 Dashboard":             dashboard_association.show()
    elif page == "🔍 Chercher un don":     chercher_don.show()
    elif page == "📦 Mes réservations":  gerer_reservations.show()
    elif page == "✅ Contrôle réception":  controle_reception.show()
    elif page == "📋 Historique":          historique_association.show()
    elif page == "👤 Mes informations":    mes_informations.show()
