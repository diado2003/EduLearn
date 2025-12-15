import streamlit as st
from datetime import datetime

# --- HEADER NAVIGARE (Codul tău existent) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Home", icon="🏠"):
        st.switch_page("Home_page.py")
with col2:
    if st.button("Rank", icon="👨‍👨‍👦‍👦"):
        st.switch_page("Pages/Rank.py")
with col3:
    if st.button("ML", icon="🧠"):
        st.switch_page("Pages/ML.py")
with col4:
    if st.button("Profil", icon="🪪"):
        st.switch_page("Pages/Profil.py")

st.divider()

# --- SELECTIA QUIZ-ULUI ---
cola, colb, colc = st.columns(3)
with colb:
    st.title("Quizz Time")

st.subheader("Alege capitolul quiz-ului")
# Salvăm alegerea într-o variabilă
domeniu_ales = st.selectbox("Domeniu", ["NLP", "Supervised", "Unsupervised"])

st.divider()

st.subheader("Alege dificultatea")
# Salvăm alegerea într-o variabilă
dificultate_aleasa = st.select_slider("Dificultate", ["Incepator", "Mediu", "Avansat"])

st.markdown("#####")

col_1, col_2, col_3 = st.columns(3)

# --- BUTONUL DE START ---
with col_2:
    if st.button("Incepe Quiz"):
        # 1. Salvăm setările în Session State pentru a le folosi în pagina următoare
        st.session_state['quiz_category'] = domeniu_ales
        # st.session_state['quiz_difficulty'] = dificultate_aleasa

        # 2. Resetăm întrebarea curentă (ca să nu rămână una veche dacă userul revine)
        if 'current_quiz' in st.session_state:
            del st.session_state['current_quiz']

        # 3. Schimbăm pagina
        st.switch_page("Pages/Quiz.py")

st.markdown("#####")

# Footer cu data
data_curenta = datetime.now().strftime("%d %B %Y")
cola, colb, colc = st.columns(3)
with colc:
    st.write(data_curenta)