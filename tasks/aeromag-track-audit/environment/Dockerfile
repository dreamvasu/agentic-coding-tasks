FROM python:3.11

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# ppigrf carries the IGRF Gauss coefficients as data files inside the package
# (the .shc tables it reads at import time), so pinning the package pins the
# coefficient set the field evaluation actually uses. Relocate the whole package
# into /app and make /app authoritative via PYTHONPATH: a later
# `pip install -U ppigrf` lands in site-packages but the /app copy still wins the
# import, so the coefficients in play do not change.
RUN pip install --no-cache-dir "ppigrf==1.0.0" "numpy==2.4.6" "pandas==3.0.5"
RUN set -eux; \
    SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    mv "$SP/ppigrf" /app/ppigrf
ENV PYTHONPATH=/app

RUN python -c "import ppigrf, os; \
    d=os.path.dirname(ppigrf.__file__); \
    assert d == '/app/ppigrf', d; \
    print('ppigrf resolved from', d)"

COPY app /app
RUN chmod +x /app/ops/reduce.sh
