name: "Trader Dashboard v1 – Cross‑Platform Desktop (macOS → Fedora Spin)" description: |

## Purpose

Deliver a production‑grade **Trader Dashboard** that runs natively on macOS (Apple‑Silicon) and later packages cleanly into the Fedora‑42 “Trading Terminal” spin.  It must unify low‑cost real‑time data, high‑fidelity TradingView charting, automated alerts/exec via Kairos + Chronos, and back‑testing/analytics — all in a modular, container‑friendly architecture.

## Core Principles

1. **Context is King** – surface *all* API docs, licence caveats, and existing examples (trading‑setups, Kairos, Chronos).
2. **Validation Loops** – ship unit/integration tests and lint gates that the AI can run & auto‑fix.
3. **Information‑Dense** – reuse patterns from examples and Initial.md; respect licence terms (TradingView display‑only).
4. **Progressive Success** – first milestone runs locally on macOS with mock data; second swaps in live feeds; third repackages for Fedora.

### LLM Orchestration Directives

You are **Claude**, acting as an orchestrator.

## Goal
• Spawn **planning‑agents** (OpenAI MCP · o3) to break work into milestones.  
• Spawn **file‑analysis‑agents** (Gemini MCP · 2.5 Pro) to scan code slices and return `{file, findings}` JSON.  
• Merge all agent outputs and continue execution.

## Allowed
✓ Calling both MCPs  
✓ Installing / running external tooling (brew, dnf, go install, etc.)  
✓ Reading & writing repo files

## Forbidden
✗ Hallucinating paths or docs—mark `TODO:` if unsure  
✗ Pushing to protected branches without user confirmation

## Warnings
Double‑check OS‑specific steps (macOS vs Fedora).  
Label assumptions with `ASSUMPTION:` for auditability.


---

## Goal

Create an Electron (or tauri) desktop application with:

- Multi‑pane TradingView **Advanced Charts** widget fed by a local **Data Hub** (Tradier, Tradovate, CCXT).
- Alert Management panel (Kairos YAML jobs) and **Chronos** execution log.
- Portfolio / PnL & risk cards using PyPortfolioOpt/QuantStats.
- News & macro ribbon (NewsAPI, FRED).
- Strategy runner that loads Pine scripts from `trading-setups/` and back‑tests them in **QuantConnect LEAN**.
- Config‑driven; secrets from `.env`.

## Why

- **Daily driver need**: The author trades from a Mac Studio M3 and wants Bloomberg‑like situational awareness without Bloomberg fees.
- **Scalability**: Same architecture later packages into a Fedora spin, plus OpenShift containers for always‑on automation.
- **User impact**: Retail/institutional hybrid desk can see all asset classes (equity, options, futures, crypto) in one dashboard, trigger automated trades, and iterate new strategies quickly.

## What

### User‑Visible Behaviour & Technical Reqs

- Launch app → default layout: *Charts*, *Watch‑list*, *Order ticket*, *Alerts*, *News*.
- Select symbol in watch‑list updates chart & order ticket (IPC message).
- Real‑time prices refresh sub‑100 ms (ping to Data Hub).
- Alerts defined in Kairos YAML auto‑populate Chronos execution log when fired.
- Back‑test tab runs LEAN simulation, displays equity curve & metrics.
- Config wizard prompts for API keys on first run.

#### Success Criteria

-

## All Needed Context

### Documentation & References

```yaml
# MUST READ – include in context window
- url: https://www.tradingview.com/HTML5-stock-forex-bitcoin-charting-library/  
  why: Widget API, UDF/Datafeed protocol.
- url: https://developer.tradier.com/  
  why: Quote & order REST/WebSocket endpoints.
- url: https://api.tradovate.com/#/home  
  why: Futures WebSocket + auth flow.
- url: https://docs.ccxt.com/  
  why: Unified crypto exchange interface.
- file: examples/datahub_server.py  
  why: Pattern for UDF adapter.
- file: trading-setups/strategies/*.pine  
  why: Strategies to port.
- url: https://github.com/timelyart/kairos  
  why: Alert automation YAML schema.
- url: https://github.com/timelyart/chronos  
  why: Webhook payload & broker adapter pattern.
- url: https://www.lean.io/docs  
  why: Back‑testing engine & CLI usage.
```

### Current Codebase Tree (initial)

```bash
.
├── INITIAL.md
├── examples/
│   └── datahub_server.py   # stub
└── trading-setups/         # cloned external repo
```

### Desired Codebase Tree (Milestone 1)

```bash
.
├── app/
│   ├── main.ts            # Electron/Tauri bootstrap
│   ├── preload.ts         # IPC bridge
│   ├── renderer/
│   │   ├── App.vue / React
│   │   ├── components/
│   │   └── assets/
├── datahub/
│   ├── server.py          # FastAPI + WebSocket adaptors
│   ├── feeds/
│   │   ├── tradier.py
│   │   ├── tradovate.py
│   │   └── ccxt.py
├── kairos_jobs/
│   └── *.yaml
├── chronos/
│   └── main.py            # listener + broker adapters
├── backtests/
│   └── lean_runner.py
├── tests/
│   ├── unit/
│   └── e2e/
├── pyproject.toml         # Poetry deps
├── .env.example
└── README.md
```

### Known Gotchas & Library Quirks

```python
# TradingView chart wants epoch seconds, but Tradier returns ISO8601 – convert!
# Tradovate WS auth expires every 10 minutes; refresh tokens proactively.
# CCXT markets differ per exchange – normalise symbol map.
# M1/M3 Macs need Chromium ARM build for Kairos Selenium.
# Electron auto‑update disabled during dev – enable later for spin.
```

## Implementation Blueprint

### Data Models & Structure

```python
# pydantic models for candles, trades, positions, alerts
class Candle(BaseModel):
    ts: int  # epoch seconds
    o: float; h: float; l: float; c: float; v: float
class Alert(BaseModel):
    id: str; symbol: str; condition: str; created_at: int
class Execution(BaseModel):
    broker: str; order_id: str; symbol: str; side: str; qty: float; price: float; ts: int
```

### Task List

```yaml
Task 1: CREATE datahub/server.py – FastAPI server exposing /config, /symbols, /history, /stream.
Task 2: ADD feeds/tradier.py – wrapper for quote WS & order REST.
Task 3: ADD Kairos example YAML and systemd timer.
Task 4: ADD chronos/main.py – Flask listener, Tradier execution adapter, ZeroMQ publisher.
Task 5: CREATE Electron renderer App with TradingView widget; connect to ws://localhost:9000.
Task 6: Wire IPC: symbol‑clicked → main process → send REST /history + subscribe WS.
Task 7: ADD tests/unit/test_datahub.py + tests/e2e/test_app.py (Playwright).
Task 8: GitHub CI – run Poetry install, Ruff, mypy, pytest, Playwright headless.
```

### Per‑task Pseudocode (sample)

```python
# Task 2 – tradier.py
async def websocket_feed(symbols: list[str]):
    async with websockets.connect(TRADIER_WS, extra_headers={"Authorization": f"Bearer {TOKEN}"}) as ws:
        await ws.send(json.dumps({"symbols": ",".join(symbols)}))
        async for msg in ws:
            yield normalise_tradier_tick(msg)
```

## Validation Loop

### Level 1 – Style & Types

```bash
ruff check . --fix
mypy .
```

### Level 2 – Unit Tests

```bash
pytest -q tests/unit
```

### Level 3 – E2E

```bash
playwright install chromium
pytest tests/e2e
```

## Final Validation Checklist

-

---

## Anti‑Patterns to Avoid

❌ Scraping TradingView sockets.\
❌ Mixing sync & async feeds in same loop.\
❌ Hard‑coding API keys.\
❌ Ignoring WS reconnect/back‑pressure

