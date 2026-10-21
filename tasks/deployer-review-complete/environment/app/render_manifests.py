#!/usr/bin/env python3
"""Render Kubernetes manifests through the real deployer path (no live cluster).

This is the reproduction / inspection entry point for the ZenML Kubernetes
deployer slice under ``/app``. It drives the *real* deployer code:

    KubernetesDeployer._initialize_deployment_context(...)   # builds the label set
    KubernetesDeployer._build_template_context(...)          # assembles render vars
    KubernetesTemplateEngine.render_template(...)            # renders the templates

and returns, for each requested deployment, the rendered Service selector, the
rendered Deployment ``matchLabels`` selector, and the rendered pod-template
labels. Because it goes through the actual deployer + templates, any fix you make
to either the templates or the deployer's context-building code is reflected here.

Usage
-----
Reproduce the reported symptom (a user sets a custom pod label and the Service
stops selecting its pods)::

    python /app/render_manifests.py

Render an explicit set of deployments and emit JSON (used by the test suite)::

    python /app/render_manifests.py --spec-file scenario.json --out result.json

where ``scenario.json`` is a JSON list of objects::

    [
      {"deployment_id": "11111111", "deployment_name": "demo",
       "settings_labels": {}, "pod_labels": {"app": "custom-app"}}
    ]

``settings_labels`` mirrors the user's ``settings.labels`` and ``pod_labels``
mirrors ``settings.pod_settings.labels``. Omit ``pod_labels`` (or pass null) for a
deployment that sets no pod-level labels.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

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
from zenml.integrations.kubernetes.template_engine import (
    KubernetesTemplateEngine,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(
    APP_DIR, "zenml", "integrations", "kubernetes", "templates", "kubernetes"
)


def render_deployment(
    deployment_id: str,
    deployment_name: str,
    settings_labels: Optional[Dict[str, str]] = None,
    pod_labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Render one deployment and return its selectors and pod labels.

    Args:
        deployment_id: The deployment id (server UUID in production).
        deployment_name: The human-readable deployment name.
        settings_labels: The user's ``settings.labels`` for this deployment.
        pod_labels: The user's ``settings.pod_settings.labels``; ``None`` means
            no pod settings are configured.

    Returns:
        A dict with ``service_selector``, ``deployment_matchLabels`` and
        ``pod_labels`` (the rendered pod-template labels).
    """
    pod_settings = None
    if pod_labels is not None:
        pod_settings = KubernetesPodSettings(labels=dict(pod_labels))

    settings = KubernetesDeployerSettings(
        labels=dict(settings_labels or {}),
        pod_settings=pod_settings,
    )

    snapshot = PipelineSnapshotResponse(settings=settings)
    deployment = DeploymentResponse(
        id=deployment_id, name=deployment_name, snapshot=snapshot
    )

    deployer = KubernetesDeployer(name="kubernetes")

    # Real deployer code path: build the label context, then the template
    # context, then render the two built-in templates.
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

    engine = KubernetesTemplateEngine()
    deployment_docs = engine.render_template(
        os.path.join(TEMPLATES_DIR, "deployment.yaml.j2"), context
    )
    service_docs = engine.render_template(
        os.path.join(TEMPLATES_DIR, "service.yaml.j2"), context
    )

    dep = deployment_docs[0]
    svc = service_docs[0]

    return {
        "deployment_id": deployment_id,
        "deployment_name": deployment_name,
        "resource_name": ctx.resource_name,
        "service_selector": svc["spec"]["selector"],
        "deployment_matchLabels": dep["spec"]["selector"]["matchLabels"],
        "pod_labels": dep["spec"]["template"]["metadata"]["labels"],
    }


def render_spec(spec: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Render a list of deployment specifications.

    Args:
        spec: A list of dicts with ``deployment_id``, ``deployment_name`` and
            optional ``settings_labels`` / ``pod_labels`` keys.

    Returns:
        A list of per-deployment render results.
    """
    results = []
    for item in spec:
        results.append(
            render_deployment(
                deployment_id=item["deployment_id"],
                deployment_name=item.get("deployment_name", item["deployment_id"]),
                settings_labels=item.get("settings_labels"),
                pod_labels=item.get("pod_labels"),
            )
        )
    return results


def _satisfied_by(selector: Dict[str, str], pod_labels: Dict[str, str]) -> bool:
    """Return whether ``pod_labels`` satisfies every key/value in ``selector``.

    Args:
        selector: A label selector (all keys must match).
        pod_labels: The pod's labels.

    Returns:
        True if the selector selects the pod, else False.
    """
    return all(pod_labels.get(k) == v for k, v in selector.items())


def _demo() -> int:
    """Reproduce the reported symptom and print a human-readable summary.

    Returns:
        Process exit code (0 always; this is an inspection helper).
    """
    result = render_deployment(
        deployment_id="11111111",
        deployment_name="demo-deployment",
        settings_labels={},
        pod_labels={"app": "custom-app"},
    )
    ok = _satisfied_by(result["service_selector"], result["pod_labels"])
    print("Scenario: user sets pod label app=custom-app via pod_settings.labels")
    print("  Service spec.selector      :", result["service_selector"])
    print("  rendered pod template labels:", result["pod_labels"])
    print("  Deployment matchLabels     :", result["deployment_matchLabels"])
    print(
        "  Does the Service selector select the pod? ->",
        ok,
        "(False means the Service gets NO endpoints)",
    )
    return 0


def main(argv: List[str]) -> int:
    """Command-line entry point.

    Args:
        argv: Command-line arguments (excluding the program name).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec-file",
        help="Path to a JSON file with a list of deployment specs to render.",
    )
    parser.add_argument(
        "--out",
        help="Path to write the JSON render result (defaults to stdout).",
    )
    args = parser.parse_args(argv)

    if not args.spec_file:
        return _demo()

    with open(args.spec_file, "r", encoding="utf-8") as handle:
        spec = json.load(handle)

    results = render_spec(spec)
    payload = json.dumps(results, indent=2, sort_keys=True)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
