import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="centered")

col1, col2, col3, col4= st.columns(4)
with col1:
    if st.button("Home", icon="🏠"):
        st.switch_page("Home_page.py")

with col2:
    if st.button("Quiz", icon="💯"):
        st.switch_page("Pages/Quizz_List.py")

with col3:
    if st.button("ML", icon="🧠"):
        st.switch_page("Pages/ML.py")

with col4:
     st.button("Pages/Rank", icon="👨‍👨‍👦‍👦")

st.divider()

if st.session_state['user']:
    st.title(f"Buna {st.session_state['user'].get('preferred_username')} 🩷")

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Acces neautorizat. Vă rugăm să vă autentificați pe pagina principală.")
    st.stop()

# --- Extragerea Datelor din Sesiune ---
user_data = st.session_state['user']
username = user_data.get('preferred_username')
nume_complet = user_data.get('name')

# Extragem metrica calculată anterior
zile = st.session_state.get('zile_intrate',0)

data = [10,50,45,30]
data_df=pd.DataFrame(data)


st.subheader("Dashboard-ul tau")



st.divider()
data_curenta = datetime.now().strftime("%d %B %Y")
cola, colb,colc = st.columns(3)
with colc:
    st.write(data_curenta)
