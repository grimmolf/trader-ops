<template>
  <div class="risk-meter">
    <div class="meter-container">
      <div class="meter-header">
        <label class="meter-label">{{ label }}</label>
        <div class="meter-status" :class="severityClass">
          <span class="status-dot" :class="{ pulse: isDanger }"></span>
          {{ statusText }}
        </div>
      </div>
      
      <div class="meter-bar-container">
        <div class="meter-bar" :class="severityClass">
          <div 
            class="meter-fill" 
            :style="{ width: percentage + '%' }"
            :class="{ 'danger-pulse': isDanger }"
          />
          <div class="meter-threshold" v-if="showThreshold" :style="{ left: thresholdPosition + '%' }">
            <div class="threshold-line"></div>
            <div class="threshold-label">{{ thresholdLabel }}</div>
          </div>
        </div>
        
        <div class="meter-scale">
          <span class="scale-mark" v-for="mark in scaleMarks" :key="mark" :style="{ left: mark + '%' }">
            |
          </span>
        </div>
      </div>
      
      <div class="meter-values">
        <div class="current-value">
          <span class="value-label">Current:</span>
          <span class="value" :class="{ negative: current < 0 }">
            {{ formatValue(current) }}
          </span>
        </div>
        
        <div class="limit-value">
          <span class="value-label">Limit:</span>
          <span class="value">{{ formatValue(limit) }}</span>
        </div>
        
        <div class="remaining-value" v-if="showRemaining">
          <span class="value-label">Remaining:</span>
          <span class="value" :class="remainingSeverity">
            {{ formatValue(remaining) }}
          </span>
        </div>
      </div>
      
      <div class="meter-details" v-if="showDetails">
        <div class="detail-item">
          <span class="detail-label">Utilization:</span>
          <span class="detail-value">{{ percentage.toFixed(1) }}%</span>
        </div>
        
        <div class="detail-item" v-if="timeToLimit">
          <span class="detail-label">Est. Time to Limit:</span>
          <span class="detail-value" :class="{ warning: timeToLimit < 60 }">
            {{ formatTimeToLimit(timeToLimit) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRefs } from 'vue'

interface Props {
  label: string
  current: number
  limit: number
  inverse?: boolean  // For drawdown, higher is worse
  showThreshold?: boolean
  thresholdValue?: number
  thresholdLabel?: string
  showRemaining?: boolean
  showDetails?: boolean
  timeToLimit?: number  // Minutes until limit reached at current rate
  format?: 'currency' | 'percentage' | 'number'
}

const props = withDefaults(defineProps<Props>(), {
  inverse: false,
  showThreshold: false,
  thresholdValue: 80,
  thresholdLabel: 'Warning',
  showRemaining: true,
  showDetails: false,
  timeToLimit: undefined,
  format: 'currency'
})

const { 
  current, 
  limit, 
  inverse, 
  showThreshold, 
  thresholdValue, 
  showRemaining,
  timeToLimit,
  format 
} = toRefs(props)

// Calculate percentage utilization
const percentage = computed(() => {
  if (limit.value === 0) return 0
  
  let pct: number
  if (inverse.value) {
    // For inverse metrics (like drawdown), calculate as current/limit
    pct = (Math.abs(current.value) / limit.value) * 100
  } else {
    // For normal metrics, calculate utilization
    pct = (Math.abs(current.value) / limit.value) * 100
  }
  
  return Math.min(Math.max(pct, 0), 100)
})

// Determine severity level
const severityClass = computed(() => {
  const pct = percentage.value
  if (pct >= 90) return 'critical'
  if (pct >= 80) return 'danger'
  if (pct >= 60) return 'warning'
  if (pct >= 40) return 'caution'
  return 'safe'
})

// Status text based on severity
const statusText = computed(() => {
  const pct = percentage.value
  if (pct >= 90) return 'CRITICAL'
  if (pct >= 80) return 'DANGER'
  if (pct >= 60) return 'WARNING'
  if (pct >= 40) return 'CAUTION'
  return 'SAFE'
})

// Determine if in danger zone
const isDanger = computed(() => percentage.value >= 80)

// Calculate remaining capacity
const remaining = computed(() => {
  if (inverse.value) {
    return Math.max(0, limit.value - Math.abs(current.value))
  } else {
    return Math.max(0, limit.value - Math.abs(current.value))
  }
})

// Remaining value severity
const remainingSeverity = computed(() => {
  const remainingPct = (remaining.value / limit.value) * 100
  if (remainingPct <= 10) return 'critical'
  if (remainingPct <= 20) return 'danger'
  if (remainingPct <= 40) return 'warning'
  return 'safe'
})

// Threshold position for warning line
const thresholdPosition = computed(() => {
  return Math.min(thresholdValue.value || 80, 100)
})

// Scale marks for visual reference
const scaleMarks = computed(() => [0, 25, 50, 75, 100])

// Format values based on type
function formatValue(value: number): string {
  switch (format.value) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value)
    
    case 'percentage':
      return `${value.toFixed(1)}%`
    
    case 'number':
      return value.toLocaleString()
    
    default:
      return value.toString()
  }
}

// Format time to limit
function formatTimeToLimit(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)}m`
  if (minutes < 1440) return `${Math.round(minutes / 60)}h`
  return `${Math.round(minutes / 1440)}d`
}
</script>

<style scoped>
.risk-meter {
  width: 100%;
  padding: 1rem;
  background: var(--bg-secondary, #f8f9fa);
  border: 1px solid var(--border-color, #e9ecef);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.meter-container {
  width: 100%;
}

.meter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.meter-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary, #212529);
}

.meter-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.meter-bar-container {
  position: relative;
  margin-bottom: 0.75rem;
}

.meter-bar {
  height: 24px;
  background: var(--bg-tertiary, #e9ecef);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.meter-fill {
  height: 100%;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: inherit;
  position: relative;
}

.meter-threshold {
  position: absolute;
  top: 0;
  bottom: 0;
  pointer-events: none;
}

.threshold-line {
  width: 2px;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1px;
}

.threshold-label {
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.7rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

.meter-scale {
  height: 8px;
  position: relative;
  margin-top: 2px;
}

.scale-mark {
  position: absolute;
  font-size: 0.6rem;
  color: var(--text-muted, #6c757d);
  transform: translateX(-50%);
}

.meter-values {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.meter-values.with-remaining {
  grid-template-columns: 1fr 1fr 1fr;
}

.current-value,
.limit-value,
.remaining-value {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.value-label {
  font-size: 0.75rem;
  color: var(--text-muted, #6c757d);
  font-weight: 500;
}

.value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary, #212529);
}

.value.negative {
  color: var(--danger-color, #dc3545);
}

.meter-details {
  display: flex;
  justify-content: space-between;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-color, #e9ecef);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.7rem;
  color: var(--text-muted, #6c757d);
}

.detail-value {
  font-size: 0.8rem;
  font-weight: 500;
}

/* Severity-based colors */
.safe {
  --meter-color: #28a745;
  --status-bg: #d4edda;
  --status-color: #155724;
}

.caution {
  --meter-color: #17a2b8;
  --status-bg: #d1ecf1;
  --status-color: #0c5460;
}

.warning {
  --meter-color: #ffc107;
  --status-bg: #fff3cd;
  --status-color: #856404;
}

.danger {
  --meter-color: #fd7e14;
  --status-bg: #ffe5b4;
  --status-color: #8a4d00;
}

.critical {
  --meter-color: #dc3545;
  --status-bg: #f8d7da;
  --status-color: #721c24;
}

.meter-status {
  background: var(--status-bg);
  color: var(--status-color);
}

.status-dot {
  background: var(--meter-color);
}

.meter-fill {
  background: var(--meter-color);
}

.pulse {
  animation: pulse 1s infinite;
}

.danger-pulse {
  animation: danger-pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes danger-pulse {
  0%, 100% { 
    opacity: 1; 
    box-shadow: 0 0 0 0 var(--meter-color);
  }
  50% { 
    opacity: 0.8;
    box-shadow: 0 0 0 4px rgba(220, 53, 69, 0.3);
  }
}

/* Remaining value colors */
.remaining-value .value.critical {
  color: #dc3545;
  font-weight: 700;
}

.remaining-value .value.danger {
  color: #fd7e14;
  font-weight: 600;
}

.remaining-value .value.warning {
  color: #ffc107;
  font-weight: 600;
}

.remaining-value .value.safe {
  color: #28a745;
}

.detail-value.warning {
  color: #fd7e14;
  font-weight: 600;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .risk-meter {
    --bg-secondary: #2d3748;
    --bg-tertiary: #4a5568;
    --border-color: #4a5568;
    --text-primary: #f7fafc;
    --text-muted: #a0aec0;
  }
}
</style>