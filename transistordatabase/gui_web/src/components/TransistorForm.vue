<template>
  <div class="transistor-form">
    <div class="form-header">
      <h2>{{ isEditing ? 'Edit Transistor' : 'Create New Transistor' }}</h2>
      <button @click="$emit('cancel')" class="btn btn-secondary">Cancel</button>
    </div>

    <form @submit.prevent="handleSubmit" class="form-content">
      <div class="form-section">
        <h3>Metadata</h3>
        <div class="form-grid">
          <div class="form-group">
            <label for="name">Name *</label>
            <input 
              id="name"
              v-model="formData.metadata.name" 
              type="text" 
              required 
              placeholder="e.g. IGBT_1200V_100A"
            />
          </div>

          <div class="form-group">
            <label for="type">Type *</label>
            <select id="type" v-model="formData.metadata.type" required>
              <option value="">Select type</option>
              <option value="IGBT">IGBT</option>
              <option value="MOSFET">MOSFET</option>
              <option value="BJT">BJT</option>
              <option value="Diode">Diode</option>
            </select>
          </div>

          <div class="form-group">
            <label for="manufacturer">Manufacturer *</label>
            <input 
              id="manufacturer"
              v-model="formData.metadata.manufacturer" 
              type="text" 
              required 
              placeholder="e.g. Infineon, Rohm, etc."
            />
          </div>

          <div class="form-group">
            <label for="housing">Housing Type *</label>
            <select id="housing" v-model="formData.metadata.housing_type" required>
              <option value="">Select housing</option>
              <option value="TO-247">TO-247</option>
              <option value="TO-220">TO-220</option>
              <option value="TO-252">TO-252</option>
              <option value="SO-8">SO-8</option>
              <option value="SOT-23">SOT-23</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div class="form-group">
            <label for="author">Author</label>
            <input 
              id="author"
              v-model="formData.metadata.author" 
              type="text" 
              placeholder="Optional"
            />
          </div>

          <div class="form-group form-group-wide">
            <label for="comment">Comment</label>
            <textarea 
              id="comment"
              v-model="formData.metadata.comment" 
              placeholder="Optional comments or notes"
              rows="3"
            ></textarea>
          </div>
        </div>
      </div>

      <div class="form-section">
        <h3>Electrical Ratings</h3>
        <div class="form-grid">
          <div class="form-group">
            <label for="v_abs_max">V<sub>abs,max</sub> (V) *</label>
            <input 
              id="v_abs_max"
              v-model.number="formData.electrical.v_abs_max" 
              type="number" 
              step="0.1" 
              min="0"
              required 
              placeholder="e.g. 1200"
            />
          </div>

          <div class="form-group">
            <label for="i_abs_max">I<sub>abs,max</sub> (A) *</label>
            <input 
              id="i_abs_max"
              v-model.number="formData.electrical.i_abs_max" 
              type="number" 
              step="0.1" 
              min="0"
              required 
              placeholder="e.g. 100"
            />
          </div>

          <div class="form-group">
            <label for="i_cont">I<sub>cont</sub> (A) *</label>
            <input 
              id="i_cont"
              v-model.number="formData.electrical.i_cont" 
              type="number" 
              step="0.1" 
              min="0"
              required 
              placeholder="e.g. 80"
            />
          </div>

          <div class="form-group">
            <label for="t_j_max">T<sub>j,max</sub> (°C) *</label>
            <input 
              id="t_j_max"
              v-model.number="formData.electrical.t_j_max" 
              type="number" 
              step="0.1"
              required 
              placeholder="e.g. 175"
            />
          </div>
        </div>
      </div>

      <div class="form-section">
        <h3>Thermal Properties</h3>
        <div class="form-grid">
          <div class="form-group">
            <label for="r_th_cs">R<sub>th,cs</sub> (K/W) *</label>
            <input 
              id="r_th_cs"
              v-model.number="formData.thermal.r_th_cs" 
              type="number" 
              step="0.001" 
              min="0"
              required 
              placeholder="e.g. 0.5"
            />
          </div>

          <div class="form-group">
            <label for="housing_area">Housing Area (cm²) *</label>
            <input 
              id="housing_area"
              v-model.number="formData.thermal.housing_area" 
              type="number" 
              step="0.1" 
              min="0"
              required 
              placeholder="e.g. 1.0"
            />
          </div>

          <div class="form-group">
            <label for="cooling_area">Cooling Area (cm²) *</label>
            <input 
              id="cooling_area"
              v-model.number="formData.thermal.cooling_area" 
              type="number" 
              step="0.1" 
              min="0"
              required 
              placeholder="e.g. 1.0"
            />
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" @click="$emit('cancel')" class="btn btn-secondary">
          Cancel
        </button>
        <button type="button" @click="validateForm" class="btn btn-secondary">
          Validate
        </button>
        <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
          {{ isSubmitting ? 'Saving...' : (isEditing ? 'Update' : 'Create') }}
        </button>
      </div>
    </form>

    <div v-if="validationResult" class="validation-section">
      <h3>Validation Results</h3>
      <div v-if="validationResult.errors && validationResult.errors.length > 0" class="errors">
        <h4>Errors:</h4>
        <ul>
          <li v-for="error in validationResult.errors" :key="error">{{ error }}</li>
        </ul>
      </div>
      <div v-if="validationResult.warnings && validationResult.warnings.length > 0" class="warnings">
        <h4>Warnings:</h4>
        <ul>
          <li v-for="warning in validationResult.warnings" :key="warning">{{ warning }}</li>
        </ul>
      </div>
      <div v-if="(!validationResult.errors || validationResult.errors.length === 0)" class="success">
        ✓ Validation passed successfully
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { transistorApi } from '../services/api.js'

const props = defineProps({
  transistor: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['saved', 'cancel'])

const isEditing = ref(false)
const isSubmitting = ref(false)
const validationResult = ref(null)

const formData = reactive({
  metadata: {
    name: '',
    type: '',
    manufacturer: '',
    housing_type: '',
    author: '',
    comment: ''
  },
  electrical: {
    v_abs_max: 0,
    i_abs_max: 0,
    i_cont: 0,
    t_j_max: 0
  },
  thermal: {
    r_th_cs: 0,
    housing_area: 0,
    cooling_area: 0
  }
})

onMounted(() => {
  if (props.transistor) {
    isEditing.value = true
    // Populate form with existing data
    Object.assign(formData.metadata, props.transistor.metadata)
    Object.assign(formData.electrical, props.transistor.electrical)
    Object.assign(formData.thermal, props.transistor.thermal)
  }
})

async function validateForm() {
  try {
    // Create a temporary transistor to validate
    if (isEditing.value) {
      const transistorId = props.transistor.metadata.name.replace(' ', '_').replace('/', '_')
      validationResult.value = await transistorApi.validate(transistorId)
    } else {
      // For new transistors, we can implement client-side basic validation
      const errors = []
      const warnings = []

      // Basic validation
      if (!formData.metadata.name.trim()) errors.push('Name is required')
      if (!formData.metadata.type) errors.push('Type is required')
      if (!formData.metadata.manufacturer.trim()) errors.push('Manufacturer is required')
      if (!formData.metadata.housing_type) errors.push('Housing type is required')
      
      if (formData.electrical.v_abs_max <= 0) errors.push('V_abs_max must be positive')
      if (formData.electrical.i_abs_max <= 0) errors.push('I_abs_max must be positive')
      if (formData.electrical.i_cont <= 0) errors.push('I_cont must be positive')
      if (formData.electrical.i_cont > formData.electrical.i_abs_max) {
        warnings.push('I_cont is greater than I_abs_max')
      }
      
      if (formData.thermal.r_th_cs <= 0) errors.push('R_th_cs must be positive')
      if (formData.thermal.housing_area <= 0) errors.push('Housing area must be positive')
      if (formData.thermal.cooling_area <= 0) errors.push('Cooling area must be positive')

      validationResult.value = { errors, warnings }
    }
  } catch (error) {
    console.error('Validation error:', error)
    validationResult.value = { 
      errors: ['Validation failed: ' + error.message], 
      warnings: [] 
    }
  }
}

async function handleSubmit() {
  isSubmitting.value = true
  
  try {
    if (isEditing.value) {
      const transistorId = props.transistor.metadata.name.replace(' ', '_').replace('/', '_')
      await transistorApi.update(transistorId, formData)
    } else {
      await transistorApi.create(formData)
    }
    
    emit('saved')
  } catch (error) {
    console.error('Save error:', error)
    alert('Failed to save transistor: ' + error.message)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.transistor-form {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.form-header {
  background: #3498db;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-header h2 {
  margin: 0;
}

.form-content {
  padding: 2rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h3 {
  color: #2c3e50;
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #eee;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group-wide {
  grid-column: 1 / -1;
}

.form-group label {
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #555;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.validation-section {
  padding: 1rem 2rem 2rem;
  background: #f9f9f9;
  border-top: 1px solid #eee;
}

.validation-section h3 {
  color: #2c3e50;
  margin: 0 0 1rem 0;
}

.errors {
  color: #e74c3c;
  margin-bottom: 1rem;
}

.warnings {
  color: #f39c12;
  margin-bottom: 1rem;
}

.success {
  color: #27ae60;
  font-weight: bold;
}

.errors h4, .warnings h4 {
  margin: 0 0 0.5rem 0;
}

.errors ul, .warnings ul {
  margin: 0;
  padding-left: 1.5rem;
}

/* Button styles */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
  text-decoration: none;
  display: inline-block;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

/* Responsive design */
@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-header {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
