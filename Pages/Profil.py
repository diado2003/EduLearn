import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(layout="centered", page_title="Ranking Dashboard")

# --- MENIU NAVIGARE ---
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
    if st.button("Rank", icon="👨‍👨‍👦‍👦", disabled=False):
        st.switch_page("Pages/Rank.py")

st.divider()


# --- FUNCȚII HELPER ---

def get_badge_info(xp_value):
    """Calculează badge-ul pe baza XP-ului."""
    tiers = [
        (0, "Novice", "gray"),
        (500, "Apprentice", "brown"),
        (1500, "Scholar", "silver"),
        (3000, "Master", "gold"),
        (5000, "Grandmaster", "purple"),
        (10000, "Legend", "teal")
    ]

    c_badge = tiers[0]
    n_badge = tiers[-1]

    for i, tier in enumerate(tiers):
        if xp_value >= tier[0]:
            c_badge = tier
            if i + 1 < len(tiers):
                n_badge = tiers[i + 1]
            else:
                n_badge = None
        else:
            break

    return c_badge, n_badge


def load_user_data_from_json(username_key):
    """Încarcă datele din users_db.json."""
    try:
        with open('users_db.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Returnăm gol dacă nu există fișierul

    # Returnăm datele userului sau valori default
    defaults = {
        "streak": 0,
        "total_xp": 0,
        "last_quiz_date": None,
        "history": []  # IMPORTANT: Adăugăm o listă goală pentru istoric
    }
    return data.get(username_key, defaults)


# --- LOGICA PRINCIPALĂ ---

# 1. Verificare Autentificare
if 'user' not in st.session_state or not st.session_state.get('user'):
    st.error("Acces neautorizat. Te rog să te loghezi.")
    st.stop()

# 2. Identificare User
# Presupunem că st.session_state['user'] este un dict: {'preferred_username': 'Alex', ...}
user_info = st.session_state['user']
# Folosim numele ca cheie în JSON (sau un ID unic dacă ai)
current_username_key = user_info.get('preferred_username', 'Unknown')

# 3. Încărcare Date
stats = load_user_data_from_json(current_username_key)

# Extragem variabilele necesare (folosim valori default dacă lipsesc)
current_streak = stats.get('streak', 0)
total_xp = stats.get('total_xp', 0)
history_data = stats.get('history', [])  # Lista de quiz-uri anterioare

# Calculăm Badge-ul
current_badge, next_badge = get_badge_info(total_xp)

# 4. Creare DataFrame pentru Grafice (df)
if history_data:
    # Dacă avem istoric în JSON
    df = pd.DataFrame(history_data)
    # Ne asigurăm că data e formatată corect
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
else:
    # Dacă NU avem istoric, creăm un DataFrame gol ca să nu crape graficele
    df = pd.DataFrame(columns=['Date', 'Quiz', 'XP Gained'])

# --- UI DASHBOARD ---

# Header
col_h1, col_h2 = st.columns([1, 4])
with col_h1:
    # Poți pune o poză default dacă nu găsește fișierul
    st.image("teddy.png", width=100)
with col_h2:
    st.title(f"Salut, {current_username_key} 🩷")
    # Verificăm dacă df e gol înainte să apelăm len()
    quiz_count = len(df) if not df.empty else 0
    st.write(f"Keep up the great work. Ai exersat de **{quiz_count} ori**.")

st.markdown("---")

# Top Metrics
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="🔥 Current Streak", value=f"{current_streak} Zile")
with m2:
    # Calculăm ultimul XP câștigat doar dacă avem istoric
    last_xp = df['XP Gained'].iloc[-1] if not df.empty and 'XP Gained' in df.columns else 0
    st.metric(label="✨ Total XP", value=f"{total_xp:,}", delta=f"+{last_xp} last quiz")
with m3:
    st.metric(label="🛡️ Current Badge", value=current_badge[1])

# Badge Progress Bar
if next_badge:
    prev_threshold = current_badge[0]
    next_threshold = next_badge[0]
    # Evităm împărțirea la zero
    denom = next_threshold - prev_threshold
    progress = (total_xp - prev_threshold) / denom if denom > 0 else 0
    remaining_xp = next_threshold - total_xp

    st.caption(f"**Progres către {next_badge[1]}:** {int(progress * 100)}% ({remaining_xp} XP necesar)")
    st.progress(progress)
else:
    st.success("Ai atins rangul maxim! 🏆")

st.markdown("---")

# Middle Section: Grafice
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Creștere XP")
    if not df.empty and 'XP Gained' in df.columns:
        df['Cumulative XP'] = df['XP Gained'].cumsum()
        fig = px.area(df, x='Date', y='Cumulative XP', markers=True, color_discrete_sequence=['#636EFA'])
        fig.update_layout(xaxis_title="Data", yaxis_title="Total XP", height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Rezolvă quiz-uri pentru a vedea graficul de progres.")

with c2:
    st.subheader("📝 Quiz-uri Recente")
    if not df.empty:
        # Sortăm și luăm ultimele 5
        recent_df = df[['Date', 'Quiz', 'XP Gained']].sort_values(by="Date", ascending=False).head(5)
        # Formatare dată doar pentru afișare
        recent_df['Date'] = recent_df['Date'].dt.strftime('%Y-%m-%d')
        st.dataframe(recent_df, hide_index=True, use_container_width=True)
    else:
        st.info("Niciun quiz recent.")

# Sidebar
st.sidebar.header("Statistici Profil")
# Calculăm max streak doar dacă avem coloana în istoric, altfel folosim streak-ul curent
max_streak = df['Streak Snapshot'].max() if not df.empty and 'Streak Snapshot' in df.columns else current_streak
avg_xp = int(df['XP Gained'].mean()) if not df.empty and 'XP Gained' in df.columns else 0

st.sidebar.write(f"**Cel mai mare Streak:** {max_streak} Zile")
st.sidebar.write(f"**Medie XP/Quiz:** {avg_xp}")
st.sidebar.info("Sfat: Completează quiz-uri în weekend pentru 2x XP!")