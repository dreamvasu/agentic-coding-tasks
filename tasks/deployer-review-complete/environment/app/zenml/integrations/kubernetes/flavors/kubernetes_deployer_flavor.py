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
"""Kubernetes deployer flavor.

The settings/config models below carry the fields the deployer and templates
read. Upstream these derive from ``BaseDeployerSettings`` / ``BaseDeployerConfig``
(stack-component machinery); this slice keeps the Kubernetes-specific fields on a
plain ``BaseModel`` so the deployer's context-building path runs without the full
stack-component runtime.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, PositiveInt, field_validator

from zenml.integrations.kubernetes.pod_settings import KubernetesPodSettings


class KubernetesDeployerSettings(BaseModel):
    """Settings for the Kubernetes deployer.

    Essential Settings:
        namespace: Kubernetes namespace for deployments.
        service_type: How to expose service (LoadBalancer, NodePort, ClusterIP).
        service_port: Port to expose on the service.
        image_pull_policy: When to pull images (Always, IfNotPresent, Never).
        labels: Custom labels to apply to all resources.
        command: Override container command/entrypoint.
        args: Override container args.
        service_account_name: ServiceAccount for pods (RBAC).
        image_pull_secrets: Secrets for private registries.

    Advanced Settings:
        pod_settings: Advanced pod configuration (volumes, affinity, ...).
        additional_resources: Paths to YAML files with additional K8s resources.
        custom_deployment_template_file / custom_service_template_file: Override
          the built-in Jinja2 templates.
    """

    namespace: str = Field(
        "zenml-deployments",
        description="Default Kubernetes namespace for deployments.",
    )

    service_type: str = Field(
        default="ClusterIP",
        description=(
            "Type of Kubernetes Service: LoadBalancer, NodePort, or ClusterIP."
        ),
    )

    service_port: PositiveInt = Field(
        default=8000,
        description="Port to expose on the service.",
    )

    image_pull_policy: str = Field(
        default="IfNotPresent",
        description="Kubernetes image pull policy: Always, IfNotPresent, Never.",
    )

    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional labels to apply to all Kubernetes resources.",
    )

    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Annotations to add to Pod resources.",
    )

    command: Optional[List[str]] = Field(
        default=None,
        description="Override container command (entrypoint).",
    )

    args: Optional[List[str]] = Field(
        default=None,
        description="Override container args.",
    )

    service_account_name: Optional[str] = Field(
        default=None,
        description="Kubernetes service account for the deployment pods.",
    )

    image_pull_secrets: List[str] = Field(
        default_factory=list,
        description="Names of Kubernetes secrets for pulling private images.",
    )

    # ========================================================================
    # Health Probes
    # ========================================================================

    readiness_probe_path: str = Field(default="/api/health")
    readiness_probe_initial_delay: PositiveInt = Field(default=10)
    readiness_probe_period: PositiveInt = Field(default=10)
    readiness_probe_timeout: PositiveInt = Field(default=5)
    readiness_probe_failure_threshold: PositiveInt = Field(default=3)

    liveness_probe_path: str = Field(default="/api/health")
    liveness_probe_initial_delay: PositiveInt = Field(default=30)
    liveness_probe_period: PositiveInt = Field(default=10)
    liveness_probe_timeout: PositiveInt = Field(default=5)
    liveness_probe_failure_threshold: PositiveInt = Field(default=3)

    # ========================================================================
    # Advanced Pod Configuration
    # ========================================================================

    pod_settings: Optional[KubernetesPodSettings] = Field(
        default=None,
        description="Advanced pod configuration: volumes, affinity, "
        "tolerations, node selectors, etc.",
    )

    strict_additional_resources: bool = Field(default=True)

    additional_resources: List[str] = Field(
        default_factory=list,
        description="Paths to YAML files with additional Kubernetes resources.",
    )

    atomic_provision: bool = Field(default=False)

    custom_deployment_template_file: Optional[str] = Field(default=None)
    custom_service_template_file: Optional[str] = Field(default=None)

    wait_for_load_balancer_timeout: int = Field(default=150, ge=0)
    deployment_ready_check_interval: PositiveInt = Field(default=2)

    @field_validator("readiness_probe_path", "liveness_probe_path")
    @classmethod
    def validate_probe_path(cls, v: str) -> str:
        """Validate that probe paths start with /.

        Args:
            v: The probe path value.

        Returns:
            The validated probe path.

        Raises:
            ValueError: If the path doesn't start with /.
        """
        if not v.startswith("/"):
            raise ValueError(f"Probe path must start with '/': {v}")
        return v


class KubernetesDeployerConfig(KubernetesDeployerSettings):
    """Configuration for the Kubernetes deployer."""

    incluster: bool = Field(default=False)
    kubernetes_context: Optional[str] = Field(default=None)
    local: bool = Field(default=False)
    skip_local_validations: bool = Field(default=False)

    @property
    def is_local(self) -> bool:
        """Checks if this is a local Kubernetes cluster.

        Returns:
            True if using a local Kubernetes cluster, False otherwise.
        """
        if self.local:
            return True
        if self.kubernetes_context:
            local_context_indicators = [
                "k3d-",
                "kind-",
                "minikube",
                "docker-desktop",
                "colima",
                "rancher-desktop",
            ]
            context_lower = self.kubernetes_context.lower()
            return any(
                indicator in context_lower
                for indicator in local_context_indicators
            )
        return False

    @property
    def is_remote(self) -> bool:
        """Checks if this stack component is running remotely.

        Returns:
            True if this config is for a remote component, False otherwise.
        """
        return not self.is_local
