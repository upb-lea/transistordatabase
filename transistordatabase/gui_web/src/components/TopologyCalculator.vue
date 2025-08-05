<template>
  <div class="topology-calculator">
    <div class="calc-header">
      <h2>🧮 Topology Calculator</h2>
      <div class="header-actions">
        <button @click="resetCalculations" class="btn btn-secondary">
          🔄 Reset
        </button>
        <button @click="saveResults" class="btn btn-info">
          💾 Save Results
        </button>
      </div>
    </div>

    <div class="calc-content">
      <!-- Topology Selection Panel -->
      <div class="topology-panel">
        <h3>⚙️ Power Topology</h3>
        
        <div class="topology-selection">
          <div class="topology-grid">
            <div 
              v-for="topology in topologies" 
              :key="topology.id"
              @click="selectedTopology = topology.id"
              :class="['topology-card', { active: selectedTopology === topology.id }]"
            >
              <div class="topology-icon">{{ topology.icon }}</div>
              <div class="topology-name">{{ topology.name }}</div>
              <div class="topology-desc">{{ topology.description }}</div>
            </div>
          </div>
        </div>

        <div v-if="selectedTopology" class="topology-info">
          <h4>{{ getCurrentTopology().name }} Configuration</h4>
          <div class="topology-diagram">
            <div class="circuit-svg" v-html="getCurrentTopology().svg"></div>
          </div>
        </div>
      </div>

      <!-- Input Parameters Panel -->
      <div class="parameters-panel">
        <h3>📊 Input Parameters</h3>
        
        <div class="parameter-sections">
          <!-- Power Specifications -->
          <div class="param-section">
            <h4>⚡ Power Specifications</h4>
            <div class="param-grid">
              <div class="param-item">
                <label>Input Voltage (V_in):</label>
                <input 
                  type="number" 
                  v-model.number="parameters.v_in" 
                  placeholder="400"
                  min="0"
                  step="1"
                />
                <span class="unit">V</span>
              </div>
              
              <div class="param-item">
                <label>Output Voltage (V_out):</label>
                <input 
                  type="number" 
                  v-model.number="parameters.v_out" 
                  placeholder="48"
                  min="0"
                  step="0.1"
                />
                <span class="unit">V</span>
              </div>
              
              <div class="param-item">
                <label>Output Power (P_out):</label>
                <input 
                  type="number" 
                  v-model.number="parameters.p_out" 
                  placeholder="1000"
                  min="0"
                  step="10"
                />
                <span class="unit">W</span>
              </div>
              
              <div class="param-item">
                <label>Switching Frequency (f_sw):</label>
                <input 
                  type="number" 
                  v-model.number="parameters.f_sw" 
                  placeholder="100"
                  min="1"
                  step="1"
                />
                <span class="unit">kHz</span>
              </div>
            </div>
          </div>

          <!-- Operating Conditions -->
          <div class="param-section">
            <h4>🌡️ Operating Conditions</h4>
            <div class="param-grid">
              <div class="param-item">
                <label>Ambient Temperature:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.t_amb" 
                  placeholder="25"
                  step="1"
                />
                <span class="unit">°C</span>
              </div>
              
              <div class="param-item">
                <label>Case Temperature:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.t_case" 
                  placeholder="85"
                  step="1"
                />
                <span class="unit">°C</span>
              </div>
              
              <div class="param-item">
                <label>Target Efficiency:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.efficiency" 
                  placeholder="95"
                  min="50"
                  max="99"
                  step="0.1"
                />
                <span class="unit">%</span>
              </div>
              
              <div class="param-item">
                <label>Safety Margin:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.safety_margin" 
                  placeholder="20"
                  min="10"
                  max="50"
                  step="1"
                />
                <span class="unit">%</span>
              </div>
            </div>
          </div>

          <!-- Component Specifications -->
          <div class="param-section">
            <h4>🔧 Component Specifications</h4>
            <div class="param-grid">
              <div class="param-item">
                <label>Inductor Value:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.l_value" 
                  placeholder="100"
                  min="1"
                  step="1"
                />
                <span class="unit">µH</span>
              </div>
              
              <div class="param-item">
                <label>Output Capacitor:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.c_out" 
                  placeholder="1000"
                  min="1"
                  step="1"
                />
                <span class="unit">µF</span>
              </div>
              
              <div class="param-item">
                <label>Dead Time:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.dead_time" 
                  placeholder="100"
                  min="10"
                  step="10"
                />
                <span class="unit">ns</span>
              </div>
              
              <div class="param-item">
                <label>Gate Resistance:</label>
                <input 
                  type="number" 
                  v-model.number="parameters.r_gate" 
                  placeholder="10"
                  min="1"
                  step="0.1"
                />
                <span class="unit">Ω</span>
              </div>
            </div>
          </div>
        </div>

        <div class="calculation-actions">
          <button @click="calculate" :disabled="!canCalculate" class="btn btn-primary">
            🧮 Calculate
          </button>
          <button @click="optimizeDesign" :disabled="!hasResults" class="btn btn-success">
            ⚡ Optimize Design
          </button>
        </div>
      </div>

      <!-- Results Panel -->
      <div class="results-panel">
        <h3>📈 Calculation Results</h3>
        
        <div v-if="!hasResults" class="no-results">
          Configure parameters and click "Calculate" to see results
        </div>

        <div v-if="hasResults" class="results-content">
          <!-- Calculated Values -->
          <div class="results-section">
            <h4>🔢 Calculated Values</h4>
            <div class="results-grid">
              <div class="result-item">
                <label>Duty Cycle:</label>
                <span class="value">{{ results.duty_cycle.toFixed(3) }}</span>
              </div>
              
              <div class="result-item">
                <label>Input Current:</label>
                <span class="value">{{ results.i_in.toFixed(2) }} A</span>
              </div>
              
              <div class="result-item">
                <label>Output Current:</label>
                <span class="value">{{ results.i_out.toFixed(2) }} A</span>
              </div>
              
              <div class="result-item">
                <label>Peak Inductor Current:</label>
                <span class="value">{{ results.i_l_peak.toFixed(2) }} A</span>
              </div>
              
              <div class="result-item">
                <label>Current Ripple:</label>
                <span class="value">{{ results.i_ripple.toFixed(2) }} A</span>
              </div>
              
              <div class="result-item">
                <label>Voltage Ripple:</label>
                <span class="value">{{ results.v_ripple.toFixed(3) }} V</span>
              </div>
            </div>
          </div>

          <!-- Transistor Requirements -->
          <div class="results-section">
            <h4>🔌 Transistor Requirements</h4>
            <div class="requirements-grid">
              <div class="req-item">
                <label>Required V_DS:</label>
                <span class="value">{{ results.v_ds_req.toFixed(0) }} V</span>
                <span class="note">(with {{ parameters.safety_margin }}% margin)</span>
              </div>
              
              <div class="req-item">
                <label>Required I_D:</label>
                <span class="value">{{ results.i_d_req.toFixed(2) }} A</span>
                <span class="note">(RMS current)</span>
              </div>
              
              <div class="req-item">
                <label>Max Junction Temperature:</label>
                <span class="value">{{ results.t_j_max.toFixed(1) }} °C</span>
              </div>
              
              <div class="req-item">
                <label>Required R_th_ja:</label>
                <span class="value">{{ results.r_th_req.toFixed(3) }} K/W</span>
              </div>
            </div>
          </div>

          <!-- Power Loss Analysis -->
          <div class="results-section">
            <h4>📊 Power Loss Analysis</h4>
            <div class="loss-grid">
              <div class="loss-item">
                <label>Conduction Losses:</label>
                <span class="value">{{ results.p_cond.toFixed(2) }} W</span>
                <span class="percent">({{ (results.p_cond / results.p_total * 100).toFixed(1) }}%)</span>
              </div>
              
              <div class="loss-item">
                <label>Switching Losses:</label>
                <span class="value">{{ results.p_sw.toFixed(2) }} W</span>
                <span class="percent">({{ (results.p_sw / results.p_total * 100).toFixed(1) }}%)</span>
              </div>
              
              <div class="loss-item">
                <label>Gate Drive Losses:</label>
                <span class="value">{{ results.p_gate.toFixed(2) }} W</span>
                <span class="percent">({{ (results.p_gate / results.p_total * 100).toFixed(1) }}%)</span>
              </div>
              
              <div class="loss-item total">
                <label>Total Losses:</label>
                <span class="value">{{ results.p_total.toFixed(2) }} W</span>
                <span class="percent">({{ (100 - results.efficiency).toFixed(2) }}%)</span>
              </div>
            </div>
          </div>

          <!-- Recommended Transistors -->
          <div class="results-section">
            <h4>💡 Recommended Transistors</h4>
            <div v-if="recommendedTransistors.length === 0" class="no-recommendations">
              No transistors in database meet the requirements
            </div>
            <div v-else class="recommendations-list">
              <div 
                v-for="(transistor, index) in recommendedTransistors.slice(0, 5)" 
                :key="transistor.metadata.name"
                :class="['recommendation-item', { best: index === 0 }]"
              >
                <div class="rec-header">
                  <span class="rec-rank">{{ index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '📋' }}</span>
                  <strong>{{ transistor.metadata.name }}</strong>
                  <span class="rec-score">Score: {{ transistor.score.toFixed(1) }}</span>
                </div>
                <div class="rec-details">
                  <span>{{ transistor.metadata.manufacturer }}</span>
                  <span>{{ transistor.electrical.v_abs_max }}V / {{ transistor.electrical.i_abs_max }}A</span>
                  <span>R_th: {{ transistor.thermal.r_th_cs.toFixed(3) }} K/W</span>
                </div>
                <div class="rec-actions">
                  <button @click="selectTransistor(transistor)" class="btn btn-sm btn-primary">
                    ✅ Select
                  </button>
                  <button @click="viewDetails(transistor)" class="btn btn-sm btn-secondary">
                    👁️ Details
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Charts -->
          <div class="charts-section">
            <h4>📈 Analysis Charts</h4>
            <div class="charts-grid">
              <div class="chart-container">
                <canvas ref="lossChart"></canvas>
              </div>
              <div class="chart-container">
                <canvas ref="efficiencyChart"></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  transistors: Array
})

const emit = defineEmits(['transistor-selected'])

// State
const selectedTopology = ref('buck')
const hasResults = ref(false)
const lossChart = ref(null)
const efficiencyChart = ref(null)
let lossChartInstance = null
let efficiencyChartInstance = null

// Topology definitions
const topologies = ref([
  {
    id: 'buck',
    name: 'Buck Converter',
    icon: '⬇️',
    description: 'Step-down DC-DC converter',
    svg: `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" y="30" width="30" height="20" fill="#007bff" stroke="#000" stroke-width="1"/>
      <text x="25" y="45" text-anchor="middle" font-size="8">Q1</text>
      <rect x="10" y="60" width="30" height="20" fill="#6c757d" stroke="#000" stroke-width="1"/>
      <text x="25" y="75" text-anchor="middle" font-size="8">D1</text>
      <circle cx="80" cy="55" r="8" fill="none" stroke="#000" stroke-width="2"/>
      <text x="80" y="60" text-anchor="middle" font-size="8">L</text>
      <rect x="130" y="45" width="15" height="20" fill="none" stroke="#000" stroke-width="2"/>
      <text x="137" y="57" text-anchor="middle" font-size="8">C</text>
      <line x1="0" y1="40" x2="10" y2="40" stroke="#000" stroke-width="2"/>
      <line x1="40" y1="40" x2="72" y2="40" stroke="#000" stroke-width="2"/>
      <line x1="88" y1="55" x2="130" y2="55" stroke="#000" stroke-width="2"/>
      <line x1="145" y1="55" x2="180" y2="55" stroke="#000" stroke-width="2"/>
      <text x="5" y="25" font-size="10">Vin</text>
      <text x="165" y="25" font-size="10">Vout</text>
    </svg>`
  },
  {
    id: 'boost',
    name: 'Boost Converter',
    icon: '⬆️',
    description: 'Step-up DC-DC converter',
    svg: `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="40" cy="55" r="8" fill="none" stroke="#000" stroke-width="2"/>
      <text x="40" y="60" text-anchor="middle" font-size="8">L</text>
      <rect x="80" y="30" width="30" height="20" fill="#007bff" stroke="#000" stroke-width="1"/>
      <text x="95" y="45" text-anchor="middle" font-size="8">Q1</text>
      <rect x="80" y="60" width="30" height="20" fill="#6c757d" stroke="#000" stroke-width="1"/>
      <text x="95" y="75" text-anchor="middle" font-size="8">D1</text>
      <rect x="140" y="45" width="15" height="20" fill="none" stroke="#000" stroke-width="2"/>
      <text x="147" y="57" text-anchor="middle" font-size="8">C</text>
    </svg>`
  },
  {
    id: 'buck_boost',
    name: 'Buck-Boost Converter',
    icon: '⚡',
    description: 'Step-up/down converter',
    svg: `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="30" y="30" width="30" height="20" fill="#007bff" stroke="#000" stroke-width="1"/>
      <text x="45" y="45" text-anchor="middle" font-size="8">Q1</text>
      <circle cx="90" cy="55" r="8" fill="none" stroke="#000" stroke-width="2"/>
      <text x="90" y="60" text-anchor="middle" font-size="8">L</text>
      <rect x="120" y="60" width="30" height="20" fill="#6c757d" stroke="#000" stroke-width="1"/>
      <text x="135" y="75" text-anchor="middle" font-size="8">D1</text>
    </svg>`
  },
  {
    id: 'flyback',
    name: 'Flyback Converter',
    icon: '🔄',
    description: 'Isolated converter',
    svg: `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="30" width="30" height="20" fill="#007bff" stroke="#000" stroke-width="1"/>
      <text x="35" y="45" text-anchor="middle" font-size="8">Q1</text>
      <circle cx="80" cy="40" r="6" fill="none" stroke="#000" stroke-width="1"/>
      <circle cx="120" cy="40" r="6" fill="none" stroke="#000" stroke-width="1"/>
      <line x1="90" y1="35" x2="110" y2="35" stroke="#000" stroke-width="1"/>
      <text x="100" y="32" text-anchor="middle" font-size="6">T1</text>
      <rect x="140" y="30" width="30" height="20" fill="#6c757d" stroke="#000" stroke-width="1"/>
      <text x="155" y="45" text-anchor="middle" font-size="8">D1</text>
    </svg>`
  }
])

// Parameters
const parameters = ref({
  v_in: 400,
  v_out: 48,
  p_out: 1000,
  f_sw: 100,
  t_amb: 25,
  t_case: 85,
  efficiency: 95,
  safety_margin: 20,
  l_value: 100,
  c_out: 1000,
  dead_time: 100,
  r_gate: 10
})

// Results
const results = ref({})

// Computed properties
const getCurrentTopology = computed(() => {
  return topologies.value.find(t => t.id === selectedTopology.value)
})

const canCalculate = computed(() => {
  return parameters.value.v_in > 0 && 
         parameters.value.v_out > 0 && 
         parameters.value.p_out > 0 &&
         parameters.value.f_sw > 0
})

const recommendedTransistors = computed(() => {
  if (!hasResults.value || !props.transistors) return []
  
  const requirements = {
    v_ds_min: results.value.v_ds_req,
    i_d_min: results.value.i_d_req,
    r_th_max: results.value.r_th_req,
    t_j_max: results.value.t_j_max
  }
  
  return props.transistors
    .filter(t => {
      return t.electrical.v_abs_max >= requirements.v_ds_min &&
             t.electrical.i_abs_max >= requirements.i_d_min &&
             t.thermal.r_th_cs <= requirements.r_th_max &&
             t.thermal.t_j_max >= requirements.t_j_max
    })
    .map(t => {
      // Calculate suitability score
      const vMargin = (t.electrical.v_abs_max - requirements.v_ds_min) / requirements.v_ds_min
      const iMargin = (t.electrical.i_abs_max - requirements.i_d_min) / requirements.i_d_min
      const rthMargin = (requirements.r_th_max - t.thermal.r_th_cs) / requirements.r_th_max
      const tjMargin = (t.thermal.t_j_max - requirements.t_j_max) / requirements.t_j_max
      
      // Weighted score (lower thermal resistance is better)
      const score = (vMargin * 0.2 + iMargin * 0.3 + rthMargin * 0.4 + tjMargin * 0.1) * 100
      
      return {
        ...t,
        score: Math.max(0, score)
      }
    })
    .sort((a, b) => b.score - a.score)
})

// Methods
function calculate() {
  const p = parameters.value
  
  // Basic calculations based on topology
  let duty_cycle, i_in, i_out, i_l_peak, i_ripple, v_ripple
  
  switch (selectedTopology.value) {
    case 'buck':
      duty_cycle = p.v_out / p.v_in
      i_out = p.p_out / p.v_out
      i_in = i_out * duty_cycle
      i_ripple = (p.v_in - p.v_out) * duty_cycle / (p.l_value * 1e-6 * p.f_sw * 1000)
      i_l_peak = i_out + i_ripple / 2
      v_ripple = i_ripple / (8 * p.f_sw * 1000 * p.c_out * 1e-6)
      break
      
    case 'boost':
      duty_cycle = 1 - (p.v_in / p.v_out)
      i_out = p.p_out / p.v_out
      i_in = i_out / (1 - duty_cycle)
      i_ripple = p.v_in * duty_cycle / (p.l_value * 1e-6 * p.f_sw * 1000)
      i_l_peak = i_in + i_ripple / 2
      v_ripple = i_out * duty_cycle / (p.f_sw * 1000 * p.c_out * 1e-6)
      break
      
    case 'buck_boost':
      duty_cycle = p.v_out / (p.v_in + p.v_out)
      i_out = p.p_out / p.v_out
      i_in = i_out * p.v_out / (p.v_in * (1 - duty_cycle))
      i_ripple = p.v_in * duty_cycle / (p.l_value * 1e-6 * p.f_sw * 1000)
      i_l_peak = i_in + i_ripple / 2
      v_ripple = i_out * duty_cycle / (p.f_sw * 1000 * p.c_out * 1e-6)
      break
      
    default:
      duty_cycle = 0.5
      i_out = p.p_out / p.v_out
      i_in = i_out * 1.2
      i_l_peak = i_out * 1.5
      i_ripple = i_out * 0.2
      v_ripple = 0.05
  }
  
  // Power loss calculations
  const rds_on_est = 0.1 // Estimated RDS(on) in ohms
  const p_cond = Math.pow(i_l_peak, 2) * rds_on_est * duty_cycle
  
  const e_sw_est = 100e-6 // Estimated switching energy in J
  const p_sw = e_sw_est * p.f_sw * 1000
  
  const q_gate_est = 50e-9 // Estimated gate charge in C
  const p_gate = q_gate_est * 12 * p.f_sw * 1000 // Assuming 12V gate drive
  
  const p_total = p_cond + p_sw + p_gate
  const efficiency = (p.p_out / (p.p_out + p_total)) * 100
  
  // Requirements calculations
  const v_ds_req = p.v_in * (1 + p.safety_margin / 100)
  const i_d_req = i_l_peak * (1 + p.safety_margin / 100)
  const t_j_max = p.t_case + 50 // Conservative estimate
  const r_th_req = (t_j_max - p.t_case) / p_total
  
  results.value = {
    duty_cycle,
    i_in,
    i_out,
    i_l_peak,
    i_ripple,
    v_ripple,
    p_cond,
    p_sw,
    p_gate,
    p_total,
    efficiency,
    v_ds_req,
    i_d_req,
    t_j_max,
    r_th_req
  }
  
  hasResults.value = true
  
  // Update charts
  nextTick(() => {
    updateCharts()
  })
}

function optimizeDesign() {
  if (!hasResults.value) return
  
  // Simple optimization: adjust switching frequency for best efficiency
  const originalFreq = parameters.value.f_sw
  let bestEff = results.value.efficiency
  let bestFreq = originalFreq
  
  for (let freq = 50; freq <= 200; freq += 10) {
    parameters.value.f_sw = freq
    calculate()
    if (results.value.efficiency > bestEff) {
      bestEff = results.value.efficiency
      bestFreq = freq
    }
  }
  
  parameters.value.f_sw = bestFreq
  calculate()
  
  alert(`Optimized switching frequency: ${bestFreq} kHz (Efficiency: ${bestEff.toFixed(2)}%)`)
}

function updateCharts() {
  // Destroy existing charts
  if (lossChartInstance) {
    lossChartInstance.destroy()
  }
  if (efficiencyChartInstance) {
    efficiencyChartInstance.destroy()
  }
  
  // Power loss breakdown chart
  if (lossChart.value) {
    lossChartInstance = new Chart(lossChart.value, {
      type: 'doughnut',
      data: {
        labels: ['Conduction', 'Switching', 'Gate Drive'],
        datasets: [{
          data: [results.value.p_cond, results.value.p_sw, results.value.p_gate],
          backgroundColor: ['#ff6384', '#36a2eb', '#ffce56'],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Power Loss Breakdown'
          },
          legend: {
            position: 'bottom'
          }
        }
      }
    })
  }
  
  // Efficiency vs frequency chart
  if (efficiencyChart.value) {
    const frequencies = []
    const efficiencies = []
    const originalFreq = parameters.value.f_sw
    
    for (let freq = 50; freq <= 200; freq += 10) {
      parameters.value.f_sw = freq
      calculate()
      frequencies.push(freq)
      efficiencies.push(results.value.efficiency)
    }
    
    // Restore original frequency
    parameters.value.f_sw = originalFreq
    calculate()
    
    efficiencyChartInstance = new Chart(efficiencyChart.value, {
      type: 'line',
      data: {
        labels: frequencies,
        datasets: [{
          label: 'Efficiency (%)',
          data: efficiencies,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          fill: true,
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Efficiency vs Switching Frequency'
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Frequency (kHz)'
            }
          },
          y: {
            title: {
              display: true,
              text: 'Efficiency (%)'
            }
          }
        }
      }
    })
  }
}

function resetCalculations() {
  parameters.value = {
    v_in: 400,
    v_out: 48,
    p_out: 1000,
    f_sw: 100,
    t_amb: 25,
    t_case: 85,
    efficiency: 95,
    safety_margin: 20,
    l_value: 100,
    c_out: 1000,
    dead_time: 100,
    r_gate: 10
  }
  
  results.value = {}
  hasResults.value = false
  
  if (lossChartInstance) {
    lossChartInstance.destroy()
    lossChartInstance = null
  }
  if (efficiencyChartInstance) {
    efficiencyChartInstance.destroy()
    efficiencyChartInstance = null
  }
}

function saveResults() {
  if (!hasResults.value) return
  
  const exportData = {
    topology: getCurrentTopology().value.name,
    parameters: parameters.value,
    results: results.value,
    recommendations: recommendedTransistors.value.slice(0, 5),
    timestamp: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `topology_calculation_${new Date().toISOString().split('T')[0]}.json`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function selectTransistor(transistor) {
  emit('transistor-selected', transistor)
}

function viewDetails(transistor) {
  // Emit event to show transistor details
  emit('view-transistor-details', transistor)
}

// Auto-calculate when topology changes
watch(selectedTopology, () => {
  if (hasResults.value) {
    calculate()
  }
})
</script>

<style scoped>
.topology-calculator {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1rem;
}

.calc-header {
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

.calc-content {
  display: grid;
  grid-template-columns: 350px 400px 1fr;
  gap: 2rem;
}

.topology-panel,
.parameters-panel,
.results-panel {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: fit-content;
}

.topology-panel h3,
.parameters-panel h3,
.results-panel h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.5rem;
}

.topology-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

.topology-card {
  padding: 1rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.topology-card:hover {
  border-color: #007bff;
  transform: translateY(-2px);
}

.topology-card.active {
  border-color: #007bff;
  background: #f8f9ff;
}

.topology-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.topology-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.topology-desc {
  font-size: 0.8rem;
  color: #666;
}

.topology-info {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.topology-info h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.circuit-svg {
  text-align: center;
}

.circuit-svg svg {
  width: 100%;
  max-width: 300px;
  height: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

.parameter-sections {
  margin-bottom: 2rem;
}

.param-section {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.param-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.param-grid {
  display: grid;
  gap: 1rem;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.param-item label {
  min-width: 140px;
  font-size: 0.9rem;
  color: #555;
}

.param-item input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.param-item .unit {
  min-width: 30px;
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
}

.calculation-actions {
  display: flex;
  gap: 1rem;
}

.results-panel {
  max-height: 80vh;
  overflow-y: auto;
}

.no-results {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 2rem;
}

.results-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.results-section {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.results-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.results-grid,
.requirements-grid,
.loss-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.result-item,
.req-item,
.loss-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.loss-item.total {
  grid-column: 1 / -1;
  border-left-color: #28a745;
  font-weight: 600;
}

.result-item label,
.req-item label,
.loss-item label {
  font-size: 0.9rem;
  color: #555;
}

.value {
  font-weight: 600;
  color: #2c3e50;
}

.note,
.percent {
  font-size: 0.8rem;
  color: #666;
  margin-left: 0.5rem;
}

.no-recommendations {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 1rem;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recommendation-item {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: all 0.3s;
}

.recommendation-item.best {
  border-color: #ffc107;
  background: #fff8e1;
}

.recommendation-item:hover {
  border-color: #007bff;
  transform: translateY(-1px);
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.rec-rank {
  font-size: 1.2rem;
}

.rec-score {
  margin-left: auto;
  font-size: 0.8rem;
  color: #666;
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.rec-details {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.rec-actions {
  display: flex;
  gap: 0.5rem;
}

.charts-section {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.chart-container {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  height: 300px;
}

.chart-container canvas {
  max-height: 100%;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  text-decoration: none;
  display: inline-block;
  font-size: 0.9rem;
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

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #138496;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #1e7e34;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

@media (max-width: 1400px) {
  .calc-content {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .calc-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .topology-grid {
    grid-template-columns: 1fr;
  }
  
  .results-grid,
  .requirements-grid,
  .loss-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .calculation-actions {
    flex-direction: column;
  }
}
</style>
