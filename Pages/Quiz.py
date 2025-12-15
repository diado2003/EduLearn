import streamlit as st
import json
import os
from datetime import date, timedelta
import random
import time
from Pages.Profil import get_badge_info

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

if 'quiz_category' not in st.session_state:
    st.warning("Te rog să alegi mai întâi un domeniu!")
    time.sleep(2)
    st.switch_page("Pages/Quizz_List.py") # Sau cum se numește pagina ta anterioară

# Preluăm setările
category = st.session_state['quiz_category']
# difficulty = st.session_state['quiz_difficulty']

# Buton de Ieșire
if st.button("⬅️ Înapoi la setări"):
    st.switch_page("Pages/Quizz_List.py")

st.title(f"Quiz: {category}")
# st.caption(f"Dificultate: {difficulty}")
st.divider()

# --- 1. DEFINIM "JSON-ul" CU ÎNTREBĂRI ---
# În realitate, acesta ar putea fi încărcat dintr-un fișier .json extern
quiz_data = {
    "NLP": [
        {
            "question": "Ce este NLP și de ce este important?",
            "correct": """Este ramura Inteligenței Artificiale care se ocupă cu înțelegerea, 
                       interpretarea și generarea limbajului uman de către calculatoare.
                       """,
            "wrong": ["54", "48", "62"]
        },
        {
            "question": "Care sunt principalele subdomenii ale NLP?",
            "correct": "NLU, NLG.",
            "wrong": ["NLU", "NLG", "LLM"]
        },
        {
            "question": """"Cum funcționează modelele lingvistice mari (LLM-uri)?
                        """,
            "correct": """Un Large Language Model este un model neuronal 
                       (de obicei Transformer) antrenat pe cantități uriașe de 
                       text pentru a învăț și prezice probabilistic următorul cuvânt (token) 
                       într-o secvență.
                       """,
            "wrong":["","",""]
        },
        {
            "question":"Ce sunt prompt-urile într-un LLM?",
            "correct":"Un prompt este instrucțiunea / textul de intrare oferit modelului.",
            "wrong": ["","",""]
        },
        {
            "question":"Ce sunt vectorii de cuvinte (word embeddings)?",
            "correct":"Sunt reprezentări numerice (vectori) ale cuvintelor într-un spațiu multidimensional.",
            "wrong":["Sunt liste (vectori) de cuvinte.","",""]
        },
        {
            "question": "Cum ajută vectorii de cuvinte (word embeddings)la înțelegerea sensului?",
            "correct": """surprind relații semantice, permit modelelor să generalizeze si oferă context
                       matematic limbajului""",
            "wrong": ["surprind relații semantice si oferă context matematic limbajului",
                      "permit modelelor să generalizeze si surprind relații semantice",
                      "surprind relații semantice si permit modelelor să generalizeze"]
        },
        {
            "question": "Cum se abordează ambiguitatea (polisemia, homonimia) în NLP?",
            "correct": "Ambiguitatea este rezolvată prin context și embeddings contextuale",
            "wrong": ["Modelele moderne folosesc contextul complet al propoziției.",
                      "Produc vectori diferiți pentru același cuvânt, în funcție de context.",
                      "Modelul alege sensul cel mai probabil în context."]
        },
        {
            "question": "Care este o tehnică de tokenizare?",
            "correct": "WordPunct",
            "wrong": ["ResNet", "K-Means", "Random Forest"]
        }
    ],
    "Supervised": [
        {
            "question": "Ce este învățarea supervizată?",
            "correct": """
                        Învățarea supervizată este o metodă de machine learning 
                        în care algoritmii învață din date etichetate, adică fiecare 
                        intrare este asociată cu un răspuns corect.
                        """,
            "wrong": ["1859", "1877", "1945"]
        },
        {
            "question": "Care sunt tipurile comune de sarcini de învățare supervizată?",
            "correct": "Clasificarea si Regresia",
            "wrong": ["Clasificarea", "Regresia", "Niciuna"]
        },
        {
            "question": "Care sunt exemple de algoritmi de învățare supervizată?",
            "correct": """Exemple includ regresia liniară, regresia logistică, 
                        arbori de decizie, mașini cu vectori de suport (SVM) 
                        și rețele neuronale. """,
            "wrong": ["Regresia liniara, masini cu vectori de suport",
                      "Retele neuronale, arbori de decizie si regresia logistica",
                      "Multe altele"]
        },
        {
            "question": "Care sunt principalele avantaje ale învățării supervizate?",
            "correct": """Acuratețe ridicată și putere predictivă 
            puternică atunci când sunt antrenate pe date etichetate de calitate. """,
            "wrong": ["Puterea predictiva care rezulta in rapiditatea modelului",
                      "Acuratețea ridicată care indica rezultate de calitate ",
                      "Multe altele"]
        },
        {   "question": "Care sunt principalele avantaje ale învățării supervizate?",
            "correct": """Dezavantajele sunt dependența de seturi mari de date
             etichetate și riscul de overfitting dacă modelul este prea complex.""",
            "wrong": ["Nu are nici un dezavanta.","Acuratetea nu este ridicata cand sunt antrenate pe date etichetate.",
                      "Overfitiing-ul apare la toate modelele, indiferent de complexitate."]

        },
        {
            "question": "Ce sunt etichetele (labels)?",
            "correct": "Output-ul așteptat",
            "wrong": ["Input-ul brut", "Zgomotul", "Feature-urile"]
        }
    ],
    "Unsupervised": [
        {
            "question": "Ce este învățarea nesupravegheată?",
            "correct": """Învățarea nesupravegheată este o abordare a învățării automate în care modelele analizează
             și identifică tipare în date fără ieșiri etichetate, permițând sarcini precum gruparea 
             în clustere, reducerea dimensionalității și învățarea regulilor de asociere.""",
            "wrong": ["Dunărea", "Rin", "Sena"]
        },
        {
            "question": "Cum diferă învățarea nesupravegheată de cea supravegheată?",
            "correct": """Spre deosebire de învățarea supravegheată, care folosește date 
            etichetate pentru antrenarea modelelor, învățarea nesupravegheată lucrează cu date neetichetate
             pentru a descoperi structuri și tipare ascunse fără ieșiri predefinite.""",
            "wrong": ["","",""]
        },
        {
            "question": "Care sunt principalele provocări ale învățării nesupravegheate?",
            "correct": """
                        Provocările includ complexitatea computațională, dificultatea interpretării rezultatelor, 
                        evaluarea performanței modelului fără etichete și riscul de supraînvățare asupra unor tipare
                        care nu se generalizează.""",
            "wrong": ["","",""]
        },
        {
            "question": "Care sunt tehnicile cheie în învățarea nesupravegheată?",
            "correct": """Tehnicile cheie includ gruparea în clustere, reducerea dimensionalității
             și învățarea regulilor de asociere.""",
            "wrong": ["Gruparea in clustere si reducerea dimensionalitatii",
                      "Reducerea dimensionalitatii si invatarea regulilor de asociere",
                      "Invatarea regulilor de asociere si gruparea in clustere"]
        },
        {
            "question": "Ce face PCA?",
            "correct": "Reduce dimensionalitatea",
            "wrong": ["Clasifică imagini", "Prezice prețuri", "Etichetează date"]
        }
    ]
}

if 'quiz_questions' not in st.session_state:
    # 1. Verificăm dacă avem întrebări
    if category in quiz_data:
        available_questions = quiz_data[category]

        # 2. Alegem random 5 întrebări (sau mai puține dacă nu sunt destule în JSON)
        num_questions = min(5, len(available_questions))
        selected_questions = random.sample(available_questions, num_questions)

        # 3. Pregătim întrebările (amestecăm variantele de acum ca să fie gata)
        final_quiz_list = []
        for q in selected_questions:
            options = q["wrong"] + [q["correct"]]
            random.shuffle(options)
            final_quiz_list.append({
                "question": q["question"],
                "options": options,
                "correct_answer": q["correct"]
            })

        # 4. Salvăm totul în session_state
        st.session_state.quiz_questions = final_quiz_list
        st.session_state.question_index = 0
        st.session_state.score = 0
    else:
        st.error("Nu există întrebări pentru această categorie.")
        st.stop()

# --- 3. AFIȘARE PROGRES SAU REZULTAT FINAL ---

# Verificăm dacă am terminat toate întrebările
if st.session_state.question_index >= len(st.session_state.quiz_questions):
    # --- ECRAN DE FINAL ---
    st.balloons()
    st.title("Quiz Finalizat! 🏁")

    score = st.session_state.score
    total = len(st.session_state.quiz_questions)

    st.markdown(f"### Ai răspuns corect la **{score}** din **{total}** întrebări.")

    if score == total:
        st.success("Excelent! Ești un expert! 🏆")
    elif score >= total / 2:
        st.info("Rezultat bun! Mai ai puțin de învățat. 📚")
    else:
        st.warning("Mai încearcă, repetiția e mama învățăturii. 💪")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Încearcă din nou (Același set)"):
            st.session_state.question_index = 0
            st.session_state.score = 0
            st.rerun()
    with col2:
        if st.button("🏠 Înapoi la Meniu"):
            # Curățăm datele quiz-ului curent
            del st.session_state.quiz_questions
            del st.session_state.question_index
            del st.session_state.score
            st.switch_page("Pages/Home_page.py")

    st.stop()  # Oprim execuția aici ca să nu mai afișeze întrebarea de jos

# --- 4. AFIȘARE ÎNTREBARE CURENTĂ ---
current_idx = st.session_state.question_index
current_q = st.session_state.quiz_questions[current_idx]
total_q = len(st.session_state.quiz_questions)

st.progress((current_idx) / total_q)
st.caption(f"Categoria: **{category}** | Întrebarea {current_idx + 1} din {total_q}")
st.subheader(current_q['question'])

user_choice = st.radio(
    "Alege varianta corectă:",
    options=current_q['options'],
    index=None,
    key=f"q_{current_idx}"
)

st.markdown("---")

# --- 5. VERIFICARE ȘI UPDATE XP ---
if st.button("Trimite Răspuns", type="primary"):
    if user_choice is None:
        st.warning("Te rog selectează o opțiune!")
    else:
        # --- CAZUL CORECT ---
        if user_choice == current_q['correct_answer']:
            st.balloons()
            st.session_state.score += 1

            # --- INTEGRAREA CODULUI TĂU DE XP ---
            try:
                # 50 XP per întrebare corectă. Categoria este variabila 'category'
                new_stats, status, leveled_up = update_student_progress(current_user, 50, category)

                # Afișare mesaje XP / Streak
                if status == "increased":
                    st.success(
                        f"Bravo! Ai acum {new_stats.get('xp', '???')} XP! Streak: {new_stats.get('streak', 0)} 🔥")
                elif status == "reset":
                    st.warning("Streak resetat, dar ai început o serie nouă! 🚀")
                elif status == "same_day":
                    st.info("XP adăugat! Streak-ul e deja marcat pe azi.")
                else:
                    st.success("Răspuns corect! 🎉")
                #
                # if leveled_up:
                #     st.write("🆙 **LEVEL UP! Ai crescut în nivel!**")

            except NameError:
                # Fallback dacă funcția nu e importată (pentru testare)
                st.success("Răspuns corect! (XP system offline)")
            except Exception as e:
                st.error(f"Eroare la actualizare XP: {e}")

        # --- CAZUL GREȘIT ---
        else:
            st.error(f"Greșit! Răspunsul corect era: **{current_q['correct_answer']}**")

        # Trecem la următoarea întrebare
        st.session_state.question_index += 1

        # Așteptăm puțin să vadă XP-ul și mesajele, apoi refresh
        time.sleep(2.5)
        st.rerun()