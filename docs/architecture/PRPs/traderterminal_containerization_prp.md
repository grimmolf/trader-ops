# PRP: Containerized TraderTerminal Architecture

## 1. Purpose
Design a fully-containerized deployment of the TraderTerminal suite (grimm-chronos, grimm-kairos, highseat, trader-ops, armory, data-services) using Podman pods.  This PRP targets integration with the Fedora TraderTerminal spin while remaining portable to macOS and other Podman-compatible hosts.

## 2. Goals & Success Criteria
- **Modularity:** Each major subsystem runs in its own lightweight container yet shares a common network namespace via a Podman pod.
- **Portability:** Deployment works rootless on Fedora 40+ and macOS (via Podman Desktop or podman-machine).
- **Persistence:** Market data, configuration, and logs survive container upgrades.
- **Autostart:** Services start automatically on boot using SystemD on Fedora and `launchd` agents on macOS.
- **Observability:** Health endpoints exposed; trader-ops container aggregates metrics.

## 3. Component Overview
| Container | Image Base | Responsibility | Exposed Ports |
|-----------|-----------|----------------|---------------|
| chronos   | `registry.fedoraproject.org/fedora:latest` | Historical/time-series DB (TimescaleDB) | 5432 |
| kairos    | `registry.fedoraproject.org/fedora-minimal:latest` | Scheduler & strategy executor (Go binary) | 8081 |
| highseat  | `registry.fedoraproject.org/fedora-minimal:latest` | Primary API + UI | 8080 |
| ops       | `quay.io/prometheus/prometheus:v2.52.0` | Metrics & alerting | 9090 |
| armory    | `registry.fedoraproject.org/fedora-minimal:latest` | Auxiliary tools (backtesting, risk) | — |
| data-svc  | `registry.fedoraproject.org/fedora-minimal:latest` | Market data ingestion (Python) | 8090 |

## 4. Inter-Component Communication
All containers reside in a single pod `traderterminal-pod`, sharing the localhost network namespace.  Services address each other via `localhost:<port>` eliminating service discovery overhead.

```
chronos (5432) <─┐
                 │   traderterminal-pod (shared net, IPC, UTS)
 kairos (8081) ──┼──> highseat (8080) ──> ops (9090)
                 │
 data-svc (8090) ─┘
```

Authentication between services uses mTLS certificates mounted from a shared secret volume (`/etc/traderterminal/certs`).  Access to the database is via a service account credential also injected as a secret volume.

## 5. Pod & Container Configuration
### 5.1 Pod Creation
```bash
podman pod create \
  --name traderterminal-pod \
  --infra-name traderterminal-infra \
  --publish 8080:8080 \
  --publish 9090:9090
```
*Infra container shares namespaces; external ports limited to UI and metrics.*

### 5.2 Container Run Examples
```bash
podman run -d --name chronos --pod traderterminal-pod \
  -v tt_pgdata:/var/lib/postgresql/data:z \
  -v tt_secrets:/etc/traderterminal/secrets:ro,z \
  -e POSTGRES_PASSWORD_FILE=/etc/traderterminal/secrets/pg_pass \
  docker.io/timescale/timescaledb:latest-pg15

podman run -d --name kairos --pod traderterminal-pod \
  -v tt_config:/etc/traderterminal:z \
  ghcr.io/yourorg/kairos:latest
# Repeat for other containers…
```
> **Volumes** use `:z` SELinux relabel for Fedora.

## 6. Volume Strategy & Persistence
| Volume | Purpose | Driver | Backup Strategy |
|--------|---------|--------|-----------------|
| `tt_pgdata` | TimescaleDB data | local | Nightly pg_dump to host path `/var/backups/traderterminal` |
| `tt_marketdata` | Raw market data files | local | `rsync` to external NAS weekly |
| `tt_config` | Shared YAML config for all services | local | Git-tracked, bind mount to `$HOME/.config/traderterminal` |
| `tt_secrets` | mTLS certs + passwords | tmpfs for runtime, seeded by host secret manager | Rotate quarterly |

All volumes are declared and managed via `podman volume` with explicit SELinux labels for Fedora.

## 7. Autostart Integration
### 7.1 Fedora / SystemD
Generate unit files via `podman generate systemd`:
```bash
podman generate systemd \
  --name traderterminal-pod \
  --files --new --container-prefix tt
mv tt-traderterminal-pod.service ~/.config/systemd/user/
systemctl --user enable --now tt-traderterminal-pod.service
```
Key points:
- Runs rootless under the user session.
- `RequiresMountsFor` ensures volumes are ready.
- `Restart=on-failure` for resiliency.
- Log rotation handled by journald.

### 7.2 macOS / launchd
Podman Desktop (or brew `podman`) uses a Lima VM (`podman-machine`).  Autostart accomplished via a user LaunchAgent:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.traderterminal.pod</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/podman</string>
    <string>pod</string><string>start</string><string>traderterminal-pod</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/traderterminal_pod.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/traderterminal_pod.err</string>
</dict>
</plist>
```
Install with:
```bash
mkdir -p ~/Library/LaunchAgents
cp com.traderterminal.pod.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.traderterminal.pod.plist
```

## 8. Implementation Steps
1. **Create Containerfiles** for each service with minimal base images (Fedora minimal or scratch for Go binaries).
2. **Set up CI** to build & push images to Quay/GHCR on tag.
3. **Write Podman Compose file** (`traderterminal.compose.yaml`) for local dev.
4. **Provide make targets**: `make podman-up`, `make podman-down`, `make podman-logs`.
5. **Generate SystemD units** and ship in `packaging/fedora/` for spin.
6. **Provide LaunchAgent plist** template in `packaging/macos/`.
7. **Document volume backup procedures** (scripts in `scripts/backup/`).
8. **Add readiness/liveness probes** to all services (HTTP `/healthz`).
9. **Integrate Prometheus** scrape configs in ops image.
10. **Write end-to-end tests** using `podman pod exec` to verify startup.

## 9. Validation & KPIs
- Pod starts & all containers healthy in <15 s on Fedora 40.
- Database data persists after `podman pod rm -f` & recreation.
- SystemD service restarts pod on failure within 10 s.
- LaunchAgent autostarts pod after macOS reboot.
- Prometheus dashboard displays metrics from kairos & highseat.

## 10. Open Questions / Future Work
- GPU passthrough for ML-based strategies?
- Optional Traefik container for TLS termination?
- Kubernetes deployment option (kind / minikube) once project grows.

---
*Generated following Context Engineering PRP guidelines inspired by [context-engineering-intro](https://github.com/coleam00/context-engineering-intro) and tailored to TraderTerminal.* 