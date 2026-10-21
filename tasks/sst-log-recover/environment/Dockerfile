FROM ubuntu:24.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
        python3 python3-pip libleveldb-dev build-essential xxd \
    && rm -rf /var/lib/apt/lists/*

# The LevelDB python binding, so the store can be opened with the real engine.
RUN pip install --no-cache-dir --break-system-packages "plyvel==1.5.1"

RUN mkdir -p output

COPY data/store /app/data/store
