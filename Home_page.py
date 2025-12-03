import streamlit as st
import requests
from requests_oauthlib import OAuth2Session
import urllib.parse
import os
from datetime import datetime
from streamlit import divider

st.logo("teddy.png", size="large")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# --- CONFIG (completează după ce ai setările Keycloak) ---
KEYCLOAK_URL_PUBLIC = "http://localhost:8082"   # așa cum ai pus tu
REALM_NAME = "streamlit"
CLIENT_ID = "streamlit-id"                  # pune clientul tău
CLIENT_SECRET = "03Hv5NBdPJSg93CtXbgnYEdQVbfM0ArC"            # pune-l doar dacă client e 'confidential'
REDIRECT_URI = "http://localhost:8501/"         # trebuie să fie identic în Keycloak (Valid Redirect URI)
SCOPE = ["openid", "profile", "email"]

# Endpoints standard Keycloak
AUTH_BASE_URL = f"{KEYCLOAK_URL_PUBLIC}/realms/{REALM_NAME}/protocol/openid-connect/auth"
TOKEN_URL = f"{KEYCLOAK_URL_PUBLIC}/realms/{REALM_NAME}/protocol/openid-connect/token"
USERINFO_URL = f"{KEYCLOAK_URL_PUBLIC}/realms/{REALM_NAME}/protocol/openid-connect/userinfo"
LOGOUT_URL = f"{KEYCLOAK_URL_PUBLIC}/realms/{REALM_NAME}/protocol/openid-connect/logout"

# --- simple helper ---
def create_oauth_session(state=None):
    return OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE, state=state)

# --- Streamlit page setup ---

if 'oauth' not in st.session_state:
    st.session_state['oauth'] = None
if 'oauth_state' not in st.session_state:
    st.session_state['oauth_state'] = None
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- Meniul de Sus (Butoane pe Linie) ---
col1, col2, col3, col4, col5, col6= st.columns(6)
with col1:
    st.button("Home", icon="🏠")

with col2:
    if st.button("Quiz", icon="💯"):
        st.switch_page("Pages/Quizz_List.py")

with col3:
    if st.button("ML", icon="🧠"):
        st.switch_page("Pages/ML.py")

with col4:
    if st.button("Profil", icon="🪪"):
        st.switch_page("Pages/Profil.py")

with col5:
    if st.button("Rank", icon="👨‍👦‍👦"):
        st.switch_page("Pages/Rank.py")

# Butonul de Login/Logout (simplificat)
with col6:
    def handle_login():
        # când apasă butonul, construim session + authorization URL și afișăm linkul
        if st.button("Login"):
            if st.session_state['oauth'] is None:
                st.session_state['oauth'] = create_oauth_session()
            try:
                authorization_url, state = st.session_state['oauth'].authorization_url(AUTH_BASE_URL)
                st.session_state['oauth_state'] = state
                st.markdown(f'<a href="{authorization_url}" target="_self">Click aici pentru a te autentifica pe Keycloak</a>', unsafe_allow_html=True)
                # st.info("Veți fi redirecționat către Keycloak.")
            except Exception as e:
                st.error(f"Eroare la generarea URL-ului de login: {e}")

    handle_login()
st.divider()
#==============titlu==================
st.set_page_config(layout="centered")
col1, col2, col3 = st.columns(3)
with col2:
    st.title("EduLearn")
#=======================================

# --- Callback minimal: detectăm ?code=... în URL și facem schimbul pentru token ---
query_params = st.query_params
if 'code' in query_params:
    # extrage corect
    code = query_params.get('code')
    if isinstance(code, list):
        code = code[0]
    returned_state = query_params.get('state')
    if isinstance(returned_state, list):
        returned_state = returned_state[0]

    # verificare state (dacă ai salvat la inițiere)
    stored_state = st.session_state.get('oauth_state')
    if stored_state and returned_state != stored_state:
        st.error("State mismatch — apasă Login din nou.")
    else:
        # FACEM SCHIMBUL MANUAL CU requests (evităm dependența de OAuth2Session păstrat)
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
            }
            # adaugă client_secret doar dacă clientul e confidential
            if CLIENT_SECRET:
                data['client_secret'] = CLIENT_SECRET

            resp = requests.post(TOKEN_URL, data=data, headers={'Accept': 'application/json'})
            resp.raise_for_status()
            token = resp.json()
            st.session_state['token'] = token

            # apel userinfo pentru profil
            userinfo_resp = requests.get(USERINFO_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
            userinfo_resp.raise_for_status()
            st.session_state['user'] = userinfo_resp.json()
            st.session_state['authenticated'] = True

            # curățare și UX
            st.query_params.clear()
            st.session_state['oauth_state'] = None
            st.success("Autentificare reușită.")
            st.rerun() # Noua sintaxăs

        except Exception as e:
            st.error(f"Eroare la schimbul token/code (manual): {e}")
            import traceback, sys
            print(traceback.format_exc(), file=sys.stderr)


st.markdown("#####")


# --- Afișare stare simplă ---
if st.session_state['user']:
    st.sidebar.title(f"Buna {st.session_state['user'].get('preferred_username')} 🩷")
    st.snow()

else:
    st.info("Nu ești autentificat.")

st.sidebar.image("teddy.png")


# --- Logout simplu ---
if st.sidebar.button("Logout"):
    if st.session_state['token']:
        id_token = st.session_state['token'].get("id_token")
        params = {}
        if id_token:
            params['id_token_hint'] = id_token
        params['post_logout_redirect_uri'] = REDIRECT_URI
        logout_link = LOGOUT_URL + "?" + urllib.parse.urlencode(params)

        # curățăm sesiunea locală
        st.session_state['token'] = None
        st.session_state['user'] = None
        st.session_state['oauth'] = None
        st.session_state['oauth_state'] = None

        st.markdown(f"[Logout complet (Keycloak)]({logout_link})")
    else:
        st.info("Nu ești autentificat.")

st.subheader("""Cateva cuvinte
        EduLearn este o platforma care isi propune sa invete pasionatii de 
        Machine Learning printr-o modalitate interativa - folosind grile.
        Tot acest site a plecat de la pasiunea noastra pentru 
        Machine Learning. Sper ca va place 🩷
        """)

data_curenta = datetime.now().strftime("%d %B %Y")
st.divider()
cola, colb,colc = st.columns(3)
with colc:
    st.write(data_curenta)


