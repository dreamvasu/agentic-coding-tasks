# Fix: Service comes up with no endpoints when custom pod labels are set

## Problem

When a user sets a custom `app` label through `settings.labels` or
`settings.pod_settings.labels`, the rendered pod template emitted its managed
`app` label first and then looped the user's labels. By YAML last-key-wins the
user's `app` value overwrote the managed one, so the pod no longer carried the
`app: zenml-<uuid>` value the Service selector expects. The Service selected
nothing and the model endpoint came up with no endpoints.

## Fix

In `deployment.yaml.j2`, emit the ZenML-managed pod labels (`app`, `managed-by`)
*after* the `labels` and `pod_settings.labels` loops. A user-supplied label can no
longer displace them, so the pod always carries the `app` value the Service
selector routes on.

## Testing

- `python render_manifests.py` shows the Service selecting the pod again with a
  custom pod label set.
- `python -m pytest tests` is green, including the regression case
  `test_service_selects_pods_with_custom_pod_label` and the
  `settings.labels` override case.

Routing is restored for the reported configuration.
