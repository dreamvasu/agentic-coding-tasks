"""In-repo regression tests for the Kubernetes deployer's rendered routing.

These render the built-in Deployment and Service templates through the real
deployer path (``render_manifests.render_deployment``) and check that the
Service actually selects the pods it is meant to route to.

The reported bug was that when a user set a custom ``app`` pod label through
``settings.labels`` / ``settings.pod_settings.labels``, the rendered pod no longer
carried the ``app`` value the Service selector expects, so the Service selected
nothing and came up with no endpoints. The applied fix emits the ZenML-managed pod
labels after the user label loops, so these cases now render the Service selecting
its pods again.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HERE)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from render_manifests import render_deployment  # noqa: E402


def _selects(selector, pod_labels):
    return all(pod_labels.get(k) == v for k, v in selector.items())


def test_manifests_render():
    """The deployer renders both manifests with the expected structure."""
    result = render_deployment("11111111", "demo")
    assert result["service_selector"], "Service must declare a selector"
    assert result["deployment_matchLabels"], "Deployment must declare matchLabels"
    assert result["pod_labels"], "pod template must declare labels"


def test_service_selects_pods_baseline():
    """With no custom labels, the Service selects its pods."""
    result = render_deployment("11111111", "demo")
    assert _selects(result["service_selector"], result["pod_labels"]), (
        "Service selector %r does not select pod labels %r"
        % (result["service_selector"], result["pod_labels"])
    )


def test_deployment_selects_own_pods():
    """The Deployment's own matchLabels selects its own pod template."""
    result = render_deployment("11111111", "demo")
    assert _selects(result["deployment_matchLabels"], result["pod_labels"]), (
        "Deployment matchLabels %r does not select its own pod labels %r"
        % (result["deployment_matchLabels"], result["pod_labels"])
    )


def test_service_selects_pods_with_custom_pod_label():
    """Covers the reported empty-endpoints symptom.

    A user sets a custom ``app`` label via ``settings.pod_settings.labels``. The
    Service must still select its pods; the applied fix keeps this green.
    """
    result = render_deployment(
        "11111111", "demo", pod_labels={"app": "custom-app"}
    )
    assert _selects(result["service_selector"], result["pod_labels"]), (
        "Service gets no endpoints: selector %r does not select pod labels %r "
        "when the user sets a custom pod label"
        % (result["service_selector"], result["pod_labels"])
    )


def test_service_selects_pods_with_settings_label_override():
    """A custom ``app`` in ``settings.labels`` must also not break routing."""
    result = render_deployment(
        "11111111", "demo", settings_labels={"app": "team-app"}
    )
    assert _selects(result["service_selector"], result["pod_labels"]), (
        "Service gets no endpoints: selector %r does not select pod labels %r "
        "when the user sets app in settings.labels"
        % (result["service_selector"], result["pod_labels"])
    )
