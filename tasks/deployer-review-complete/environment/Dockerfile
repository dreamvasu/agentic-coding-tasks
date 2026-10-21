FROM python:3.11

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# The relocated ZenML Kubernetes-deployer slice: the built-in templates, the
# template engine, the deployer that assembles the label/selector context, the
# render entry point, and the in-repo tests. The grading verifier
# (tests/test_outputs.py) and its held-out scenario are NOT copied into the image.
COPY app/ /app/

# The manifest-rendering path needs Jinja2 (templating), PyYAML (parsing the
# rendered manifests) and Pydantic (the settings/deployment models).
RUN pip install --no-cache-dir \
    "jinja2==3.1.6" \
    "PyYAML==6.0.2" \
    "pydantic==2.12.5"

# Make /app authoritative so `import zenml...` resolves to the relocated slice.
ENV PYTHONPATH=/app

# Sanity: the package imports and the deployer renders both manifests at build
# time (this also prints the reported empty-endpoints symptom on the current
# code).
RUN python -c "import zenml.integrations.kubernetes.deployers.kubernetes_deployer as m; print('deployer import OK')"
RUN python /app/render_manifests.py
