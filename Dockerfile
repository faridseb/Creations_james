FROM python:3.10

WORKDIR /app

# Installer les dépendances système pour mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Exposer le port
EXPOSE 8000

# Commande par défaut pour démarrer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "creationjames.wsgi:application"] 