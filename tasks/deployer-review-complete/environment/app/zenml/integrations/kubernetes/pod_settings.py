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
"""Kubernetes pod settings.

Note: the upstream ``KubernetesPodSettings`` carries ``field_validator`` hooks
that coerce live ``kubernetes.client`` model objects (``V1Volume``,
``V1Toleration``, ...) into plain dicts. Those converters are only reachable when
a real Kubernetes client is installed; this offline slice keeps the model shape
(the attributes the templates read) without the client-object coercion.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class KubernetesPodSettings(BaseModel):
    """Kubernetes Pod settings.

    Attributes:
        node_selectors: Node selectors to apply to the pod.
        affinity: Affinity to apply to the pod.
        tolerations: Tolerations to apply to the pod.
        resources: Resource requests and limits for the pod.
        annotations: Annotations to apply to the pod metadata.
        volumes: Volumes to mount in the pod.
        volume_mounts: Volume mounts to apply to the pod containers.
        host_ipc: Whether to enable host IPC for the pod.
        scheduler_name: The name of the scheduler to use for the pod.
        image_pull_secrets: Image pull secrets to use for the pod.
        labels: Labels to apply to the pod.
        env: Environment variables to apply to the container.
        env_from: Environment variables to apply to the container.
        container_security_context: Security context settings to apply to all
            containers in the pod.
        additional_pod_spec_args: Additional arguments to pass to the pod. These
            will be applied to the pod spec.
    """

    node_selectors: Dict[str, str] = {}
    affinity: Dict[str, Any] = {}
    tolerations: List[Dict[str, Any]] = []
    resources: Dict[str, Dict[str, str]] = {}
    annotations: Dict[str, str] = {}
    volumes: List[Dict[str, Any]] = []
    volume_mounts: List[Dict[str, Any]] = []
    host_ipc: bool = False
    scheduler_name: Optional[str] = None
    image_pull_secrets: List[str] = []
    labels: Dict[str, str] = {}
    env: List[Dict[str, Any]] = []
    env_from: List[Dict[str, Any]] = []
    container_security_context: Dict[str, Any] = {}
    additional_pod_spec_args: Dict[str, Any] = {}
