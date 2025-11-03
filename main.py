import streamlit as st
from transformers import pipeline
import fitz  # PyMuPDF
import random

# --- Configurarea Aplicației Streamlit ---
st.set_page_config(page_title="EduLearn Quiz", layout="centered")
st.title("🤖 EduLearn - Quiz Generator Inteligent")


# --- Motorul NLP (Hugging Face) ---
@st.cache_resource
def load_models():
    # 1. Modelul de Generare a Întrebărilor (QG)
    qg_model_name = "valhalla/t5-small-qg-prepend"
    qg_pipeline = pipeline("text2text-generation",
                           model=qg_model_name,
                           use_fast=False)

    # 2. Modelul de Răspuns la Întrebări (QA)
    qa_model_name = "distilbert-base-cased-distilled-squad"
    qa_pipeline = pipeline("question-answering", model=qa_model_name)

    return qg_pipeline, qa_pipeline


# --- Funcție pentru împărțirea textului (Chunking) ---
def split_text_into_chunks(text, chunk_size=1500, overlap=300):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# --- Inițializarea stării sesiunii (Session State) ---
if 'context_text' not in st.session_state:
    st.session_state.context_text = ""
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'quiz_in_progress' not in st.session_state:
    st.session_state.quiz_in_progress = False
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'badges' not in st.session_state:
    st.session_state.badges = []

# --- Încărcarea Modelelor ---
with st.spinner("Se încarcă modelele NLP... Poate dura un moment."):
    qg_pipeline, qa_pipeline = load_models()

st.success("Modelele NLP au fost încărcate cu succes!")
st.markdown("---")

# --- PASUL 1: Încărcarea PDF-ului ---
st.header("1. Încarcă Cursul (PDF)")
uploaded_file = st.file_uploader("Alege un fișier PDF:", type="pdf")

if uploaded_file is not None:
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text()

        st.session_state.context_text = full_text
        st.success("PDF procesat cu succes! Textul a fost extras.")

    except Exception as e:
        st.error(f"Eroare la procesarea PDF-ului: {e}")
else:
    st.session_state.context_text = ""

if not st.session_state.context_text:
    st.info("Aștept încărcarea unui fișier PDF.")

st.markdown("---")

# --- PASUL 2: Generarea Quiz-ului ---
if st.session_state.context_text and not st.session_state.quiz_in_progress:
    st.header("2. Generează Quiz")
    st.write("Alege câte întrebări dorești să generezi din document.")

    num_questions = st.number_input(
        "Număr de întrebări:",
        min_value=1, max_value=10, value=3, step=1
    )

    if st.button(f"✨ Începe Quiz cu {num_questions} Întrebări"):
        if st.session_state.context_text:
            with st.spinner("AI-ul gândește... Se generează întrebările și răspunsurile..."):

                st.session_state.quiz_questions = []
                st.session_state.current_question_index = 0
                st.session_state.score = 0

                text_chunks = split_text_into_chunks(st.session_state.context_text)

                if not text_chunks:
                    st.error("Textul extras este prea scurt pentru a genera întrebări.")
                else:
                    generated_count = 0
                    while generated_count < num_questions:
                        random_chunk = random.choice(text_chunks)
                        input_string = f"generate question: {random_chunk}"

                        try:
                            # 1. Generăm Întrebarea
                            # --- AICI ESTE MODIFICAREA ---
                            # Am adăugat do_sample=True pentru a forța variația
                            qg_output = qg_pipeline(input_string,
                                                    max_length=64,
                                                    do_sample=True)
                            question = qg_output[0]['generated_text']

                            # 2. Găsim Răspunsul
                            qa_output = qa_pipeline(question=question, context=random_chunk)
                            answer = qa_output['answer']

                            if qa_output['score'] > 0.1:
                                st.session_state.quiz_questions.append((question, answer, random_chunk))
                                generated_count += 1

                        except Exception as e:
                            pass

                    st.session_state.quiz_in_progress = True
                    st.rerun()

        else:
            st.warning("Vă rugăm să încărcați un fișier PDF mai întâi.")

# --- PASUL 3: Desfășurarea Quiz-ului ---
if st.session_state.quiz_in_progress:

    total_questions = len(st.session_state.quiz_questions)

    if st.session_state.current_question_index >= total_questions:
        st.header(f"🎉 Quiz Terminat! Scorul tău: {st.session_state.score} / {total_questions}")
        st.subheader(f"XP Total Câștigat: {st.session_state.xp}")

        if st.session_state.badges:
            st.write("Insigne Câștigate:")
            for badge in st.session_state.badges:
                st.success(f"🏅 {badge}")

        if st.button("Începe un Quiz Nou"):
            st.session_state.quiz_in_progress = False
            st.session_state.context_text = ""
            st.session_state.quiz_questions = []
            st.rerun()

    else:
        q, a, c = st.session_state.quiz_questions[st.session_state.current_question_index]

        st.header(f"Întrebarea {st.session_state.current_question_index + 1} / {total_questions}")
        st.info(q)

        with st.form(key=f"q_form_{st.session_state.current_question_index}"):
            user_answer = st.text_input("Răspunsul tău:")
            submit_button = st.form_submit_button("Verifică Răspunsul")

        if submit_button:
            # Comparație simplă
            if user_answer.lower().strip() == a.lower().strip():
                st.success(f"**Corect!** Răspunsul a fost: **{a}**")
                st.session_state.score += 1
                st.session_state.xp += 10

                if st.session_state.xp >= 50 and "Savant de Bronz (50 XP)" not in st.session_state.badges:
                    st.balloons()
                    st.write("🎉 **Insignă Câștigată: Savant de Bronz (50 XP)!**")
                    st.session_state.badges.append("Savant de Bronz (50 XP)")

            else:
                st.error(f"**Greșit.** Răspunsul corect era: **{a}**")

            st.caption("Contextul din document:")
            st.markdown(f">...{c.replace(a, f'**{a}**')}...")

            st.session_state.current_question_index += 1

            if st.button("Următoarea Întrebare"):
                st.rerun()
