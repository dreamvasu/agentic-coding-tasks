FROM python:3.11

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# Install the tz database and relocate it (with its zone rules) to /app, then make
# /app authoritative via PYTHONPATH. This pins the version that is actually
# imported: a plain `pip install -U tzdata` installs into site-packages but
# PYTHONPATH=/app keeps the relocated copy in front, so the import does not change.
# tzdata is pure-python (no compiled extensions).
RUN pip install --no-cache-dir "tzdata==2023.3"
RUN set -eux; \
    SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    mv "$SP/tzdata" /app/tzdata
ENV PYTHONPATH=/app

# Make zoneinfo read the bundled tzdata package instead of any system copy. An
# empty TZPATH sends zoneinfo straight to the tzdata package; removing the system
# zoneinfo directories keeps that fallback in force even for a subprocess that does
# not inherit the environment variable.
ENV PYTHONTZPATH=""
RUN rm -rf /usr/share/zoneinfo /usr/lib/zoneinfo /usr/share/lib/zoneinfo /etc/zoneinfo

RUN python -c "import os, tzdata, zoneinfo; \
    from datetime import datetime, timezone; from zoneinfo import ZoneInfo; \
    assert os.path.dirname(tzdata.__file__)=='/app/tzdata', tzdata.__file__; \
    print('pinned tzdata', tzdata.IANA_VERSION, 'at', os.path.dirname(tzdata.__file__)); \
    print('resolver reads', datetime(2025,6,15,tzinfo=timezone.utc).astimezone(ZoneInfo('Asia/Almaty')).utcoffset(), 'for Asia/Almaty')"

COPY data/locations.csv /app/locations.csv
