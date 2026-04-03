# CrewChief ITA Voice Pack - Dockerfile
# Basato su crew-chief-autovoicepack, adattato per la generazione di voice pack italiani
#
# Build:   docker build -t crewchief-ita-voicepack .
# Run:     docker run --gpus all crewchief-ita-voicepack

FROM nvidia/cuda:12.9.1-base-ubuntu22.04

# Evita prompt interattivi durante l'installazione
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Rome

# Dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    espeak-ng \
    sox \
    libsox-fmt-all \
    ffmpeg \
    git \
    git-lfs \
    wget \
    curl \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Supporto locale italiano
RUN sed -i '/it_IT.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen it_IT.UTF-8
ENV LANG=it_IT.UTF-8
ENV LANGUAGE=it_IT:it
ENV LC_ALL=it_IT.UTF-8

# Inizializza git-lfs
RUN git lfs install

# Directory di lavoro
WORKDIR /app

# Crea ambiente virtuale Python
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Aggiorna pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Installa PyTorch con supporto CUDA
RUN pip install --no-cache-dir \
    torch \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Installa coqui-tts e dipendenze TTS
RUN pip install --no-cache-dir \
    coqui-tts>=0.22.0 \
    deepspeed

# Installa xtts-integrity per la validazione audio
RUN pip install --no-cache-dir xtts-integrity

# Copia requirements e installa dipendenze Python del progetto
COPY voice_generator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia file del progetto
COPY voice_generator/*.py /app/voice_generator/
COPY voice_generator/voices_config.yaml /app/voices_config.yaml
COPY lexicon/*.csv /app/lexicon/

# Crea directory di output e reference_audio
RUN mkdir -p /app/output /app/reference_audio

# Variabili d'ambiente per cache modelli
ENV TORCH_HOME=/app/.cache/torch
ENV HF_HOME=/app/.cache/huggingface
ENV COQUI_TOS_AGREED=1

# Volumi per persistenza dati
VOLUME ["/app/output", "/app/reference_audio"]

# Esponi la directory di output
EXPOSE 8080

# Comando predefinito: genera voice pack con voce Marco
CMD ["python3", "voice_generator/generate_voices.py", "--voice", "Marco", "--config", "voices_config.yaml"]
