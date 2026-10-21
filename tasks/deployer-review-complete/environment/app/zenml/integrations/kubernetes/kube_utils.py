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
#
# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for Kubernetes related functions.

Internal interface: no backwards compatibility guarantees.
Adjusted from https://github.com/tensorflow/tfx/blob/master/tfx/utils/kube_utils.py.

Note: this is the manifest-rendering subset of ``kube_utils``. The functions that
drive a live Kubernetes API server (pod/job/secret/config-map lifecycle, log
streaming, service-URL discovery) are part of the cluster path and are not
included in this offline slice; the label/name sanitizers and the resource
conversion helper that feed template rendering are kept verbatim.
"""

import enum
import re
from typing import TYPE_CHECKING, Dict, Tuple

if TYPE_CHECKING:
    from zenml.config.resource_settings import ResourceSettings


class ByteUnit(enum.Enum):
    """Byte units."""

    KB = "KB"
    KIB = "KiB"
    MB = "MB"
    MIB = "MiB"
    GB = "GB"
    GIB = "GiB"


class PodPhase(enum.Enum):
    """Phase of the Kubernetes pod.

    Pod phases are defined in
    https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase.
    """

    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class JobStatus(enum.Enum):
    """Status of a Kubernetes job."""

    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


def sanitize_label(label: str) -> str:
    """Sanitize a string for use as a Kubernetes `metadata.name` DNS label.

    Matches RFC 1123-style DNS labels: lowercase alphanumerics and hyphens,
    starting and ending with alphanumeric. For Kubernetes *label values*, use
    `sanitize_label_value` instead, which allows `_`, `.`, and mixed case.

    See https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names

    Args:
        label: The label name to sanitize.

    Returns:
        The sanitized label name.
    """
    label = re.sub(r"[^a-z0-9-]", "-", label.lower())
    label = re.sub(r"^[-]+", "", label)
    label = re.sub(r"[-]+", "-", label)
    label = label[:63]
    # Remove trailing dashes after truncation to make sure we end with an
    # alphanumeric character
    label = re.sub(r"[-]+$", "", label)

    return label


def sanitize_label_value(label: str) -> str:
    """Sanitize a string for use as a Kubernetes label `value`.

    Follows the label value rules (63 characters max; non-empty values must
    start and end with `[A-Za-z0-9]`; `-`, `_`, `.`, and alphanumerics
    are allowed between).

    See https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set

    Args:
        label: The label value to sanitize.

    Returns:
        The sanitized label value (at most 63 characters; may be empty).
    """
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", label)
    label = label.strip("._-")
    if not label:
        return ""

    label = label[:63]
    label = re.sub(r"[^A-Za-z0-9]+$", "", label)
    label = re.sub(r"^[^A-Za-z0-9]+", "", label)
    return label


def convert_resource_settings_to_k8s_format(
    resource_settings: "ResourceSettings",
) -> Tuple[Dict[str, str], Dict[str, str], int]:
    """Convert ZenML ResourceSettings to Kubernetes resource format.

    Args:
        resource_settings: The resource settings from pipeline configuration.

    Returns:
        Tuple of (requests, limits, replicas) in Kubernetes format.
        - requests: Dict with 'cpu', 'memory', and optionally 'nvidia.com/gpu' keys
        - limits: Dict with same keys as requests (GPUs require limits=requests)
        - replicas: Number of replicas
    """
    requests: Dict[str, str] = {}
    limits: Dict[str, str] = {}

    cpu_count = getattr(resource_settings, "cpu_count", None)
    if cpu_count is not None:
        if cpu_count == int(cpu_count):
            cpu_str = str(int(cpu_count))
        else:
            cpu_str = f"{int(cpu_count * 1000)}m"
        requests["cpu"] = cpu_str

    memory_mib = getattr(resource_settings, "memory_mib", None)
    if memory_mib:
        requests["memory"] = f"{int(memory_mib)}Mi"

    min_r = getattr(resource_settings, "min_replicas", None)
    max_r = getattr(resource_settings, "max_replicas", None)

    if min_r is not None and min_r > 0:
        replicas = min_r
    elif max_r is not None and max_r > 0:
        replicas = max_r
    else:
        replicas = 1

    gpu_count = getattr(resource_settings, "gpu_count", None)
    if gpu_count:
        gpu_str = str(gpu_count)
        requests["nvidia.com/gpu"] = gpu_str
        limits["nvidia.com/gpu"] = gpu_str

    return requests, limits, replicas
