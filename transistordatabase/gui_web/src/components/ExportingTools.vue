<template>
  <div class="exporting-tools">
    <div class="export-header">
      <h2>📤 Exporting Tools</h2>
      <div class="export-actions">
        <button @click="clearAll" class="btn btn-secondary">
          🗑️ Clear All
        </button>
        <button @click="loadExample" class="btn btn-info">
          📝 Load Example
        </button>
      </div>
    </div>

    <div class="export-content">
      <!-- Transistor Selection Panel -->
      <div class="selection-panel">
        <h3>🎯 Transistor Selection</h3>
        
        <div class="current-selection" v-if="selectedTransistors.length > 0">
          <h4>Selected Transistors ({{ selectedTransistors.length }})</h4>
          <div class="selected-list">
            <div 
              v-for="(transistor, index) in selectedTransistors" 
              :key="transistor.metadata.name"
              class="selected-item"
            >
              <div class="item-info">
                <strong>{{ transistor.metadata.name }}</strong>
                <span class="manufacturer">{{ transistor.metadata.manufacturer }}</span>
                <span :class="['type-badge', transistor.metadata.type.toLowerCase()]">
                  {{ transistor.metadata.type }}
                </span>
              </div>
              <button @click="removeTransistor(index)" class="btn btn-sm btn-danger">
                ❌
              </button>
            </div>
          </div>
        </div>

        <div class="selection-actions">
          <button @click="$emit('open-database-search')" class="btn btn-primary">
            🔍 Search Database
          </button>
          <div class="file-upload">
            <input 
              type="file" 
              ref="fileInput"
              @change="loadFromFile"
              accept=".json"
              style="display: none"
            />
            <button @click="triggerFileInput" class="btn btn-secondary">
              📁 Load from File
            </button>
          </div>
        </div>
      </div>

      <!-- Export Formats Panel -->
      <div class="formats-panel">
        <h3>🛠️ Export Formats</h3>
        
        <div class="format-tabs">
          <button 
            v-for="format in exportFormats" 
            :key="format.id"
            @click="activeFormat = format.id"
            :class="['format-tab', { active: activeFormat === format.id }]"
          >
            {{ format.icon }} {{ format.name }}
          </button>
        </div>

        <div class="format-content">
          <!-- MATLAB Export -->
          <div v-if="activeFormat === 'matlab'" class="format-section">
            <h4>📊 MATLAB Export Settings</h4>
            <div class="export-options">
              <div class="option-group">
                <label>
                  <input type="checkbox" v-model="matlabOptions.includeMetadata" />
                  Include Metadata
                </label>
                <label>
                  <input type="checkbox" v-model="matlabOptions.includeCharacteristics" />
                  Include Electrical Characteristics
                </label>
                <label>
                  <input type="checkbox" v-model="matlabOptions.includeThermal" />
                  Include Thermal Properties
                </label>
                <label>
                  <input type="checkbox" v-model="matlabOptions.createStructArray" />
                  Create Struct Array
                </label>
              </div>
              <div class="option-group">
                <label>Variable Name:</label>
                <input 
                  type="text" 
                  v-model="matlabOptions.variableName" 
                  placeholder="transistor_data"
                />
              </div>
            </div>
            <div class="export-preview">
              <h5>Preview:</h5>
              <pre>{{ generateMatlabPreview() }}</pre>
            </div>
            <button @click="exportToMatlab" :disabled="selectedTransistors.length === 0" class="btn btn-primary">
              📊 Export to MATLAB (.m)
            </button>
          </div>

          <!-- Simulink Export -->
          <div v-if="activeFormat === 'simulink'" class="format-section">
            <h4>🔗 Simulink Export Settings</h4>
            <div class="export-options">
              <div class="option-group">
                <label>Model Type:</label>
                <select v-model="simulinkOptions.modelType">
                  <option value="lookup_table">Lookup Table</option>
                  <option value="thermal_model">Thermal Model</option>
                  <option value="switching_model">Switching Model</option>
                  <option value="complete_model">Complete Model</option>
                </select>
              </div>
              <div class="option-group">
                <label>
                  <input type="checkbox" v-model="simulinkOptions.includeTemperatureDependence" />
                  Include Temperature Dependence
                </label>
                <label>
                  <input type="checkbox" v-model="simulinkOptions.includeLosses" />
                  Include Switching Losses
                </label>
                <label>
                  <input type="checkbox" v-model="simulinkOptions.includeSOA" />
                  Include Safe Operating Area
                </label>
              </div>
            </div>
            <button @click="exportToSimulink" :disabled="selectedTransistors.length === 0" class="btn btn-primary">
              🔗 Export to Simulink (.slx)
            </button>
          </div>

          <!-- PLECS Export -->
          <div v-if="activeFormat === 'plecs'" class="format-section">
            <h4>⚡ PLECS Export Settings</h4>
            <div class="export-options">
              <div class="option-group">
                <label>Component Type:</label>
                <select v-model="plecsOptions.componentType">
                  <option value="mosfet">MOSFET</option>
                  <option value="igbt">IGBT</option>
                  <option value="diode">Diode</option>
                  <option value="thermal">Thermal Network</option>
                </select>
              </div>
              <div class="option-group">
                <label>
                  <input type="checkbox" v-model="plecsOptions.includeThermalNetwork" />
                  Include Thermal Network
                </label>
                <label>
                  <input type="checkbox" v-model="plecsOptions.includeLossModel" />
                  Include Loss Model
                </label>
                <label>
                  <input type="checkbox" v-model="plecsOptions.includeCapacitances" />
                  Include Parasitic Capacitances
                </label>
              </div>
            </div>
            <button @click="exportToPlecs" :disabled="selectedTransistors.length === 0" class="btn btn-primary">
              ⚡ Export to PLECS (.xml)
            </button>
          </div>

          <!-- GeckoCIRCUITS Export -->
          <div v-if="activeFormat === 'geckocircuits'" class="format-section">
            <h4>🦎 GeckoCIRCUITS Export Settings</h4>
            <div class="export-options">
              <div class="option-group">
                <label>Circuit Type:</label>
                <select v-model="geckoOptions.circuitType">
                  <option value="power_mosfet">Power MOSFET</option>
                  <option value="igbt_diode">IGBT + Diode</option>
                  <option value="thermal_only">Thermal Model Only</option>
                </select>
              </div>
              <div class="option-group">
                <label>
                  <input type="checkbox" v-model="geckoOptions.includeGateDriver" />
                  Include Gate Driver Model
                </label>
                <label>
                  <input type="checkbox" v-model="geckoOptions.includeThermalCoupling" />
                  Include Thermal Coupling
                </label>
              </div>
            </div>
            <button @click="exportToGeckoCIRCUITS" :disabled="selectedTransistors.length === 0" class="btn btn-primary">
              🦎 Export to GeckoCIRCUITS (.ipe)
            </button>
          </div>

          <!-- SPICE Export -->
          <div v-if="activeFormat === 'spice'" class="format-section">
            <h4>🔌 SPICE Export Settings</h4>
            <div class="export-options">
              <div class="option-group">
                <label>SPICE Variant:</label>
                <select v-model="spiceOptions.variant">
                  <option value="ngspice">NGSpice</option>
                  <option value="ltspice">LTSpice</option>
                  <option value="pspice">PSpice</option>
                  <option value="hspice">HSPICE</option>
                </select>
              </div>
              <div class="option-group">
                <label>Model Type:</label>
                <select v-model="spiceOptions.modelType">
                  <option value="level1">Level 1 (Basic)</option>
                  <option value="level3">Level 3 (Advanced)</option>
                  <option value="bsim">BSIM Model</option>
                  <option value="thermal">Thermal Subcircuit</option>
                </select>
              </div>
              <div class="option-group">
                <label>
                  <input type="checkbox" v-model="spiceOptions.includeTemperatureModel" />
                  Include Temperature Model
                </label>
                <label>
                  <input type="checkbox" v-model="spiceOptions.includeParasitics" />
                  Include Parasitic Elements
                </label>
              </div>
            </div>
            <button @click="exportToSpice" :disabled="selectedTransistors.length === 0" class="btn btn-primary">
              🔌 Export to SPICE (.cir)
            </button>
          </div>

          <!-- JSON Export -->
          <div v-if="activeFormat === 'json'" class="format-section">
            <h4>📋 JSON Export Settings</h4>
            <div class="export-options">
              <div class="option-group">
                <label>Format:</label>
                <select v-model="jsonOptions.format">
                  <option value="tdb">Transistor Database Format</option>
                  <option value="minimal">Minimal (Key properties only)</option>
                  <option value="complete">Complete (All data)</option>
                  <option value="custom">Custom Selection</option>
                </select>
              </div>
              <div v-if="jsonOptions.format === 'custom'" class="option-group">
                <label>Include Sections:</label>
                <div class="checkbox-grid">
                  <label><input type="checkbox" v-model="jsonOptions.includeMetadata" /> Metadata</label>
                  <label><input type="checkbox" v-model="jsonOptions.includeElectrical" /> Electrical</label>
                  <label><input type="checkbox" v-model="jsonOptions.includeThermal" /> Thermal</label>
                  <label><input type="checkbox" v-model="jsonOptions.includeCurves" /> Characteristic Curves</label>
                </div>
              </div>
              <div class="option-group">
                <label>
                  <input type="checkbox" v-model="jsonOptions.prettify" />
                  Pretty Print (Formatted)
                </label>
              </div>
            </div>
            <button @click="exportToJson" :disabled="selectedTransistors.length === 0" class="btn btn-primary">
              📋 Export to JSON
            </button>
          </div>
        </div>
      </div>

      <!-- Export History Panel -->
      <div class="history-panel">
        <h3>📋 Export History</h3>
        <div class="history-list">
          <div 
            v-for="(export_item, index) in exportHistory" 
            :key="index"
            class="history-item"
          >
            <div class="history-info">
              <strong>{{ export_item.format }}</strong>
              <span class="timestamp">{{ formatTimestamp(export_item.timestamp) }}</span>
              <span class="count">{{ export_item.count }} transistors</span>
            </div>
            <div class="history-actions">
              <button @click="reExport(export_item)" class="btn btn-sm btn-secondary">
                🔄 Re-export
              </button>
              <button @click="removeFromHistory(index)" class="btn btn-sm btn-danger">
                🗑️
              </button>
            </div>
          </div>
        </div>
        <div v-if="exportHistory.length === 0" class="no-history">
          No export history yet. Export some transistors to see them here!
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  transistors: Array,
  selectedFromSearch: Array
})

const emit = defineEmits(['open-database-search'])

// State
const selectedTransistors = ref([])
const activeFormat = ref('matlab')
const exportHistory = ref([])
const fileInput = ref(null)

// Export format definitions
const exportFormats = ref([
  { id: 'matlab', name: 'MATLAB', icon: '📊' },
  { id: 'simulink', name: 'Simulink', icon: '🔗' },
  { id: 'plecs', name: 'PLECS', icon: '⚡' },
  { id: 'geckocircuits', name: 'GeckoCIRCUITS', icon: '🦎' },
  { id: 'spice', name: 'SPICE', icon: '🔌' },
  { id: 'json', name: 'JSON', icon: '📋' }
])

// Export options
const matlabOptions = ref({
  includeMetadata: true,
  includeCharacteristics: true,
  includeThermal: true,
  createStructArray: true,
  variableName: 'transistor_data'
})

const simulinkOptions = ref({
  modelType: 'lookup_table',
  includeTemperatureDependence: true,
  includeLosses: true,
  includeSOA: false
})

const plecsOptions = ref({
  componentType: 'mosfet',
  includeThermalNetwork: true,
  includeLossModel: true,
  includeCapacitances: false
})

const geckoOptions = ref({
  circuitType: 'power_mosfet',
  includeGateDriver: false,
  includeThermalCoupling: true
})

const spiceOptions = ref({
  variant: 'ngspice',
  modelType: 'level3',
  includeTemperatureModel: true,
  includeParasitics: false
})

const jsonOptions = ref({
  format: 'tdb',
  prettify: true,
  includeMetadata: true,
  includeElectrical: true,
  includeThermal: true,
  includeCurves: true
})

// Methods
function addTransistor(transistor) {
  if (!selectedTransistors.value.find(t => t.metadata.name === transistor.metadata.name)) {
    selectedTransistors.value.push(transistor)
  }
}

function removeTransistor(index) {
  selectedTransistors.value.splice(index, 1)
}

function clearAll() {
  selectedTransistors.value = []
}

function loadExample() {
  if (props.transistors && props.transistors.length > 0) {
    // Load first 3 transistors as example
    selectedTransistors.value = props.transistors.slice(0, 3)
  }
}

function triggerFileInput() {
  console.log('Triggering file input...')
  if (fileInput.value) {
    fileInput.value.click()
    console.log('File input clicked')
  } else {
    console.error('File input ref not found')
  }
}

function loadFromFile(event) {
  const file = event.target.files[0]
  if (!file) {
    console.log('No file selected')
    return
  }
  
  console.log('Loading file:', file.name, 'Size:', file.size, 'Type:', file.type)
  
  if (!file.name.toLowerCase().endsWith('.json')) {
    alert('Please select a JSON file (.json)')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      console.log('File content loaded, parsing JSON...')
      const data = JSON.parse(e.target.result)
      console.log('Parsed data:', data)
      
      let loadedTransistors = []
      
      if (Array.isArray(data)) {
        loadedTransistors = data
        console.log('Loaded array of', data.length, 'transistors')
      } else if (data.metadata && data.metadata.name) {
        // Standard format with nested metadata
        loadedTransistors = [data]
        console.log('Loaded single transistor (nested format):', data.metadata.name)
      } else if (data.name && data.type) {
        // TDB format with flat structure - convert to nested format
        console.log('Converting TDB format to nested format...')
        const convertedData = {
          metadata: {
            name: data.name,
            manufacturer: data.manufacturer || 'Unknown',
            datasheet: data.datasheet || '',
            type: data.type,
            technology: data.technology || '',
            housing_type: data.housing_type || data.housing || '',
            author: data.author || '',
            comment: data.comment || ''
          },
          electrical: {
            v_abs_max: data.v_abs_max || 0,
            i_abs_max: data.i_abs_max || 0,
            i_cont: data.i_cont || data.i_abs_max || 0,
            r_ds_on: data.r_ds_on || 0,
            v_gs_th: data.v_gs_th || 0,
            c_oss: data.c_oss || 0,
            c_iss: data.c_iss || 0,
            c_rss: data.c_rss || 0
          },
          thermal: {
            r_th_jc: data.r_th_jc || 0,
            r_th_cs: data.r_th_cs || 0,
            t_j_max: data.t_j_max || 0
          }
        }
        loadedTransistors = [convertedData]
        console.log('Loaded single transistor (TDB format):', data.name)
      } else {
        throw new Error('Invalid file format. Expected transistor data with either:\n- metadata.name property (nested format)\n- name and type properties (TDB format)')
      }
      
      selectedTransistors.value = loadedTransistors
      alert(`Successfully loaded ${loadedTransistors.length} transistor(s) from file!`)
      
    } catch (error) {
      console.error('Error parsing file:', error)
      alert('Error reading file: ' + error.message + '\n\nPlease ensure the file contains valid transistor JSON data.')
    }
  }
  
  reader.onerror = () => {
    console.error('Error reading file')
    alert('Error reading file. Please try again.')
  }
  
  reader.readAsText(file)
}

function generateMatlabPreview() {
  if (selectedTransistors.value.length === 0) {
    return '% No transistors selected'
  }
  
  const transistor = selectedTransistors.value[0]
  return `% MATLAB Export Preview
${matlabOptions.value.variableName}(1).name = '${transistor.metadata.name}';
${matlabOptions.value.variableName}(1).manufacturer = '${transistor.metadata.manufacturer}';
${matlabOptions.value.variableName}(1).v_abs_max = ${transistor.electrical.v_abs_max};
${matlabOptions.value.variableName}(1).i_abs_max = ${transistor.electrical.i_abs_max};
% ... (${selectedTransistors.value.length} transistors total)`
}

function exportToMatlab() {
  const timestamp = new Date().toISOString()
  let matlabCode = `% Transistor Database Export\n% Generated: ${timestamp}\n% Total transistors: ${selectedTransistors.value.length}\n\n`
  
  selectedTransistors.value.forEach((transistor, index) => {
    const idx = index + 1
    const varName = matlabOptions.value.variableName
    
    if (matlabOptions.value.includeMetadata) {
      matlabCode += `${varName}(${idx}).name = '${transistor.metadata.name}';\n`
      matlabCode += `${varName}(${idx}).manufacturer = '${transistor.metadata.manufacturer}';\n`
      matlabCode += `${varName}(${idx}).type = '${transistor.metadata.type}';\n`
      matlabCode += `${varName}(${idx}).housing_type = '${transistor.metadata.housing_type}';\n`
    }
    
    if (matlabOptions.value.includeCharacteristics) {
      matlabCode += `${varName}(${idx}).v_abs_max = ${transistor.electrical.v_abs_max};\n`
      matlabCode += `${varName}(${idx}).i_abs_max = ${transistor.electrical.i_abs_max};\n`
      if (transistor.electrical.i_cont) {
        matlabCode += `${varName}(${idx}).i_cont = ${transistor.electrical.i_cont};\n`
      }
    }
    
    if (matlabOptions.value.includeThermal) {
      matlabCode += `${varName}(${idx}).r_th_cs = ${transistor.thermal.r_th_cs};\n`
      matlabCode += `${varName}(${idx}).t_j_max = ${transistor.thermal.t_j_max};\n`
    }
    
    matlabCode += '\n'
  })
  
  downloadFile(matlabCode, `${matlabOptions.value.variableName}_export.m`, 'text/plain')
  addToHistory('MATLAB', selectedTransistors.value.length)
}

function exportToSimulink() {
  // Generate Simulink XML format
  const xmlContent = generateSimulinkXML()
  downloadFile(xmlContent, 'transistor_model.xml', 'text/xml')
  addToHistory('Simulink', selectedTransistors.value.length)
}

function exportToPlecs() {
  // Generate PLECS XML format
  const xmlContent = generatePlecsXML()
  downloadFile(xmlContent, 'transistor_plecs.xml', 'text/xml')
  addToHistory('PLECS', selectedTransistors.value.length)
}

function exportToGeckoCIRCUITS() {
  // Generate GeckoCIRCUITS IPE format
  const ipeContent = generateGeckoIPE()
  downloadFile(ipeContent, 'transistor_gecko.ipe', 'text/plain')
  addToHistory('GeckoCIRCUITS', selectedTransistors.value.length)
}

function exportToSpice() {
  // Generate SPICE netlist
  const spiceContent = generateSpiceNetlist()
  downloadFile(spiceContent, 'transistor_models.cir', 'text/plain')
  addToHistory('SPICE', selectedTransistors.value.length)
}

function exportToJson() {
  let data
  
  switch (jsonOptions.value.format) {
    case 'minimal':
      data = selectedTransistors.value.map(t => ({
        name: t.metadata.name,
        manufacturer: t.metadata.manufacturer,
        type: t.metadata.type,
        v_max: t.electrical.v_abs_max,
        i_max: t.electrical.i_abs_max
      }))
      break
    case 'custom':
      data = selectedTransistors.value.map(t => {
        const result = {}
        if (jsonOptions.value.includeMetadata) result.metadata = t.metadata
        if (jsonOptions.value.includeElectrical) result.electrical = t.electrical
        if (jsonOptions.value.includeThermal) result.thermal = t.thermal
        if (jsonOptions.value.includeCurves && t.curves) result.curves = t.curves
        return result
      })
      break
    default:
      data = selectedTransistors.value
  }
  
  const jsonString = jsonOptions.value.prettify 
    ? JSON.stringify(data, null, 2)
    : JSON.stringify(data)
  
  downloadFile(jsonString, 'transistor_export.json', 'application/json')
  addToHistory('JSON', selectedTransistors.value.length)
}

function generateSimulinkXML() {
  // Simplified Simulink XML generation
  return `<?xml version="1.0" encoding="UTF-8"?>
<SimulinkModel>
  <ModelSettings>
    <Name>TransistorModel</Name>
    <Type>${simulinkOptions.value.modelType}</Type>
  </ModelSettings>
  <Components>
    ${selectedTransistors.value.map(t => `
    <Transistor>
      <Name>${t.metadata.name}</Name>
      <Type>${t.metadata.type}</Type>
      <VMax>${t.electrical.v_abs_max}</VMax>
      <IMax>${t.electrical.i_abs_max}</IMax>
      <RthCS>${t.thermal.r_th_cs}</RthCS>
    </Transistor>`).join('')}
  </Components>
</SimulinkModel>`
}

function generatePlecsXML() {
  return `<?xml version="1.0" encoding="UTF-8"?>
<PlecsThermalDescription>
  ${selectedTransistors.value.map(t => `
  <ThermalModel name="${t.metadata.name}">
    <RthCS>${t.thermal.r_th_cs}</RthCS>
    <TjMax>${t.thermal.t_j_max}</TjMax>
    <Type>${t.metadata.type}</Type>
  </ThermalModel>`).join('')}
</PlecsThermalDescription>`
}

function generateGeckoIPE() {
  return selectedTransistors.value.map(t => `
; GeckoCIRCUITS Component: ${t.metadata.name}
.model ${t.metadata.name} ${t.metadata.type.toLowerCase()}
+ vt0=${t.electrical.v_abs_max}
+ it0=${t.electrical.i_abs_max}
+ rth=${t.thermal.r_th_cs}
+ tjmax=${t.thermal.t_j_max}
`).join('\n')
}

function generateSpiceNetlist() {
  const header = `* SPICE Transistor Models
* Generated: ${new Date().toISOString()}
* Variant: ${spiceOptions.value.variant}
* Model Type: ${spiceOptions.value.modelType}

`
  
  const models = selectedTransistors.value.map(t => {
    const modelName = t.metadata.name.replace(/[^a-zA-Z0-9_]/g, '_')
    return `.model ${modelName} NMOS (
+ VTO=4.0
+ KP=${(t.electrical.i_abs_max / Math.pow(t.electrical.v_abs_max, 2) * 1000).toFixed(6)}
+ LAMBDA=0.01
+ RDS=${(1 / t.electrical.i_abs_max * 100).toFixed(6)}
+ CGS=${(t.electrical.v_abs_max * 1e-9).toFixed(2)}p
+ CGD=${(t.electrical.v_abs_max * 0.5e-9).toFixed(2)}p
+ IS=1e-14
+ RS=0.001
+ RD=0.001
)`
  }).join('\n\n')
  
  return header + models
}

function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function addToHistory(format, count) {
  exportHistory.value.unshift({
    format,
    count,
    timestamp: Date.now(),
    options: getOptionsForFormat(format)
  })
  
  // Keep only last 10 exports
  if (exportHistory.value.length > 10) {
    exportHistory.value = exportHistory.value.slice(0, 10)
  }
}

function getOptionsForFormat(format) {
  switch (format) {
    case 'MATLAB': return { ...matlabOptions.value }
    case 'Simulink': return { ...simulinkOptions.value }
    case 'PLECS': return { ...plecsOptions.value }
    case 'GeckoCIRCUITS': return { ...geckoOptions.value }
    case 'SPICE': return { ...spiceOptions.value }
    case 'JSON': return { ...jsonOptions.value }
    default: return {}
  }
}

function reExport(exportItem) {
  // Restore options and re-export
  switch (exportItem.format) {
    case 'MATLAB':
      Object.assign(matlabOptions.value, exportItem.options)
      activeFormat.value = 'matlab'
      break
    case 'Simulink':
      Object.assign(simulinkOptions.value, exportItem.options)
      activeFormat.value = 'simulink'
      break
    // Add other cases...
  }
}

function removeFromHistory(index) {
  exportHistory.value.splice(index, 1)
}

function formatTimestamp(timestamp) {
  return new Date(timestamp).toLocaleString()
}

// Watch for transistors selected from search
watch(() => props.selectedFromSearch, (newSelection) => {
  if (newSelection && newSelection.length > 0) {
    newSelection.forEach(transistor => addTransistor(transistor))
  }
}, { immediate: true })

// Load history from localStorage on mount
onMounted(() => {
  const savedHistory = localStorage.getItem('exportHistory')
  if (savedHistory) {
    try {
      exportHistory.value = JSON.parse(savedHistory)
    } catch (e) {
      console.error('Error loading export history:', e)
    }
  }
})

// Save history to localStorage whenever it changes
watch(exportHistory, (newHistory) => {
  localStorage.setItem('exportHistory', JSON.stringify(newHistory))
}, { deep: true })

// Expose methods for parent component
defineExpose({
  addTransistor,
  clearAll
})
</script>

<style scoped>
/* Dark theme CSS variables support */
.exporting-tools {
  --bg-primary: #f5f5f5;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f8f9fa;
  --text-primary: #333;
  --text-secondary: #666;
  --text-muted: #999;
  --border-color: #e1e5e9;
  --shadow: rgba(0,0,0,0.1);
  --accent-blue: #007bff;
  --accent-blue-light: #f8f9ff;
}

:global(.dark-theme) .exporting-tools {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --bg-tertiary: #3a3a3a;
  --text-primary: #e0e0e0;
  --text-secondary: #b0b0b0;
  --text-muted: #888;
  --border-color: #404040;
  --shadow: rgba(0,0,0,0.3);
  --accent-blue: #4a9eff;
  --accent-blue-light: #1a2332;
}

.exporting-tools {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

.export-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
}

.export-actions {
  display: flex;
  gap: 1rem;
}

.export-content {
  display: grid;
  grid-template-columns: 300px 1fr 300px;
  gap: 2rem;
}

.selection-panel,
.formats-panel,
.history-panel {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: fit-content;
}

.selection-panel h3,
.formats-panel h3,
.history-panel h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.5rem;
}

.current-selection h4 {
  margin: 0 0 1rem 0;
  color: #555;
}

.selected-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.selected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.item-info strong {
  color: #2c3e50;
  font-size: 0.9rem;
}

.manufacturer {
  color: #666;
  font-size: 0.8rem;
}

.type-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  width: fit-content;
}

.type-badge.igbt {
  background: #e3f2fd;
  color: #1976d2;
}

.type-badge.mosfet,
.type-badge.sic-mosfet {
  background: #f3e5f5;
  color: #7b1fa2;
}

.type-badge.diode {
  background: #e8f5e8;
  color: #388e3c;
}

.selection-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-upload {
  display: flex;
}

.format-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 1rem;
}

.format-tab {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color, #ddd);
  background: var(--bg-tertiary, #f8f9fa);
  color: var(--text-primary, #333);
  border-radius: 4px 4px 0 0;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.format-tab:hover {
  background: var(--bg-secondary, #e9ecef);
  color: var(--text-primary, #333);
}

.format-tab.active {
  background: var(--accent-blue, #007bff);
  color: white;
  border-color: var(--accent-blue, #007bff);
}

.format-content {
  min-height: 400px;
}

.format-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.export-options {
  margin-bottom: 2rem;
}

.option-group {
  margin-bottom: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.option-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #555;
}

.option-group input[type="text"],
.option-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-top: 0.5rem;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.export-preview {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.export-preview h5 {
  margin: 0 0 0.5rem 0;
  color: #555;
}

.export-preview pre {
  margin: 0;
  font-size: 0.8rem;
  color: #333;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #28a745;
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.history-info strong {
  color: #2c3e50;
  font-size: 0.9rem;
}

.timestamp,
.count {
  color: #666;
  font-size: 0.8rem;
}

.history-actions {
  display: flex;
  gap: 0.5rem;
}

.no-history {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 2rem;
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

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

@media (max-width: 1200px) {
  .export-content {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .export-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .format-tabs {
    flex-direction: column;
  }
  
  .checkbox-grid {
    grid-template-columns: 1fr;
  }
  
  .history-item {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
