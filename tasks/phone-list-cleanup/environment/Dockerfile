FROM python:3.11

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir "phonenumbers==8.13.52"

# Relocate phonenumbers (with its bundled numbering-plan/carrier/geocoder data) to
# /app and make /app authoritative via PYTHONPATH. This pins the version that is
# actually imported: a plain `pip install -U phonenumbers` installs into
# site-packages but PYTHONPATH=/app keeps the relocated copy in front, so the
# import does not change. phonenumbers is pure-python (no compiled extensions).
RUN set -eux; \
    SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    mv "$SP/phonenumbers" /app/phonenumbers
ENV PYTHONPATH=/app
RUN python -c "import phonenumbers, os; \
    assert os.path.dirname(phonenumbers.__file__)=='/app/phonenumbers', phonenumbers.__file__; \
    print('pinned phonenumbers', phonenumbers.__version__, 'at', os.path.dirname(phonenumbers.__file__))"

COPY data/contacts.csv /app/contacts.csv
