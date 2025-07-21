<template>
  <div class="tradingview-chart">
    <div v-if="isLoading" class="chart-loading">
      <div class="loading-spinner"></div>
      <span>Loading chart...</span>
    </div>
    <div 
      ref="chartContainer" 
      class="chart-container"
      :style="{ visibility: isLoading ? 'hidden' : 'visible' }"
    ></div>
    <div v-if="error" class="chart-error">
      <span>{{ error }}</span>
      <button @click="retry" class="retry-btn">Retry</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'

interface TradingViewWidget {
  chart(): any
  onChartReady(callback: () => void): void
  remove(): void
}

const props = defineProps<{
  symbol: string
  datafeedUrl: string
}>()

const emit = defineEmits<{
  'alert-created': [alertData: any]
}>()

const chartContainer = ref<HTMLDivElement>()
const isLoading = ref(true)
const error = ref<string | null>(null)
let tvWidget: TradingViewWidget | null = null

// Custom UDF Datafeed implementation
class UDFDatafeed {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  onReady(callback: (configuration: any) => void) {
    fetch(`${this.baseUrl}/config`)
      .then(response => response.json())
      .then(data => {
        callback({
          supported_resolutions: data.supported_resolutions || ['1', '5', '15', '30', '60', '240', '1D'],
          supports_group_request: false,
          supports_marks: false,
          supports_search: true,
          supports_timescale_marks: false,
          exchanges: data.exchanges || [
            { value: 'NASDAQ', name: 'NASDAQ', desc: 'NASDAQ' },
            { value: 'CME', name: 'CME', desc: 'Chicago Mercantile Exchange' }
          ]
        })
      })
      .catch(err => {
        console.error('UDF config failed:', err)
        callback({
          supported_resolutions: ['1', '5', '15', '30', '60', '240', '1D'],
          supports_group_request: false,
          supports_marks: false,
          supports_search: true,
          supports_timescale_marks: false
        })
      })
  }

  searchSymbols(userInput: string, exchange: string, symbolType: string, onResult: (symbols: any[]) => void) {
    fetch(`${this.baseUrl}/search?query=${encodeURIComponent(userInput)}`)
      .then(response => response.json())
      .then(data => {
        onResult(data.symbols || [])
      })
      .catch(err => {
        console.error('Symbol search failed:', err)
        onResult([])
      })
  }

  resolveSymbol(symbolName: string, onResolve: (symbolInfo: any) => void, onError: (error: string) => void) {
    fetch(`${this.baseUrl}/symbols?symbol=${encodeURIComponent(symbolName)}`)
      .then(response => response.json())
      .then(data => {
        if (data.symbol) {
          onResolve({
            name: data.symbol,
            full_name: data.full_name || data.symbol,
            description: data.description || data.symbol,
            type: data.type || 'stock',
            session: '24x7',
            timezone: 'America/New_York',
            ticker: data.symbol,
            exchange: data.exchange || 'CME',
            minmov: 1,
            pricescale: data.pricescale || 100,
            has_intraday: true,
            has_no_volume: false,
            has_weekly_and_monthly: true,
            supported_resolutions: ['1', '5', '15', '30', '60', '240', '1D'],
            volume_precision: 0,
            data_status: 'streaming'
          })
        } else {
          onError('Symbol not found')
        }
      })
      .catch(err => {
        console.error('Symbol resolve failed:', err)
        onError('Failed to resolve symbol')
      })
  }

  getBars(symbolInfo: any, resolution: string, periodParams: any, onResult: (bars: any[], meta: any) => void, onError: (error: string) => void) {
    const { from, to, firstDataRequest } = periodParams
    
    const url = `${this.baseUrl}/history?symbol=${encodeURIComponent(symbolInfo.ticker)}&resolution=${resolution}&from=${from}&to=${to}`
    
    fetch(url)
      .then(response => response.json())
      .then(data => {
        if (data.s === 'ok' && data.t && data.c && data.o && data.h && data.l) {
          const bars = data.t.map((time: number, index: number) => ({
            time: time * 1000, // Convert to milliseconds
            open: data.o[index],
            high: data.h[index],
            low: data.l[index],
            close: data.c[index],
            volume: data.v ? data.v[index] : 0
          }))
          
          onResult(bars, { noData: false })
        } else if (data.s === 'no_data') {
          onResult([], { noData: true })
        } else {
          onError('Invalid data format')
        }
      })
      .catch(err => {
        console.error('History request failed:', err)
        onError('Failed to load historical data')
      })
  }

  subscribeBars(symbolInfo: any, resolution: string, onTick: (bar: any) => void, subscriberUID: string, onResetCacheNeededCallback: () => void) {
    // Real-time data subscription would be implemented here
    // For now, we'll use a mock implementation
    console.log('Subscribing to bars:', symbolInfo.ticker, resolution)
  }

  unsubscribeBars(subscriberUID: string) {
    console.log('Unsubscribing bars:', subscriberUID)
  }
}

async function initializeChart() {
  if (!chartContainer.value) return

  try {
    isLoading.value = true
    error.value = null

    // Ensure TradingView library is loaded
    if (typeof window.TradingView === 'undefined') {
      throw new Error('TradingView library not loaded')
    }

    const widgetOptions = {
      symbol: props.symbol,
      datafeed: new UDFDatafeed(props.datafeedUrl),
      interval: '5' as const,
      container: chartContainer.value,
      library_path: '/charting_library/',
      locale: 'en',
      disabled_features: [
        'use_localstorage_for_settings',
        'volume_force_overlay',
        'header_symbol_search',
        'header_compare'
      ],
      enabled_features: [
        'study_templates',
        'side_toolbar_in_fullscreen_mode'
      ],
      charts_storage_url: `${props.datafeedUrl}/charts`,
      charts_storage_api_version: '1.1',
      client_id: 'traderterminal',
      user_id: 'public_user',
      fullscreen: false,
      autosize: true,
      studies_overrides: {},
      theme: 'dark',
      custom_css_url: '/custom_chart.css',
      overrides: {
        'mainSeriesProperties.style': 1, // Candles
        'mainSeriesProperties.showCountdown': true,
        'paneProperties.background': '#0d1117',
        'paneProperties.vertGridProperties.color': '#21262d',
        'paneProperties.horzGridProperties.color': '#21262d',
        'symbolWatermarkProperties.transparency': 90,
        'scalesProperties.textColor': '#8b949e',
        'mainSeriesProperties.candleStyle.upColor': '#3fb950',
        'mainSeriesProperties.candleStyle.downColor': '#f85149',
        'mainSeriesProperties.candleStyle.borderUpColor': '#3fb950',
        'mainSeriesProperties.candleStyle.borderDownColor': '#f85149',
        'mainSeriesProperties.candleStyle.wickUpColor': '#3fb950',
        'mainSeriesProperties.candleStyle.wickDownColor': '#f85149'
      }
    }

    tvWidget = new window.TradingView.widget(widgetOptions)

    tvWidget.onChartReady(() => {
      console.log('TradingView chart ready')
      isLoading.value = false

      // Add default studies
      const chart = tvWidget!.chart()
      
      // Add moving averages
      chart.createStudy('Moving Average', false, false, [20], null, { 'plot.color': '#58a6ff' })
      chart.createStudy('Moving Average', false, false, [50], null, { 'plot.color': '#d29922' })
      
      // Add RSI
      chart.createStudy('RSI', false, false, [14])
      
      // Add volume
      chart.createStudy('Volume', false, false)

      // Listen for alert creation
      chart.onDataLoaded().subscribe(null, () => {
        console.log('Chart data loaded')
      })
    })

  } catch (err) {
    console.error('Failed to initialize TradingView chart:', err)
    error.value = err instanceof Error ? err.message : 'Unknown error'
    isLoading.value = false
  }
}

function destroyChart() {
  if (tvWidget) {
    try {
      tvWidget.remove()
      tvWidget = null
    } catch (err) {
      console.error('Error destroying chart:', err)
    }
  }
}

function retry() {
  error.value = null
  nextTick(() => {
    initializeChart()
  })
}

// Watch for symbol changes
watch(() => props.symbol, (newSymbol) => {
  if (tvWidget && newSymbol) {
    try {
      tvWidget.chart().setSymbol(newSymbol)
      console.log(`Chart symbol changed to: ${newSymbol}`)
    } catch (err) {
      console.error('Failed to change symbol:', err)
      // Reinitialize chart if symbol change fails
      destroyChart()
      nextTick(() => {
        initializeChart()
      })
    }
  }
})

onMounted(() => {
  // Small delay to ensure DOM is ready
  setTimeout(() => {
    initializeChart()
  }, 100)
})

onUnmounted(() => {
  destroyChart()
})
</script>

<style scoped>
.tradingview-chart {
  height: 100%;
  width: 100%;
  position: relative;
  background: var(--bg-primary);
}

.chart-container {
  height: 100%;
  width: 100%;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 14px;
  z-index: 1000;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--border-primary);
  border-top: 2px solid var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chart-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
  z-index: 1000;
}

.retry-btn {
  padding: 8px 16px;
  background: var(--accent-blue);
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 12px;
}

.retry-btn:hover {
  background: #4f8ce9;
}

/* Global TradingView widget styling */
:global(.tv-chart-container) {
  background: var(--bg-primary) !important;
}

:global(.chart-container-border) {
  border: none !important;
}
</style>