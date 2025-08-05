<template>
  <div class="transistor-plotter">
    <div class="plotter-header">
      <h2>📈 Transistor Plotter</h2>
      <div class="plotter-controls">
        <select v-model="selectedTransistorId" class="transistor-select">
          <option value="">Select a transistor...</option>
          <option v-for="(transistor, index) in transistors" :key="index" :value="index">
            {{ transistor.metadata.name }} ({{ transistor.metadata.type }})
          </option>
        </select>
        <button @click="refreshPlots" class="btn btn-primary">🔄 Refresh Plots</button>
      </div>
    </div>

    <div v-if="!selectedTransistorId" class="no-selection">
      <p>Please select a transistor to view its characteristics plots.</p>
    </div>

    <div v-else class="plotter-content">
      <div class="plot-tabs">
        <button 
          v-for="tab in plotTabs" 
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
        >
          {{ tab.icon }} {{ tab.name }}
        </button>
      </div>

      <div class="plot-container">
        <!-- Channel Characteristics -->
        <div v-if="activeTab === 'channel'" class="plot-section">
          <div class="plot-controls">
            <h3>🔌 Channel Characteristics (I-V Curves)</h3>
            <div class="control-row">
              <label>
                Component:
                <select v-model="channelComponent">
                  <option value="switch">Switch</option>
                  <option value="diode">Diode</option>
                </select>
              </label>
              <label>
                Temperature:
                <select v-model="channelTemperature">
                  <option value="25">25°C</option>
                  <option value="100">100°C</option>
                  <option value="150">150°C</option>
                  <option value="175">175°C</option>
                </select>
              </label>
              <label>
                Gate Voltage:
                <select v-model="channelGateVoltage">
                  <option value="10">10V</option>
                  <option value="12">12V</option>
                  <option value="15">15V</option>
                  <option value="18">18V</option>
                </select>
              </label>
            </div>
          </div>
          <div class="plot-canvas" ref="channelPlot">
            <canvas id="channelChart" width="800" height="400"></canvas>
          </div>
          <div class="plot-info">
            <p><strong>Description:</strong> Shows the relationship between drain-source voltage and drain current for different gate voltages and temperatures.</p>
          </div>
        </div>

        <!-- Switching Losses -->
        <div v-if="activeTab === 'losses'" class="plot-section">
          <div class="plot-controls">
            <h3>⚡ Switching Losses</h3>
            <div class="control-row">
              <label>
                Loss Type:
                <select v-model="lossType">
                  <option value="e_on">Turn-on Energy (E_on)</option>
                  <option value="e_off">Turn-off Energy (E_off)</option>
                  <option value="e_rr">Reverse Recovery (E_rr)</option>
                </select>
              </label>
              <label>
                Plot Type:
                <select v-model="lossPlotType">
                  <option value="i_e">Current vs Energy</option>
                  <option value="v_e">Voltage vs Energy</option>
                  <option value="temp_e">Temperature vs Energy</option>
                </select>
              </label>
            </div>
          </div>
          <div class="plot-canvas" ref="lossesPlot">
            <canvas id="lossesChart" width="800" height="400"></canvas>
          </div>
          <div class="plot-info">
            <p><strong>Description:</strong> Displays switching energy losses as a function of operating current, voltage, or temperature.</p>
          </div>
        </div>

        <!-- Safe Operating Area -->
        <div v-if="activeTab === 'soa'" class="plot-section">
          <div class="plot-controls">
            <h3>🛡️ Safe Operating Area (SOA)</h3>
            <div class="control-row">
              <label>
                Pulse Duration:
                <select v-model="soaPulseDuration">
                  <option value="1us">1μs</option>
                  <option value="10us">10μs</option>
                  <option value="100us">100μs</option>
                  <option value="1ms">1ms</option>
                  <option value="10ms">10ms</option>
                  <option value="100ms">100ms</option>
                  <option value="dc">DC</option>
                </select>
              </label>
              <label>
                Case Temperature:
                <select v-model="soaCaseTemp">
                  <option value="25">25°C</option>
                  <option value="100">100°C</option>
                  <option value="150">150°C</option>
                </select>
              </label>
            </div>
          </div>
          <div class="plot-canvas" ref="soaPlot">
            <canvas id="soaChart" width="800" height="400"></canvas>
          </div>
          <div class="plot-info">
            <p><strong>Description:</strong> Shows the safe operating limits for voltage and current combinations at different pulse durations and temperatures.</p>
          </div>
        </div>

        <!-- Thermal Impedance -->
        <div v-if="activeTab === 'thermal'" class="plot-section">
          <div class="plot-controls">
            <h3>🌡️ Thermal Impedance</h3>
            <div class="control-row">
              <label>
                Time Range:
                <select v-model="thermalTimeRange">
                  <option value="1us-1s">1μs - 1s</option>
                  <option value="1ms-100s">1ms - 100s</option>
                  <option value="1s-1h">1s - 1h</option>
                </select>
              </label>
            </div>
          </div>
          <div class="plot-canvas" ref="thermalPlot">
            <canvas id="thermalChart" width="800" height="400"></canvas>
          </div>
          <div class="plot-info">
            <p><strong>Description:</strong> Shows the thermal impedance from junction to case as a function of time/pulse duration.</p>
          </div>
        </div>

        <!-- Gate Charge -->
        <div v-if="activeTab === 'gate'" class="plot-section">
          <div class="plot-controls">
            <h3>🔋 Gate Charge</h3>
            <div class="control-row">
              <label>
                Drain Voltage:
                <select v-model="gateVoltage">
                  <option value="400">400V</option>
                  <option value="600">600V</option>
                  <option value="800">800V</option>
                  <option value="1000">1000V</option>
                </select>
              </label>
              <label>
                Drain Current:
                <select v-model="gateCurrent">
                  <option value="25">25A</option>
                  <option value="50">50A</option>
                  <option value="75">75A</option>
                  <option value="100">100A</option>
                </select>
              </label>
            </div>
          </div>
          <div class="plot-canvas" ref="gatePlot">
            <canvas id="gateChart" width="800" height="400"></canvas>
          </div>
          <div class="plot-info">
            <p><strong>Description:</strong> Shows gate voltage vs gate charge, important for calculating switching times and gate drive requirements.</p>
          </div>
        </div>
      </div>

      <!-- Plot Data Export -->
      <div class="plot-export">
        <h3>📊 Export Plot Data</h3>
        <div class="export-buttons">
          <button @click="exportPlotData('csv')" class="btn btn-secondary">
            📄 Export as CSV
          </button>
          <button @click="exportPlotData('json')" class="btn btn-secondary">
            📋 Export as JSON
          </button>
          <button @click="exportPlotImage()" class="btn btn-secondary">
            🖼️ Save as Image
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  transistors: Array,
  selectedTransistor: Object
})

// Reactive data
const selectedTransistorId = ref('')
const activeTab = ref('channel')

// Plot parameters
const channelComponent = ref('switch')
const channelTemperature = ref('25')
const channelGateVoltage = ref('15')

const lossType = ref('e_on')
const lossPlotType = ref('i_e')

const soaPulseDuration = ref('100us')
const soaCaseTemp = ref('25')

const thermalTimeRange = ref('1us-1s')

const gateVoltage = ref('600')
const gateCurrent = ref('50')

// Plot tabs configuration
const plotTabs = [
  { id: 'channel', name: 'I-V Curves', icon: '🔌' },
  { id: 'losses', name: 'Switching Losses', icon: '⚡' },
  { id: 'soa', name: 'Safe Operating Area', icon: '🛡️' },
  { id: 'thermal', name: 'Thermal Impedance', icon: '🌡️' },
  { id: 'gate', name: 'Gate Charge', icon: '🔋' }
]

// Chart instances
let channelChart = null
let lossesChart = null
let soaChart = null
let thermalChart = null
let gateChart = null

// Computed properties
const currentTransistor = computed(() => {
  if (!selectedTransistorId.value) return null
  return props.transistors[parseInt(selectedTransistorId.value)]
})

// Watchers
watch(currentTransistor, () => {
  if (currentTransistor.value) {
    refreshPlots()
  }
})

watch([channelComponent, channelTemperature, channelGateVoltage], () => {
  if (activeTab.value === 'channel') updateChannelPlot()
})

watch([lossType, lossPlotType], () => {
  if (activeTab.value === 'losses') updateLossesPlot()
})

watch([soaPulseDuration, soaCaseTemp], () => {
  if (activeTab.value === 'soa') updateSoaPlot()
})

watch(thermalTimeRange, () => {
  if (activeTab.value === 'thermal') updateThermalPlot()
})

watch([gateVoltage, gateCurrent], () => {
  if (activeTab.value === 'gate') updateGatePlot()
})

watch(activeTab, () => {
  nextTick(() => {
    refreshPlots()
  })
})

// Methods
function refreshPlots() {
  if (!currentTransistor.value) return
  
  switch (activeTab.value) {
    case 'channel':
      updateChannelPlot()
      break
    case 'losses':
      updateLossesPlot()
      break
    case 'soa':
      updateSoaPlot()
      break
    case 'thermal':
      updateThermalPlot()
      break
    case 'gate':
      updateGatePlot()
      break
  }
}

function updateChannelPlot() {
  const canvas = document.getElementById('channelChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (channelChart) {
    channelChart.destroy()
  }
  
  // Generate sample I-V curve data based on transistor parameters
  const transistor = currentTransistor.value
  const vMax = transistor.electrical.v_abs_max
  const iMax = transistor.electrical.i_abs_max
  
  const voltages = []
  const currents = []
  
  // Generate characteristic curve data
  for (let v = 0; v <= Math.min(vMax * 0.8, 10); v += 0.1) {
    voltages.push(v)
    // Simplified MOSFET/IGBT characteristic equation
    const vth = 3 // Threshold voltage
    const gateV = parseFloat(channelGateVoltage.value)
    const tempFactor = 1 - (parseFloat(channelTemperature.value) - 25) * 0.002
    
    if (gateV > vth) {
      const gm = iMax / (gateV - vth) // Transconductance approximation
      const current = Math.min(gm * (gateV - vth) * tempFactor, iMax)
      currents.push(current)
    } else {
      currents.push(0)
    }
  }
  
  // Create Chart.js chart
  channelChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: voltages,
      datasets: [{
        label: `${transistor.metadata.name} @ ${channelTemperature.value}°C, Vgs=${channelGateVoltage.value}V`,
        data: currents,
        borderColor: '#007bff',
        backgroundColor: 'rgba(0, 123, 255, 0.1)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `${channelComponent.value.toUpperCase()} I-V Characteristics`
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Voltage (V)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Current (A)'
          }
        }
      }
    }
  })
}

function updateLossesPlot() {
  const canvas = document.getElementById('lossesChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (lossesChart) {
    lossesChart.destroy()
  }
  
  const transistor = currentTransistor.value
  
  // Generate switching losses data
  const data = []
  const labels = []
  
  if (lossPlotType.value === 'i_e') {
    // Current vs Energy
    for (let i = 10; i <= transistor.electrical.i_abs_max; i += 10) {
      labels.push(i)
      // Simplified switching energy calculation: E = k * I^1.3 * V
      const energy = 0.1 * Math.pow(i, 1.3) * (transistor.electrical.v_abs_max / 1000)
      data.push(energy)
    }
  }
  
  lossesChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: `${lossType.value.toUpperCase()} Energy`,
        data: data,
        borderColor: '#dc3545',
        backgroundColor: 'rgba(220, 53, 69, 0.1)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Switching Losses - ${lossType.value.toUpperCase()}`
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: lossPlotType.value === 'i_e' ? 'Current (A)' : 'Voltage (V)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Energy (mJ)'
          }
        }
      }
    }
  })
}

function updateSoaPlot() {
  const canvas = document.getElementById('soaChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (soaChart) {
    soaChart.destroy()
  }
  
  const transistor = currentTransistor.value
  
  // Generate SOA boundary data
  const voltages = []
  const currents = []
  
  // Current limit
  for (let v = 0; v <= transistor.electrical.v_abs_max * 0.1; v += 1) {
    voltages.push(v)
    currents.push(transistor.electrical.i_abs_max)
  }
  
  // Power limit (simplified)
  const maxPower = transistor.electrical.i_abs_max * transistor.electrical.v_abs_max * 0.1
  for (let v = transistor.electrical.v_abs_max * 0.1; v <= transistor.electrical.v_abs_max; v += 10) {
    voltages.push(v)
    currents.push(Math.min(maxPower / v, transistor.electrical.i_abs_max))
  }
  
  soaChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: voltages,
      datasets: [{
        label: `SOA Boundary (${soaPulseDuration.value}, ${soaCaseTemp.value}°C)`,
        data: currents,
        borderColor: '#28a745',
        backgroundColor: 'rgba(40, 167, 69, 0.1)',
        fill: true,
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Safe Operating Area'
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Voltage (V)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Current (A)'
          }
        }
      }
    }
  })
}

function updateThermalPlot() {
  const canvas = document.getElementById('thermalChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (thermalChart) {
    thermalChart.destroy()
  }
  
  const transistor = currentTransistor.value
  
  // Generate thermal impedance data
  const times = []
  const impedances = []
  
  const rthSteady = transistor.thermal.r_th_cs
  
  // Simplified thermal impedance curve: Zth(t) = Rth * (1 - exp(-t/tau))
  const tau = 0.1 // Time constant in seconds
  
  for (let t = 1e-6; t <= 1; t *= 1.5) {
    times.push(t * 1000) // Convert to ms for display
    const zth = rthSteady * (1 - Math.exp(-t / tau))
    impedances.push(zth)
  }
  
  thermalChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: times,
      datasets: [{
        label: 'Thermal Impedance Zth(j-c)',
        data: impedances,
        borderColor: '#fd7e14',
        backgroundColor: 'rgba(253, 126, 20, 0.1)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Thermal Impedance Junction to Case'
        }
      },
      scales: {
        x: {
          type: 'logarithmic',
          title: {
            display: true,
            text: 'Time (ms)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Thermal Impedance (K/W)'
          }
        }
      }
    }
  })
}

function updateGatePlot() {
  const canvas = document.getElementById('gateChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (gateChart) {
    gateChart.destroy()
  }
  
  // Generate gate charge data
  const charges = []
  const voltages = []
  
  // Simplified gate charge curve
  for (let q = 0; q <= 100; q += 2) {
    charges.push(q)
    
    if (q < 20) {
      // Initial charging phase
      voltages.push(q * 0.25)
    } else if (q < 60) {
      // Miller plateau
      voltages.push(5 + (q - 20) * 0.05)
    } else {
      // Final charging phase
      voltages.push(7 + (q - 60) * 0.2)
    }
  }
  
  gateChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: charges,
      datasets: [{
        label: `Gate Charge @ Vds=${gateVoltage.value}V, Id=${gateCurrent.value}A`,
        data: voltages,
        borderColor: '#6f42c1',
        backgroundColor: 'rgba(111, 66, 193, 0.1)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Gate Charge Characteristics'
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Gate Charge (nC)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Gate Voltage (V)'
          }
        }
      }
    }
  })
}

function exportPlotData(format) {
  if (!currentTransistor.value) return
  
  const plotData = {
    transistor: currentTransistor.value.metadata.name,
    plotType: activeTab.value,
    parameters: getPlotParameters(),
    data: getCurrentPlotData()
  }
  
  if (format === 'json') {
    const blob = new Blob([JSON.stringify(plotData, null, 2)], { type: 'application/json' })
    downloadFile(blob, `${currentTransistor.value.metadata.name}_${activeTab.value}.json`)
  } else if (format === 'csv') {
    const csv = convertToCSV(plotData.data)
    const blob = new Blob([csv], { type: 'text/csv' })
    downloadFile(blob, `${currentTransistor.value.metadata.name}_${activeTab.value}.csv`)
  }
}

function exportPlotImage() {
  const canvas = document.getElementById(`${activeTab.value}Chart`)
  if (!canvas) return
  
  canvas.toBlob((blob) => {
    downloadFile(blob, `${currentTransistor.value.metadata.name}_${activeTab.value}.png`)
  })
}

function getPlotParameters() {
  switch (activeTab.value) {
    case 'channel':
      return {
        component: channelComponent.value,
        temperature: channelTemperature.value,
        gateVoltage: channelGateVoltage.value
      }
    case 'losses':
      return {
        lossType: lossType.value,
        plotType: lossPlotType.value
      }
    case 'soa':
      return {
        pulseDuration: soaPulseDuration.value,
        caseTemp: soaCaseTemp.value
      }
    case 'thermal':
      return {
        timeRange: thermalTimeRange.value
      }
    case 'gate':
      return {
        voltage: gateVoltage.value,
        current: gateCurrent.value
      }
    default:
      return {}
  }
}

function getCurrentPlotData() {
  // This would extract data from the current chart
  // For now, return placeholder data
  return {
    x: [1, 2, 3, 4, 5],
    y: [1, 4, 9, 16, 25]
  }
}

function convertToCSV(data) {
  const headers = Object.keys(data)
  const rows = []
  
  const maxLength = Math.max(...headers.map(h => data[h].length))
  
  for (let i = 0; i < maxLength; i++) {
    const row = headers.map(h => data[h][i] || '').join(',')
    rows.push(row)
  }
  
  return [headers.join(','), ...rows].join('\n')
}

function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
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
.transistor-plotter {
  max-width: 1400px;
  margin: 0 auto;
}

.plotter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.plotter-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.transistor-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 250px;
}

.no-selection {
  text-align: center;
  padding: 4rem;
  color: #666;
  font-size: 1.2rem;
}

.plot-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  overflow-x: auto;
}

.tab-button {
  padding: 0.75rem 1.5rem;
  border: none;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-button:hover {
  background: #e9ecef;
}

.tab-button.active {
  background: white;
  border-bottom: 3px solid #007bff;
  color: #007bff;
}

.plot-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.plot-section {
  padding: 2rem;
}

.plot-controls {
  margin-bottom: 2rem;
}

.plot-controls h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.control-row {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.control-row label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-weight: 500;
}

.control-row select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.plot-canvas {
  margin: 2rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.plot-canvas canvas {
  max-width: 100%;
  height: auto;
}

.plot-info {
  padding: 1rem;
  background: #e3f2fd;
  border-radius: 4px;
  margin-top: 1rem;
}

.plot-info p {
  margin: 0;
  color: #1565c0;
  font-style: italic;
}

.plot-export {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-top: 2rem;
}

.plot-export h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.export-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
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

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

@media (max-width: 768px) {
  .plotter-header {
    flex-direction: column;
    gap: 1rem;
  }

  .control-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .export-buttons {
    flex-direction: column;
  }
}
</style>
