FROM python:3.12

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# apache-airflow 2.10.5 (wheel + official py3.12 constraints)
RUN pip install "apache-airflow==2.10.5" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"

# Relocate airflow to /app/airflow and redirect imports there, so any edit the agent makes
# to /app/airflow/**/*.py takes effect immediately (editable-equivalent, no rebuild).
RUN set -eux; \
    SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    mkdir -p /app; \
    mv "$SP/airflow" /app/airflow; \
    printf '/app\n' > "$SP/airflow_editable.pth"; \
    python -c "import airflow; assert airflow.__file__ == '/app/airflow/__init__.py', airflow.__file__"

# Faithful minimal reproduction DAG the agent inspects/runs
COPY data /app/data

WORKDIR /app
