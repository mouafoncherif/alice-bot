FROM python:3.11-slim

# Évite les messages d'erreur de pip
ENV PYTHONUNBUFFERED=1

# Définit le répertoire de travail
WORKDIR /app

# Copie les fichiers requis
COPY requirements.txt .

# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du code
COPY alicebot.py .

# Lance le bot
CMD ["python", "alicebot.py"]
