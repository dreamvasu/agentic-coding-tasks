"""Grading verifier for the ZenML Kubernetes deployer selector review task.

The rendered Kubernetes resources must route correctly for ANY user label
configuration. This verifier grades the rendered selectors -- never a specific
edit -- so a fix in the templates OR in the deployer's context-building code is
honored equally.

Anti-cheat design (two-stage render; no agent Python ever runs in the grading
process):

* STAGE 1 -- context only. A throwaway subprocess (``PYTHONPATH=/app``) runs the
  agent's real deployer (``_initialize_deployment_context`` ->
  ``_build_template_context``) and emits ONLY the template *context* (labels,
  name, settings, ...) as JSON. This is the legitimate Site-D fix surface (the
  deployer decides the label dict); it cannot fabricate the rendered selectors,
  because it does not render.

* STAGE 2 -- render, verifier-owned. A second subprocess launched with the test
  runner's OWN interpreter (pinned jinja2 / PyYAML from the isolated pytest venv,
  NOT the container's ``/app``) reproduces the deployer's Jinja2 environment
  verbatim and renders the agent's template *files as data*. It imports no agent
  Python and ``/app`` is not on its path, so a planted ``/app/sitecustomize.py``
  or a module-level monkeypatch in an imported deployer/engine cannot execute
  inside it. The rendered selectors therefore genuinely come from the agent's
  shipped templates + context, so "hard-coding the output" is not possible.

* STAGE 3 -- the pytest process below only reads the rendered selectors (JSON)
  and checks the routing invariants; it never renders agent-controlled input, so
  template-side SSTI cannot reach the grading logic.

Scenarios:

* VISIBLE GATE (single deployment, the reported symptom): a user sets a custom
  ``app`` pod label. The Service selector must still select the deployment's pods.

* HELD-OUT (two deployments, never shown to the agent): both pin
  ``zenml-deployment-id`` and ``zenml-deployment-name`` to the SAME constant via
  ``settings.labels``. Each Deployment's ``matchLabels`` must select ONLY its own
  pod; if the two selectors collide, the ReplicaSet controllers fight over each
  other's pods and endpoints churn to empty (the same user-visible symptom,
  reached at the Deployment selector site). The held-out scenario data lives only
  in this file.
"""

import json
import os
import subprocess
import sys
import tempfile

import pytest

APP_DIR = "/app"
TPL_DIR = os.path.join(
    APP_DIR, "zenml", "integrations", "kubernetes", "templates", "kubernetes"
)

# ---------------------------------------------------------------------------
# STAGE 1 -- build ONLY the template context via the agent's deployer.
# Runs under the container interpreter with PYTHONPATH=/app. Its sole output is
# context data; it never renders, so it cannot fabricate a passing selector.
# ---------------------------------------------------------------------------
_CONTEXT_PROBE = r'''
import json
import sys

from zenml.integrations.kubernetes.deployers._offline import (
    DeploymentResponse,
    PipelineSnapshotResponse,
)
from zenml.integrations.kubernetes.deployers.kubernetes_deployer import (
    KubernetesDeployer,
)
from zenml.integrations.kubernetes.flavors.kubernetes_deployer_flavor import (
    KubernetesDeployerSettings,
)
from zenml.integrations.kubernetes.pod_settings import KubernetesPodSettings


def build(item):
    pod_labels = item.get("pod_labels")
    pod_settings = (
        KubernetesPodSettings(labels=dict(pod_labels))
        if pod_labels is not None
        else None
    )
    settings = KubernetesDeployerSettings(
        labels=dict(item.get("settings_labels") or {}),
        pod_settings=pod_settings,
    )
    snapshot = PipelineSnapshotResponse(settings=settings)
    deployment = DeploymentResponse(
        id=item["deployment_id"],
        name=item.get("deployment_name", item["deployment_id"]),
        snapshot=snapshot,
    )
    deployer = KubernetesDeployer(name="kubernetes")
    ctx = deployer._initialize_deployment_context(deployment)
    context = deployer._build_template_context(
        deployment=deployment,
        settings=ctx.settings,
        resource_name=ctx.resource_name,
        namespace=ctx.namespace,
        labels=ctx.labels,
        image=ctx.image,
        env_vars={},
        secret_env_vars={},
        secret_name=ctx.secret_name,
        resource_requests={},
        resource_limits={},
        replicas=1,
    )
    # The Jinja2 templates never reference `deployment`; drop it so the context
    # is plain JSON (settings / pod_settings are dumped to dicts below).
    context.pop("deployment", None)
    return context


def _default(obj):
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        try:
            return dump(mode="json")
        except TypeError:
            return dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


spec = json.load(open(sys.argv[1], encoding="utf-8"))
contexts = [build(x) for x in spec]
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(contexts, handle, default=_default)
'''

# ---------------------------------------------------------------------------
# STAGE 2 -- verifier-owned render. Reproduces the deployer's Jinja2 environment
# verbatim (KubernetesTemplateEngine) and renders the agent's template FILES as
# data. Imports no agent Python; /app is not on its path.
# ---------------------------------------------------------------------------
_RENDER_STAGE = r'''
import json
import os
import sys

import yaml
from jinja2 import Environment, StrictUndefined, select_autoescape


def _to_yaml(obj):
    return yaml.safe_dump(
        obj, default_flow_style=False, allow_unicode=True
    ).rstrip()


def _to_json(obj):
    return json.dumps(obj)


def _engine():
    env = Environment(
        undefined=StrictUndefined,
        autoescape=select_autoescape(
            enabled_extensions=("html", "htm", "xml"),
            default=False,
            default_for_string=False,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["to_yaml"] = _to_yaml
    env.filters["tojson"] = _to_json
    return env


def _render_file(env, path, context):
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    text = env.from_string(source).render(**context)
    docs = [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]
    if not docs:
        raise ValueError("template %s rendered no document" % path)
    return docs[0]


tpl_dir = sys.argv[1]
contexts = json.load(open(sys.argv[2], encoding="utf-8"))
env = _engine()
out = []
for ctx in contexts:
    dep = _render_file(env, os.path.join(tpl_dir, "deployment.yaml.j2"), ctx)
    svc = _render_file(env, os.path.join(tpl_dir, "service.yaml.j2"), ctx)
    out.append(
        {
            "service_selector": svc["spec"]["selector"],
            "deployment_matchLabels": dep["spec"]["selector"]["matchLabels"],
            "pod_labels": dep["spec"]["template"]["metadata"]["labels"],
        }
    )
with open(sys.argv[3], "w", encoding="utf-8") as handle:
    json.dump(out, handle)
'''

# Scenario 0 is the visible gate; scenarios 1 and 2 are the held-out
# cross-deployment collision (both pin the identity labels to a shared constant).
SPEC = [
    {
        "deployment_id": "11111111",
        "deployment_name": "checkout-api",
        "pod_labels": {"app": "team-frontend"},
    },
    {
        "deployment_id": "aaaaaaaa",
        "deployment_name": "fraud-scorer",
        "settings_labels": {
            "zenml-deployment-id": "prod-scorer",
            "zenml-deployment-name": "prod-scorer",
        },
    },
    {
        "deployment_id": "bbbbbbbb",
        "deployment_name": "risk-scorer",
        "settings_labels": {
            "zenml-deployment-id": "prod-scorer",
            "zenml-deployment-name": "prod-scorer",
        },
    },
]


def _container_python():
    for candidate in (
        "/usr/local/bin/python3",
        "/usr/local/bin/python",
        "/usr/bin/python3",
    ):
        if os.path.exists(candidate):
            return candidate
    import shutil

    return shutil.which("python3") or sys.executable


def _selects(selector, pod_labels):
    """Whether every key/value in ``selector`` is present in ``pod_labels``."""
    return bool(selector) and all(
        pod_labels.get(k) == v for k, v in selector.items()
    )


@pytest.fixture(scope="module")
def rendered():
    """Render the scenarios: agent deployer -> context (stage 1), then a
    verifier-owned engine -> selectors (stage 2). No agent code runs here."""
    assert os.path.isdir(APP_DIR), "/app does not exist"
    assert os.path.isdir(TPL_DIR), "template directory missing under /app"

    with tempfile.TemporaryDirectory() as work:
        spec_path = os.path.join(work, "spec.json")
        ctx_path = os.path.join(work, "contexts.json")
        out_path = os.path.join(work, "out.json")
        ctx_probe = os.path.join(work, "_context_probe.py")
        render_stage = os.path.join(work, "_render_stage.py")
        with open(spec_path, "w", encoding="utf-8") as handle:
            json.dump(SPEC, handle)
        with open(ctx_probe, "w", encoding="utf-8") as handle:
            handle.write(_CONTEXT_PROBE)
        with open(render_stage, "w", encoding="utf-8") as handle:
            handle.write(_RENDER_STAGE)

        # Stage 1: agent deployer builds the context (PYTHONPATH=/app).
        env1 = dict(os.environ)
        env1["PYTHONPATH"] = APP_DIR + os.pathsep + env1.get("PYTHONPATH", "")
        proc1 = subprocess.run(
            [_container_python(), ctx_probe, spec_path, ctx_path],
            env=env1,
            capture_output=True,
            text=True,
        )
        assert proc1.returncode == 0, (
            "stage 1 (building the template context through the deployer under "
            "/app) failed (exit %d).\nstdout:\n%s\nstderr:\n%s"
            % (proc1.returncode, proc1.stdout, proc1.stderr)
        )

        # Stage 2: verifier-owned render, no agent Python, /app not on the path.
        env2 = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        env2["PYTHONNOUSERSITE"] = "1"
        proc2 = subprocess.run(
            [sys.executable, render_stage, TPL_DIR, ctx_path, out_path],
            env=env2,
            cwd=work,
            capture_output=True,
            text=True,
        )
        assert proc2.returncode == 0, (
            "stage 2 (rendering the agent's templates through the verifier's own "
            "engine) failed (exit %d).\nstdout:\n%s\nstderr:\n%s"
            % (proc2.returncode, proc2.stdout, proc2.stderr)
        )
        assert os.path.exists(out_path), "render stage produced no output"
        with open(out_path, encoding="utf-8") as handle:
            data = json.load(handle)

    assert isinstance(data, list) and len(data) == len(SPEC), (
        "expected %d rendered results, got %r" % (len(SPEC), data)
    )
    for item, spec in zip(data, SPEC):
        item["deployment_id"] = spec["deployment_id"]
    return data


def test_visible_service_routes(rendered):
    """VISIBLE GATE: with a custom pod label, the Service still selects its pods.

    This is the reported symptom. A change that fails here has broken the obvious
    single-deployment case and cannot pass the task.
    """
    gate = rendered[0]
    assert _selects(gate["service_selector"], gate["pod_labels"]), (
        "Service gets no endpoints on the reported single-deployment case: "
        "selector %r does not select the rendered pod labels %r when the user "
        "sets a custom pod label."
        % (gate["service_selector"], gate["pod_labels"])
    )


def test_each_service_routes_to_own_pods(rendered):
    """Every deployment's Service selects its own pods (both held-out ones too)."""
    problems = []
    for item in rendered:
        if not _selects(item["service_selector"], item["pod_labels"]):
            problems.append(
                "%s: Service selector %r does not select pod labels %r"
                % (
                    item["deployment_id"],
                    item["service_selector"],
                    item["pod_labels"],
                )
            )
    assert not problems, "\n".join(problems)


def test_deployment_selects_own_pods(rendered):
    """Every deployment's matchLabels selects its own pod template."""
    problems = []
    for item in rendered:
        if not _selects(item["deployment_matchLabels"], item["pod_labels"]):
            problems.append(
                "%s: matchLabels %r does not select its own pod labels %r"
                % (
                    item["deployment_id"],
                    item["deployment_matchLabels"],
                    item["pod_labels"],
                )
            )
    assert not problems, "\n".join(problems)


def test_matchlabels_do_not_collide_across_deployments(rendered):
    """HELD-OUT: two deployments pinning the identity labels to a shared constant
    must NOT end up selecting each other's pods.

    Each Deployment's ``matchLabels`` must select only its own pod. If the
    selector keys on a user-overridable label, the two deployments render
    identical ``matchLabels`` and each one grabs the other's pod -- the
    controllers fight and endpoints churn to empty (the reported symptom, reached
    at the Deployment selector site).
    """
    dep_a = rendered[1]
    dep_b = rendered[2]

    a_grabs_b = _selects(dep_a["deployment_matchLabels"], dep_b["pod_labels"])
    b_grabs_a = _selects(dep_b["deployment_matchLabels"], dep_a["pod_labels"])

    assert not (a_grabs_b or b_grabs_a), (
        "Cross-deployment selector collision: two deployments that both set "
        "zenml-deployment-id/zenml-deployment-name via settings.labels render "
        "overlapping Deployment matchLabels, so each selects the other's pods.\n"
        "  deployment %s matchLabels: %r\n"
        "  deployment %s matchLabels: %r\n"
        "  %s pods: %r\n  %s pods: %r\n"
        "  %s selects %s pods: %s\n  %s selects %s pods: %s\n"
        "The selector must key on a value the user cannot reach (unique per "
        "deployment), so it selects only its own pods."
        % (
            dep_a["deployment_id"],
            dep_a["deployment_matchLabels"],
            dep_b["deployment_id"],
            dep_b["deployment_matchLabels"],
            dep_a["deployment_id"],
            dep_a["pod_labels"],
            dep_b["deployment_id"],
            dep_b["pod_labels"],
            dep_a["deployment_id"],
            dep_b["deployment_id"],
            a_grabs_b,
            dep_b["deployment_id"],
            dep_a["deployment_id"],
            b_grabs_a,
        )
    )
