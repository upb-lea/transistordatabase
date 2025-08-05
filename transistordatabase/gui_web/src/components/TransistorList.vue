<template>
  <div class="transistor-list">
    <div class="list-header">
      <h2>Transistor Database</h2>
      <div class="list-actions">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search transistors..." 
          class="search-input"
        />
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileUpload" 
          accept=".json" 
          style="display: none"
        />
        <button @click="$refs.fileInput.click()" class="btn btn-secondary">
          Upload JSON
        </button>
      </div>
    </div>

    <div v-if="filteredTransistors.length === 0" class="empty-state">
      <p>No transistors found. <a href="#" @click="$emit('create')">Add your first transistor</a></p>
    </div>

    <div v-else class="transistor-grid">
      <div 
        v-for="(transistor, index) in filteredTransistors" 
        :key="index"
        class="transistor-card"
      >
        <div class="card-header">
          <h3>{{ transistor.metadata.name }}</h3>
          <div class="card-actions">
            <button @click="$emit('edit', transistor)" class="btn btn-small btn-primary">
              Edit
            </button>
            <button @click="validateTransistor(transistor)" class="btn btn-small btn-secondary">
              Validate
            </button>
            <button @click="exportTransistor(transistor, 'json')" class="btn btn-small btn-secondary">
              Export
            </button>
            <button @click="deleteTransistor(transistor)" class="btn btn-small btn-danger">
              Delete
            </button>
          </div>
        </div>

        <div class="card-content">
          <div class="transistor-info">
            <div class="info-group">
              <label>Type:</label>
              <span>{{ transistor.metadata.type }}</span>
            </div>
            <div class="info-group">
              <label>Manufacturer:</label>
              <span>{{ transistor.metadata.manufacturer }}</span>
            </div>
            <div class="info-group">
              <label>Housing:</label>
              <span>{{ transistor.metadata.housing_type }}</span>
            </div>
          </div>

          <div class="transistor-specs">
            <h4>Electrical Ratings</h4>
            <div class="specs-grid">
              <div class="spec-item">
                <label>V<sub>abs,max</sub>:</label>
                <span>{{ transistor.electrical.v_abs_max }}V</span>
              </div>
              <div class="spec-item">
                <label>I<sub>abs,max</sub>:</label>
                <span>{{ transistor.electrical.i_abs_max }}A</span>
              </div>
              <div class="spec-item">
                <label>I<sub>cont</sub>:</label>
                <span>{{ transistor.electrical.i_cont }}A</span>
              </div>
              <div class="spec-item">
                <label>T<sub>j,max</sub>:</label>
                <span>{{ transistor.electrical.t_j_max }}°C</span>
              </div>
            </div>

            <h4>Thermal Properties</h4>
            <div class="specs-grid">
              <div class="spec-item">
                <label>R<sub>th,cs</sub>:</label>
                <span>{{ transistor.thermal.r_th_cs }}K/W</span>
              </div>
              <div class="spec-item">
                <label>Housing Area:</label>
                <span>{{ transistor.thermal.housing_area }}cm²</span>
              </div>
              <div class="spec-item">
                <label>Cooling Area:</label>
                <span>{{ transistor.thermal.cooling_area }}cm²</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="validationResults[transistor.metadata.name]" class="validation-results">
          <h4>Validation Results</h4>
          <div v-if="validationResults[transistor.metadata.name].errors.length > 0" class="errors">
            <p><strong>Errors:</strong></p>
            <ul>
              <li v-for="error in validationResults[transistor.metadata.name].errors" :key="error">
                {{ error }}
              </li>
            </ul>
          </div>
          <div v-if="validationResults[transistor.metadata.name].warnings.length > 0" class="warnings">
            <p><strong>Warnings:</strong></p>
            <ul>
              <li v-for="warning in validationResults[transistor.metadata.name].warnings" :key="warning">
                {{ warning }}
              </li>
            </ul>
          </div>
          <div v-if="validationResults[transistor.metadata.name].errors.length === 0" class="success">
            ✓ Validation passed
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { transistorApi } from '../services/api.js'

const props = defineProps({
  transistors: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'create'])

const searchQuery = ref('')
const validationResults = ref({})

const filteredTransistors = computed(() => {
  if (!searchQuery.value) return props.transistors
  
  const query = searchQuery.value.toLowerCase()
  return props.transistors.filter(transistor => 
    transistor.metadata.name.toLowerCase().includes(query) ||
    transistor.metadata.type.toLowerCase().includes(query) ||
    transistor.metadata.manufacturer.toLowerCase().includes(query)
  )
})

async function validateTransistor(transistor) {
  try {
    const transistorId = transistor.metadata.name.replace(' ', '_').replace('/', '_')
    const result = await transistorApi.validate(transistorId)
    validationResults.value[transistor.metadata.name] = result
  } catch (error) {
    console.error('Validation error:', error)
  }
}

async function exportTransistor(transistor, format) {
  try {
    const transistorId = transistor.metadata.name.replace(' ', '_').replace('/', '_')
    const blob = await transistorApi.export(transistorId, format)
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${transistor.metadata.name}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Export error:', error)
  }
}

function deleteTransistor(transistor) {
  if (confirm(`Are you sure you want to delete ${transistor.metadata.name}?`)) {
    const transistorId = transistor.metadata.name.replace(' ', '_').replace('/', '_')
    emit('delete', transistorId)
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  try {
    await transistorApi.upload(file)
    // Reset file input
    event.target.value = ''
    // Trigger parent to reload data
    emit('create')
  } catch (error) {
    console.error('Upload error:', error)
    alert('Failed to upload file. Please check the file format.')
  }
}
</script>

<style scoped>
.transistor-list {
  padding: 1rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #eee;
}

.list-header h2 {
  margin: 0;
  color: #2c3e50;
}

.list-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 200px;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.empty-state a {
  color: #3498db;
  text-decoration: none;
}

.transistor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.transistor-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  transition: transform 0.2s;
}

.transistor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.card-header {
  background: #3498db;
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.card-content {
  padding: 1rem;
}

.transistor-info {
  margin-bottom: 1rem;
}

.info-group {
  display: flex;
  margin-bottom: 0.5rem;
}

.info-group label {
  font-weight: bold;
  width: 100px;
  color: #555;
}

.transistor-specs h4 {
  color: #2c3e50;
  margin: 1rem 0 0.5rem 0;
  font-size: 1rem;
}

.specs-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.spec-item {
  display: flex;
  justify-content: space-between;
}

.spec-item label {
  font-weight: bold;
  color: #555;
}

.validation-results {
  border-top: 1px solid #eee;
  padding: 1rem;
  background: #f9f9f9;
}

.validation-results h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.errors {
  color: #e74c3c;
}

.warnings {
  color: #f39c12;
}

.success {
  color: #27ae60;
  font-weight: bold;
}

.errors ul, .warnings ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

/* Button styles */
.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s;
}

.btn-small {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-danger:hover {
  background: #c0392b;
}
</style>
