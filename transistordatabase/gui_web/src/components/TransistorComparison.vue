<template>
  <div class="transistor-comparison">
    <div class="comparison-header">
      <h2>🔍 Transistor Comparison</h2>
      <div class="header-actions">
        <button @click="clearSelection" class="btn btn-secondary">
          🗑️ Clear Selection
        </button>
        <button @click="exportComparison" :disabled="selectedTransistors.length < 2" class="btn btn-primary">
          💾 Export Comparison
        </button>
      </div>
    </div>

    <div class="selection-section">
      <h3>Select Transistors to Compare ({{ selectedTransistors.length }}/{{ maxComparisons }})</h3>
      <div class="transistor-selector">
        <div class="selector-filters">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="🔍 Search transistors..." 
            class="search-input"
          />
          <select v-model="typeFilter" class="filter-select">
            <option value="">All Types</option>
            <option v-for="type in availableTypes" :key="type" :value="type">{{ type }}</option>
          </select>
          <select v-model="manufacturerFilter" class="filter-select">
            <option value="">All Manufacturers</option>
            <option v-for="mfg in availableManufacturers" :key="mfg" :value="mfg">{{ mfg }}</option>
          </select>
        </div>

        <div class="transistor-grid">
          <div 
            v-for="(transistor, index) in filteredTransistors" 
            :key="index"
            @click="toggleTransistorSelection(transistor)"
            :class="['transistor-card', { 
              selected: isSelected(transistor),
              disabled: !isSelected(transistor) && selectedTransistors.length >= maxComparisons
            }]"
          >
            <div class="card-header">
              <h4>{{ transistor.metadata.name }}</h4>
              <div class="selection-indicator">
                {{ isSelected(transistor) ? '✅' : '⭕' }}
              </div>
            </div>
            <div class="card-content">
              <p><strong>Type:</strong> {{ transistor.metadata.type }}</p>
              <p><strong>Manufacturer:</strong> {{ transistor.metadata.manufacturer }}</p>
              <p><strong>Max V:</strong> {{ transistor.electrical.v_abs_max }}V</p>
              <p><strong>Max I:</strong> {{ transistor.electrical.i_abs_max }}A</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedTransistors.length >= 2" class="comparison-results">
      <h3>📊 Comparison Results</h3>
      
      <!-- Summary Statistics -->
      <div class="comparison-summary">
        <div class="summary-card">
          <h4>⚡ Electrical Ratings</h4>
          <div class="stat-row">
            <span>Voltage Range:</span>
            <span>{{ Math.min(...selectedTransistors.map(t => t.electrical.v_abs_max)) }}V - {{ Math.max(...selectedTransistors.map(t => t.electrical.v_abs_max)) }}V</span>
          </div>
          <div class="stat-row">
            <span>Current Range:</span>
            <span>{{ Math.min(...selectedTransistors.map(t => t.electrical.i_abs_max)) }}A - {{ Math.max(...selectedTransistors.map(t => t.electrical.i_abs_max)) }}A</span>
          </div>
          <div class="stat-row">
            <span>Temperature Range:</span>
            <span>{{ Math.min(...selectedTransistors.map(t => t.electrical.t_j_max)) }}°C - {{ Math.max(...selectedTransistors.map(t => t.electrical.t_j_max)) }}°C</span>
          </div>
        </div>

        <div class="summary-card">
          <h4>🌡️ Thermal Properties</h4>
          <div class="stat-row">
            <span>Thermal Resistance Range:</span>
            <span>{{ Math.min(...selectedTransistors.map(t => t.thermal.r_th_cs)).toFixed(2) }} - {{ Math.max(...selectedTransistors.map(t => t.thermal.r_th_cs)).toFixed(2) }} K/W</span>
          </div>
          <div class="stat-row">
            <span>Best Thermal Performance:</span>
            <span>{{ getBestThermalTransistor().metadata.name }}</span>
          </div>
        </div>

        <div class="summary-card">
          <h4>🏆 Recommendations</h4>
          <div class="stat-row">
            <span>Highest Voltage:</span>
            <span>{{ getHighestVoltageTransistor().metadata.name }} ({{ getHighestVoltageTransistor().electrical.v_abs_max }}V)</span>
          </div>
          <div class="stat-row">
            <span>Highest Current:</span>
            <span>{{ getHighestCurrentTransistor().metadata.name }} ({{ getHighestCurrentTransistor().electrical.i_abs_max }}A)</span>
          </div>
          <div class="stat-row">
            <span>Best Power Density:</span>
            <span>{{ getBestPowerDensityTransistor().metadata.name }}</span>
          </div>
        </div>
      </div>

      <!-- Detailed Comparison Table -->
      <div class="comparison-table">
        <h4>📋 Detailed Comparison</h4>
        <table>
          <thead>
            <tr>
              <th>Property</th>
              <th v-for="transistor in selectedTransistors" :key="transistor.metadata.name">
                {{ transistor.metadata.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Metadata -->
            <tr class="section-header">
              <td colspan="100%"><strong>📋 Metadata</strong></td>
            </tr>
            <tr>
              <td>Type</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name">
                <span :class="['type-badge', transistor.metadata.type.toLowerCase()]">
                  {{ transistor.metadata.type }}
                </span>
              </td>
            </tr>
            <tr>
              <td>Manufacturer</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name">
                {{ transistor.metadata.manufacturer }}
              </td>
            </tr>
            <tr>
              <td>Housing Type</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name">
                {{ transistor.metadata.housing_type }}
              </td>
            </tr>

            <!-- Electrical -->
            <tr class="section-header">
              <td colspan="100%"><strong>⚡ Electrical Ratings</strong></td>
            </tr>
            <tr>
              <td>Max Voltage (V)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name"
                  :class="{ 'best-value': transistor.electrical.v_abs_max === Math.max(...selectedTransistors.map(t => t.electrical.v_abs_max)) }">
                {{ transistor.electrical.v_abs_max }}V
              </td>
            </tr>
            <tr>
              <td>Max Current (A)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name"
                  :class="{ 'best-value': transistor.electrical.i_abs_max === Math.max(...selectedTransistors.map(t => t.electrical.i_abs_max)) }">
                {{ transistor.electrical.i_abs_max }}A
              </td>
            </tr>
            <tr>
              <td>Continuous Current (A)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name"
                  :class="{ 'best-value': transistor.electrical.i_cont === Math.max(...selectedTransistors.map(t => t.electrical.i_cont)) }">
                {{ transistor.electrical.i_cont }}A
              </td>
            </tr>
            <tr>
              <td>Max Junction Temp (°C)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name"
                  :class="{ 'best-value': transistor.electrical.t_j_max === Math.max(...selectedTransistors.map(t => t.electrical.t_j_max)) }">
                {{ transistor.electrical.t_j_max }}°C
              </td>
            </tr>
            <tr>
              <td>Power Rating (W)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name"
                  :class="{ 'best-value': calculatePowerRating(transistor) === Math.max(...selectedTransistors.map(t => calculatePowerRating(t))) }">
                {{ calculatePowerRating(transistor).toFixed(0) }}W
              </td>
            </tr>

            <!-- Thermal -->
            <tr class="section-header">
              <td colspan="100%"><strong>🌡️ Thermal Properties</strong></td>
            </tr>
            <tr>
              <td>Thermal Resistance (K/W)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name"
                  :class="{ 'best-value': transistor.thermal.r_th_cs === Math.min(...selectedTransistors.map(t => t.thermal.r_th_cs)) }">
                {{ transistor.thermal.r_th_cs.toFixed(3) }}
              </td>
            </tr>
            <tr>
              <td>Housing Area (cm²)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name">
                {{ transistor.thermal.housing_area }}
              </td>
            </tr>
            <tr>
              <td>Cooling Area (cm²)</td>
              <td v-for="transistor in selectedTransistors" :key="transistor.metadata.name">
                {{ transistor.thermal.cooling_area }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Visual Comparison Charts -->
      <div class="comparison-charts">
        <h4>📊 Visual Comparison</h4>
        <div class="charts-grid">
          <div class="chart-container">
            <canvas id="voltageCurrentChart" width="400" height="300"></canvas>
            <p>Voltage vs Current Rating</p>
          </div>
          <div class="chart-container">
            <canvas id="powerThermalChart" width="400" height="300"></canvas>
            <p>Power Rating vs Thermal Resistance</p>
          </div>
          <div class="chart-container">
            <canvas id="radarChart" width="400" height="300"></canvas>
            <p>Performance Radar</p>
          </div>
        </div>
      </div>

      <!-- Similar Transistors -->
      <div class="similar-suggestions">
        <h4>💡 Similar Transistors</h4>
        <button @click="findSimilarTransistors" class="btn btn-secondary">
          🔍 Find Similar Transistors
        </button>
        <div v-if="similarTransistors.length > 0" class="similar-list">
          <div v-for="similar in similarTransistors" :key="similar.metadata.name" class="similar-card">
            <h5>{{ similar.metadata.name }}</h5>
            <p>{{ similar.metadata.manufacturer }} - {{ similar.metadata.type }}</p>
            <p>{{ similar.electrical.v_abs_max }}V / {{ similar.electrical.i_abs_max }}A</p>
            <p class="similarity-score">Similarity: {{ similar.similarity }}%</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="selectedTransistors.length === 1" class="single-selection">
      <p>Select at least one more transistor to start comparison.</p>
    </div>

    <div v-else class="no-selection">
      <p>Select at least 2 transistors to compare their specifications.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { transistorApi } from '../services/api.js'

const props = defineProps({
  transistors: Array
})

// Reactive data
const selectedTransistors = ref([])
const searchQuery = ref('')
const typeFilter = ref('')
const manufacturerFilter = ref('')
const similarTransistors = ref([])
const maxComparisons = 5

// Chart instances
let voltageCurrentChart = null
let powerThermalChart = null
let radarChart = null

// Computed properties
const availableTypes = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.type))].sort()
})

const availableManufacturers = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.manufacturer))].sort()
})

const filteredTransistors = computed(() => {
  return props.transistors.filter(transistor => {
    const matchesSearch = transistor.metadata.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         transistor.metadata.manufacturer.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesType = !typeFilter.value || transistor.metadata.type === typeFilter.value
    const matchesManufacturer = !manufacturerFilter.value || transistor.metadata.manufacturer === manufacturerFilter.value
    
    return matchesSearch && matchesType && matchesManufacturer
  })
})

// Watchers
watch(selectedTransistors, () => {
  if (selectedTransistors.value.length >= 2) {
    nextTick(() => {
      updateComparisonCharts()
    })
  }
}, { deep: true })

// Methods
function toggleTransistorSelection(transistor) {
  const index = selectedTransistors.value.findIndex(t => t.metadata.name === transistor.metadata.name)
  
  if (index >= 0) {
    // Remove if already selected
    selectedTransistors.value.splice(index, 1)
  } else if (selectedTransistors.value.length < maxComparisons) {
    // Add if not at max capacity
    selectedTransistors.value.push(transistor)
  }
}

function isSelected(transistor) {
  return selectedTransistors.value.some(t => t.metadata.name === transistor.metadata.name)
}

function clearSelection() {
  selectedTransistors.value = []
  similarTransistors.value = []
}

function getBestThermalTransistor() {
  return selectedTransistors.value.reduce((best, current) => 
    current.thermal.r_th_cs < best.thermal.r_th_cs ? current : best
  )
}

function getHighestVoltageTransistor() {
  return selectedTransistors.value.reduce((highest, current) => 
    current.electrical.v_abs_max > highest.electrical.v_abs_max ? current : highest
  )
}

function getHighestCurrentTransistor() {
  return selectedTransistors.value.reduce((highest, current) => 
    current.electrical.i_abs_max > highest.electrical.i_abs_max ? current : highest
  )
}

function getBestPowerDensityTransistor() {
  return selectedTransistors.value.reduce((best, current) => {
    const currentDensity = calculatePowerRating(current) / current.thermal.housing_area
    const bestDensity = calculatePowerRating(best) / best.thermal.housing_area
    return currentDensity > bestDensity ? current : best
  })
}

function calculatePowerRating(transistor) {
  // Simplified power rating calculation
  return transistor.electrical.v_abs_max * transistor.electrical.i_abs_max * 0.1
}

async function findSimilarTransistors() {
  if (selectedTransistors.value.length === 0) return
  
  try {
    const targetTransistor = selectedTransistors.value[0]
    const transistorIds = selectedTransistors.value.map(t => 
      t.metadata.name.replace(/[^a-zA-Z0-9]/g, '_')
    )
    
    const result = await transistorApi.compare(transistorIds)
    
    // For now, simulate finding similar transistors
    const unselected = props.transistors.filter(t => !isSelected(t))
    const similar = unselected
      .map(t => ({
        ...t,
        similarity: calculateSimilarity(targetTransistor, t)
      }))
      .filter(t => t.similarity > 70)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 5)
    
    similarTransistors.value = similar
  } catch (error) {
    console.error('Error finding similar transistors:', error)
  }
}

function calculateSimilarity(transistor1, transistor2) {
  // Simple similarity calculation based on specs
  const voltageScore = 100 - Math.abs(transistor1.electrical.v_abs_max - transistor2.electrical.v_abs_max) / Math.max(transistor1.electrical.v_abs_max, transistor2.electrical.v_abs_max) * 100
  const currentScore = 100 - Math.abs(transistor1.electrical.i_abs_max - transistor2.electrical.i_abs_max) / Math.max(transistor1.electrical.i_abs_max, transistor2.electrical.i_abs_max) * 100
  const typeScore = transistor1.metadata.type === transistor2.metadata.type ? 100 : 0
  
  return Math.round((voltageScore + currentScore + typeScore) / 3)
}

function updateComparisonCharts() {
  updateVoltageCurrentChart()
  updatePowerThermalChart()
  updateRadarChart()
}

function updateVoltageCurrentChart() {
  const canvas = document.getElementById('voltageCurrentChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (voltageCurrentChart) {
    voltageCurrentChart.destroy()
  }
  
  const datasets = selectedTransistors.value.map((transistor, index) => ({
    label: transistor.metadata.name,
    data: [{
      x: transistor.electrical.v_abs_max,
      y: transistor.electrical.i_abs_max
    }],
    backgroundColor: getChartColor(index),
    borderColor: getChartColor(index),
    pointRadius: 8
  }))
  
  voltageCurrentChart = new Chart(ctx, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Voltage vs Current Rating'
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Max Voltage (V)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Max Current (A)'
          }
        }
      }
    }
  })
}

function updatePowerThermalChart() {
  const canvas = document.getElementById('powerThermalChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (powerThermalChart) {
    powerThermalChart.destroy()
  }
  
  const datasets = selectedTransistors.value.map((transistor, index) => ({
    label: transistor.metadata.name,
    data: [{
      x: calculatePowerRating(transistor),
      y: transistor.thermal.r_th_cs
    }],
    backgroundColor: getChartColor(index),
    borderColor: getChartColor(index),
    pointRadius: 8
  }))
  
  powerThermalChart = new Chart(ctx, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Power Rating vs Thermal Resistance'
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Power Rating (W)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Thermal Resistance (K/W)'
          }
        }
      }
    }
  })
}

function updateRadarChart() {
  const canvas = document.getElementById('radarChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (radarChart) {
    radarChart.destroy()
  }
  
  const maxVoltage = Math.max(...selectedTransistors.value.map(t => t.electrical.v_abs_max))
  const maxCurrent = Math.max(...selectedTransistors.value.map(t => t.electrical.i_abs_max))
  const maxTemp = Math.max(...selectedTransistors.value.map(t => t.electrical.t_j_max))
  const minThermal = Math.min(...selectedTransistors.value.map(t => t.thermal.r_th_cs))
  
  const datasets = selectedTransistors.value.map((transistor, index) => ({
    label: transistor.metadata.name,
    data: [
      (transistor.electrical.v_abs_max / maxVoltage) * 100,
      (transistor.electrical.i_abs_max / maxCurrent) * 100,
      (transistor.electrical.t_j_max / maxTemp) * 100,
      (minThermal / transistor.thermal.r_th_cs) * 100, // Inverted for thermal resistance
      (calculatePowerRating(transistor) / Math.max(...selectedTransistors.value.map(t => calculatePowerRating(t)))) * 100
    ],
    backgroundColor: getChartColor(index, 0.2),
    borderColor: getChartColor(index),
    pointBackgroundColor: getChartColor(index),
    pointBorderColor: '#fff',
    pointHoverBackgroundColor: '#fff',
    pointHoverBorderColor: getChartColor(index)
  }))
  
  radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Voltage', 'Current', 'Temperature', 'Thermal Performance', 'Power Rating'],
      datasets
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Performance Comparison'
        }
      },
      scales: {
        r: {
          beginAtZero: true,
          max: 100
        }
      }
    }
  })
}

function getChartColor(index, alpha = 1) {
  const colors = [
    `rgba(255, 99, 132, ${alpha})`,
    `rgba(54, 162, 235, ${alpha})`,
    `rgba(255, 205, 86, ${alpha})`,
    `rgba(75, 192, 192, ${alpha})`,
    `rgba(153, 102, 255, ${alpha})`
  ]
  return colors[index % colors.length]
}

async function exportComparison() {
  try {
    const comparisonData = {
      selectedTransistors: selectedTransistors.value,
      summary: {
        voltageRange: `${Math.min(...selectedTransistors.value.map(t => t.electrical.v_abs_max))}V - ${Math.max(...selectedTransistors.value.map(t => t.electrical.v_abs_max))}V`,
        currentRange: `${Math.min(...selectedTransistors.value.map(t => t.electrical.i_abs_max))}A - ${Math.max(...selectedTransistors.value.map(t => t.electrical.i_abs_max))}A`,
        bestThermal: getBestThermalTransistor().metadata.name,
        highestVoltage: getHighestVoltageTransistor().metadata.name,
        highestCurrent: getHighestCurrentTransistor().metadata.name
      },
      timestamp: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(comparisonData, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `transistor_comparison_${new Date().toISOString().split('T')[0]}.json`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('❌ Export failed: ' + error.message)
  }
}

// Load Chart.js if not already loaded
onMounted(() => {
  if (typeof Chart === 'undefined') {
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js'
    document.head.appendChild(script)
  }
})
</script>

<style scoped>
.transistor-comparison {
  max-width: 1400px;
  margin: 0 auto;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.selection-section {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.selector-filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

.search-input, .filter-select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.transistor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.transistor-card {
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.transistor-card:hover {
  border-color: #007bff;
  transform: translateY(-2px);
}

.transistor-card.selected {
  border-color: #28a745;
  background: #f8fff9;
}

.transistor-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.card-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #2c3e50;
}

.selection-indicator {
  font-size: 1.2rem;
}

.card-content p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  color: #666;
}

.comparison-results {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.comparison-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.summary-card h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #eee;
}

.stat-row:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.comparison-table {
  margin: 2rem 0;
}

.comparison-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.comparison-table th,
.comparison-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.comparison-table th {
  background: #f8f9fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.section-header td {
  background: #e9ecef;
  font-weight: 600;
  color: #495057;
}

.best-value {
  background: #d4edda;
  font-weight: 600;
  color: #155724;
}

.type-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.type-badge.igbt {
  background: #e3f2fd;
  color: #1976d2;
}

.type-badge.mosfet {
  background: #f3e5f5;
  color: #7b1fa2;
}

.type-badge.diode {
  background: #e8f5e8;
  color: #388e3c;
}

.comparison-charts {
  margin: 2rem 0;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin-top: 1rem;
}

.chart-container {
  text-align: center;
}

.chart-container canvas {
  max-width: 100%;
  height: auto;
}

.chart-container p {
  margin-top: 0.5rem;
  font-weight: 500;
  color: #666;
}

.similar-suggestions {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.similar-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.similar-card {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #ffc107;
}

.similar-card h5 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.similar-card p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}

.similarity-score {
  font-weight: 600;
  color: #ffc107 !important;
}

.no-selection, .single-selection {
  text-align: center;
  padding: 4rem;
  color: #666;
  font-size: 1.2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  text-decoration: none;
  display: inline-block;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

@media (max-width: 768px) {
  .comparison-header {
    flex-direction: column;
    gap: 1rem;
  }

  .selector-filters {
    grid-template-columns: 1fr;
  }

  .transistor-grid {
    grid-template-columns: 1fr;
  }

  .comparison-summary {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
