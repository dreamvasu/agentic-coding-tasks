#!/usr/bin/env python3
"""Reference completion for the ZenML Kubernetes deployer selector fix review.

The tree under ``/app`` already carries the teammate's partial fix: the pod
template emits the ZenML-managed labels (``app``, ``managed-by``) AFTER the user
label loops, so a user ``app`` label can no longer displace the value the Service
selector expects. That closes the reported single-deployment symptom and the
in-repo suite is green.

The fix is incomplete. The Deployment ``spec.selector.matchLabels`` still keys on
``zenml-deployment-id`` / ``zenml-deployment-name``, whose values come from the
``labels`` dict AFTER ``labels.update(**settings.labels)`` in
``_initialize_deployment_context`` -- i.e. the user can overwrite them through
``settings.labels``. Two deployments that pin those keys to the same value render
identical ``matchLabels`` and each one selects the other's pods (the ReplicaSet
controllers fight and endpoints churn to empty -- the same user-visible symptom,
reached at the Deployment selector instead of the Service).

The completion re-points the Deployment selector onto the unreachable, unique
per-deployment ``app: {{ name }}`` value (``name`` = ``zenml-<uuid>``), so it
selects only its own pods regardless of what the user sets. The grader renders the
resulting manifests and checks the rendered selectors, not the specific edit.
"""

import os

APP = "/app"
DEPLOYMENT_TEMPLATE = os.path.join(
    APP,
    "zenml",
    "integrations",
    "kubernetes",
    "templates",
    "kubernetes",
    "deployment.yaml.j2",
)


def patch(path, old, new):
    """Replace exactly one occurrence of ``old`` with ``new`` in ``path``.

    Args:
        path: The file to edit.
        old: The exact snippet to replace (must occur exactly once).
        new: The replacement snippet.

    Raises:
        SystemExit: If the snippet is not found.
    """
    text = open(path, encoding="utf-8").read()
    if old not in text:
        raise SystemExit("expected snippet not found in %s" % path)
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))


# Complete the fix: the Deployment selector must key on the unreachable, unique
# per-deployment `app: {{ name }}` value instead of the user-overridable identity
# labels, so two deployments can never render colliding matchLabels.
patch(
    DEPLOYMENT_TEMPLATE,
    """  selector:
    matchLabels:
      managed-by: zenml
      zenml-deployment-id: {{ labels.get('zenml-deployment-id') | tojson }}
      zenml-deployment-name: {{ labels.get('zenml-deployment-name') | tojson }}""",
    """  selector:
    matchLabels:
      app: {{ name }}
      managed-by: zenml""",
)

print("Completed selector fix in", DEPLOYMENT_TEMPLATE)
