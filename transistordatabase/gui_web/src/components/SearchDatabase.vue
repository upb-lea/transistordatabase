<template>
  <div class="search-database">
    <div class="search-header">
      <h2>🔍 Search Database</h2>
      <div class="header-actions">
        <button @click="resetFilters" class="btn btn-secondary">
          🔄 Reset Filters
        </button>
        <button @click="exportResults" :disabled="filteredTransistors.length === 0" class="btn btn-primary">
          💾 Export Results
        </button>
      </div>
    </div>

    <div class="search-content">
      <!-- Filter Panel -->
      <div class="filter-panel">
        <h3>🎛️ Advanced Filters</h3>
        
        <!-- Basic Filters -->
        <div class="filter-section">
          <h4>Basic Properties</h4>
          <div class="filter-grid">
            <div class="filter-item">
              <label>
                <input type="checkbox" v-model="filters.name.enabled" />
                Name Contains:
              </label>
              <input 
                type="text" 
                v-model="filters.name.value" 
                :disabled="!filters.name.enabled"
                placeholder="Enter name filter..."
              />
            </div>

            <div class="filter-item">
              <label>
                <input type="checkbox" v-model="filters.type.enabled" />
                Type:
              </label>
              <select v-model="filters.type.value" :disabled="!filters.type.enabled">
                <option value="">All Types</option>
                <option v-for="type in availableTypes" :key="type" :value="type">
                  {{ type }}
                </option>
              </select>
            </div>

            <div class="filter-item">
              <label>
                <input type="checkbox" v-model="filters.manufacturer.enabled" />
                Manufacturer:
              </label>
              <select v-model="filters.manufacturer.value" :disabled="!filters.manufacturer.enabled">
                <option value="">All Manufacturers</option>
                <option v-for="mfg in availableManufacturers" :key="mfg" :value="mfg">
                  {{ mfg }}
                </option>
              </select>
            </div>

            <div class="filter-item">
              <label>
                <input type="checkbox" v-model="filters.housing_type.enabled" />
                Housing Type:
              </label>
              <select v-model="filters.housing_type.value" :disabled="!filters.housing_type.enabled">
                <option value="">All Housing Types</option>
                <option v-for="housing in availableHousingTypes" :key="housing" :value="housing">
                  {{ housing }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Electrical Ratings Filters -->
        <div class="filter-section">
          <h4>⚡ Electrical Ratings</h4>
          <div class="filter-grid">
            <div class="filter-item range-filter">
              <label>
                <input type="checkbox" v-model="filters.v_abs_max.enabled" />
                Max Voltage (V):
              </label>
              <div class="range-inputs">
                <input 
                  type="number" 
                  v-model.number="filters.v_abs_max.min" 
                  :disabled="!filters.v_abs_max.enabled"
                  placeholder="Min"
                />
                <span>to</span>
                <input 
                  type="number" 
                  v-model.number="filters.v_abs_max.max" 
                  :disabled="!filters.v_abs_max.enabled"
                  placeholder="Max"
                />
              </div>
            </div>

            <div class="filter-item range-filter">
              <label>
                <input type="checkbox" v-model="filters.i_abs_max.enabled" />
                Max Current (A):
              </label>
              <div class="range-inputs">
                <input 
                  type="number" 
                  v-model.number="filters.i_abs_max.min" 
                  :disabled="!filters.i_abs_max.enabled"
                  placeholder="Min"
                />
                <span>to</span>
                <input 
                  type="number" 
                  v-model.number="filters.i_abs_max.max" 
                  :disabled="!filters.i_abs_max.enabled"
                  placeholder="Max"
                />
              </div>
            </div>

            <div class="filter-item range-filter">
              <label>
                <input type="checkbox" v-model="filters.i_cont.enabled" />
                Continuous Current (A):
              </label>
              <div class="range-inputs">
                <input 
                  type="number" 
                  v-model.number="filters.i_cont.min" 
                  :disabled="!filters.i_cont.enabled"
                  placeholder="Min"
                />
                <span>to</span>
                <input 
                  type="number" 
                  v-model.number="filters.i_cont.max" 
                  :disabled="!filters.i_cont.enabled"
                  placeholder="Max"
                />
              </div>
            </div>

            <div class="filter-item range-filter">
              <label>
                <input type="checkbox" v-model="filters.t_j_max.enabled" />
                Max Junction Temperature (°C):
              </label>
              <div class="range-inputs">
                <input 
                  type="number" 
                  v-model.number="filters.t_j_max.min" 
                  :disabled="!filters.t_j_max.enabled"
                  placeholder="Min"
                />
                <span>to</span>
                <input 
                  type="number" 
                  v-model.number="filters.t_j_max.max" 
                  :disabled="!filters.t_j_max.enabled"
                  placeholder="Max"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Thermal Properties Filters -->
        <div class="filter-section">
          <h4>🌡️ Thermal Properties</h4>
          <div class="filter-grid">
            <div class="filter-item range-filter">
              <label>
                <input type="checkbox" v-model="filters.r_th_cs.enabled" />
                Thermal Resistance (K/W):
              </label>
              <div class="range-inputs">
                <input 
                  type="number" 
                  v-model.number="filters.r_th_cs.min" 
                  :disabled="!filters.r_th_cs.enabled"
                  placeholder="Min"
                  step="0.001"
                />
                <span>to</span>
                <input 
                  type="number" 
                  v-model.number="filters.r_th_cs.max" 
                  :disabled="!filters.r_th_cs.enabled"
                  placeholder="Max"
                  step="0.001"
                />
              </div>
            </div>

            <div class="filter-item range-filter">
              <label>
                <input type="checkbox" v-model="filters.housing_area.enabled" />
                Housing Area (m²):
              </label>
              <div class="range-inputs">
                <input 
                  type="number" 
                  v-model.number="filters.housing_area.min" 
                  :disabled="!filters.housing_area.enabled"
                  placeholder="Min"
                  step="0.000001"
                />
                <span>to</span>
                <input 
                  type="number" 
                  v-model.number="filters.housing_area.max" 
                  :disabled="!filters.housing_area.enabled"
                  placeholder="Max"
                  step="0.000001"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Filters -->
        <div class="filter-section">
          <h4>🚀 Quick Filters</h4>
          <div class="quick-filters">
            <button @click="applyQuickFilter('high_voltage')" class="btn btn-quick">
              High Voltage (>1000V)
            </button>
            <button @click="applyQuickFilter('high_current')" class="btn btn-quick">
              High Current (>100A)
            </button>
            <button @click="applyQuickFilter('sic_mosfet')" class="btn btn-quick">
              SiC MOSFETs
            </button>
            <button @click="applyQuickFilter('igbt')" class="btn btn-quick">
              IGBTs
            </button>
            <button @click="applyQuickFilter('low_thermal')" class="btn btn-quick">
              Low Thermal Resistance
            </button>
          </div>
        </div>
      </div>

      <!-- Results Panel -->
      <div class="results-panel">
        <div class="results-header">
          <h3>📋 Search Results ({{ filteredTransistors.length }} devices)</h3>
          <div class="view-controls">
            <button 
              @click="viewMode = 'table'" 
              :class="{ active: viewMode === 'table' }"
              class="btn btn-sm"
            >
              📊 Table
            </button>
            <button 
              @click="viewMode = 'cards'" 
              :class="{ active: viewMode === 'cards' }"
              class="btn btn-sm"
            >
              🗃️ Cards
            </button>
          </div>
        </div>

        <!-- Table View -->
        <div v-if="viewMode === 'table'" class="table-view">
          <table class="results-table">
            <thead>
              <tr>
                <th @click="sortBy('name')" class="sortable">
                  Name {{ getSortIcon('name') }}
                </th>
                <th @click="sortBy('manufacturer')" class="sortable">
                  Manufacturer {{ getSortIcon('manufacturer') }}
                </th>
                <th @click="sortBy('type')" class="sortable">
                  Type {{ getSortIcon('type') }}
                </th>
                <th @click="sortBy('v_abs_max')" class="sortable">
                  Max V {{ getSortIcon('v_abs_max') }}
                </th>
                <th @click="sortBy('i_abs_max')" class="sortable">
                  Max I {{ getSortIcon('i_abs_max') }}
                </th>
                <th @click="sortBy('r_th_cs')" class="sortable">
                  R_th {{ getSortIcon('r_th_cs') }}
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="transistor in paginatedTransistors" :key="transistor.metadata.name">
                <td class="transistor-name">{{ transistor.metadata.name }}</td>
                <td>{{ transistor.metadata.manufacturer }}</td>
                <td>
                  <span :class="['type-badge', transistor.metadata.type.toLowerCase()]">
                    {{ transistor.metadata.type }}
                  </span>
                </td>
                <td>{{ transistor.electrical.v_abs_max }}V</td>
                <td>{{ transistor.electrical.i_abs_max }}A</td>
                <td>{{ transistor.thermal.r_th_cs.toFixed(3) }} K/W</td>
                <td class="actions">
                  <button @click="loadToExportingTools(transistor)" class="btn btn-sm btn-primary">
                    📤 Export
                  </button>
                  <button @click="loadToComparison(transistor)" class="btn btn-sm btn-secondary">
                    🔍 Compare
                  </button>
                  <button @click="loadToTopology(transistor)" class="btn btn-sm btn-info">
                    🧮 Topology
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div class="pagination" v-if="totalPages > 1">
            <button @click="currentPage = 1" :disabled="currentPage === 1" class="btn btn-sm">
              « First
            </button>
            <button @click="currentPage--" :disabled="currentPage === 1" class="btn btn-sm">
              ‹ Prev
            </button>
            <span class="page-info">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button @click="currentPage++" :disabled="currentPage === totalPages" class="btn btn-sm">
              Next ›
            </button>
            <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="btn btn-sm">
              Last »
            </button>
          </div>
        </div>

        <!-- Cards View -->
        <div v-if="viewMode === 'cards'" class="cards-view">
          <div class="transistor-cards">
            <div 
              v-for="transistor in paginatedTransistors" 
              :key="transistor.metadata.name"
              class="transistor-card"
            >
              <div class="card-header">
                <h4>{{ transistor.metadata.name }}</h4>
                <span :class="['type-badge', transistor.metadata.type.toLowerCase()]">
                  {{ transistor.metadata.type }}
                </span>
              </div>
              <div class="card-content">
                <div class="card-info">
                  <p><strong>Manufacturer:</strong> {{ transistor.metadata.manufacturer }}</p>
                  <p><strong>Housing:</strong> {{ transistor.metadata.housing_type }}</p>
                  <p><strong>Max Voltage:</strong> {{ transistor.electrical.v_abs_max }}V</p>
                  <p><strong>Max Current:</strong> {{ transistor.electrical.i_abs_max }}A</p>
                  <p><strong>Thermal Resistance:</strong> {{ transistor.thermal.r_th_cs.toFixed(3) }} K/W</p>
                </div>
                <div class="card-actions">
                  <button @click="loadToExportingTools(transistor)" class="btn btn-sm btn-primary">
                    📤 Export
                  </button>
                  <button @click="loadToComparison(transistor)" class="btn btn-sm btn-secondary">
                    🔍 Compare
                  </button>
                  <button @click="loadToTopology(transistor)" class="btn btn-sm btn-info">
                    🧮 Topology
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  transistors: Array
})

const emit = defineEmits(['load-to-exporting', 'load-to-comparison', 'load-to-topology'])

// Filter state
const filters = ref({
  name: { enabled: false, value: '' },
  type: { enabled: false, value: '' },
  manufacturer: { enabled: false, value: '' },
  housing_type: { enabled: false, value: '' },
  v_abs_max: { enabled: false, min: null, max: null },
  i_abs_max: { enabled: false, min: null, max: null },
  i_cont: { enabled: false, min: null, max: null },
  t_j_max: { enabled: false, min: null, max: null },
  r_th_cs: { enabled: false, min: null, max: null },
  housing_area: { enabled: false, min: null, max: null }
})

// View state
const viewMode = ref('table')
const sortField = ref('')
const sortDirection = ref('asc')
const currentPage = ref(1)
const itemsPerPage = ref(20)

// Computed properties for filter options
const availableTypes = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.type))].sort()
})

const availableManufacturers = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.manufacturer))].sort()
})

const availableHousingTypes = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.housing_type))].sort()
})

// Filtered and sorted transistors
const filteredTransistors = computed(() => {
  let result = props.transistors.filter(transistor => {
    // Name filter
    if (filters.value.name.enabled) {
      if (!transistor.metadata.name.toLowerCase().includes(filters.value.name.value.toLowerCase())) {
        return false
      }
    }

    // Type filter
    if (filters.value.type.enabled && filters.value.type.value) {
      if (transistor.metadata.type !== filters.value.type.value) {
        return false
      }
    }

    // Manufacturer filter
    if (filters.value.manufacturer.enabled && filters.value.manufacturer.value) {
      if (transistor.metadata.manufacturer !== filters.value.manufacturer.value) {
        return false
      }
    }

    // Housing type filter
    if (filters.value.housing_type.enabled && filters.value.housing_type.value) {
      if (transistor.metadata.housing_type !== filters.value.housing_type.value) {
        return false
      }
    }

    // Range filters
    const rangeFilters = ['v_abs_max', 'i_abs_max', 'i_cont', 't_j_max', 'r_th_cs', 'housing_area']
    for (const field of rangeFilters) {
      const filter = filters.value[field]
      if (filter.enabled) {
        let value
        if (field === 'housing_area') {
          value = transistor.thermal[field]
        } else if (field === 'r_th_cs') {
          value = transistor.thermal[field]
        } else {
          value = transistor.electrical[field]
        }

        if (filter.min !== null && value < filter.min) return false
        if (filter.max !== null && value > filter.max) return false
      }
    }

    return true
  })

  // Apply sorting
  if (sortField.value) {
    result.sort((a, b) => {
      let aVal, bVal
      
      if (sortField.value === 'name' || sortField.value === 'manufacturer' || sortField.value === 'type' || sortField.value === 'housing_type') {
        aVal = a.metadata[sortField.value]
        bVal = b.metadata[sortField.value]
      } else if (sortField.value === 'r_th_cs' || sortField.value === 'housing_area') {
        aVal = a.thermal[sortField.value]
        bVal = b.thermal[sortField.value]
      } else {
        aVal = a.electrical[sortField.value]
        bVal = b.electrical[sortField.value]
      }

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase()
        bVal = bVal.toLowerCase()
      }

      if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
      return 0
    })
  }

  return result
})

// Pagination
const totalPages = computed(() => Math.ceil(filteredTransistors.value.length / itemsPerPage.value))

const paginatedTransistors = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredTransistors.value.slice(start, end)
})

// Methods
function resetFilters() {
  filters.value = {
    name: { enabled: false, value: '' },
    type: { enabled: false, value: '' },
    manufacturer: { enabled: false, value: '' },
    housing_type: { enabled: false, value: '' },
    v_abs_max: { enabled: false, min: null, max: null },
    i_abs_max: { enabled: false, min: null, max: null },
    i_cont: { enabled: false, min: null, max: null },
    t_j_max: { enabled: false, min: null, max: null },
    r_th_cs: { enabled: false, min: null, max: null },
    housing_area: { enabled: false, min: null, max: null }
  }
  currentPage.value = 1
}

function applyQuickFilter(filterType) {
  resetFilters()
  
  switch (filterType) {
    case 'high_voltage':
      filters.value.v_abs_max.enabled = true
      filters.value.v_abs_max.min = 1000
      break
    case 'high_current':
      filters.value.i_abs_max.enabled = true
      filters.value.i_abs_max.min = 100
      break
    case 'sic_mosfet':
      filters.value.type.enabled = true
      filters.value.type.value = 'SiC-MOSFET'
      break
    case 'igbt':
      filters.value.type.enabled = true
      filters.value.type.value = 'IGBT'
      break
    case 'low_thermal':
      filters.value.r_th_cs.enabled = true
      filters.value.r_th_cs.max = 0.5
      break
  }
}

function sortBy(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
}

function getSortIcon(field) {
  if (sortField.value !== field) return ''
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

function loadToExportingTools(transistor) {
  emit('load-to-exporting', transistor)
}

function loadToComparison(transistor) {
  emit('load-to-comparison', transistor)
}

function loadToTopology(transistor) {
  emit('load-to-topology', transistor)
}

function exportResults() {
  const data = {
    filters: filters.value,
    results: filteredTransistors.value,
    totalCount: filteredTransistors.value.length,
    exportDate: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `transistor_search_results_${new Date().toISOString().split('T')[0]}.json`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// Reset page when filters change
watch(filters, () => {
  currentPage.value = 1
}, { deep: true })
</script>

<style scoped>
.search-database {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

.search-header {
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

.search-content {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 2rem;
}

.filter-panel {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: fit-content;
  max-height: 80vh;
  overflow-y: auto;
}

.filter-section {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.filter-section:last-child {
  border-bottom: none;
}

.filter-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.filter-grid {
  display: grid;
  gap: 1rem;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-item label {
  font-weight: 500;
  color: #555;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-item input[type="text"],
.filter-item input[type="number"],
.filter-item select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.filter-item input:disabled,
.filter-item select:disabled {
  background: #f5f5f5;
  color: #999;
}

.range-filter .range-inputs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.range-filter .range-inputs input {
  flex: 1;
}

.range-filter .range-inputs span {
  color: #666;
  font-size: 0.9rem;
}

.quick-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn-quick {
  padding: 0.5rem 1rem;
  background: #e9ecef;
  color: #495057;
  border: 1px solid #ced4da;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-quick:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.results-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.view-controls {
  display: flex;
  gap: 0.5rem;
}

.view-controls .btn {
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
}

.view-controls .btn.active {
  background: #007bff;
  color: white;
}

.table-view {
  overflow-x: auto;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
}

.results-table th,
.results-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.results-table th {
  background: #f8f9fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.results-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.results-table th.sortable:hover {
  background: #e9ecef;
}

.transistor-name {
  font-weight: 600;
  color: #007bff;
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

.type-badge.mosfet, .type-badge.sic-mosfet {
  background: #f3e5f5;
  color: #7b1fa2;
}

.type-badge.diode {
  background: #e8f5e8;
  color: #388e3c;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-top: 1px solid #eee;
}

.page-info {
  color: #666;
  font-size: 0.9rem;
}

.cards-view {
  padding: 1.5rem;
}

.transistor-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.transistor-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s;
}

.transistor-card:hover {
  border-color: #007bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-header h4 {
  margin: 0;
  color: #2c3e50;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card-info p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  color: #555;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
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

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

@media (max-width: 1024px) {
  .search-content {
    grid-template-columns: 1fr;
  }
  
  .filter-panel {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .search-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .results-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .transistor-cards {
    grid-template-columns: 1fr;
  }
  
  .actions {
    flex-direction: column;
  }
}
</style>
