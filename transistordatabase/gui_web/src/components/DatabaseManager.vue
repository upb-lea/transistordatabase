<template>
  <div class="database-manager">
    <div class="manager-header">
      <h2>📊 Database Manager</h2>
      <div class="header-actions">
        <button @click="refreshDatabase" class="btn btn-secondary">
          🔄 Refresh
        </button>
        <button @click="importDatabase" class="btn btn-primary">
          📂 Import Database
        </button>
        <button @click="exportDatabase" class="btn btn-primary">
          💾 Export Database
        </button>
      </div>
    </div>

    <div class="database-stats">
      <div class="stat-card">
        <h3>{{ transistors.length }}</h3>
        <p>Total Transistors</p>
      </div>
      <div class="stat-card">
        <h3>{{ uniqueManufacturers }}</h3>
        <p>Manufacturers</p>
      </div>
      <div class="stat-card">
        <h3>{{ uniqueTypes }}</h3>
        <p>Transistor Types</p>
      </div>
      <div class="stat-card">
        <h3>{{ averageVoltage }}V</h3>
        <p>Avg Max Voltage</p>
      </div>
    </div>

    <div class="database-filters">
      <div class="filter-row">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="🔍 Search transistors..." 
          class="search-input"
        />
        <select v-model="selectedManufacturer" class="filter-select">
          <option value="">All Manufacturers</option>
          <option v-for="mfg in manufacturers" :key="mfg" :value="mfg">{{ mfg }}</option>
        </select>
        <select v-model="selectedType" class="filter-select">
          <option value="">All Types</option>
          <option v-for="type in types" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
    </div>

    <div class="database-table">
      <table>
        <thead>
          <tr>
            <th @click="sortBy('name')" class="sortable">
              Name {{ getSortIcon('name') }}
            </th>
            <th @click="sortBy('type')" class="sortable">
              Type {{ getSortIcon('type') }}
            </th>
            <th @click="sortBy('manufacturer')" class="sortable">
              Manufacturer {{ getSortIcon('manufacturer') }}
            </th>
            <th @click="sortBy('voltage')" class="sortable">
              Max Voltage {{ getSortIcon('voltage') }}
            </th>
            <th @click="sortBy('current')" class="sortable">
              Max Current {{ getSortIcon('current') }}
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(transistor, index) in filteredAndSortedTransistors" 
            :key="index"
            @click="selectTransistor(transistor)"
            :class="{ selected: selectedTransistor?.metadata?.name === transistor.metadata?.name }"
          >
            <td class="transistor-name">{{ transistor.metadata.name }}</td>
            <td>
              <span class="type-badge" :class="transistor.metadata.type.toLowerCase()">
                {{ transistor.metadata.type }}
              </span>
            </td>
            <td>{{ transistor.metadata.manufacturer }}</td>
            <td>{{ transistor.electrical.v_abs_max }}V</td>
            <td>{{ transistor.electrical.i_abs_max }}A</td>
            <td class="actions">
              <button @click.stop="editTransistor(transistor)" class="btn btn-small btn-primary">
                ✏️ Edit
              </button>
              <button @click.stop="validateTransistor(transistor)" class="btn btn-small btn-secondary">
                ✅ Validate
              </button>
              <button @click.stop="exportTransistor(transistor)" class="btn btn-small btn-secondary">
                💾 Export
              </button>
              <button @click.stop="deleteTransistor(transistor)" class="btn btn-small btn-danger">
                🗑️ Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="selectedTransistor" class="transistor-details">
      <h3>Selected: {{ selectedTransistor.metadata.name }}</h3>
      <div class="details-grid">
        <div class="detail-section">
          <h4>📋 Metadata</h4>
          <p><strong>Type:</strong> {{ selectedTransistor.metadata.type }}</p>
          <p><strong>Manufacturer:</strong> {{ selectedTransistor.metadata.manufacturer }}</p>
          <p><strong>Housing:</strong> {{ selectedTransistor.metadata.housing_type }}</p>
          <p><strong>Author:</strong> {{ selectedTransistor.metadata.author }}</p>
        </div>
        <div class="detail-section">
          <h4>⚡ Electrical</h4>
          <p><strong>Max Voltage:</strong> {{ selectedTransistor.electrical.v_abs_max }}V</p>
          <p><strong>Max Current:</strong> {{ selectedTransistor.electrical.i_abs_max }}A</p>
          <p><strong>Continuous Current:</strong> {{ selectedTransistor.electrical.i_cont }}A</p>
          <p><strong>Max Junction Temp:</strong> {{ selectedTransistor.electrical.t_j_max }}°C</p>
        </div>
        <div class="detail-section">
          <h4>🌡️ Thermal</h4>
          <p><strong>Thermal Resistance:</strong> {{ selectedTransistor.thermal.r_th_cs }}K/W</p>
          <p><strong>Housing Area:</strong> {{ selectedTransistor.thermal.housing_area }}cm²</p>
          <p><strong>Cooling Area:</strong> {{ selectedTransistor.thermal.cooling_area }}cm²</p>
        </div>
      </div>
    </div>

    <!-- File input for import -->
    <input 
      type="file" 
      ref="fileInput" 
      @change="handleFileImport" 
      accept=".json,.csv" 
      style="display: none"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { transistorApi } from '../services/api.js'

const props = defineProps({
  transistors: Array
})

const emit = defineEmits(['transistor-selected', 'refresh'])

const searchQuery = ref('')
const selectedManufacturer = ref('')
const selectedType = ref('')
const selectedTransistor = ref(null)
const sortField = ref('name')
const sortDirection = ref('asc')
const fileInput = ref(null)

// Computed properties
const manufacturers = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.manufacturer))].sort()
})

const types = computed(() => {
  return [...new Set(props.transistors.map(t => t.metadata.type))].sort()
})

const uniqueManufacturers = computed(() => manufacturers.value.length)
const uniqueTypes = computed(() => types.value.length)

const averageVoltage = computed(() => {
  if (props.transistors.length === 0) return 0
  const sum = props.transistors.reduce((acc, t) => acc + t.electrical.v_abs_max, 0)
  return Math.round(sum / props.transistors.length)
})

const filteredAndSortedTransistors = computed(() => {
  let filtered = props.transistors.filter(transistor => {
    const matchesSearch = transistor.metadata.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         transistor.metadata.manufacturer.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesManufacturer = !selectedManufacturer.value || transistor.metadata.manufacturer === selectedManufacturer.value
    const matchesType = !selectedType.value || transistor.metadata.type === selectedType.value
    
    return matchesSearch && matchesManufacturer && matchesType
  })

  // Sort
  filtered.sort((a, b) => {
    let aVal, bVal
    
    switch (sortField.value) {
      case 'name':
        aVal = a.metadata.name
        bVal = b.metadata.name
        break
      case 'type':
        aVal = a.metadata.type
        bVal = b.metadata.type
        break
      case 'manufacturer':
        aVal = a.metadata.manufacturer
        bVal = b.metadata.manufacturer
        break
      case 'voltage':
        aVal = a.electrical.v_abs_max
        bVal = b.electrical.v_abs_max
        break
      case 'current':
        aVal = a.electrical.i_abs_max
        bVal = b.electrical.i_abs_max
        break
      default:
        return 0
    }

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = bVal.toLowerCase()
    }

    if (sortDirection.value === 'asc') {
      return aVal < bVal ? -1 : aVal > bVal ? 1 : 0
    } else {
      return aVal > bVal ? -1 : aVal < bVal ? 1 : 0
    }
  })

  return filtered
})

// Methods
function sortBy(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

function getSortIcon(field) {
  if (sortField.value !== field) return '↕️'
  return sortDirection.value === 'asc' ? '⬆️' : '⬇️'
}

function selectTransistor(transistor) {
  selectedTransistor.value = transistor
}

function editTransistor(transistor) {
  emit('transistor-selected', transistor)
}

async function validateTransistor(transistor) {
  try {
    const result = await transistorApi.validate(transistor.metadata.name.replace(/[^a-zA-Z0-9]/g, '_'))
    const errors = result.errors || []
    const warnings = result.warnings || []
    
    if (errors.length === 0 && warnings.length === 0) {
      alert('✅ Transistor validation passed!')
    } else {
      let message = '⚠️ Validation Results:\n\n'
      if (errors.length > 0) {
        message += 'Errors:\n' + errors.join('\n') + '\n\n'
      }
      if (warnings.length > 0) {
        message += 'Warnings:\n' + warnings.join('\n')
      }
      alert(message)
    }
  } catch (error) {
    alert('❌ Validation failed: ' + error.message)
  }
}

async function exportTransistor(transistor) {
  try {
    const format = prompt('Export format (json, csv, spice):', 'json')
    if (!format) return
    
    const transistorId = transistor.metadata.name.replace(/[^a-zA-Z0-9]/g, '_')
    const response = await transistorApi.export(transistorId, format)
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${transistor.metadata.name}.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('❌ Export failed: ' + error.message)
  }
}

async function deleteTransistor(transistor) {
  if (confirm(`Are you sure you want to delete "${transistor.metadata.name}"?`)) {
    try {
      const transistorId = transistor.metadata.name.replace(/[^a-zA-Z0-9]/g, '_')
      await transistorApi.delete(transistorId)
      emit('refresh')
      if (selectedTransistor.value?.metadata?.name === transistor.metadata.name) {
        selectedTransistor.value = null
      }
    } catch (error) {
      alert('❌ Delete failed: ' + error.message)
    }
  }
}

function refreshDatabase() {
  emit('refresh')
}

function importDatabase() {
  fileInput.value.click()
}

async function handleFileImport(event) {
  const file = event.target.files[0]
  if (!file) return

  try {
    const formData = new FormData()
    formData.append('file', file)
    
    await transistorApi.upload(formData)
    emit('refresh')
    alert('✅ Database imported successfully!')
  } catch (error) {
    alert('❌ Import failed: ' + error.message)
  }
}

async function exportDatabase() {
  try {
    const format = prompt('Export format (json, csv):', 'json')
    if (!format) return
    
    // Export all transistors
    const allData = JSON.stringify(props.transistors, null, 2)
    const blob = new Blob([allData], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `transistor_database.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('❌ Export failed: ' + error.message)
  }
}
</script>

<style scoped>
.database-manager {
  max-width: 1400px;
  margin: 0 auto;
}

.manager-header {
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

.database-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.stat-card h3 {
  font-size: 2rem;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.stat-card p {
  margin: 0;
  color: #666;
  font-weight: 500;
}

.database-filters {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.filter-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1rem;
}

.search-input, .filter-select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.database-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
  margin-bottom: 2rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background: #e9ecef;
}

tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

tbody tr:hover {
  background: #f8f9fa;
}

tbody tr.selected {
  background: #e3f2fd;
}

.transistor-name {
  font-weight: 600;
  color: #2c3e50;
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

.actions {
  display: flex;
  gap: 0.5rem;
}

.transistor-details {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-top: 1rem;
}

.detail-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.detail-section p {
  margin: 0.5rem 0;
  color: #555;
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

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-small {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}
</style>
