# Kubernetes manifests

Plain manifests (no Helm) for deploying the POC app to AKS. Nothing here is
applied automatically - see docs/SECURITY_AND_COST.md and
docs/AZURE_ARCHITECTURE.md before ever running these against a real cluster.

## Files

- `namespace.yaml` - the `adops-poc` namespace.
- `configmap.yaml` - non-secret configuration.
- `secret.example.yaml` - documents the shape of a secret the app could
  read; not a real secret, not applied by default.
- `deployment.yaml` - the app Deployment: 2 replicas, rolling update,
  liveness/readiness probes on `/health` and `/ready`, resource
  requests/limits.
- `service.yaml` - a ClusterIP Service in front of the Deployment.

## Applying (against a real cluster only, never automatic)

```bash
kubectl apply -f infra/kubernetes/namespace.yaml
kubectl apply -f infra/kubernetes/configmap.yaml
kubectl apply -f infra/kubernetes/deployment.yaml
kubectl apply -f infra/kubernetes/service.yaml
```

## Validating locally without a cluster

```bash
kubectl apply --dry-run=client -f infra/kubernetes/
```

## Rollback

A rolling update keeps revision history (`revisionHistoryLimit: 3`), so a
bad rollout can be reverted with:

```bash
kubectl rollout status deployment/adops-poc -n adops-poc
kubectl rollout undo deployment/adops-poc -n adops-poc
```

This is the same "rollback" concept the application's rule engine
recommends and that a human approves through the API - see
docs/OPERATIONS_RUNBOOK.md. The application itself never runs these
commands; a human or a pipeline step does, only after approval.
