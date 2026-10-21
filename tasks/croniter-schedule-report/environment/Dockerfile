FROM python:3.12

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# croniter 6.2.0 (pure python; depends only on python-dateutil).
RUN pip install --timeout 300 --retries 10 "croniter==6.2.0"

# Relocate croniter to /app/croniter and make /app authoritative via PYTHONPATH, so edits to
# /app/croniter take effect immediately and a plain `pip install -U croniter` cannot shadow it.
RUN set -eux; \
    SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    mkdir -p /app; \
    mv "$SP/croniter" /app/croniter
ENV PYTHONPATH=/app
RUN python -c "import croniter, os; assert os.path.dirname(croniter.__file__) == '/app/croniter', croniter.__file__"

COPY data/schedules.json /app/schedules.json

WORKDIR /app
