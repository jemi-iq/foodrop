# ============================================================
# app.py — Point d'entrée principal de Foodrop
# ============================================================

import streamlit as st

st.set_page_config(
    page_title="Foodrop",
    page_icon="🌿",
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
  [data-testid="stSidebar"] { background-color: var(--foret) !important; }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] .stRadio label { font-family:'Syne',sans-serif; font-size:0.95rem; padding:6px 0; cursor:pointer; }
  h1, h2, h3 { font-family:'Syne',sans-serif !important; color:var(--foret) !important; }
  .stButton > button { background-color:var(--foret); color:white !important; border:none; border-radius:50px; font-family:'Syne',sans-serif; font-weight:700; padding:0.5rem 1.5rem; transition:background 0.2s; }
  .stButton > button:hover { background-color:var(--herbe); color:white !important; }
  .stButton > button p { color:white !important; }
  .foodrop-card { background:white; border-radius:16px; padding:1.2rem; margin-bottom:1rem; border:1px solid #E0DDD5; box-shadow:0 2px 8px rgba(42,92,30,0.06); }
  p, li, label { font-family:'Fraunces',serif; color:var(--texte); }
</style>
""", unsafe_allow_html=True)

from vues import auth
from vues import creer_don
from vues import dashboard_magasin
from vues import chercher_don
from vues import dashboard_association
from vues import controle_reception
from vues import gerer_dons

if "connecte" not in st.session_state:
    st.session_state.connecte         = False
    st.session_state.user_id          = None
    st.session_state.user_email       = None
    st.session_state.type_utilisateur = None
    st.session_state.entite_id        = None

if not st.session_state.connecte:
    auth.show()
    st.stop()

type_u = st.session_state.type_utilisateur

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.5rem 0 1rem;">
      <span style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:white;">
        food<span style="color:#A8D455;">rop</span>
      </span>
      <p style="color:rgba(255,255,255,0.6); font-size:0.75rem; margin-top:4px;">Rien ne se gaspille.</p>
    </div>
    <hr style="border-color:rgba(255,255,255,0.2); margin-bottom:1rem;">
    """, unsafe_allow_html=True)

    st.markdown(
        f"<p style='font-size:0.78rem; color:rgba(255,255,255,0.7); font-family:Fraunces,serif; margin-bottom:0.5rem;'>"
        f"{'🏪' if type_u == 'magasin' else '🤝'} {st.session_state.user_email}</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if type_u == "magasin":
        page = st.radio("Navigation", ["🏠 Dashboard","➕ Créer un don","📦 Gérer les dons","📋 Historique","👤 Mes informations"])
    else:
        page = st.radio("Navigation", ["🏠 Dashboard","🔍 Chercher un don","📦 Mes réservations","✅ Contrôle réception","📋 Historique","👤 Mes informations"])

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem; color:rgba(255,255,255,0.4);'>FAQ · Mentions légales</p>", unsafe_allow_html=True)
    if st.button("🚪 Se déconnecter", use_container_width=True):
        auth.deconnecter()

if type_u == "magasin":
    if page == "🏠 Dashboard":           dashboard_magasin.show()
    elif page == "➕ Créer un don":       creer_don.show()
    elif page == "📦 Gérer les dons":     gerer_dons.show()
    elif page == "📋 Historique":
        st.title("📋 Historique des dons")
        st.info("🚧 Page en cours de construction — reviens bientôt !")
    elif page == "👤 Mes informations":
        st.title("👤 Mes informations")
        st.info("🚧 Page en cours de construction — reviens bientôt !")

elif type_u == "association":
    if page == "🏠 Dashboard":             dashboard_association.show()
    elif page == "🔍 Chercher un don":     chercher_don.show()
    elif page == "📦 Mes réservations":
        st.title("📦 Mes réservations")
        st.info("🚧 Page en cours de construction — reviens bientôt !")
    elif page == "✅ Contrôle réception":  controle_reception.show()
    elif page == "📋 Historique":
        st.title("📋 Historique des collectes")
        st.info("🚧 Page en cours de construction — reviens bientôt !")
    elif page == "👤 Mes informations":
        st.title("👤 Mes informations")
        st.info("🚧 Page en cours de construction — reviens bientôt !")