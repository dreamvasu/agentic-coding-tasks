#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Utility functions for building Kubernetes manifests (rendering subset)."""

from typing import Any, Dict, Optional


def build_namespace_manifest(
    namespace: str, labels: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Build a Kubernetes namespace manifest.

    Args:
        namespace: The namespace name.
        labels: Optional labels to apply to the namespace.

    Returns:
        The namespace manifest as a dict.
    """
    metadata: Dict[str, Any] = {"name": namespace}
    if labels:
        metadata["labels"] = labels
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": metadata,
    }


def build_secret_manifest(
    name: str,
    data: Dict[str, Optional[str]],
    namespace: str = "default",
) -> Dict[str, Any]:
    """Build a Kubernetes secret manifest.

    Args:
        name: The name of the secret.
        data: The secret string data.
        namespace: The namespace of the secret.

    Returns:
        The secret manifest as a dict.
    """
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": name, "namespace": namespace},
        "stringData": {k: v for k, v in data.items() if v is not None},
        "type": "Opaque",
    }
