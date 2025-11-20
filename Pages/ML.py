import streamlit as st
from transformers import pipeline
import fitz  # PyMuPDF
import random

# --- Configurarea Aplicației Streamlit ---
st.set_page_config(page_title="EduLearn Quiz & Summary", layout="centered")
st.title("📚 EduLearn - Quiz Generator & Sumarizator Inteligent")


# --- Motorul NLP (Hugging Face) ---
@st.cache_resource
def load_models():
    # 1. Modelul de Generare a Întrebărilor (QG)
    t5_qg_summary_name = "valhalla/t5-small-qg-prepend"
    t5_pipeline = pipeline("text2text-generation", model=t5_qg_summary_name, use_fast=False)

    # 2. Modelul de Răspuns la Întrebări (QA)
    qa_model_name = "distilbert-base-cased-distilled-squad"
    qa_pipeline = pipeline("question-answering", model=qa_model_name)

    # 3. Model dedicat pentru Sumarizare (BART - Fallback)
    try:
        # Încercăm BART-base care este mai mic decât BART-large
        summarizer_pipeline = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", use_fast=False)
    except Exception as e:
        # Dacă BART-base eșuează, folosim T5 Fallback
        st.warning(f"Modelul BART a eșuat la încărcare ({e}). Se folosește T5 pentru sumarizare.")
        summarizer_pipeline = pipeline("summarization", model="falconsai/text_summarization", use_fast=False)

    return t5_pipeline, summarizer_pipeline, qa_pipeline


# --- Funcție pentru împărțirea textului (Chunking) ---
def split_text_into_chunks(text, chunk_size=1500, overlap=300):
    chunks = []
    text = ' '.join(text.split())
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# --- Funcție NOUĂ pentru Generarea Rezumatului (MAP-REDUCE) ---
def generate_summary(text, pipeline, max_new_tokens=80, min_length=20,
                     chunk_size=3800, overlap=50, show_progress=False):
    """ Generează rezumatul (Logica Map-Reduce) """
    if not text or not text.strip():
        return "Eroare: Textul este gol."

    text = ' '.join(text.split())
    chunks = split_text_into_chunks(text, chunk_size=chunk_size, overlap=overlap)

    partials = []

    for idx, chunk in enumerate(chunks):
        input_text = chunk.strip()
        if getattr(pipeline, "task", "") == "text2text-generation":
            input_to_call = "summarize: " + input_text
        else:
            input_to_call = input_text

        try:
            out = pipeline(
                input_to_call,
                max_length=max_new_tokens,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            text_out = ""
            if isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict):
                text_out = out[0].get('summary_text') or out[0].get('generated_text') or ""
            elif isinstance(out, dict):
                text_out = out.get('summary_text') or out.get('generated_text') or ""
            text_out = (text_out or "").strip()
            if not text_out:
                text_out = chunk[:200].strip() + "..."
        except Exception as e:
            text_out = chunk[:200].strip() + "..."

        partials.append(text_out)

        if show_progress:
            st.write(f"Parțial {idx + 1}/{len(chunks)}:")
            st.info(text_out)

    combined = " ".join(partials)
    final = combined
    if len(partials) > 1:
        try:
            reduce_input = combined
            if getattr(pipeline, "task", "") == "text2text-generation":
                reduce_input = "summarize: " + combined

            out2 = pipeline(
                reduce_input,
                max_length=max_new_tokens,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            if isinstance(out2, list) and len(out2) > 0 and isinstance(out2[0], dict):
                final = out2[0].get('summary_text') or out2[0].get('generated_text') or combined
            elif isinstance(out2, dict):
                final = out2.get('summary_text') or out2.get('generated_text') or combined
            final = final.strip()
        except Exception:
            final = combined

    return final


# --- Inițializarea stării sesiunii (Session State) ---
if 'context_text' not in st.session_state:
    st.session_state.context_text = ""
if 'pdf_summary' not in st.session_state:
    st.session_state.pdf_summary = ""
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
with st.spinner("Se încarcă modelele NLP (T5 Generator/Summarizer și QA)... Poate dura un moment."):
    t5_pipeline, summarizer_pipeline, qa_pipeline = load_models()

st.success("Modelele NLP au fost încărcate cu succes!")
st.markdown("---")

# --- PASUL 1: Încărcarea PDF-ului și Rezumatul ---
st.header("1. Încarcă Cursul (PDF)")
uploaded_file = st.file_uploader("Alege un fișier PDF:", type="pdf")

if uploaded_file is not None:
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text()

        st.session_state.context_text = full_text
        st.session_state.pdf_summary = ""
        st.success("PDF procesat cu succes! Textul a fost extras.")

    except Exception as e:
        st.error(f"Eroare la procesarea PDF-ului: {e}")
        st.session_state.context_text = ""
else:
    st.session_state.context_text = ""
    st.session_state.pdf_summary = ""

# --- Secțiunea NOUĂ de Rezumat (Vizibilă după încărcare) ---
if st.session_state.context_text:
    st.subheader("1.1. Instrument de Sumarizare")

    # Afișează rezumatul sau eroarea dacă există
    if st.session_state.pdf_summary and "Eroare" not in st.session_state.pdf_summary:
        st.info("Rezumatul extras:")
        st.markdown(f"> **{st.session_state.pdf_summary}**")
    elif "Eroare" in st.session_state.pdf_summary:
        st.error(st.session_state.pdf_summary)

    # Butonul de generare a rezumatului
    if st.button("📝 Generează Rezumatul Documentului"):
        with st.spinner("AI-ul gândește... Se generează rezumatul..."):
            summary = generate_summary(
                st.session_state.context_text,
                summarizer_pipeline,
                max_new_tokens=80,
                min_length=20,
                chunk_size=3800,
                overlap=50,
                show_progress=True
            )

            if not summary:
                st.session_state.pdf_summary = "Eroare: Rezumatul generat este gol. Vă rugăm să încercați un alt document."
            else:
                st.session_state.pdf_summary = summary
                st.rerun()

    st.markdown("---")

if not st.session_state.context_text:
    st.info("Aștept încărcarea unui fișier PDF.")

# --- PASUL 2: Generarea Quiz-ului (Rămâne neschimbat) ---
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

                # Folosim funcția existentă de chunking pentru quiz
                text_chunks = split_text_into_chunks(st.session_state.context_text, chunk_size=1500, overlap=300)

                if not text_chunks:
                    st.error("Textul extras este prea scurt pentru a genera întrebări.")
                else:
                    generated_count = 0
                    while generated_count < num_questions:
                        # Logică de generare a întrebărilor și răspunsurilor (neschimbată)
                        random_chunk = random.choice(text_chunks)
                        # Prefix QG
                        input_string = f"generate question: {random_chunk}"

                        try:
                            # 1. Generăm Întrebarea (Folosim t5_pipeline)
                            qg_output = t5_pipeline(input_string,
                                                    do_sample=True)
                            question = qg_output[0]['generated_text']

                            # 2. Găsim Răspunsul (Folosim qa_pipeline)
                            qa_output = qa_pipeline(question=question, context=random_chunk)
                            answer = qa_output['answer']

                            if qa_output['score'] > 0.1:
                                st.session_state.quiz_questions.append((question, answer, random_chunk))
                                generated_count += 1

                        except Exception as e:
                            # st.caption(f"Eroare la generarea întrebării: {e}") # Debugging
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

        # Final Quiz Buttons
        if st.button("Începe un Quiz Nou"):
            st.session_state.quiz_in_progress = False
            st.session_state.quiz_questions = []
            st.session_state.current_question_index = 0
            st.rerun()

    else:
        q, a, c = st.session_state.quiz_questions[st.session_state.current_question_index]

        st.header(f"Întrebarea {st.session_state.current_question_index + 1} / {total_questions}")
        st.info(q)

        # 1. Formularul de răspuns (conține doar răspunsul și butonul de submit)
        with st.form(key=f"q_form_{st.session_state.current_question_index}"):
            user_answer = st.text_input("Răspunsul tău:")
            # Acesta este singurul buton permis în formular
            submit_button = st.form_submit_button("Verifică Răspunsul")

        # 2. Logica de Verificare (Dacă submit_button a fost apăsat)
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
            context_highlighted = c.replace(a, f'**{a}**')
            st.markdown(f"> ...{context_highlighted}...")

            # 3. Butonul de Navigare (ATENȚIE: în afara with st.form)
            # Acesta apare numai după ce s-a verificat răspunsul
            st.session_state.current_question_index += 1
            if st.button("Următoarea Întrebare"):
                st.rerun()