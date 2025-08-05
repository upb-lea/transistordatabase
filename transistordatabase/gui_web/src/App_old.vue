<script setup>
import { ref, onMounted } from 'vue'
import TransistorList from './components/TransistorList.vue'
import TransistorForm from './components/TransistorForm.vue'
import TransistorComparison from './components/TransistorComparison.vue'
import TransistorPlotter from './components/TransistorPlotter.vue'
import DatabaseManager from './components/DatabaseManager.vue'
import SearchDatabase from './components/SearchDatabase.vue'
import ExportingTools from './components/ExportingTools.vue'
import TopologyCalculator from './components/TopologyCalculator.vue'
import { transistorApi } from './services/api.js'

const currentView = ref('search')
const transistors = ref([])
const selectedTransistor = ref(null)
const selectedForExport = ref([])
const selectedForTopology = ref(null)
const isLoading = ref(false)
const isDarkTheme = ref(false)

onMounted(async () => {
  await loadTransistors()
  // Load theme preference
  const savedTheme = localStorage.getItem('darkTheme')
  if (savedTheme !== null) {
    isDarkTheme.value = JSON.parse(savedTheme)
  }
  applyTheme()
})

async function loadTransistors() {
  isLoading.value = true
  try {
    transistors.value = await transistorApi.getAll()
  } catch (error) {
    console.error('Error loading transistors:', error)
  } finally {
    isLoading.value = false
  }
}

function toggleTheme() {
  isDarkTheme.value = !isDarkTheme.value
  localStorage.setItem('darkTheme', JSON.stringify(isDarkTheme.value))
  applyTheme()
}

function applyTheme() {
  if (isDarkTheme.value) {
    document.documentElement.classList.add('dark-theme')
  } else {
    document.documentElement.classList.remove('dark-theme')
  }
}

function showSearch() {
  currentView.value = 'search'
}

function showCreate() {
  selectedTransistor.value = null
  currentView.value = 'create'
}

function showExport() {
  currentView.value = 'export'
}

function showComparison() {
  currentView.value = 'compare'
}

function showTopology() {
  currentView.value = 'topology'
}

function showEditForm(transistor) {
  selectedTransistor.value = transistor
  currentView.value = 'create'
}

async function handleTransistorSaved() {
  await loadTransistors()
  currentView.value = 'search'
}

async function handleTransistorDeleted(transistorId) {
  try {
    await transistorApi.delete(transistorId)
    await loadTransistors()
  } catch (error) {
    console.error('Error deleting transistor:', error)
  }
}

// Handle inter-component communication
function handleLoadToExporting(transistor) {
  selectedForExport.value = [transistor]
  currentView.value = 'export'
}

function handleLoadToComparison(transistor) {
  // Let comparison component handle the transistor
  currentView.value = 'compare'
  // You could emit an event or use a store for more complex state management
}

function handleLoadToTopology(transistor) {
  selectedForTopology.value = transistor
  currentView.value = 'topology'
}

function handleTransistorSelected(transistor) {
  selectedTransistor.value = transistor
}

function handleOpenDatabaseSearch() {
  currentView.value = 'search'
}
</script>

<template>
  <div id="app">
    <header class="app-header">
      <h1>🔌 Transistor Database - Web Interface</h1>
      <div class="stats">
        <span>📊 Total Transistors: {{ transistors.length }}</span>
        <span v-if="selectedTransistor">| 🎯 Selected: {{ selectedTransistor.metadata.name }}</span>
      </div>
    </header>

    <nav class="main-nav">
      <button 
        @click="showSearch" 
        :class="{ active: currentView === 'search' }"
        class="nav-btn"
      >
        � Search Database
      </button>
      <button 
        @click="showCreate" 
        :class="{ active: currentView === 'create' }"
        class="nav-btn"
      >
        ➕ Create Transistor
      </button>
      <button 
        @click="showExport" 
        :class="{ active: currentView === 'export' }"
        class="nav-btn"
      >
        📤 Exporting Tools
      </button>
      <button 
        @click="showComparison" 
        :class="{ active: currentView === 'compare' }"
        class="nav-btn"
      >
        � Comparison Tools
      </button>
      <button 
        @click="showTopology" 
        :class="{ active: currentView === 'topology' }"
        class="nav-btn"
      >
        🧮 Topology Calculator
      </button>
    </nav>

    <main class="app-main">
      <div v-if="isLoading" class="loading">
        <div class="loading-spinner"></div>
        <p>Loading transistor database...</p>
      </div>
      
      <!-- Search Database View (Advanced filtering) -->
      <SearchDatabase 
        v-if="currentView === 'search' && !isLoading"
        :transistors="transistors"
        @load-to-exporting="handleLoadToExporting"
        @load-to-comparison="handleLoadToComparison"
        @load-to-topology="handleLoadToTopology"
      />
      
      <!-- Create/Edit Transistor Form -->
      <TransistorForm 
        v-if="currentView === 'create'"
        :transistor="selectedTransistor"
        @saved="handleTransistorSaved"
        @cancel="showSearch"
      />
      
      <!-- Exporting Tools -->
      <ExportingTools 
        v-if="currentView === 'export'"
        :transistors="transistors"
        :selected-from-search="selectedForExport"
        @open-database-search="handleOpenDatabaseSearch"
      />
      
      <!-- Comparison Tools -->
      <TransistorComparison 
        v-if="currentView === 'compare'"
        :transistors="transistors"
      />
      
      <!-- Topology Calculator -->
      <TopologyCalculator 
        v-if="currentView === 'topology'"
        :transistors="transistors"
        @transistor-selected="handleTransistorSelected"
        @view-transistor-details="showEditForm"
      />
    </main>

    <!-- Global notification system -->
    <div class="notification-area" id="notifications">
      <!-- Notifications will be injected here -->
    </div>
  </div>
</template>

<style>
/* Global styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  line-height: 1.6;
  color: #333;
  background: #f5f5f5;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.app-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.stats {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  opacity: 0.9;
}

.main-nav {
  background: white;
  padding: 0 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  display: flex;
  gap: 0;
  overflow-x: auto;
}

.nav-btn {
  background: transparent;
  border: none;
  color: #666;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.9rem;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
  min-width: fit-content;
}

.nav-btn:hover {
  background: #f8f9fa;
  color: #2c3e50;
}

.nav-btn.active {
  color: #007bff;
  border-bottom-color: #007bff;
  background: #f8f9ff;
}

.app-main {
  flex: 1;
  padding: 0;
  max-width: 100%;
  margin: 0;
  background: #f5f5f5;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.notification-area {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  max-width: 400px;
}

/* Responsive design */
@media (max-width: 768px) {
  .app-header {
    padding: 1rem;
  }
  
  .app-header h1 {
    font-size: 1.4rem;
  }
  
  .stats {
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.8rem;
  }
  
  .main-nav {
    padding: 0 1rem;
  }
  
  .nav-btn {
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 0.75rem;
  }
  
  .app-header h1 {
    font-size: 1.2rem;
  }
  
  .main-nav {
    padding: 0 0.5rem;
  }
  
  .nav-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
  }
}

/* Accessibility improvements */
.nav-btn:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* Print styles */
@media print {
  .app-header,
  .main-nav {
    display: none;
  }
  
  .app-main {
    padding: 0;
  }
}
</style>
