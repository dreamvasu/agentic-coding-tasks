# ZenML Kubernetes deployer (relocated slice)

This is a self-contained subset of the ZenML source tree carrying the Kubernetes
deployer's manifest-rendering path. It runs offline (no Kubernetes cluster).

## Layout

```
/app
  render_manifests.py                  # render the manifests through the deployer
  tests/                               # in-repo tests (pytest)
  zenml/integrations/kubernetes/
    templates/kubernetes/
      deployment.yaml.j2               # Deployment manifest template
      service.yaml.j2                  # Service manifest template
    template_engine.py                 # KubernetesTemplateEngine (Jinja2 render)
    deployers/
      kubernetes_deployer.py           # KubernetesDeployer: builds the render context
      _offline.py                      # offline stand-ins for live-cluster deps
    flavors/
      kubernetes_deployer_flavor.py    # deployer settings / config models
    pod_settings.py                    # KubernetesPodSettings model
    kube_utils.py                      # label/name sanitizers, resource conversion
    manifest_utils.py                  # manifest builders
    serialization_utils.py             # resource normalization
    constants.py
```

## Rendering path

`render_manifests.py` drives the real deployer code:

1. `KubernetesDeployer._initialize_deployment_context(...)` assembles the label
   set for the deployment.
2. `KubernetesDeployer._build_template_context(...)` assembles the full Jinja2
   render context.
3. `KubernetesTemplateEngine.render_template(...)` renders each template and
   parses the YAML into resource dicts.

Run `python /app/render_manifests.py` to render a demo deployment, or
`python /app/render_manifests.py --spec-file <file> --out <file>` to render an
explicit list of deployments.

## Offline slice

The cluster-facing deployer methods (provisioning, deprovisioning, status
polling, log streaming) and the live Kubernetes client they use are not part of
this slice; the symbols they reference are provided by `deployers/_offline.py` so
the module imports and the rendering path runs without a Kubernetes API server.

## Tests

```
cd /app && python -m pytest tests
```
