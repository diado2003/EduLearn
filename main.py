import streamlit as st
from huggingface_hub import snapshot_download
# fallback
from transformers import AutoTokenizer,pipeline

# --- Configurarea Aplicației Streamlit ---
st.set_page_config(page_title="EduLearn Generator", layout="centered")
st.title("🤖 Generator de Întrebări EduLearn")


# --- Motorul NLP (Hugging Face) ---
# Această funcție folosește cache-ul Streamlit pentru a nu re-descărca
# modelul de fiecare dată când rulează scriptul. Se încarcă o singură dată.
@st.cache_resource
def load_nlp_pipeline():
    # Alegem un model mic, specializat pe generarea de întrebări (QG)
    # Acesta este un model T5 "finetunat" pentru sarcina de QG
    # "valhalla/t5-small-qg-prepend" este open-source și gratuit.
    model_name = "valhalla/t5-small-qg-prepend"
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)

    # Încărcăm "conducta" (pipeline)
    # Prima dată când rulează, va descărca automat modelul (poate dura 1-2 min)
    qg_pipeline = pipeline("text2text-generation", model=model_name)
    return qg_pipeline


# Încărcăm modelul (cu mesaj de așteptare)
with st.spinner("Se încarcă modelul NLP... Poate dura un moment."):
    generator_nlp = load_nlp_pipeline()

st.success("Modelul NLP a fost încărcat cu succes!")
st.markdown("---")

# --- Interfața Utilizator ---

st.header("1. Introduceți Contextul")
st.write("Introduceți textul din cursul dumneavoastră (de preferat 1-2 paragrafe):")

# Textul din care se generează întrebarea
context_text = st.text_area("Textul Contextului:",
                            """Hello Kitty (Kiti howaito?) este un personaj fictiv produs de compania japoneză Sanrio. Acest personaj a fost creat de către Yuko Shimizu, iar în prezent este proiectat de către Yuko Yamaguchi. Hello Kitty reprezintă o pisicuță albă care zâmbește și poartă mereu o fundiță roșie.

Hello Kitty apare pentru prima dată pe o pungă, în Japonia în anul 1974, iar mai târziu,în 1976, acesta ajunge și în Statele Unite. Caracterul reprezintă un segment din cultura japoneză populară. Până în anul 2010, Sanrio a reușit să facă din Hello Kiity un fenomen de marketing la nivel global, ce a adus câștiguri în valoare de 5 miliarde de dolari pe an. În 2014, când Hello Kitty a împlinit 40 de ani, valoarea ei reprezenta aproximativ 7 miliarde de dolari pe an, toate acestea fără publicitate.

Piața Hello Kitty vizează femeile, pre-adolescentele, tinerele fete, dar mai nou, aceștia au introdus o gamă de produse dedicată și adulților. Pisicuța se găsește într-o gamă variată de produse începând cu rechizite școlare pentru cei mici până la produse cosmetice și haine. Ea este de asemenea prezentă și la TV în diferite serii de televiziune dedicate celor mici.""",
                            height=150)

# Butonul de generare
if st.button("✨ Generează Întrebare"):
    if context_text:
        with st.spinner("AI-ul gândește... Se generează întrebarea..."):
            # Pregătim inputul pentru modelul T5
            # Formatul "generate question: [CONTEXT]" este specific acestui model
            input_string = f"generate question: {context_text}"

            # Rulăm modelul NLP
            generated_output = generator_nlp(input_string, max_length=64)

            # Extragem textul întrebării
            generated_question = generated_output[0]['generated_text']

            # Afișăm rezultatul
            st.subheader("2. Rezultat Generat")
            st.info(generated_question)
    else:
        st.warning("Vă rugăm să introduceți un text în câmpul de context.")


st.write(":purple_heart:")
st.divider()
st.write(":green[buna] :alien: ")
st.divider()
st.badge("Extraterestrial", icon=":material/check:", color="green")
st.divider()
