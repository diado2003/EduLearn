import streamlit as st
import json
import os
from datetime import date, timedelta
import random
import time
from Pages.Profil import get_badge_info

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Home", icon="🏠"):
        st.switch_page("Home_page.py")
with col2:
    if st.button("Profil", icon="🪪"):
        st.switch_page("Pages/Quizz_List.py")
with col3:
    if st.button("ML", icon="🧠"):
        st.switch_page("Pages/ML.py")
with col4:
    if st.button("Rank", icon="👨‍👨‍👦‍👦", disabled=False):
        st.switch_page("Pages/Rank.py")


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


# Asigură-te că importi funcția dacă e în alt fișier
# from profil import get_badge_info

def update_student_progress(username, xp_earned, quiz_name="General Quiz"):
    all_data = load_all_users()

    # --- SETUP DEFAULT ---
    # Default badge e primul din lista ta: Novice
    default_badge = (0, "Novice", "gray")

    defaults = {
        "streak": 0,
        "last_quiz_date": None,
        "total_xp": 0,
        "history": [],
        "current_badge": default_badge
    }

    user_data = all_data.get(username, defaults.copy())

    # Compatibilitate cu date vechi
    for key, val in defaults.items():
        if key not in user_data:
            user_data[key] = val

    today_str = str(date.today())
    last_date_str = user_data["last_quiz_date"]

    # --- 1. ACTUALIZARE XP ---
    old_badge = user_data["current_badge"]

    # Fix rapid: dacă badge-ul vechi e salvat greșit (doar string), îl resetăm
    if not isinstance(old_badge, (list, tuple)):
        old_badge = default_badge

    user_data["total_xp"] += xp_earned

    # --- 2. CALCUL STREAK ---
    status = "neutral"
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

    # --- 3. CALCUL BADGE NOU (Folosind funcția ta) ---
    new_badge = get_badge_info(user_data["total_xp"])
    user_data["current_badge"] = new_badge

    # Verificăm dacă numele badge-ului s-a schimbat (indexul 1 din tuplu)
    # old_badge[1] este numele (ex: "Novice")
    leveled_up = (new_badge[1] != old_badge[1])

    # --- 4. ISTORIC ---
    new_entry = {
        "Date": today_str,
        "Quiz": quiz_name,
        "XP Gained": xp_earned,
        "Streak Snapshot": user_data["streak"],
        "Badge Snapshot": new_badge[1]  # Salvăm doar numele în istoric
    }
    user_data["history"].append(new_entry)

    # --- 5. SALVARE ---
    all_data[username] = user_data
    save_all_users(all_data)

    return user_data, status, leveled_up

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

if 'a' not in st.session_state:
    st.session_state.a = random.randint(1, 10)
    st.session_state.b = random.randint(1, 10)

# Preluăm numerele din memorie
a = st.session_state.a
b = st.session_state.b
correct_sum = a + b

# --- INTERFAȚA ---
st.subheader(f"Întrebare: Cât fac {a} + {b}?")
ans = st.number_input("Răspuns:", value=None, placeholder="Scrie un numar...", step=1, key="quiz_input")

if st.button("Trimite Răspuns", key="submit_quiz_answer"):
    if ans == correct_sum:
        st.balloons()

        # --- AICI ESTE CHEIA ---
        # 1. Apelăm funcția ta REALĂ (asigură-te că nu are # în față)
        # Presupunem că 'current_user' este definit undeva mai sus în codul tău
        try:
            new_stats, status, leveled_up = update_student_progress(current_user, 50, "Math Multiplication")
        except NameError:
            st.error("Eroare: Funcția 'update_student_progress' sau variabila 'current_user' nu sunt definite.")
            st.stop()

        # 2. Afișăm mesajele bazate pe ce a returnat funcția
        if status == "increased":
            st.success(f"Bravo! Ai acum {new_stats.get('xp', '???')} XP! Streak: {new_stats.get('streak', 0)} 🔥")
        elif status == "reset":
            st.warning("Streak resetat, dar ai început o serie nouă! 🚀")
        elif status == "same_day":
            st.info("XP adăugat! Streak-ul e deja marcat pe azi.")
        else:
            st.success("Răspuns corect! 🎉")

        # 3. RESETĂM ÎNTREBAREA PENTRU TURA URMĂTOARE
        del st.session_state.a
        del st.session_state.b

        # O mică pauză ca utilizatorul să vadă mesajul de succes înainte de refresh
        time.sleep(1.5)
        st.rerun()

    else:
        st.error(f"Greșit. Mai încearcă! (Suma era {correct_sum})")