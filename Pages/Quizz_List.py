import streamlit as st
from datetime import datetime

cola, colb,colc = st.columns(3)
with colb:
    st.title("Quizz Time")
st.subheader("Alege capitolul quiz-ului")
st.selectbox("Domeniu",["NLP","Supervised","Unsupervised"])
st.divider()
st.subheader("Alege dificultatea")
st.select_slider("Dificultate",["Incepator","Meniu", "Avansat"])
st.markdown("#####")
col1, col2, col3 = st.columns(3)
with col2:
    submit_button = st.button("Incepe Quiz")
st.markdown("#####")

data_curenta = datetime.now().strftime("%d %B %Y")
cola, colb,colc = st.columns(3)
with colc:
    st.write(data_curenta)

# if submit_button:
#     # Comparație simplă
#     if user_answer.lower().strip() == a.lower().strip():
#         st.success(f"**Corect!** Răspunsul a fost: **{a}**")
#         st.session_state.score += 1
#         st.session_state.xp += 10
#
#         if st.session_state.xp >= 50 and "Savant de Bronz (50 XP)" not in st.session_state.badges:
#             st.balloons()
#             st.write("🎉 **Insignă Câștigată: Savant de Bronz (50 XP)!**")
#             st.session_state.badges.append("Savant de Bronz (50 XP)")
#
#     else:
#         st.error(f"**Greșit.** Răspunsul corect era: **{a}**")