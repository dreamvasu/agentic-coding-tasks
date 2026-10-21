#  Copyright (c) ZenML GmbH 2025. All Rights Reserved.
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
"""Offline stand-ins for the Kubernetes deployer's live-cluster dependencies.

The deployer module is relocated verbatim. Its manifest-rendering path
(``_initialize_deployment_context`` -> ``_build_template_context`` -> the
template engine) runs entirely offline, but the file also imports symbols used
only by the cluster-facing methods (provisioning, deprovisioning, status polling,
log streaming). Those symbols are provided here so the module imports and the
rendering path executes without a live Kubernetes API server or the full ZenML
runtime. The cluster-facing methods are never exercised by the rendering path.
"""

import enum
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """Return a standard-library logger.

    Args:
        name: Logger name.

    Returns:
        A configured ``logging.Logger``.
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Deployer exceptions
# ---------------------------------------------------------------------------
class DeployerError(Exception):
    """Base deployer error."""


class DeploymentProvisionError(DeployerError):
    """Raised when provisioning a deployment fails."""


class DeploymentDeprovisionError(DeployerError):
    """Raised when deprovisioning a deployment fails."""


class DeploymentNotFoundError(DeployerError):
    """Raised when a deployment is not found."""


class DeploymentLogsNotFoundError(DeployerError):
    """Raised when deployment logs are not found."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class DeploymentStatus(str, enum.Enum):
    """Operational status of a deployment."""

    PENDING = "pending"
    RUNNING = "running"
    ERROR = "error"
    ABSENT = "absent"


class StackComponentType(str, enum.Enum):
    """Stack component types (subset)."""

    IMAGE_BUILDER = "image_builder"
    CONTAINER_REGISTRY = "container_registry"


# ---------------------------------------------------------------------------
# Entrypoint configuration
# ---------------------------------------------------------------------------
DEPLOYMENT_ID_OPTION = "deployment_id"
SNAPSHOT_ID_OPTION = "snapshot_id"


class DeploymentEntrypointConfiguration:
    """Stand-in for the deployment server entrypoint configuration."""

    @staticmethod
    def get_entrypoint_command() -> List[str]:
        """Return the container entrypoint command.

        Returns:
            The entrypoint command as a list of strings.
        """
        return ["python", "-m", "zenml.deployers.server.entrypoint"]

    @staticmethod
    def get_entrypoint_arguments(**kwargs: Any) -> List[str]:
        """Return the container entrypoint arguments.

        Args:
            **kwargs: Entrypoint option name/value pairs.

        Returns:
            The entrypoint arguments as a flat list of strings.
        """
        arguments: List[str] = []
        for key, value in kwargs.items():
            arguments.append(f"--{key}")
            arguments.append(str(value))
        return arguments


# ---------------------------------------------------------------------------
# Model stand-ins
# ---------------------------------------------------------------------------
class PipelineSnapshotResponse(BaseModel):
    """Minimal snapshot carrying the resolved deployer settings."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = "snapshot-00000000"
    settings: Any = None
    pipeline_configuration: Any = None


class DeploymentResponse(BaseModel):
    """Minimal deployment response the rendering path reads."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    snapshot: Optional[PipelineSnapshotResponse] = None
    deployment_metadata: Dict[str, Any] = {}


class DeploymentOperationalState(BaseModel):
    """Operational state returned by the (unused offline) cluster methods."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: Any = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Base deployer
# ---------------------------------------------------------------------------
class ContainerizedDeployer:
    """Offline base deployer.

    Provides the hooks the rendering path calls on ``self`` (``get_settings`` /
    ``get_image``). The full base deployer also owns the deployment lifecycle
    state machine, which is not part of this rendering slice.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the base deployer.

        Args:
            **kwargs: Component keyword arguments (name, id, config, ...).
        """
        self._name = kwargs.get("name", "kubernetes")
        self._config = kwargs.get("config")
        self.connector = kwargs.get("connector")

    def get_settings(self, snapshot: Any) -> Any:
        """Resolve the deployer settings for a snapshot.

        Args:
            snapshot: The pipeline snapshot.

        Returns:
            The resolved settings object.
        """
        return snapshot.settings

    def get_image(self, snapshot: Any) -> str:
        """Resolve the container image for a snapshot.

        Args:
            snapshot: The pipeline snapshot.

        Returns:
            The container image reference.
        """
        image = getattr(snapshot, "image", None)
        return image or "zenml-deployment:latest"

    def _update_deployment(self, deployment: Any, state: Any) -> Any:
        """Persist an updated deployment state (no-op offline).

        Args:
            deployment: The deployment.
            state: The new operational state.

        Returns:
            The deployment.
        """
        return deployment

    @property
    def name(self) -> str:
        """The deployer name.

        Returns:
            The deployer name.
        """
        return self._name


class StackValidator:
    """Stand-in stack validator (never invoked in the rendering path)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the validator.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        self.args = args
        self.kwargs = kwargs


# ---------------------------------------------------------------------------
# Applier stand-ins (cluster path only)
# ---------------------------------------------------------------------------
class ResourceInventoryItem(BaseModel):
    """A provisioned-resource inventory entry."""

    model_config = ConfigDict(extra="allow")

    kind: str = ""
    api_version: str = ""
    name: str = ""
    namespace: Optional[str] = None


class ProvisioningError(Exception):
    """Raised by the applier when provisioning fails."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the provisioning error.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments (``inventory``, ``errors``).
        """
        super().__init__(*args)
        self.inventory: List[ResourceInventoryItem] = kwargs.get(
            "inventory", []
        )
        self.errors: List[str] = kwargs.get("errors", [])


class KubernetesApplier:
    """Stand-in applier (never instantiated in the rendering path)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the applier.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        raise RuntimeError(
            "KubernetesApplier requires a live Kubernetes API client, which is "
            "not available in the offline rendering slice."
        )


def normalize_resource_to_dict(resource: Any) -> Dict[str, Any]:
    """Normalize a Kubernetes resource (model or dict) to a plain dict.

    Args:
        resource: A dict or a Kubernetes client model.

    Returns:
        The resource as a plain dict.
    """
    if isinstance(resource, dict):
        return resource
    to_dict = getattr(resource, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(vars(resource))


# ---------------------------------------------------------------------------
# Kubernetes client stand-ins (cluster path only)
# ---------------------------------------------------------------------------
class ApiException(Exception):
    """Stand-in for ``kubernetes.client.rest.ApiException``."""

    def __init__(self, status: Any = None, *args: Any, **kwargs: Any) -> None:
        """Initialize the API exception.

        Args:
            status: HTTP status code.
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        super().__init__(*args)
        self.status = status
        self.body = kwargs.get("body")


class _UnavailableClient:
    """Placeholder that errors if the live client is actually used."""

    def __getattr__(self, item: str) -> Any:
        """Raise on any attribute access.

        Args:
            item: The attribute name.

        Raises:
            RuntimeError: Always.
        """
        raise RuntimeError(
            "The live Kubernetes client is not available in the offline "
            "rendering slice (attempted to access %r)." % item
        )


k8s_client = _UnavailableClient()
k8s_config = _UnavailableClient()
