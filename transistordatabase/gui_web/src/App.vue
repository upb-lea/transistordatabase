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
  <div id="app" :class="{ 'dark-theme': isDarkTheme }">
    <!-- Contact Links Header -->
    <div class="contact-header">
      <div class="contact-links">
        <a href="https://linkedin.com/in/your-profile" target="_blank" title="LinkedIn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
          </svg>
          LinkedIn
        </a>
        <a href="https://discord.gg/your-server" target="_blank" title="Discord">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.211.375-.445.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.010c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
          </svg>
          Discord
        </a>
        <a href="https://github.com/tinix84/transistordatabase" target="_blank" title="GitHub">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          GitHub
        </a>
      </div>
      <button @click="toggleTheme" class="theme-toggle" :title="isDarkTheme ? 'Switch to Light Theme' : 'Switch to Dark Theme'">
        <svg v-if="isDarkTheme" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 18a6 6 0 1 1 0-12 6 6 0 0 1 0 12zm0-2a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.293 13.293A8 8 0 0 1 6.707 2.707a8.001 8.001 0 1 0 10.586 10.586z"/>
        </svg>
      </button>
    </div>

    <header class="app-header">
      <h1>🔌 Transistor Database - Web Interface</h1>
      <div class="stats">
        <span>📊 Total Transistors: {{ transistors.length }}</span>
        <span v-if="selectedTransistor">| 🎯 Selected: {{ selectedTransistor.metadata.name }}</span>
      </div>
    </header>

    <nav class="main-nav sticky-nav">
      <button 
        @click="showSearch" 
        :class="{ active: currentView === 'search' }"
        class="nav-btn"
      >
        🔍 Search Database
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
        🔍 Comparison Tools
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
  transition: all 0.3s ease;
}

/* Dark Theme Variables */
:root {
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

.dark-theme {
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

.dark-theme body {
  background: var(--bg-primary);
  color: var(--text-primary);
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  color: var(--text-primary);
}
</style>

<style scoped>
.contact-header {
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  padding: 0.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 200;
}

.contact-links {
  display: flex;
  gap: 1.5rem;
}

.contact-links a {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.85rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.contact-links a:hover {
  color: var(--accent-blue);
  background: var(--accent-blue-light);
}

.theme-toggle {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle:hover {
  background: var(--accent-blue-light);
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.app-header {
  background: linear-gradient(135deg, var(--accent-blue) 0%, #0056b3 100%);
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 4px 6px var(--shadow);
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

.sticky-nav {
  position: sticky;
  top: 50px; /* Adjust based on contact header height */
  z-index: 150;
}

.main-nav {
  background: var(--bg-secondary);
  padding: 0 2rem;
  box-shadow: 0 2px 4px var(--shadow);
  display: flex;
  gap: 0;
  overflow-x: auto;
  border-bottom: 1px solid var(--border-color);
}

.nav-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
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
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
  background: var(--accent-blue-light);
}

.app-main {
  flex: 1;
  padding: 0;
  max-width: 100%;
  margin: 0;
  background: var(--bg-primary);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top: 3px solid var(--accent-blue);
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
  .contact-header {
    padding: 0.5rem 1rem;
  }
  
  .contact-links {
    gap: 1rem;
  }
  
  .contact-links a {
    font-size: 0.75rem;
    padding: 0.25rem;
  }
  
  .contact-links a span {
    display: none; /* Hide text on mobile, show only icons */
  }
  
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
  
  .sticky-nav {
    top: 40px;
  }
}

@media (max-width: 480px) {
  .contact-header {
    padding: 0.25rem 0.75rem;
  }
  
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
  
  .sticky-nav {
    top: 35px;
  }
}

/* Accessibility improvements */
.nav-btn:focus,
.theme-toggle:focus,
.contact-links a:focus {
  outline: 2px solid var(--accent-blue);
  outline-offset: 2px;
}

/* Print styles */
@media print {
  .contact-header,
  .app-header,
  .main-nav {
    display: none;
  }
  
  .app-main {
    padding: 0;
  }
}
</style>
