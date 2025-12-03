import streamlit as st
import json
import os
from datetime import date, timedelta

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
    st.button("Rank", icon="👨‍👨‍👦‍👦", disabled=True)  # Butonul curent dezactivat vizual

st.divider()


# --- CONFIGURARE FIȘIER ---
DB_FILE = 'users_db.json'


# --- 1. FUNCȚII BAZĂ DE DATE (ROBUSTE) ---

def init_db():
    """Verifică dacă fișierul există. Dacă nu, îl creează gol."""
    if not os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'w') as f:
                json.dump({}, f)
            print("DB: Fișier creat cu succes.")
        except Exception as e:
            st.error(f"Eroare fatală: Nu pot crea fișierul JSON. Motiv: {e}")
            st.stop()


def load_all_users():
    """Încarcă baza de date în siguranță."""
    init_db()  # Asigură-te că fișierul există înainte să citim
    try:
        with open(DB_FILE, 'r') as f:
            content = f.read()
            if not content:  # Dacă fișierul e gol
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}  # Dacă fișierul e corupt, returnăm dicționar gol


def save_all_users(all_data):
    """Salvează datele."""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(all_data, f, indent=4)
    except Exception as e:
        st.error(f"Eroare la salvare: {e}")


def update_student_progress(username, xp_earned, quiz_name="General Quiz"):
    """Logica principală de update."""
    all_data = load_all_users()

    # Valori default
    defaults = {"streak": 0, "last_quiz_date": None, "total_xp": 0, "history": []}
    user_data = all_data.get(username, defaults)

    # Asigurăm compatibilitatea cu history
    if "history" not in user_data:
        user_data["history"] = []

    today_str = str(date.today())
    last_date_str = user_data["last_quiz_date"]

    # --- CALCUL STREAK ---
    status = "neutral"
    user_data["total_xp"] += xp_earned

    if last_date_str == today_str:
        status = "same_day"
    elif last_date_str == str(date.today() - timedelta(days=1)):
        user_data["streak"] += 1
        status = "increased"
    else:
        if user_data["streak"] > 0:
            status = "reset"
        else:
            status = "first_time"
        user_data["streak"] = 1

    user_data["last_quiz_date"] = today_str

    # --- ADĂUGARE ÎN ISTORIC ---
    new_entry = {
        "Date": today_str,
        "Quiz": quiz_name,
        "XP Gained": xp_earned,
        "Streak Snapshot": user_data["streak"]
    }
    user_data["history"].append(new_entry)

    # --- SALVARE ---
    all_data[username] = user_data
    save_all_users(all_data)

    return user_data, status


# --- 2. INTERFAȚA GRAFICĂ (UI) ---

# --- DEBUGGING / AUTO-LOGIN PENTRU TEST ---
# Această parte previne pagina albă dacă rulezi fișierul direct
if 'user' not in st.session_state or not st.session_state['user']:
    st.warning("⚠️ Acces neautorizat. Te rog să te loghezi.!")
    st.stop()
else:
    st.title(f"Buna {st.session_state['user'].get('preferred_username')} :heart:")

# Verificăm din nou (pentru siguranță)
if not st.session_state.get('authenticated'):
    st.error("Eroare de autentificare.")
    st.stop()

# --- PRELUARE USER CURENT ---
current_user = st.session_state['user'].get('preferred_username')
if not current_user:
    st.error("Eroare: Userul nu are un nume (preferred_username).")
    st.stop()

# --- AFIȘARE STATISTICI ---
# Inițializăm DB la pornirea paginii
init_db()
stats = load_all_users().get(current_user, {"streak": 0, "total_xp": 0})

col1, col2 = st.columns(2)
col1.metric("🔥 Streak", f"{stats.get('streak', 0)} Zile")
col2.metric("✨ XP", f"{stats.get('total_xp', 0)}")

st.divider()

# --- QUIZ ---
st.subheader("Întrebare: Cât fac 5 * 5?")
ans = st.number_input("Răspuns:", key="q_math", step=1)

if st.button("Trimite Răspuns"):
    if ans == 25:
        st.balloons()
        new_stats, status = update_student_progress(current_user, 50, "Math Multiplication")

        if status == "increased":
            st.success(f"Bravo! Streak crescut la {new_stats['streak']}! 🔥")
        elif status == "reset":
            st.warning("Streak resetat, dar ai început o serie nouă! 🚀")
        elif status == "same_day":
            st.info("XP adăugat! Streak-ul e deja marcat pe azi.")
        else:
            st.success("Primul tău quiz! 🎉")

        st.rerun()
    else:
        st.error("Greșit. Mai încearcă!")