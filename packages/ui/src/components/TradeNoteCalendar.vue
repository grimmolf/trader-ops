<template>
  <div class="tradenote-calendar">
    <!-- Calendar Header -->
    <div class="calendar-header">
      <div class="header-title">
        <h4>Trading Calendar</h4>
        <div class="date-range" v-if="dateRange">
          {{ formatDateRange(dateRange.start, dateRange.end) }}
        </div>
      </div>
      
      <div class="header-actions">
        <select v-model="selectedPeriod" @change="onPeriodChanged" class="period-select">
          <option value="1m">1 Month</option>
          <option value="3m">3 Months</option>
          <option value="6m">6 Months</option>
          <option value="1y">1 Year</option>
        </select>
        
        <button 
          class="refresh-btn"
          @click="refreshCalendar"
          :disabled="isLoading"
          title="Refresh calendar data"
        >
          <span class="btn-icon" :class="{ spinning: isLoading }">↻</span>
        </button>
      </div>
    </div>

    <!-- Calendar Legend -->
    <div class="calendar-legend">
      <div class="legend-item">
        <div class="legend-color profit-high"></div>
        <span>High Profit</span>
      </div>
      <div class="legend-item">
        <div class="legend-color profit-medium"></div>
        <span>Profit</span>
      </div>
      <div class="legend-item">
        <div class="legend-color neutral"></div>
        <span>Neutral</span>
      </div>
      <div class="legend-item">
        <div class="legend-color loss-medium"></div>
        <span>Loss</span>
      </div>
      <div class="legend-item">
        <div class="legend-color loss-high"></div>
        <span>High Loss</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="calendar-loading">
      <div class="loading-spinner"></div>
      <p>Loading calendar data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="calendar-error">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="refreshCalendar" class="retry-btn">Retry</button>
    </div>

    <!-- Calendar Grid -->
    <div v-else class="calendar-container">
      <div class="calendar-months">
        <div 
          v-for="month in calendarMonths" 
          :key="month.key"
          class="calendar-month"
        >
          <div class="month-header">{{ month.name }}</div>
          <div class="month-grid">
            <!-- Week day headers -->
            <div class="weekday-headers">
              <div v-for="day in weekDays" :key="day" class="weekday-header">
                {{ day }}
              </div>
            </div>
            
            <!-- Calendar days -->
            <div class="calendar-days">
              <div
                v-for="day in month.days"
                :key="day.date"
                class="calendar-day"
                :class="getDayClasses(day)"
                @click="selectDay(day)"
                @mouseenter="showDayTooltip(day, $event)"
                @mouseleave="hideDayTooltip"
              >
                <span class="day-number">{{ day.dayNumber }}</span>
                <div v-if="day.data" class="day-indicator" :style="getDayStyle(day.data)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Day Details Tooltip -->
    <div 
      v-if="tooltip.visible" 
      class="day-tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div class="tooltip-date">{{ tooltip.data?.date }}</div>
      <div class="tooltip-stats">
        <div class="stat-row">
          <span class="label">P&L:</span>
          <span class="value" :class="getPnLClass(tooltip.data?.value)">
            ${{ formatNumber(tooltip.data?.value) }}
          </span>
        </div>
        <div class="stat-row">
          <span class="label">Trades:</span>
          <span class="value">{{ tooltip.data?.trades_count || 0 }}</span>
        </div>
        <div class="stat-row" v-if="tooltip.data?.win_rate">
          <span class="label">Win Rate:</span>
          <span class="value">{{ (tooltip.data.win_rate * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>

    <!-- Selected Day Details Panel -->
    <div v-if="selectedDay" class="day-details-panel">
      <div class="details-header">
        <h5>{{ formatDate(selectedDay.date) }}</h5>
        <button @click="closeDetails" class="close-btn">×</button>
      </div>
      
      <div class="details-content">
        <div class="details-stats">
          <div class="stat-card">
            <div class="stat-value" :class="getPnLClass(selectedDay.data?.value)">
              ${{ formatNumber(selectedDay.data?.value) }}
            </div>
            <div class="stat-label">Total P&L</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">{{ selectedDay.data?.trades_count || 0 }}</div>
            <div class="stat-label">Trades</div>
          </div>
          
          <div class="stat-card" v-if="selectedDay.data?.win_rate">
            <div class="stat-value">{{ (selectedDay.data.win_rate * 100).toFixed(1) }}%</div>
            <div class="stat-label">Win Rate</div>
          </div>
        </div>
        
        <button @click="viewDayTrades" class="view-trades-btn">
          View Day's Trades in TradeNote
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useTradeNoteStore } from '../stores/tradenote'

// Store
const tradeNoteStore = useTradeNoteStore()

// Reactive data
const isLoading = ref(false)
const error = ref(null)
const selectedPeriod = ref('3m')
const calendarData = ref([])
const selectedDay = ref(null)
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  data: null
})

// Date range for current period
const dateRange = computed(() => {
  const end = new Date()
  const start = new Date()
  
  switch (selectedPeriod.value) {
    case '1m':
      start.setMonth(start.getMonth() - 1)
      break
    case '3m':
      start.setMonth(start.getMonth() - 3)
      break
    case '6m':
      start.setMonth(start.getMonth() - 6)
      break
    case '1y':
      start.setFullYear(start.getFullYear() - 1)
      break
  }
  
  return { start, end }
})

// Week days
const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

// Calendar months structure
const calendarMonths = computed(() => {
  if (!dateRange.value) return []
  
  const months = []
  const current = new Date(dateRange.value.start)
  const end = new Date(dateRange.value.end)
  
  while (current <= end) {
    const monthStart = new Date(current.getFullYear(), current.getMonth(), 1)
    const monthEnd = new Date(current.getFullYear(), current.getMonth() + 1, 0)
    
    const month = {
      key: `${current.getFullYear()}-${current.getMonth()}`,
      name: current.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      days: generateMonthDays(monthStart, monthEnd)
    }
    
    months.push(month)
    current.setMonth(current.getMonth() + 1)
  }
  
  return months
})

// Generate days for a month
function generateMonthDays(monthStart, monthEnd) {
  const days = []
  
  // Add padding days from previous month
  const startPadding = monthStart.getDay()
  for (let i = startPadding - 1; i >= 0; i--) {
    const paddingDate = new Date(monthStart)
    paddingDate.setDate(paddingDate.getDate() - i - 1)
    days.push({
      date: paddingDate.toISOString().split('T')[0],
      dayNumber: paddingDate.getDate(),
      isPadding: true,
      data: null
    })
  }
  
  // Add actual month days
  const current = new Date(monthStart)
  while (current <= monthEnd) {
    const dateString = current.toISOString().split('T')[0]
    const dayData = calendarData.value.find(d => d.date === dateString)
    
    days.push({
      date: dateString,
      dayNumber: current.getDate(),
      isPadding: false,
      data: dayData
    })
    
    current.setDate(current.getDate() + 1)
  }
  
  // Add padding days from next month
  const endPadding = 6 - monthEnd.getDay()
  for (let i = 1; i <= endPadding; i++) {
    const paddingDate = new Date(monthEnd)
    paddingDate.setDate(paddingDate.getDate() + i)
    days.push({
      date: paddingDate.toISOString().split('T')[0],
      dayNumber: paddingDate.getDate(),
      isPadding: true,
      data: null
    })
  }
  
  return days
}

// Get CSS classes for a day
function getDayClasses(day) {
  const classes = []
  
  if (day.isPadding) {
    classes.push('padding-day')
  }
  
  if (day.data) {
    classes.push('has-data')
    
    if (day.data.value > 0) {
      classes.push('profit')
      if (day.data.value > 500) classes.push('high')
      else if (day.data.value > 100) classes.push('medium')
      else classes.push('low')
    } else if (day.data.value < 0) {
      classes.push('loss')
      if (day.data.value < -500) classes.push('high')
      else if (day.data.value < -100) classes.push('medium')
      else classes.push('low')
    } else {
      classes.push('neutral')
    }
  }
  
  if (selectedDay.value && selectedDay.value.date === day.date) {
    classes.push('selected')
  }
  
  return classes
}

// Get inline styles for day indicator
function getDayStyle(data) {
  if (!data || !data.value) return {}
  
  const maxValue = Math.max(...calendarData.value.map(d => Math.abs(d.value)))
  const intensity = Math.min(Math.abs(data.value) / maxValue, 1)
  
  if (data.value > 0) {
    return {
      backgroundColor: `rgba(34, 197, 94, ${0.3 + intensity * 0.7})`
    }
  } else {
    return {
      backgroundColor: `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`
    }
  }
}

// Get P&L class for styling
function getPnLClass(value) {
  if (!value) return 'neutral'
  return value > 0 ? 'profit' : 'loss'
}

// Load calendar data
async function loadCalendarData() {
  if (!dateRange.value) return
  
  isLoading.value = true
  error.value = null
  
  try {
    const response = await tradeNoteStore.getCalendarData(
      dateRange.value.start,
      dateRange.value.end
    )
    
    if (response.success) {
      calendarData.value = response.data || []
    } else {
      error.value = response.message || 'Failed to load calendar data'
    }
  } catch (err) {
    console.error('Error loading calendar data:', err)
    error.value = 'Failed to load calendar data'
  } finally {
    isLoading.value = false
  }
}

// Event handlers
function onPeriodChanged() {
  loadCalendarData()
}

function refreshCalendar() {
  loadCalendarData()
}

function selectDay(day) {
  if (day.isPadding || !day.data) return
  selectedDay.value = day
}

function closeDetails() {
  selectedDay.value = null
}

function showDayTooltip(day, event) {
  if (day.isPadding || !day.data) return
  
  tooltip.value = {
    visible: true,
    x: event.pageX + 10,
    y: event.pageY - 10,
    data: day.data
  }
}

function hideDayTooltip() {
  tooltip.value.visible = false
}

function viewDayTrades() {
  if (!selectedDay.value) return
  
  // Open TradeNote in external browser for the specific date
  const date = selectedDay.value.date
  const url = `${tradeNoteStore.config.base_url}/trades?date=${date}`
  window.electron.openExternal(url)
}

// Utility functions
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function formatDateRange(start, end) {
  const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return `${startStr} - ${endStr}`
}

function formatNumber(value) {
  if (!value) return '0.00'
  return Math.abs(value).toFixed(2)
}

// Watchers
watch(dateRange, () => {
  loadCalendarData()
}, { immediate: false })

// Lifecycle
onMounted(() => {
  loadCalendarData()
})
</script>

<style scoped>
.tradenote-calendar {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 16px;
  color: #e5e5e5;
}

/* Header */
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
}

.header-title h4 {
  margin: 0 0 4px 0;
  color: #fff;
  font-size: 18px;
}

.date-range {
  font-size: 12px;
  color: #888;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.period-select {
  background: #2a2a2a;
  border: 1px solid #444;
  color: #e5e5e5;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.refresh-btn {
  background: #333;
  border: 1px solid #555;
  color: #e5e5e5;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.refresh-btn:hover {
  background: #444;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Legend */
.calendar-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.profit-high { background: rgba(34, 197, 94, 1); }
.profit-medium { background: rgba(34, 197, 94, 0.6); }
.neutral { background: #444; }
.loss-medium { background: rgba(239, 68, 68, 0.6); }
.loss-high { background: rgba(239, 68, 68, 1); }

/* Loading/Error States */
.calendar-loading,
.calendar-error {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #333;
  border-top: 3px solid #0ea5e9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.error-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.retry-btn {
  background: #0ea5e9;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
}

/* Calendar Grid */
.calendar-container {
  overflow-x: auto;
}

.calendar-months {
  display: flex;
  gap: 24px;
  min-width: min-content;
}

.calendar-month {
  flex: 1;
  min-width: 240px;
}

.month-header {
  font-weight: bold;
  margin-bottom: 8px;
  text-align: center;
  color: #fff;
}

.weekday-headers {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 4px;
}

.weekday-header {
  text-align: center;
  font-size: 11px;
  color: #888;
  padding: 4px;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.calendar-day {
  aspect-ratio: 1;
  border: 1px solid #333;
  background: #2a2a2a;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.calendar-day:hover {
  border-color: #555;
  transform: scale(1.05);
}

.calendar-day.padding-day {
  opacity: 0.3;
  cursor: default;
}

.calendar-day.padding-day:hover {
  transform: none;
}

.calendar-day.selected {
  border-color: #0ea5e9;
  background: #1e3a8a;
}

.day-number {
  font-size: 12px;
  font-weight: 500;
  z-index: 1;
}

.day-indicator {
  position: absolute;
  inset: 2px;
  border-radius: 2px;
  pointer-events: none;
}

/* Tooltip */
.day-tooltip {
  position: fixed;
  background: #000;
  border: 1px solid #555;
  border-radius: 6px;
  padding: 8px;
  font-size: 12px;
  z-index: 1000;
  min-width: 150px;
}

.tooltip-date {
  font-weight: bold;
  margin-bottom: 4px;
  color: #fff;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2px;
}

.stat-row .label {
  color: #888;
}

.value.profit {
  color: #22c55e;
}

.value.loss {
  color: #ef4444;
}

.value.neutral {
  color: #888;
}

/* Day Details Panel */
.day-details-panel {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  margin-top: 16px;
  overflow: hidden;
}

.details-header {
  background: #333;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.details-header h5 {
  margin: 0;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #fff;
}

.details-content {
  padding: 16px;
}

.details-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 12px;
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #888;
}

.view-trades-btn {
  background: #0ea5e9;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
}

.view-trades-btn:hover {
  background: #0284c7;
}
</style>