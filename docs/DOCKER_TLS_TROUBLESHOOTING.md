# Docker TLS / Certificate Troubleshooting

This document covers a class of `docker build` failure that is common on Windows machines with
corporate networking, VPN, or endpoint-security software installed. It is an **environment
issue**, not a defect in this project's `Dockerfile` or application code.

## Common symptoms

The build fails during `pip install --no-cache-dir -r requirements.txt` (or an equivalent step
that fetches packages/images over HTTPS), with errors such as:

```
SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate
Could not fetch URL https://pypi.org/simple/...: There was a problem confirming the ssl certificate
tls: failed to verify certificate: x509: certificate signed by unknown authority
```

If a plain `pip install` or `python -m venv` on the host (outside Docker) works fine, but the
identical install fails only *inside* a container, that is a strong signal this is the cause.

## Likely causes

Something between the build container and the public package/image repository (PyPI,
`registry-1.docker.io`, etc.) is intercepting HTTPS traffic and re-signing it with a certificate
the container does not trust - even though the host OS does. This is typically one of:

- **Endpoint security / antivirus software** that inspects encrypted traffic locally (e.g. an
  antivirus "web protection" or intrusion-prevention feature that runs a local TLS-terminating
  proxy). Docker Desktop routes through this proxy along with everything else on the machine, but
  the Linux container image does not have that vendor's root certificate installed.
- **A corporate forward proxy or firewall** doing TLS inspection for compliance/DLP reasons.
- **A VPN client** that reroutes and inspects traffic while connected.
- Less commonly, a misconfigured system clock (certificate validity checks can fail if the clock
  is badly wrong) or a genuinely expired/misconfigured certificate on the remote side.

In every case, the host machine trusts the intercepting certificate (it's usually installed into
the Windows certificate store by the software above) but the ephemeral Linux build container does
not, because that trust store is local to the container's base image.

## Safe, preferred solutions

In order of preference:

1. **Exclude Docker Desktop from TLS inspection in your security software.** Most antivirus/VPN
   products let you add an exclusion for specific applications or processes (e.g. `Docker
   Desktop`, `com.docker.backend.exe`, `vpnkit.exe`) so their traffic is not intercepted. This
   fixes the problem without weakening protection for anything else on the machine. Restart
   Docker Desktop after changing this setting - it can cache proxy configuration at startup.
2. **Ask your network/security team for the correct trusted CA certificate** if this is a managed
   corporate device, and add it to the image's trust store at build time (e.g. via
   `update-ca-certificates` in a build stage that copies in a certificate file supplied through a
   `--build-context` or a build argument). This keeps TLS verification fully intact - it simply
   adds one more trusted root, the same way the host OS already does. Do not commit the
   certificate file to source control; treat it the same as any other machine-specific
   configuration.
3. **Configure Docker Desktop's own proxy settings** (Settings > Resources > Proxies) if your
   environment requires a specific corporate proxy for outbound HTTPS, rather than letting
   security software silently intercept traffic Docker doesn't know about.

## Project-supported scoped fallback

This repository does **not** ship a built-in bypass for this problem - no build argument, script,
or alternate Dockerfile is checked in for it, because the correct fix depends on what is
intercepting traffic on your specific machine, which this project cannot know in advance.

If you need to get a build working *temporarily* while pursuing one of the fixes above, the
lowest-risk technique is to avoid the container ever making an HTTPS call at all, by pre-fetching
the Python dependencies on the host (where the OS already trusts whatever is intercepting
traffic) and installing from those local files instead of from PyPI:

```bash
# On the host, with the project's virtualenv active:
pip download -r requirements.txt -d ./local-wheels \
  --platform manylinux2014_x86_64 --python-version 312 --implementation cp --abi cp312 \
  --only-binary=:all:

# Then build with a Dockerfile variant that installs from ./local-wheels instead of the network,
# e.g. `pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt`.
```

This does not touch TLS trust at all - it simply avoids needing it during the build - and does
not require any change to the committed `Dockerfile`. Treat any such variant Dockerfile as a
**local, temporary, throwaway file**: do not commit it, and do not rely on it for CI or any
shared image build, since it depends on a wheel cache that isn't part of the repository.

## Security implications

- **Do not** globally disable TLS/certificate verification (for example, `pip`'s
  `--trusted-host`/`PIP_CERT` tricks, or removing certificate checks from `docker build` or the
  base OS) as a fix. That weakens protection against real man-in-the-middle attacks, not just the
  benign local interception causing this error, and the weakness would persist even after the
  underlying network/software issue is resolved.
- Adding one additional trusted root certificate (option 2 above) is materially different from
  disabling verification: TLS validation still runs in full, against a slightly larger set of
  trusted issuers. This is the same trust model your host OS already uses.
- Never commit a certificate file, private key, or exported machine-specific trust material to
  this repository.

## Restoring normal secure configuration

If you temporarily excluded Docker Desktop from your security software's inspection, or added an
extra trusted CA to a local build, remove that exclusion/addition once you have finished local
development, unless your organization's standard configuration is to leave it excluded. There is
nothing in this repository that depends on either change being left in place.

## Verification steps after applying a solution

```bash
# Confirm a container can reach a public HTTPS endpoint at all
docker run --rm python:3.12-slim python -c "import urllib.request; print(urllib.request.urlopen('https://pypi.org', timeout=10).status)"

# Then confirm the project's own image builds and runs
docker build -t azure-devops-operations-poc:local .
docker compose up --build
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

If the first command succeeds (prints `200`), the underlying TLS trust issue is resolved and the
project's `Dockerfile` needs no further changes.
