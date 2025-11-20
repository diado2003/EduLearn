# 1. Baza: Folosim o imagine Python subțire (slim) pentru a menține dimensiunea redusă
FROM python:3.11-slim

# 2. Configurare: Setăm variabile de mediu critice pentru Streamlit
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501

# 3. Directorul de Lucru: Setăm /app ca director principal în container
WORKDIR /app

# 4. Dependențe: Copiem și instalăm cerințele.txt
#    Asta se face într-un pas separat pentru a folosi cache-ul Docker dacă doar codul se schimbă.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Codul Aplicației: Copiem toate celelalte fișiere (inclusiv app.py)
#    Punctul . se referă la directorul curent al mașinii gazdă.
COPY . .

# 6. Portul: Declarăm portul pe care Streamlit va asculta
EXPOSE 8501

# 7. Pornirea Aplicației: Comanda care va rula când pornește containerul
#    --server.address=0.0.0.0 este esențial pentru accesul extern din container.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]