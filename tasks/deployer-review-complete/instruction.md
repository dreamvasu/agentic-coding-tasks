## ZenML Kubernetes deployer: review a fix for the empty-endpoints bug

You are working in a relocated slice of the ZenML codebase under `/app`. It holds
the Kubernetes deployer, which turns a deployment configuration into Kubernetes
manifests (a Deployment and a Service) by rendering the Jinja2 templates in
`/app/zenml/integrations/kubernetes/templates/kubernetes/` with a context built by
`/app/zenml/integrations/kubernetes/deployers/kubernetes_deployer.py`.

### The reported bug

A user deploys a model server and sets custom pod labels through their deployer
configuration -- `settings.labels` and `settings.pod_settings.labels`. The
Deployment rolls out and the pods come up Running, but the model endpoint is
unreachable: the Service ends up with no endpoints, so nothing routes to the
pods. When they remove their custom labels, routing works again.

### The change under review

A teammate has already submitted a fix for this and it is applied to the tree
under `/app` (see `/app/PR.md` for their summary). Their change reorders how the
pod template emits labels so a user-supplied `app` label can no longer displace
the value the Service selector expects. The reported single-deployment symptom no
longer reproduces and the in-repo test suite is green:

```
python /app/render_manifests.py
cd /app && python -m pytest tests
```

### Your task

Review the applied change and decide whether it *correctly and completely* fixes
the routing defect -- i.e. whether the rendered Deployment and Service route to
the right pods for the label configurations a user can set through
`settings.labels` or `settings.pod_settings.labels`. If the fix is incomplete,
finish it so routing is correct, keeping the change at the template / deployer
level (no live cluster is involved; the manifests are produced only by the
templates and the deployer's context-building code under `/app`).

Add or update a regression test under `/app/tests/` that renders the manifests
through the deployer path and fails on the tree as you received it, then passes
once your change is in place. If you conclude the fix is already complete, state
that and back it with a test.

### Constraints

- Do not change the reported public behavior of the deployer beyond fixing the
  routing defect: the same manifests, the same field names, the same rendering
  entry point (`render_manifests.py` and the deployer's context-building
  methods) must keep working.
- Standard library plus the already-installed `jinja2`, `pyyaml`, and `pydantic`
  only; do not add new third-party dependencies.
- Write your changes into the files under `/app`; do not hard-code rendered
  output.
