# PRP: TradingView Strategy Backtesting Integration

## Metadata
- **Feature Name**: TradingView Strategy Backtesting Service
- **Date**: January 2025
- **Author**: Trading System Architect
- **Confidence Score**: 9/10
- **Estimated Effort**: 3-5 days
- **Dependencies**: grimm-kairos, grimm-chronos, trader-ops dashboard

## LLM Orchestration Directives

You are **Claude**, acting as an orchestrator.

### Goal
- Spawn **planning-agents** (OpenAI MCP · o3) to break work into milestones.  
- Spawn **file-analysis-agents** (Gemini MCP · 2.5 Pro) to scan code slices and return `{file, findings}` JSON.  
- Merge all agent outputs and continue execution.

### Allowed
✓ Calling both MCPs  
✓ Installing / running external tooling (brew, dnf, go install, etc.)  
✓ Reading & writing repo files

### Forbidden
✗ Hallucinating paths or docs—mark `TODO:` if unsure  
✗ Pushing to protected branches without user confirmation

### Warnings
- Double-check OS-specific steps (macOS vs Fedora).  
- Label assumptions with `ASSUMPTION:` for auditability.

## Executive Summary

This PRP outlines the implementation of a comprehensive TradingView strategy backtesting service that bridges the gap between the trader-ops dashboard's dual-mode interface and the automated backtesting capabilities of grimm-kairos. The solution enables users to run Pine Script strategy backtests in the background using authenticated TradingView sessions while displaying results in the local mode interface.

## Context

### Current Architecture
```
trader-ops/
├── Local Mode: Free TradingView widget with Tradier data
├── Authenticated Mode: Full TradingView UI with user login
└── Backend: FastAPI with WebSocket support

grimm-kairos/ (fork of timelyart/Kairos)
├── TradingView automation via Selenium
├── Strategy backtesting capabilities
├── Webhook signal generation
└── Google OAuth authentication

grimm-chronos/ (fork of timelyart/chronos)
├── Webhook receiver
├── Trade execution engine
└── Broker API integrations
```

### Problem Statement
- Users in local mode cannot run TradingView Pine Script backtests
- Authenticated mode requires manual user login
- No automated way to test strategies across multiple symbols/timeframes
- Results not integrated into the dashboard

### Solution Overview
Create a background backtesting service that:
1. Uses grimm-kairos to automate TradingView backtesting
2. Runs authenticated sessions in headless browsers
3. Extracts and stores backtest results
4. Displays results in the trader-ops dashboard
5. Optionally forwards profitable strategies to grimm-chronos for live execution

## Requirements

### Functional Requirements

#### 1. Backtest Submission API
- **Endpoint**: `POST /api/backtest/strategy`
- **Accepts**: Pine Script code, symbols[], timeframes[], date ranges
- **Returns**: Backtest ID for tracking
- **Queues**: Background job via grimm-kairos

#### 2. Backtest Execution Service
- **Authenticates**: Using stored TradingView credentials
- **Navigates**: To TradingView strategy tester
- **Injects**: Pine Script code
- **Runs**: Backtests across specified parameters
- **Extracts**: Performance metrics, trade list, equity curve

#### 3. Results Storage & Retrieval
- **Database**: PostgreSQL with backtest_results table
- **Schema**: Includes metrics, trades, parameters, timestamps
- **API**: GET endpoints for status and results
- **WebSocket**: Real-time progress updates

#### 4. Dashboard Integration
- **Component**: BacktestPanel.vue with Pine Script editor
- **Display**: Results visualization (charts, metrics, trade list)
- **Export**: CSV/JSON download options
- **History**: Previous backtest results browser

#### 5. Strategy Deployment Pipeline
- **Validation**: Profitable strategies meeting criteria
- **Export**: Generate Kairos YAML config for alerts
- **Deploy**: Send to Chronos for live execution
- **Monitor**: Track live vs backtest performance

### Non-Functional Requirements

#### Performance
- Parallel backtest execution (up to 5 concurrent)
- Results caching for repeated queries
- <5 second API response times
- WebSocket updates every 2 seconds

#### Security
- Encrypted credential storage
- Session isolation between users
- Rate limiting on backtest submissions
- Audit logging of all operations

#### Reliability
- Retry logic for failed backtests
- Graceful degradation on Kairos failures
- Queue persistence across restarts
- Result data backup strategy

## Implementation Plan

### Phase 1: Backend Service Architecture (Day 1)

#### Step 1.1: Create Backtest Service Module
```python
# src/backend/services/backtest_service.py
from typing import List, Dict, Any
import asyncio
from pathlib import Path
import uuid
import yaml
from fastapi import BackgroundTasks

class BacktestService:
    def __init__(self, kairos_path: Path, db_connection):
        self.kairos_path = kairos_path
        self.db = db_connection
        self.active_backtests = {}
    
    async def submit_backtest(
        self,
        pine_script: str,
        symbols: List[str],
        timeframes: List[str],
        date_range: Dict[str, str],
        background_tasks: BackgroundTasks
    ) -> str:
        """Submit a new backtest job"""
        backtest_id = str(uuid.uuid4())
        
        # Store initial record
        await self.db.create_backtest(
            backtest_id=backtest_id,
            status="queued",
            config={
                "symbols": symbols,
                "timeframes": timeframes,
                "date_range": date_range
            }
        )
        
        # Queue background execution
        background_tasks.add_task(
            self._execute_backtest,
            backtest_id,
            pine_script,
            symbols,
            timeframes,
            date_range
        )
        
        return backtest_id
```

#### Step 1.2: Kairos Integration Layer
```python
# src/backend/services/kairos_integration.py
class KairosBacktestRunner:
    def __init__(self, kairos_path: Path):
        self.kairos_path = kairos_path
        
    async def run_backtest(
        self,
        strategy_code: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Execute single backtest via Kairos"""
        # Create Kairos config
        config = self._create_kairos_config(
            strategy_code, symbol, timeframe, 
            start_date, end_date
        )
        
        # Run Kairos subprocess
        results = await self._execute_kairos(config)
        
        # Parse and return results
        return self._parse_results(results)
```

#### Validation Gate 1.1
```bash
# Test service initialization
pytest src/backend/tests/test_backtest_service.py::test_service_init

# Test Kairos integration
pytest src/backend/tests/test_kairos_integration.py::test_kairos_config_generation
```

### Phase 2: API Endpoints (Day 1-2)

#### Step 2.1: Backtest Management API
```python
# src/backend/api/backtest.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/backtest")

class BacktestRequest(BaseModel):
    pine_script: str
    symbols: List[str] = ["MNQ1!"]
    timeframes: List[str] = ["1h", "4h", "1d"]
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@router.post("/strategy")
async def submit_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """Submit a new strategy backtest"""
    backtest_id = await backtest_service.submit_backtest(
        pine_script=request.pine_script,
        symbols=request.symbols,
        timeframes=request.timeframes,
        date_range={
            "start": request.start_date,
            "end": request.end_date
        },
        background_tasks=background_tasks
    )
    
    return {
        "backtest_id": backtest_id,
        "status": "queued",
        "message": "Backtest submitted successfully"
    }

@router.get("/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """Get current backtest status"""
    status = await backtest_service.get_status(backtest_id)
    if not status:
        raise HTTPException(404, "Backtest not found")
    return status

@router.get("/{backtest_id}/results")
async def get_backtest_results(backtest_id: str):
    """Get completed backtest results"""
    results = await backtest_service.get_results(backtest_id)
    if not results:
        raise HTTPException(404, "Results not found")
    return results
```

#### Step 2.2: WebSocket Progress Updates
```python
# src/backend/api/websocket.py
@app.websocket("/ws/backtest/{backtest_id}")
async def backtest_progress(websocket: WebSocket, backtest_id: str):
    await websocket.accept()
    
    while True:
        # Get current progress
        progress = await backtest_service.get_progress(backtest_id)
        
        if progress:
            await websocket.send_json({
                "type": "progress",
                "data": progress
            })
            
            if progress["status"] in ["completed", "failed"]:
                break
                
        await asyncio.sleep(2)
    
    await websocket.close()
```

#### Validation Gate 2.1
```bash
# Test API endpoints
pytest src/backend/tests/test_backtest_api.py -v

# Test WebSocket functionality
pytest src/backend/tests/test_websocket_progress.py -v
```

### Phase 3: Frontend Components (Day 2-3)

#### Step 3.1: Backtest Panel Component
```vue
<!-- src/frontend/components/BacktestPanel.vue -->
<template>
  <div class="backtest-panel">
    <div class="header">
      <h2>Strategy Backtesting</h2>
      <span class="beta-badge">BETA</span>
    </div>
    
    <!-- Pine Script Editor Section -->
    <div class="editor-section">
      <div class="editor-header">
        <label>Pine Script Strategy</label>
        <button @click="loadExample" class="secondary-btn">
          Load Example
        </button>
      </div>
      
      <MonacoEditor
        v-model="pineScript"
        language="pinescript"
        :height="400"
        :options="{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          theme: 'vs-dark'
        }"
      />
    </div>
    
    <!-- Configuration Section -->
    <div class="config-section">
      <div class="config-row">
        <div class="config-item">
          <label>Symbols</label>
          <SymbolSelector 
            v-model="selectedSymbols" 
            :multiple="true"
            :default-symbols="['MNQ1!', 'ES1!', 'NQ1!']"
          />
        </div>
        
        <div class="config-item">
          <label>Timeframes</label>
          <TimeframeSelector 
            v-model="selectedTimeframes" 
            :multiple="true"
            :options="['1m', '5m', '15m', '1h', '4h', '1d']"
          />
        </div>
      </div>
      
      <div class="config-row">
        <div class="config-item">
          <label>Date Range</label>
          <DateRangePicker
            v-model="dateRange"
            :max-date="new Date()"
          />
        </div>
      </div>
    </div>
    
    <!-- Action Buttons -->
    <div class="actions">
      <button 
        @click="runBacktest" 
        :disabled="!canRunBacktest || isRunning"
        class="primary-btn"
      >
        <span v-if="!isRunning">Run Backtest</span>
        <span v-else>
          <LoadingSpinner /> Running...
        </span>
      </button>
      
      <button 
        @click="viewHistory" 
        class="secondary-btn"
      >
        View History
      </button>
    </div>
    
    <!-- Progress Display -->
    <BacktestProgress
      v-if="currentBacktestId"
      :backtest-id="currentBacktestId"
      @complete="onBacktestComplete"
      @error="onBacktestError"
    />
    
    <!-- Results Display -->
    <BacktestResults
      v-if="latestResults"
      :results="latestResults"
      @export="exportResults"
      @deploy="deployStrategy"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBacktestAPI } from '@/composables/useBacktestAPI'
import { useNotification } from '@/composables/useNotification'
import MonacoEditor from '@/components/MonacoEditor.vue'
import SymbolSelector from '@/components/SymbolSelector.vue'
import TimeframeSelector from '@/components/TimeframeSelector.vue'
import DateRangePicker from '@/components/DateRangePicker.vue'
import BacktestProgress from '@/components/BacktestProgress.vue'
import BacktestResults from '@/components/BacktestResults.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const { submitBacktest, getResults } = useBacktestAPI()
const { showSuccess, showError } = useNotification()

// Reactive state
const pineScript = ref(`//@version=5
strategy("MA Crossover Strategy", overlay=true)

// Input parameters
fastLength = input.int(9, "Fast MA Length", minval=1)
slowLength = input.int(21, "Slow MA Length", minval=1)

// Calculate moving averages
fastMA = ta.sma(close, fastLength)
slowMA = ta.sma(close, slowLength)

// Plot MAs
plot(fastMA, "Fast MA", color.blue, 2)
plot(slowMA, "Slow MA", color.red, 2)

// Trading logic
longCondition = ta.crossover(fastMA, slowMA)
shortCondition = ta.crossunder(fastMA, slowMA)

// Execute trades
if (longCondition)
    strategy.entry("Long", strategy.long)

if (shortCondition)
    strategy.entry("Short", strategy.short)

// Risk management
strategy.exit("Exit Long", "Long", profit=1000, loss=500)
strategy.exit("Exit Short", "Short", profit=1000, loss=500)
`)

const selectedSymbols = ref(['MNQ1!'])
const selectedTimeframes = ref(['1h', '4h'])
const dateRange = ref({
  start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), // 90 days ago
  end: new Date()
})

const isRunning = ref(false)
const currentBacktestId = ref<string | null>(null)
const latestResults = ref(null)

// Computed
const canRunBacktest = computed(() => {
  return pineScript.value.trim().length > 0 &&
         selectedSymbols.value.length > 0 &&
         selectedTimeframes.value.length > 0
})

// Methods
const runBacktest = async () => {
  try {
    isRunning.value = true
    
    const response = await submitBacktest({
      pine_script: pineScript.value,
      symbols: selectedSymbols.value,
      timeframes: selectedTimeframes.value,
      start_date: dateRange.value.start.toISOString().split('T')[0],
      end_date: dateRange.value.end.toISOString().split('T')[0]
    })
    
    currentBacktestId.value = response.backtest_id
    showSuccess('Backtest submitted successfully')
    
  } catch (error) {
    showError('Failed to submit backtest: ' + error.message)
    isRunning.value = false
  }
}

const onBacktestComplete = async (backtestId: string) => {
  try {
    const results = await getResults(backtestId)
    latestResults.value = results
    isRunning.value = false
    currentBacktestId.value = null
    showSuccess('Backtest completed successfully')
  } catch (error) {
    showError('Failed to retrieve results: ' + error.message)
  }
}

const onBacktestError = (error: any) => {
  showError('Backtest failed: ' + error.message)
  isRunning.value = false
  currentBacktestId.value = null
}

const loadExample = () => {
  // Load a more complex example strategy
  pineScript.value = EXAMPLE_STRATEGIES.paintBar
}

const exportResults = (format: 'csv' | 'json') => {
  // Implementation for exporting results
  console.log('Export results as:', format)
}

const deployStrategy = async () => {
  // Implementation for deploying to Chronos
  console.log('Deploy strategy to live trading')
}

const viewHistory = () => {
  // Navigate to backtest history view
  router.push('/backtests/history')
}
</script>

<style scoped>
.backtest-panel {
  background: var(--surface-color);
  border-radius: 8px;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.beta-badge {
  background: var(--warning-color);
  color: var(--text-on-warning);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 12px;
}

.editor-section {
  margin-bottom: 24px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-section {
  background: var(--background-color);
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 24px;
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.config-row:last-child {
  margin-bottom: 0;
}

.config-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.primary-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.secondary-btn {
  background: transparent;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  padding: 12px 24px;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
}
</style>
```

#### Step 3.2: Results Visualization Component
```vue
<!-- src/frontend/components/BacktestResults.vue -->
<template>
  <div class="backtest-results">
    <h3>Backtest Results</h3>
    
    <!-- Summary Metrics -->
    <div class="metrics-grid">
      <MetricCard
        title="Total Return"
        :value="formatPercent(results.metrics.total_return)"
        :trend="results.metrics.total_return > 0 ? 'up' : 'down'"
      />
      <MetricCard
        title="Win Rate"
        :value="formatPercent(results.metrics.win_rate)"
        :trend="results.metrics.win_rate > 0.5 ? 'up' : 'down'"
      />
      <MetricCard
        title="Profit Factor"
        :value="formatNumber(results.metrics.profit_factor)"
        :trend="results.metrics.profit_factor > 1.5 ? 'up' : 'down'"
      />
      <MetricCard
        title="Max Drawdown"
        :value="formatPercent(results.metrics.max_drawdown)"
        :trend="'down'"
      />
      <MetricCard
        title="Sharpe Ratio"
        :value="formatNumber(results.metrics.sharpe_ratio)"
        :trend="results.metrics.sharpe_ratio > 1 ? 'up' : 'down'"
      />
      <MetricCard
        title="Total Trades"
        :value="results.metrics.total_trades"
      />
    </div>
    
    <!-- Equity Curve Chart -->
    <div class="chart-section">
      <h4>Equity Curve</h4>
      <EquityCurveChart
        :data="results.equity_curve"
        :height="300"
      />
    </div>
    
    <!-- Trade Analysis -->
    <div class="trades-section">
      <h4>Trade Analysis</h4>
      <TradesTable
        :trades="results.trades"
        :sortable="true"
        :paginated="true"
      />
    </div>
    
    <!-- Action Buttons -->
    <div class="result-actions">
      <button @click="$emit('export', 'csv')" class="secondary-btn">
        Export CSV
      </button>
      <button @click="$emit('export', 'json')" class="secondary-btn">
        Export JSON
      </button>
      <button 
        v-if="isProfitable" 
        @click="$emit('deploy')" 
        class="primary-btn"
      >
        Deploy to Live Trading
      </button>
    </div>
  </div>
</template>
```

#### Validation Gate 3.1
```bash
# Test frontend components
npm run test:unit -- BacktestPanel.spec.ts
npm run test:unit -- BacktestResults.spec.ts

# Test E2E flow
npm run test:e2e -- backtest-flow.spec.ts
```

### Phase 4: Kairos Configuration & Integration (Day 3-4)

#### Step 4.1: Kairos YAML Generator
```python
# src/backend/services/kairos_config_generator.py
class KairosConfigGenerator:
    def generate_backtest_config(
        self,
        strategy_code: str,
        symbol: str,
        timeframe: str,
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate Kairos YAML config for backtesting"""
        return {
            "charts": [{
                "symbol": symbol,
                "timeframes": [timeframe],
                "strategies": [{
                    "name": f"Backtest_{symbol}_{timeframe}",
                    "script": strategy_code,
                    "backtest": {
                        "enabled": True,
                        "start_date": date_range["start"],
                        "end_date": date_range["end"],
                        "initial_capital": 10000,
                        "commission": {
                            "type": "fixed",
                            "value": 0.75  # For futures
                        },
                        "slippage": {
                            "type": "ticks",
                            "value": 1
                        }
                    },
                    "extract_data": {
                        "metrics": True,
                        "trades": True,
                        "equity_curve": True
                    }
                }]
            }],
            "export": {
                "format": "json",
                "path": f"backtest_results/{symbol}_{timeframe}.json"
            }
        }
```

#### Step 4.2: Results Parser
```python
# src/backend/services/backtest_results_parser.py
class BacktestResultsParser:
    def parse_kairos_output(self, output_path: Path) -> Dict[str, Any]:
        """Parse Kairos backtest output"""
        with open(output_path) as f:
            raw_results = json.load(f)
        
        return {
            "metrics": {
                "total_return": raw_results["performance"]["total_return"],
                "win_rate": raw_results["performance"]["win_rate"],
                "profit_factor": raw_results["performance"]["profit_factor"],
                "max_drawdown": raw_results["performance"]["max_drawdown"],
                "sharpe_ratio": raw_results["performance"]["sharpe_ratio"],
                "total_trades": raw_results["summary"]["total_trades"]
            },
            "trades": self._parse_trades(raw_results["trades"]),
            "equity_curve": self._parse_equity_curve(raw_results["equity"])
        }
```

### Phase 5: Live Trading Integration (Day 4-5)

#### Step 5.1: Strategy Deployment Pipeline
```python
# src/backend/services/strategy_deployment.py
class StrategyDeploymentService:
    def __init__(self, chronos_api_url: str):
        self.chronos_api = chronos_api_url
        
    async def deploy_strategy(
        self,
        strategy_id: str,
        backtest_results: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy profitable strategy to Chronos"""
        
        # Validate strategy meets criteria
        if not self._validate_for_deployment(backtest_results):
            raise ValueError("Strategy does not meet deployment criteria")
        
        # Generate Kairos alert config
        alert_config = self._generate_alert_config(
            strategy_id,
            deployment_config
        )
        
        # Configure Chronos webhook
        webhook_config = self._generate_webhook_config(
            strategy_id,
            deployment_config
        )
        
        # Deploy to Chronos
        response = await self._deploy_to_chronos(
            alert_config,
            webhook_config
        )
        
        return response
```

#### Validation Gate 5.1
```bash
# Test deployment pipeline
pytest src/backend/tests/test_strategy_deployment.py -v

# Integration test with mock Chronos
pytest src/backend/tests/test_chronos_integration.py -v
```

## Example Usage

### 1. Submit a Backtest
```javascript
// Frontend
const response = await fetch('/api/backtest/strategy', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    pine_script: strategyCode,
    symbols: ['MNQ1!', 'ES1!'],
    timeframes: ['1h', '4h'],
    start_date: '2024-01-01',
    end_date: '2024-12-31'
  })
})

const { backtest_id } = await response.json()
```

### 2. Monitor Progress
```javascript
// WebSocket connection
const ws = new WebSocket(`ws://localhost:8000/ws/backtest/${backtest_id}`)

ws.onmessage = (event) => {
  const progress = JSON.parse(event.data)
  console.log(`Progress: ${progress.completed}/${progress.total}`)
}
```

### 3. Retrieve Results
```javascript
// Get results
const results = await fetch(`/api/backtest/${backtest_id}/results`)
const data = await results.json()

console.log(`Total Return: ${data.metrics.total_return}%`)
console.log(`Win Rate: ${data.metrics.win_rate}%`)
```

## Technical Specifications

### Database Schema
```sql
-- Backtest results table
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    metrics JSONB,
    trades JSONB,
    equity_curve JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Backtest queue table
CREATE TABLE backtest_queue (
    id UUID PRIMARY KEY,
    backtest_id UUID NOT NULL,
    priority INTEGER DEFAULT 5,
    attempts INTEGER DEFAULT 0,
    next_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id)
);

-- Deployed strategies table
CREATE TABLE deployed_strategies (
    id UUID PRIMARY KEY,
    backtest_id UUID NOT NULL,
    chronos_webhook_id VARCHAR(255),
    kairos_alert_id VARCHAR(255),
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    deployed_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id)
);
```

### API Response Formats
```typescript
// Backtest submission response
interface BacktestSubmissionResponse {
  backtest_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  message: string
  estimated_time_seconds?: number
}

// Progress update format
interface BacktestProgress {
  backtest_id: string
  status: string
  current_symbol: string
  current_timeframe: string
  completed_tests: number
  total_tests: number
  percentage: number
  estimated_time_remaining: number
}

// Results format
interface BacktestResults {
  backtest_id: string
  status: 'completed'
  config: BacktestConfig
  metrics: PerformanceMetrics
  trades: Trade[]
  equity_curve: EquityPoint[]
  created_at: string
  completed_at: string
  execution_time_seconds: number
}
```

## Success Criteria

### Functional Success
- [ ] Users can submit Pine Script strategies for backtesting
- [ ] Backtests run in background without user authentication
- [ ] Results display in dashboard with visualizations
- [ ] Profitable strategies can be deployed to live trading
- [ ] Historical backtest results are searchable

### Performance Success
- [ ] Backtests complete within 5 minutes for single symbol/timeframe
- [ ] System handles 5 concurrent backtests
- [ ] API responses under 500ms
- [ ] WebSocket updates every 2 seconds

### Quality Success
- [ ] 90% test coverage on backend services
- [ ] All API endpoints have validation
- [ ] Error messages are user-friendly
- [ ] Comprehensive logging for debugging

## Risks & Mitigations

### Technical Risks
1. **Kairos Authentication Failures**
   - Mitigation: Implement retry logic with exponential backoff
   - Fallback: Queue for manual intervention

2. **TradingView UI Changes**
   - Mitigation: Use stable selectors, implement change detection
   - Fallback: Version-lock Kairos, monitor for updates

3. **Performance Bottlenecks**
   - Mitigation: Implement caching, optimize database queries
   - Fallback: Scale horizontally with worker nodes

### Business Risks
1. **TradingView ToS Compliance**
   - Mitigation: Rate limiting, respectful automation
   - Fallback: Manual review process

2. **Data Accuracy**
   - Mitigation: Validation checks, result verification
   - Fallback: Manual spot checks

## Monitoring & Observability

### Metrics to Track
- Backtest submission rate
- Average completion time
- Success/failure ratio
- Queue depth
- Resource utilization

### Logging Strategy
```python
# Structured logging
logger.info("backtest.submitted", extra={
    "backtest_id": backtest_id,
    "symbols": symbols,
    "timeframes": timeframes,
    "user_id": user_id
})

logger.error("backtest.failed", extra={
    "backtest_id": backtest_id,
    "error": str(error),
    "stage": "kairos_execution"
})
```

### Alerting Rules
- Queue depth > 100: Scale workers
- Failure rate > 10%: Investigate issues
- Completion time > 10min: Performance review

## Glossary

- **PRP**: Product Requirements Prompt - Comprehensive implementation blueprint
- **Kairos**: TradingView automation tool (grimm-kairos fork)
- **Chronos**: Webhook-based trade execution tool (grimm-chronos fork)
- **Pine Script**: TradingView's programming language for strategies
- **UDF**: Universal Data Feed protocol for TradingView
- **MNQ1!**: Micro E-mini Nasdaq-100 futures contract

## References

- [Context Engineering Intro](https://github.com/coleam00/context-engineering-intro)
- [TradingView Pine Script Reference](https://www.tradingview.com/pine-script-reference/)
- [Kairos Documentation](https://github.com/timelyart/Kairos)
- [Chronos Documentation](https://github.com/timelyart/chronos)
- Trader-Ops Internal Documentation: `/docs/`

---

**END OF PRP**

## Validation Checklist

- [x] All requirements clearly defined
- [x] Implementation steps detailed
- [x] Code examples provided
- [x] Validation gates included
- [x] Database schema specified
- [x] API contracts defined
- [x] Error handling documented
- [x] Success criteria measurable
- [x] Risks identified with mitigations
- [x] References included 