import streamlit as st
import pandas as pd
import json
import os

col1, col2, col3, col4 = st.columns(4)
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
    if st.button("Profil", icon="🪪"):
        st.switch_page("Pages/Profil.py")

st.divider()
col_1, col_2, col_3 = st.columns(3)
with col_2:
    st.title("Ranking🏆")

DB_FILE = 'users_db.json'


def load_all_users():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def show_leaderboard():

    all_data = load_all_users()

    if not all_data:
        st.info("Încă nu sunt date pentru clasament. Fii primul care rezolvă un quiz!")
        return

    leaderboard_data = []

    # --- PARTEA CRITICĂ: EXTRAGEREA CORECTĂ ---
    # username vine din CHEIE, restul din VALOARE
    for username, info in all_data.items():
        # 1. Extragem XP
        xp = info.get("total_xp", 0)

        # NU mai extragem streak sau badge, conform cerinței

        leaderboard_data.append({
            "User": username,  # Cheia dicționarului
            "XP": xp
        })

    # --- CREARE TABEL ---
    df = pd.DataFrame(leaderboard_data)

    if not df.empty:
        # Sortare descrescătoare după XP
        df = df.sort_values(by="XP", ascending=False).reset_index(drop=True)
        df.index += 1  # Index de la 1

        # --- PODIUM ---
        col1, col2, col3 = st.columns(3)

        # Locul 1 (Mijloc)
        if len(df) > 0:
            col2.metric(label="🥇 Locul 1", value=df.iloc[0]['User'], delta=f"{df.iloc[0]['XP']} XP")

        # Locul 2 (Stânga)
        if len(df) > 1:
            col1.metric(label="🥈 Locul 2", value=df.iloc[1]['User'], delta=f"{df.iloc[1]['XP']} XP")

        # Locul 3 (Dreapta)
        if len(df) > 2:
            col3.metric(label="🥉 Locul 3", value=df.iloc[2]['User'], delta=f"{df.iloc[2]['XP']} XP")

        st.divider()

        # Calculăm maximul pentru bara de progres
        max_xp = df["XP"].max()
        if max_xp == 0: max_xp = 100

        # --- TABEL DETALIAT ---
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "User": st.column_config.TextColumn("Jucător", width="medium"),
                "XP": st.column_config.ProgressColumn(
                    "XP Total",
                    format="%d",
                    min_value=0,
                    max_value=int(max_xp * 1.2)
                )
            }
        )


# Dacă rulezi direct fișierul asta pentru test
if __name__ == "__main__":
    show_leaderboard()