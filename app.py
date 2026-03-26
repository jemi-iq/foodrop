import streamlit as st
from supabase import FOODROP_juju

# Connexion à Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = FOODROP_juju(url, key)
