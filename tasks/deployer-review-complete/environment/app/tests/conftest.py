"""Shared helpers for the in-repo deployer tests."""

import os
import sys

import pytest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def selector_selects(selector, pod_labels):
    """Return whether a label selector selects a pod with the given labels.

    Args:
        selector: A label selector (all keys must match).
        pod_labels: The pod's labels.

    Returns:
        True if the selector selects the pod, else False.
    """
    return all(pod_labels.get(k) == v for k, v in selector.items())


@pytest.fixture
def selects():
    """Expose the selector-matching helper to tests.

    Returns:
        The ``selector_selects`` function.
    """
    return selector_selects
