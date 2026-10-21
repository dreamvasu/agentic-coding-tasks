#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
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
"""Kubernetes resource serialization helpers (rendering subset)."""

from typing import Any, Dict


def normalize_resource_to_dict(resource: Any) -> Dict[str, Any]:
    """Normalize a Kubernetes resource (model or dict) to a plain dict.

    Args:
        resource: Either a plain ``dict`` (already normalized) or an object that
            exposes a ``to_dict`` method (a Kubernetes client model).

    Returns:
        The resource as a plain dictionary.
    """
    if isinstance(resource, dict):
        return resource
    to_dict = getattr(resource, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(vars(resource))
