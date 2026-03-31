# ============================================================
# config.py — Connexion à Supabase
# ============================================================
# Ce fichier crée un client Supabase réutilisable dans toute
# l'application. On le charge UNE SEULE FOIS ici, puis on
# l'importe dans chaque page avec : from config import supabase
# ============================================================

import streamlit as st
from supabase import create_client, Client

# ----------------------------------------------------------
# Paramètres de connexion
# ----------------------------------------------------------
# Ces valeurs se trouvent dans ton projet Supabase :
#   Settings > API > Project URL  &  anon public key
#
# On les stocke dans st.secrets (fichier .streamlit/secrets.toml)
# pour ne JAMAIS mettre les clés directement dans le code.
# ----------------------------------------------------------

@st.cache_resource   # Streamlit garde le client en mémoire → une seule connexion
def get_supabase_client() -> Client:
    """Retourne le client Supabase, initialisé une seule fois."""
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# Raccourci pratique : importer directement `supabase` dans les autres fichiers
supabase: Client = get_supabase_client()