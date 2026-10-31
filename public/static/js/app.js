// Full Stack Farmer Alert Registry Application Logic
let map = null;
let farmerLayer = null;
let alertLayer = null;
let sensorLayer = null;
let shelterLayer = null;

let currentTab = 'map';
let allFarmers = [];
let allAlerts = [];
let allSensors = [];
let allShelters = [];
let allSos = [];
let allDispatches = [];

// Initialize application immediately or on DOM ready
function startApplication() {
  initMap();
  setupEventListeners();
  loadAllData();
  initRealtimeSync();

  // Background fallback refresh every 15 seconds
  setInterval(loadAllData, 15000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startApplication);
} else {
  startApplication();
}

// -------------------------------------------------------------
// Real-Time Multi-User Synchronization Engine
// (Cross-Tab BroadcastChannel + SSE Live Stream + DB Fingerprint Poller)
// -------------------------------------------------------------
let liveEventSource = null;
let crossTabChannel = null;
let lastKnownVersion = null;
let lastKnownFingerprint = null;

function initRealtimeSync() {
  // 1. Cross-Tab Instant BroadcastChannel (0ms latency across browser tabs/windows)
  if ('BroadcastChannel' in window) {
    try {
      crossTabChannel = new BroadcastChannel('agrisuraksha_live_db');
      crossTabChannel.onmessage = (event) => {
        const msg = event.data;
        if (!msg) return;
        pulseSyncIndicator(`Tab Sync: ${msg.type || 'Data Updated'}`);
        handleIncomingSyncEvent(msg.type, msg.details, true);
      };
    } catch (e) {
      console.warn("BroadcastChannel not supported:", e);
    }
  }

  // 2. Server-Sent Events (SSE) Live Stream (Server-push across devices/browsers)
  setupSseStream();

  // 3. Database Fingerprint Poller (Checks every 2.5s for raw/external MySQL updates)
  setInterval(pollDatabaseFingerprint, 2500);
  pollDatabaseFingerprint();
}

function setupSseStream() {
  if (!('EventSource' in window)) {
    console.warn("EventSource SSE not supported in this browser; using rapid fingerprint poller.");
    return;
  }

  try {
    if (liveEventSource) {
      liveEventSource.close();
    }
    liveEventSource = new EventSource('/api/live-stream');

    liveEventSource.onopen = () => {
      setSyncBadge(true, "LIVE SYNC ACTIVE");
    };

    liveEventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.event === 'CONNECTED') {
          lastKnownVersion = payload.version;
          updateSyncTime();
          return;
        }

        pulseSyncIndicator(`Live: ${payload.event}`);
        handleIncomingSyncEvent(payload.event, payload.details, true);
        if (payload.version) {
          lastKnownVersion = payload.version;
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    liveEventSource.onerror = (err) => {
      setSyncBadge(false, "RECONNECTING...");
      liveEventSource.close();
      setTimeout(setupSseStream, 3000);
    };
  } catch (err) {
    console.warn("SSE connection error:", err);
    setTimeout(setupSseStream, 4000);
  }
}

function handleIncomingSyncEvent(type, details = {}, showNotification = true) {
  // Reload all application data to show latest updates
  loadAllData();
  updateSyncTime();

  if (!showNotification) return;

  switch (type) {
    case 'FARMER_REGISTERED':
      showToast(`🧑‍🌾 Real-time: New Farmer registered (${details.name || 'Farmer'} - ${details.village || ''}, ${details.district || ''})`, 'success');
      break;
    case 'FARMER_STATUS_CHANGED':
      showToast(`⚠️ Real-time: Farmer safety status changed to ${details.status}`, 'warning');
      break;
    case 'FARMER_UPDATED':
      showToast(`✏️ Real-time: Farmer profile updated (${details.name || 'Farmer'})`, 'info');
      break;
    case 'FARMER_DELETED':
      showToast(`🗑️ Real-time: A farmer record was removed from database`, 'info');
      break;
    case 'ALERT_BROADCASTED':
      window.alertAudio?.playEmergencySiren(3);
      showToast(`📢 Real-time Broadcast: ${details.title || 'Hazard Alert'} (${details.impacted || 0} farmers notified)`, 'error');
      break;
    case 'ALERT_DEACTIVATED':
      showToast(`ℹ️ Real-time: Weather alert deactivated`, 'info');
      break;
    case 'ALERT_CREATED':
      showToast(`⚡ Real-time: New weather alert issued: ${details.title || ''}`, 'warning');
      break;
    case 'SENSOR_UPDATED':
      showToast(`📡 Real-time: Telemetry reading updated for ${details.station_code || 'sensor'} (${details.status})`, 'info');
      break;
    case 'SOS_TRIGGERED':
      window.alertAudio?.playEmergencySiren(4);
      showToast(`🆘 Real-time: EMERGENCY SOS DISTRESS BEACON ACTIVATED!`, 'error');
      break;
    case 'SOS_STATUS_UPDATED':
      showToast(`🚑 Real-time: SOS Rescue status updated to ${details.status}`, 'success');
      break;
    case 'SIMULATION_TRIGGERED':
      window.alertAudio?.playEmergencySiren(3);
      showToast(`🚨 Real-time Simulation: ${details.type} storm triggered in ${details.district}!`, 'error');
      break;
    case 'DB_CHANGED':
      showToast(`🔄 Real-time Sync: Database updated from another session.`, 'info');
      break;
    default:
      showToast(`🔄 Real-time Sync: Database updated.`, 'info');
      break;
  }
}

function broadcastLocalChange(type, details = {}) {
  if (crossTabChannel) {
    try {
      crossTabChannel.postMessage({ type, details, timestamp: Date.now() });
    } catch (e) {}
  }
}

async function pollDatabaseFingerprint() {
  try {
    const res = await fetch('/api/sync/version');
    const json = await res.json();
    if (!json.success) return;

    const newFp = json.fingerprint;
    const newVer = json.version;

    if (lastKnownFingerprint === null) {
      lastKnownFingerprint = newFp;
      lastKnownVersion = newVer;
      updateSyncTime();
      return;
    }

    if (newFp !== lastKnownFingerprint || (newVer !== null && newVer !== lastKnownVersion)) {
      lastKnownFingerprint = newFp;
      lastKnownVersion = newVer;
      pulseSyncIndicator("Database Updated");
      handleIncomingSyncEvent('DB_CHANGED', {}, true);
    } else {
      updateSyncTime();
    }
  } catch (e) {
    // Network or server temporarily rebooting
  }
}

function setSyncBadge(isActive, text) {
  const badge = document.getElementById('live-sync-indicator');
  const dot = document.getElementById('live-sync-dot');
  const txt = document.getElementById('live-sync-text');
  if (!badge) return;

  if (isActive) {
    badge.className = "px-2.5 py-0.5 rounded text-[10px] font-mono bg-emerald-800 text-emerald-200 border border-emerald-600 flex items-center gap-1.5 shadow-sm transition-all";
    if (dot) dot.className = "w-2 h-2 rounded-full bg-emerald-400 animate-ping";
    if (txt) txt.innerText = text || "LIVE SYNC ACTIVE";
  } else {
    badge.className = "px-2.5 py-0.5 rounded text-[10px] font-mono bg-amber-900 text-amber-200 border border-amber-600 flex items-center gap-1.5 shadow-sm transition-all";
    if (dot) dot.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
    if (txt) txt.innerText = text || "SYNC OFFLINE";
  }
}

function pulseSyncIndicator(actionLabel) {
  const badge = document.getElementById('live-sync-indicator');
  if (!badge) return;
  badge.classList.add('ring-2', 'ring-white', 'bg-emerald-600');
  setTimeout(() => {
    badge.classList.remove('ring-2', 'ring-white', 'bg-emerald-600');
  }, 1000);
}

function updateSyncTime() {
  const el = document.getElementById('live-sync-time');
  if (el) {
    const now = new Date();
    el.innerText = `Synced ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
  }
}

// -------------------------------------------------------------
// Map Initialization
// -------------------------------------------------------------
function initMap() {
  const mapElement = document.getElementById('map');
  if (!mapElement) return;

// Center on Gangetic plain and Eastern India (UP, Bihar, West Bengal)
  map = L.map('map').setView([24.6, 86.0], 7);

  // CartoDB Positron / OSM tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '© OpenStreetMap contributors, AgriSuraksha GeoSpatial'
  }).addTo(map);

  farmerLayer = L.layerGroup().addTo(map);
  alertLayer = L.layerGroup().addTo(map);
  sensorLayer = L.layerGroup().addTo(map);
  shelterLayer = L.layerGroup().addTo(map);

  // Map layer controls
  document.getElementById('toggle-farmers')?.addEventListener('change', (e) => {
    if (e.target.checked) map.addLayer(farmerLayer); else map.removeLayer(farmerLayer);
  });
  document.getElementById('toggle-alerts')?.addEventListener('change', (e) => {
    if (e.target.checked) map.addLayer(alertLayer); else map.removeLayer(alertLayer);
  });
  document.getElementById('toggle-sensors')?.addEventListener('change', (e) => {
    if (e.target.checked) map.addLayer(sensorLayer); else map.removeLayer(sensorLayer);
  });
  document.getElementById('toggle-shelters')?.addEventListener('change', (e) => {
    if (e.target.checked) map.addLayer(shelterLayer); else map.removeLayer(shelterLayer);
  });
}

// -------------------------------------------------------------
// Data Fetching & Sync
// -------------------------------------------------------------
async function loadAllData() {
  try {
    await Promise.allSettled([
      fetchStats(),
      fetchFarmers(),
      fetchAlerts(),
      fetchSensors(),
      fetchShelters(),
      fetchSos(),
      fetchDispatches()
    ]);
    renderMapMarkers();
  } catch (err) {
    console.error("Data load error:", err);
  }
}

async function fetchStats() {
  const res = await fetch('/api/stats');
  const json = await res.json();
  if (json.success) {
    const s = json.data;
    document.getElementById('stat-total-farmers').innerText = s.total_farmers;
    document.getElementById('stat-at-risk').innerText = s.at_risk_farmers;
    document.getElementById('stat-active-alerts').innerText = s.active_alerts;
    document.getElementById('stat-dispatches').innerText = s.total_dispatches;
    document.getElementById('stat-pending-sos').innerText = s.pending_sos;
    document.getElementById('stat-shelter-cap').innerText = `${s.current_shelter_occupancy} / ${s.total_shelter_capacity || s.total_capacity || 0}`;
  }
}

async function fetchFarmers() {
  const district = document.getElementById('filter-district')?.value || '';
  const status = document.getElementById('filter-status')?.value || '';
  const search = document.getElementById('search-farmer')?.value || '';

  let url = `/api/farmers?district=${encodeURIComponent(district)}&status=${encodeURIComponent(status)}&search=${encodeURIComponent(search)}`;
  const res = await fetch(url);
  const json = await res.json();
  if (json.success) {
    allFarmers = json.data;
    renderFarmersTable();
    populateFarmerSelectDropdowns();
  }
}

async function fetchAlerts() {
  const res = await fetch('/api/alerts');
  const json = await res.json();
  if (json.success) {
    allAlerts = json.data;
    renderAlertsList();
    renderAlertBanner();
  }
}

async function fetchSensors() {
  const res = await fetch('/api/sensors');
  const json = await res.json();
  if (json.success) {
    allSensors = json.data;
    renderSensorsList();
  }
}

async function fetchShelters() {
  const res = await fetch('/api/shelters');
  const json = await res.json();
  if (json.success) {
    allShelters = json.data;
    renderSheltersList();
  }
}

async function fetchSos() {
  const res = await fetch('/api/sos');
  const json = await res.json();
  if (json.success) {
    allSos = json.data;
    renderSosList();
  }
}

async function fetchDispatches() {
  const res = await fetch('/api/dispatches?limit=20');
  const json = await res.json();
  if (json.success) {
    allDispatches = json.data;
    renderDispatchesList();
    updatePhonePreview();
  }
}

// -------------------------------------------------------------
// Map Markers Rendering
// -------------------------------------------------------------
function renderMapMarkers() {
  if (!map) return;

  // 1. Farmers Markers
  farmerLayer.clearLayers();
  allFarmers.forEach(f => {
    let statusClass = 'icon-safe';
    let iconLetter = '🧑‍🌾';
    if (f.safety_status === 'In Field') { statusClass = 'icon-infield'; iconLetter = '🌾'; }
    else if (f.safety_status === 'At Risk') { statusClass = 'icon-atrisk'; iconLetter = '⚠️'; }
    else if (f.safety_status === 'SOS_Distress') { statusClass = 'icon-sos'; iconLetter = '🆘'; }
    else if (f.safety_status === 'Evacuating') { statusClass = 'icon-infield'; iconLetter = '🏃'; }

    const customIcon = L.divIcon({
      className: `custom-farmer-icon ${statusClass}`,
      html: `<span>${iconLetter}</span>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    const marker = L.marker([f.latitude, f.longitude], { icon: customIcon });
    marker.bindPopup(`
      <div style="min-width: 200px; font-family: inherit;">
        <h4 style="margin: 0 0 4px 0; color: #166534; font-size: 15px;">🧑‍🌾 ${f.full_name} (${f.farmer_code})</h4>
        <p style="margin: 2px 0; font-size: 12px; color: #4b5563;"><strong>Village:</strong> ${f.village}, ${f.district}</p>
        <p style="margin: 2px 0; font-size: 12px; color: #4b5563;"><strong>Phone:</strong> ${f.phone}</p>
        <p style="margin: 2px 0; font-size: 12px; color: #4b5563;"><strong>Crops:</strong> ${f.crops_grown}</p>
        <p style="margin: 4px 0 8px 0; font-size: 12px;"><strong>Status:</strong> 
          <span style="display:inline-block; padding: 2px 6px; border-radius: 4px; font-weight: bold; background: ${getStatusBg(f.safety_status)}; color: white;">
            ${f.safety_status}
          </span>
        </p>
        <div style="display: flex; gap: 4px; margin-top: 6px;">
          <button onclick="changeFarmerStatus(${f.id}, 'Safe')" style="flex:1; background:#16a34a; color:white; border:none; padding:4px; font-size:11px; border-radius:4px; cursor:pointer;">Safe</button>
          <button onclick="changeFarmerStatus(${f.id}, 'In Field')" style="flex:1; background:#d97706; color:white; border:none; padding:4px; font-size:11px; border-radius:4px; cursor:pointer;">In Field</button>
          <button onclick="triggerQuickSos(${f.id})" style="flex:1; background:#dc2626; color:white; border:none; padding:4px; font-size:11px; border-radius:4px; cursor:pointer;">SOS</button>
        </div>
      </div>
    `);
    farmerLayer.addLayer(marker);
  });

  // 2. Active Weather Alerts Hazard Zones (Circles & Center Icons)
  alertLayer.clearLayers();
  allAlerts.filter(a => a.is_active).forEach(a => {
    const isLightning = a.hazard_type === 'Lightning';
    const color = isLightning ? '#eab308' : '#0284c7';
    const fillCol = isLightning ? '#fef08a' : '#bae6fd';
    const iconEmoji = isLightning ? '⚡' : '🌊';

    // Danger radius circle
    const circle = L.circle([a.epicenter_lat, a.epicenter_lon], {
      color: color,
      fillColor: fillCol,
      fillOpacity: 0.35,
      radius: a.radius_km * 1000,
      weight: 2
    });

    circle.bindPopup(`
      <div style="min-width: 220px;">
        <h4 style="margin: 0 0 6px 0; color: ${color}; font-size: 15px;">${iconEmoji} ${a.title}</h4>
        <p style="margin: 2px 0; font-size: 12px;"><strong>Hazard Type:</strong> ${a.hazard_type}</p>
        <p style="margin: 2px 0; font-size: 12px;"><strong>Severity:</strong> <span style="color: red; font-weight:bold;">${a.severity_level}</span></p>
        <p style="margin: 2px 0; font-size: 12px;"><strong>Danger Radius:</strong> ${a.radius_km} km</p>
        <p style="margin: 2px 0; font-size: 12px;"><strong>Farmers Impacted:</strong> ${a.farmers_impacted}</p>
        <p style="margin: 6px 0; font-size: 12px; background:#fef2f2; padding:6px; border-left:3px solid #ef4444;">${a.instruction_text}</p>
        <button onclick="broadcastAlert(${a.id})" style="width:100%; background:#dc2626; color:white; border:none; padding:6px; border-radius:4px; font-weight:bold; cursor:pointer;">📢 Re-Broadcast Alert</button>
      </div>
    `);
    alertLayer.addLayer(circle);

    // Epicenter icon marker
    const hazardIcon = L.divIcon({
      className: 'custom-hazard-icon pulsing-lightning',
      html: `<span>${iconEmoji}</span>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18]
    });
    const epicMarker = L.marker([a.epicenter_lat, a.epicenter_lon], { icon: hazardIcon });
    alertLayer.addLayer(epicMarker);
  });

  // 3. Sensor Stations Markers
  sensorLayer.clearLayers();
  allSensors.forEach(s => {
    let iconSymbol = s.station_type === 'Lightning_Detector' ? '📡' : '💧';
    let markerColor = s.status === 'Emergency' ? '#dc2626' : (s.status === 'Warning' ? '#ea580c' : '#2563eb');

    const sensorIcon = L.divIcon({
      className: 'custom-sensor-icon',
      html: `<div style="background:${markerColor}; color:white; border-radius:6px; padding:3px 6px; font-size:12px; font-weight:bold; border:2px solid white; box-shadow:0 2px 4px rgba(0,0,0,0.3);">${iconSymbol} ${s.station_code}</div>`,
      iconSize: [70, 26],
      iconAnchor: [35, 13]
    });

    const marker = L.marker([s.latitude, s.longitude], { icon: sensorIcon });
    marker.bindPopup(`
      <div style="min-width: 220px;">
        <h4 style="margin:0 0 4px 0; color:#1e3a8a;">${iconSymbol} ${s.station_name}</h4>
        <p style="margin:2px 0; font-size:12px;"><strong>Type:</strong> ${s.station_type}</p>
        <p style="margin:2px 0; font-size:12px;"><strong>District:</strong> ${s.district}</p>
        ${s.lightning_flash_rate_per_min > 0 ? `<p style="margin:2px 0; font-size:12px; color:#d97706;">⚡ Flash Rate: <strong>${s.lightning_flash_rate_per_min} / min</strong> (Peak: ${s.peak_strike_current_ka} kA)</p>` : ''}
        ${s.river_water_level_m > 0 ? `<p style="margin:2px 0; font-size:12px; color:#0284c7;">🌊 Water Level: <strong>${s.river_water_level_m}m</strong> (Danger Mark: ${s.danger_water_level_m}m)</p>` : ''}
        <p style="margin:2px 0; font-size:12px;"><strong>Status:</strong> <span style="font-weight:bold; color:${markerColor};">${s.status}</span></p>
      </div>
    `);
    sensorLayer.addLayer(marker);
  });

  // 4. Safe Shelters Markers
  shelterLayer.clearLayers();
  allShelters.forEach(sh => {
    const shelterIcon = L.divIcon({
      className: 'custom-shelter-icon',
      html: `<div style="background:#059669; color:white; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:2px solid white; box-shadow:0 2px 5px rgba(0,0,0,0.3); font-size:14px;">🏛️</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = L.marker([sh.latitude, sh.longitude], { icon: shelterIcon });
    marker.bindPopup(`
      <div style="min-width: 220px;">
        <h4 style="margin:0 0 4px 0; color:#065f46;">🏛️ ${sh.shelter_name}</h4>
        <p style="margin:2px 0; font-size:12px;"><strong>Type:</strong> ${sh.shelter_type}</p>
        <p style="margin:2px 0; font-size:12px;"><strong>Location:</strong> ${sh.village}, ${sh.district}</p>
        <p style="margin:2px 0; font-size:12px;"><strong>Capacity:</strong> ${sh.current_occupancy} / ${sh.capacity_persons} persons</p>
        <p style="margin:2px 0; font-size:12px;"><strong>Lightning Protected:</strong> ${sh.lightning_protection_installed ? '✅ Yes (Rod & Grounded)' : '❌ No'}</p>
        <p style="margin:2px 0; font-size:12px;"><strong>Officer:</strong> ${sh.contact_officer} (<a href="tel:${sh.contact_phone}">${sh.contact_phone}</a>)</p>
      </div>
    `);
    shelterLayer.addLayer(marker);
  });
}

function getStatusBg(status) {
  switch (status) {
    case 'Safe': return '#16a34a';
    case 'In Field': return '#d97706';
    case 'At Risk': return '#ea580c';
    case 'SOS_Distress': return '#dc2626';
    case 'Evacuating': return '#7c3aed';
    default: return '#6b7280';
  }
}

// -------------------------------------------------------------
// UI Rendering Functions
// -------------------------------------------------------------
function renderAlertBanner() {
  const banner = document.getElementById('active-alert-ticker');
  if (!banner) return;
  const activeAlerts = allAlerts.filter(a => a.is_active);
  if (activeAlerts.length === 0) {
    banner.classList.add('hidden');
    return;
  }
  banner.classList.remove('hidden');
  const alert = activeAlerts[0];
  document.getElementById('ticker-title').innerText = `${alert.hazard_type.toUpperCase()} WARNING (${alert.district}): ${alert.title}`;
  document.getElementById('ticker-text').innerText = `${alert.instruction_text} (${alert.farmers_impacted} farmers impacted)`;
}

function renderFarmersTable() {
  const tbody = document.getElementById('farmers-table-body');
  if (!tbody) return;

  if (allFarmers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-gray-500">No farmers found matching filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = allFarmers.map(f => `
    <tr class="border-b hover:bg-gray-50 text-sm">
      <td class="py-3 px-4 font-medium text-gray-900">
        <div>${f.full_name}</div>
        <div class="text-xs text-gray-400 font-mono">${f.farmer_code}</div>
      </td>
      <td class="py-3 px-4">
        <div>${f.phone}</div>
        <div class="text-xs text-gray-400">${f.preferred_language}</div>
      </td>
      <td class="py-3 px-4">
        <div>${f.village}</div>
        <div class="text-xs text-gray-500">${f.district}, ${f.state}</div>
      </td>
      <td class="py-3 px-4">
        <span class="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">
          ${parseFloat(f.latitude).toFixed(4)}, ${parseFloat(f.longitude).toFixed(4)}
        </span>
      </td>
      <td class="py-3 px-4">
        <div class="text-xs font-medium text-gray-700">${f.crops_grown}</div>
        <div class="text-xs text-gray-400">${f.farm_size_acres} acres</div>
      </td>
      <td class="py-3 px-4">
        <span class="px-2.5 py-1 rounded-full text-xs font-semibold text-white" style="background-color: ${getStatusBg(f.safety_status)}">
          ${f.safety_status}
        </span>
      </td>
      <td class="py-3 px-4 text-right">
        <div class="inline-flex gap-1.5">
          <button onclick="changeFarmerStatus(${f.id}, 'Safe')" title="Mark Safe" class="px-2 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded text-xs">Safe</button>
          <button onclick="changeFarmerStatus(${f.id}, 'In Field')" title="Mark In Field" class="px-2 py-1 bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded text-xs">In Field</button>
          <button onclick="triggerQuickSos(${f.id})" title="Trigger SOS Beacon" class="px-2 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded text-xs font-bold">SOS</button>
          <button onclick="deleteFarmer(${f.id})" title="Delete" class="px-2 py-1 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded text-xs">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function renderAlertsList() {
  const container = document.getElementById('alerts-container');
  if (!container) return;

  if (allAlerts.length === 0) {
    container.innerHTML = `<div class="p-6 text-center text-gray-500">No active alerts. All agricultural zones currently normal.</div>`;
    return;
  }

  container.innerHTML = allAlerts.map(a => `
    <div class="border rounded-xl p-4 mb-3 ${a.is_active ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}">
      <div class="flex items-start justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-lg">${a.hazard_type === 'Lightning' ? '⚡' : '🌊'}</span>
            <h4 class="font-bold text-gray-900">${a.title}</h4>
            <span class="px-2 py-0.5 rounded text-xs font-bold ${a.is_active ? 'bg-red-600 text-white' : 'bg-gray-400 text-white'}">
              ${a.is_active ? 'ACTIVE WARNING' : 'RESOLVED'}
            </span>
            <span class="px-2 py-0.5 rounded text-xs bg-yellow-100 text-yellow-800 font-semibold">${a.severity_level}</span>
          </div>
          <div class="text-xs text-gray-500 mt-1">
            District: <strong class="text-gray-700">${a.district}</strong> | Danger Radius: <strong class="text-gray-700">${a.radius_km} km</strong> | Impacted Farmers: <strong class="text-red-700">${a.farmers_impacted}</strong> | Dispatches: <strong>${a.dispatched_count}</strong>
          </div>
        </div>
        <div class="flex gap-2">
          ${a.is_active ? `
            <button onclick="broadcastAlert(${a.id})" class="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-sm">
              📢 Re-Broadcast
            </button>
            <button onclick="deactivateAlert(${a.id})" class="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-semibold rounded-lg">
              Deactivate
            </button>
          ` : `
            <span class="text-xs text-gray-400 italic">Expired</span>
          `}
        </div>
      </div>
      <div class="mt-3 p-3 bg-white rounded-lg border text-sm text-gray-800">
        <p class="font-medium text-red-900">🇬🇧 Advisory: ${a.instruction_text}</p>
        ${a.instruction_text_hindi ? `<p class="mt-1 text-xs text-gray-600">🇮🇳 हिन्दी: ${a.instruction_text_hindi}</p>` : ''}
      </div>
    </div>
  `).join('');
}

function renderSensorsList() {
  const container = document.getElementById('sensors-container');
  if (!container) return;

  container.innerHTML = allSensors.map(s => `
    <div class="border rounded-xl p-4 bg-white shadow-sm flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="font-mono text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded font-bold">${s.station_code}</span>
          <span class="px-2 py-0.5 text-xs font-semibold rounded-full ${s.status === 'Emergency' ? 'bg-red-100 text-red-700' : (s.status === 'Warning' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700')}">
            ${s.status}
          </span>
        </div>
        <h4 class="font-bold text-gray-900 text-sm mb-1">${s.station_name}</h4>
        <div class="text-xs text-gray-500 mb-3">${s.district} • ${s.river_basin || 'Basin Network'}</div>

        <div class="space-y-2 text-xs">
          ${s.lightning_flash_rate_per_min > 0 ? `
            <div class="p-2 bg-yellow-50 rounded border border-yellow-200">
              <div class="flex justify-between">
                <span>⚡ Flash Rate:</span>
                <strong class="text-yellow-900">${s.lightning_flash_rate_per_min} / min</strong>
              </div>
              <div class="flex justify-between mt-0.5 text-gray-500">
                <span>Peak Current:</span>
                <span>${s.peak_strike_current_ka} kA</span>
              </div>
            </div>
          ` : ''}

          ${s.river_water_level_m > 0 ? `
            <div class="p-2 bg-blue-50 rounded border border-blue-200">
              <div class="flex justify-between">
                <span>🌊 River Gauge:</span>
                <strong class="text-blue-900">${s.river_water_level_m} m</strong>
              </div>
              <div class="flex justify-between mt-0.5 text-gray-500">
                <span>Danger Mark:</span>
                <span>${s.danger_water_level_m} m</span>
              </div>
            </div>
          ` : ''}

          <div class="flex justify-between text-gray-600">
            <span>🌧️ 24h Rain:</span>
            <strong>${s.current_rainfall_mm} mm</strong>
          </div>
        </div>
      </div>

      <div class="mt-4 pt-3 border-t flex gap-2">
        <button onclick="promptSimulateSensor(${s.id}, '${s.station_name}')" class="w-full text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1.5 rounded font-medium">
          ⚙️ Simulate Surge / Strikes
        </button>
      </div>
    </div>
  `).join('');
}

function renderSheltersList() {
  const container = document.getElementById('shelters-container');
  if (!container) return;

  container.innerHTML = allShelters.map(sh => {
    const occPct = Math.round((sh.current_occupancy / sh.capacity_persons) * 100);
    return `
      <div class="border rounded-xl p-4 bg-white shadow-sm">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl">🏛️</span>
              <h4 class="font-bold text-gray-900 text-base">${sh.shelter_name}</h4>
            </div>
            <p class="text-xs text-gray-500 mt-1">${sh.village}, ${sh.district} • Type: ${sh.shelter_type.replace('_', ' ')}</p>
          </div>
          <span class="px-2.5 py-1 text-xs rounded-full font-bold ${occPct > 80 ? 'bg-red-100 text-red-800' : 'bg-emerald-100 text-emerald-800'}">
            ${occPct}% Occupied
          </span>
        </div>

        <div class="mt-3">
          <div class="flex justify-between text-xs text-gray-600 mb-1">
            <span>Current Occupancy</span>
            <strong>${sh.current_occupancy} / ${sh.capacity_persons} persons</strong>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="h-2 rounded-full ${occPct > 80 ? 'bg-red-600' : 'bg-emerald-600'}" style="width: ${Math.min(occPct, 100)}%"></div>
          </div>
        </div>

        <div class="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg">
          <div>⚡ Lightning Arrestor: <strong>${sh.lightning_protection_installed ? 'Installed' : 'None'}</strong></div>
          <div>🔋 GenSet Backup: <strong>${sh.generator_backup ? 'Available' : 'No'}</strong></div>
          <div class="col-span-2">
            Officer: <strong>${sh.contact_officer}</strong> (<a href="tel:${sh.contact_phone}" class="text-blue-600 underline">${sh.contact_phone}</a>)
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderSosList() {
  const container = document.getElementById('sos-container');
  if (!container) return;

  if (allSos.length === 0) {
    container.innerHTML = `<div class="p-6 text-center text-gray-500">No emergency distress requests reported.</div>`;
    return;
  }

  container.innerHTML = allSos.map(s => `
    <div class="border rounded-xl p-4 bg-white shadow-sm mb-3 border-l-4 ${s.rescue_status === 'Rescued' ? 'border-l-green-500' : 'border-l-red-500'}">
      <div class="flex items-start justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white animate-pulse">🆘 DISTRESS</span>
            <h4 class="font-bold text-gray-900">${s.farmer_name} (${s.farmer_phone})</h4>
            <span class="text-xs text-gray-500">${s.village}, ${s.district}</span>
          </div>
          <div class="mt-2 text-sm text-red-900 bg-red-50 p-2.5 rounded border border-red-200">
            <strong>Situation:</strong> ${s.emergency_notes}
          </div>
          <div class="text-xs text-gray-500 mt-2">
            GPS: <span class="font-mono">${parseFloat(s.gps_lat).toFixed(4)}, ${parseFloat(s.gps_lon).toFixed(4)}</span> |
            Reported: <strong>${new Date(s.reported_at).toLocaleTimeString()}</strong> |
            Assigned Team: <strong>${s.assigned_team}</strong>
          </div>
        </div>
        <div>
          <div class="mb-2">
            <span class="px-2.5 py-1 text-xs rounded-full font-bold ${s.rescue_status === 'Rescued' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
              ${s.rescue_status}
            </span>
          </div>
          <div class="flex flex-col gap-1">
            <button onclick="updateSosStatus(${s.id}, 'Team_Dispatched', 'SDRF Quick Response Unit #1')" class="px-2 py-1 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-xs font-medium">
              Dispatch Team
            </button>
            <button onclick="updateSosStatus(${s.id}, 'Rescued', '${s.assigned_team}')" class="px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-medium">
              Mark Rescued
            </button>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

function renderDispatchesList() {
  const tbody = document.getElementById('dispatches-table-body');
  if (!tbody) return;

  tbody.innerHTML = allDispatches.map(d => `
    <tr class="border-b text-xs hover:bg-gray-50">
      <td class="py-2.5 px-3 font-mono text-gray-500">${new Date(d.dispatched_at).toLocaleTimeString()}</td>
      <td class="py-2.5 px-3">
        <span class="px-2 py-0.5 rounded font-bold ${d.delivery_channel === 'WhatsApp' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}">
          ${d.delivery_channel}
        </span>
      </td>
      <td class="py-2.5 px-3">
        <strong>${d.farmer_name}</strong>
        <div class="text-gray-400">${d.farmer_phone} (${d.district})</div>
      </td>
      <td class="py-2.5 px-3 max-w-xs truncate text-gray-700" title="${d.message_content}">
        ${d.message_content}
      </td>
      <td class="py-2.5 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-xs bg-emerald-100 text-emerald-800 font-semibold">
          ✓ ${d.status}
        </span>
      </td>
    </tr>
  `).join('');
}

function updatePhonePreview() {
  const container = document.getElementById('phone-messages-stream');
  if (!container) return;

  if (allDispatches.length === 0) {
    container.innerHTML = `<div class="text-center text-xs text-gray-400 py-20">No simulated incoming alerts yet.</div>`;
    return;
  }

  // Show top 3 recent dispatches
  const recent = allDispatches.slice(0, 3);
  container.innerHTML = recent.map(d => {
    const isWa = d.delivery_channel === 'WhatsApp';
    return `
      <div class="${isWa ? 'whatsapp-bubble' : 'sms-bubble'}">
        <div class="flex justify-between items-center text-[10px] text-gray-500 mb-1">
          <span class="font-bold text-gray-700">${isWa ? '🟢 Kisan WhatsApp Bot' : '📱 GOV-AGRI-ALERT'}</span>
          <span>${new Date(d.dispatched_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
        <div class="text-xs font-sans text-gray-800 whitespace-pre-line">${d.message_content}</div>
        <div class="text-[10px] text-right text-gray-400 mt-1">✓✓ Delivered to ${d.farmer_name}</div>
      </div>
    `;
  }).join('');
}

function populateFarmerSelectDropdowns() {
  const select = document.getElementById('sos-farmer-select');
  if (!select) return;
  select.innerHTML = `<option value="">Select Farmer...</option>` + allFarmers.map(f => `
    <option value="${f.id}">${f.full_name} (${f.farmer_code} - ${f.village}, ${f.district})</option>
  `).join('');
}

// -------------------------------------------------------------
// Action Handlers (CRUD, Simulation, Broadcasts)
// -------------------------------------------------------------
async function changeFarmerStatus(farmerId, newStatus) {
  try {
    const res = await fetch(`/api/farmers/${farmerId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const json = await res.json();
    if (json.success) {
      showToast(`Farmer status updated to ${newStatus}`, 'success');
      broadcastLocalChange('FARMER_STATUS_CHANGED', { farmerId, status: newStatus });
      loadAllData();
    }
  } catch (e) {
    showToast('Failed to update status', 'error');
  }
}

async function triggerQuickSos(farmerId) {
  if (!confirm("Are you sure you want to trigger an EMERGENCY SOS distress beacon for this farmer?")) return;
  try {
    const res = await fetch('/api/sos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        farmer_id: farmerId,
        distress_type: 'Trapped_In_Field',
        emergency_notes: 'Urgent distress beacon triggered from field. Water surge / lightning imminent!'
      })
    });
    const json = await res.json();
    if (json.success) {
      window.alertAudio?.playEmergencySiren(2);
      showToast('🚨 SOS DISTRESS BEACON ACTIVATED! Rescue team notified.', 'error');
      broadcastLocalChange('SOS_TRIGGERED', { farmerId });
      loadAllData();
    }
  } catch (e) {
    showToast('Failed to trigger SOS', 'error');
  }
}

async function deleteFarmer(farmerId) {
  if (!confirm("Delete this farmer record from the registry?")) return;
  try {
    const res = await fetch(`/api/farmers/${farmerId}`, { method: 'DELETE' });
    const json = await res.json();
    if (json.success) {
      showToast('Farmer deleted from registry', 'info');
      broadcastLocalChange('FARMER_DELETED', { farmerId });
      loadAllData();
    }
  } catch (e) {
    showToast('Failed to delete farmer', 'error');
  }
}

async function broadcastAlert(alertId) {
  try {
    const res = await fetch(`/api/alerts/${alertId}/broadcast`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      window.alertAudio?.playEmergencySiren(3);
      showToast(`📢 Alert Broadcasted! ${json.impacted_count} farmers in danger zone notified (${json.dispatched_count} messages sent).`, 'warning');
      broadcastLocalChange('ALERT_BROADCASTED', { alertId, impacted: json.impacted_count });
      loadAllData();
    }
  } catch (e) {
    showToast('Failed to broadcast alert', 'error');
  }
}

async function deactivateAlert(alertId) {
  try {
    const res = await fetch(`/api/alerts/${alertId}/deactivate`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      showToast('Alert deactivated', 'info');
      broadcastLocalChange('ALERT_DEACTIVATED', { alertId });
      loadAllData();
    }
  } catch (e) {
    showToast('Failed to deactivate alert', 'error');
  }
}

async function updateSosStatus(sosId, status, team) {
  try {
    const res = await fetch(`/api/sos/${sosId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rescue_status: status, assigned_team: team })
    });
    const json = await res.json();
    if (json.success) {
      showToast(`SOS Rescue status updated to ${status}`, 'success');
      broadcastLocalChange('SOS_STATUS_UPDATED', { sosId, status, team });
      loadAllData();
    }
  } catch (e) {
    showToast('Failed to update rescue status', 'error');
  }
}

async function triggerThreatSimulation(type, district) {
  showToast(`⚡ Initiating real-time ${type} threat simulation for ${district}...`, 'info');
  try {
    const res = await fetch('/api/simulate-threat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, district })
    });
    const json = await res.json();
    if (json.success) {
      window.alertAudio?.playEmergencySiren(4);
      showToast(`🚨 THREAT SIMULATION TRIGGERED: ${type} Warning broadcasted to ${json.broadcast?.impacted_count || 0} farmers!`, 'error');
      broadcastLocalChange('SIMULATION_TRIGGERED', { type, district });
      loadAllData();
    }
  } catch (e) {
    showToast('Simulation failed', 'error');
  }
}

function promptSimulateSensor(stationId, stationName) {
  const val = prompt(`Simulate telemetry spike for ${stationName}:\nEnter simulated flash rate (0-100) or water level (0-80m):`, "75");
  if (!val) return;
  const num = parseFloat(val);

  fetch(`/api/sensors/${stationId}/reading`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_rainfall_mm: 55.0,
      river_water_level_m: num,
      lightning_flash_rate_per_min: Math.round(num),
      peak_strike_current_ka: 68.5,
      status: num > 50 ? 'Emergency' : 'Normal'
    })
  }).then(r => r.json()).then(json => {
    if (json.success) {
      showToast('Sensor telemetry updated!', 'success');
      broadcastLocalChange('SENSOR_UPDATED', { stationId, status: num > 50 ? 'Emergency' : 'Normal' });
      loadAllData();
    }
  });
}

// -------------------------------------------------------------
// Event Listeners & Modals
// -------------------------------------------------------------
function setupEventListeners() {
  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  // Farmer filter triggers
  document.getElementById('filter-district')?.addEventListener('change', fetchFarmers);
  document.getElementById('filter-status')?.addEventListener('change', fetchFarmers);
  document.getElementById('search-farmer')?.addEventListener('input', debounce(fetchFarmers, 300));

  // Audio siren toggle
  const audioToggle = document.getElementById('btn-audio-toggle');
  audioToggle?.addEventListener('click', () => {
    const enabled = window.alertAudio?.toggleSound();
    audioToggle.innerHTML = enabled ? '🔔 Siren Sound: ON' : '🔕 Siren Sound: OFF';
    audioToggle.className = enabled 
      ? 'px-3 py-1.5 text-xs font-bold rounded-lg bg-emerald-100 text-emerald-800 border border-emerald-300'
      : 'px-3 py-1.5 text-xs font-bold rounded-lg bg-gray-100 text-gray-700 border border-gray-300';
    showToast(enabled ? 'Emergency siren audio enabled' : 'Audio muted', 'info');
  });

  // New Farmer Registration Form Submit
  const farmerForm = document.getElementById('form-register-farmer');
  farmerForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(farmerForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch('/api/farmers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        showToast('Farmer registered successfully into MySQL registry!', 'success');
        broadcastLocalChange('FARMER_REGISTERED', { name: payload.full_name, district: payload.district, village: payload.village });
        farmerForm.reset();
        closeModal('modal-farmer-register');
        loadAllData();
      } else {
        showToast(json.error || 'Registration failed', 'error');
      }
    } catch (err) {
      showToast('Network error during registration', 'error');
    }
  });

  // Create Weather Alert Form Submit
  const alertForm = document.getElementById('form-create-alert');
  alertForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(alertForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        window.alertAudio?.playEmergencySiren(2);
        showToast('Weather alert broadcasted successfully to all farmers!', 'success');
        broadcastLocalChange('ALERT_CREATED', { title: payload.title });
        alertForm.reset();
        closeModal('modal-create-alert');
        loadAllData();
      } else {
        showToast(json.error || 'Alert creation failed', 'error');
      }
    } catch (err) {
      showToast('Error broadcasting alert', 'error');
    }
  });

  // File SOS Request Form Submit
  const sosForm = document.getElementById('form-submit-sos');
  sosForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(sosForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch('/api/sos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        window.alertAudio?.playEmergencySiren(3);
        showToast('🆘 Distress Beacon Registered! Emergency Response Activated.', 'error');
        broadcastLocalChange('SOS_TRIGGERED', { farmerId: payload.farmer_id });
        sosForm.reset();
        closeModal('modal-submit-sos');
        loadAllData();
      } else {
        showToast(json.error || 'Alert creation failed', 'error');
      }
    } catch (err) {
      showToast('Error submitting SOS', 'error');
    }
  });

  // District autofill coordinates
  const DISTRICT_COORDS = {
    'Varanasi': [25.4215, 82.8423],
    'Gorakhpur': [26.7451, 83.2145],
    'Prayagraj': [25.5120, 81.8540],
    'Patna': [25.6412, 85.0425],
    'Ayodhya': [26.7725, 81.8964],
    'Malda': [25.0108, 88.1411],
    'Murshidabad': [24.1850, 88.2700],
    'Purba Bardhaman': [23.2324, 87.8615],
    'South 24 Parganas': [22.1648, 88.8021],
    'North 24 Parganas': [22.6540, 88.8920],
    'Nadia': [23.4013, 88.4952],
    'Bankura': [23.2321, 87.0716],
    'Paschim Medinipur': [22.6710, 87.7215],
    'Hooghly': [22.8845, 87.7812],
    'Jalpaiguri': [26.5405, 88.7196],
    'Cooch Behar': [26.1340, 89.4670],
    'Guntur': [16.2415, 80.6421]
  };

  document.querySelector('#form-register-farmer select[name="district"]')?.addEventListener('change', (e) => {
    const coords = DISTRICT_COORDS[e.target.value];
    if (coords) {
      const form = document.getElementById('form-register-farmer');
      if (form) {
        form.querySelector('input[name="latitude"]').value = coords[0].toFixed(6);
        form.querySelector('input[name="longitude"]').value = coords[1].toFixed(6);
      }
    }
  });

  document.querySelector('#form-create-alert select[name="district"]')?.addEventListener('change', (e) => {
    const coords = DISTRICT_COORDS[e.target.value];
    if (coords) {
      const form = document.getElementById('form-create-alert');
      if (form) {
        form.querySelector('input[name="epicenter_lat"]').value = coords[0].toFixed(6);
        form.querySelector('input[name="epicenter_lon"]').value = coords[1].toFixed(6);
      }
    }
  });
}

function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-btn').forEach(b => {
    if (b.getAttribute('data-tab') === tabId) {
      b.className = 'tab-btn px-4 py-2 text-sm font-bold text-emerald-800 border-b-2 border-emerald-600';
    } else {
      b.className = 'tab-btn px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent';
    }
  });

  document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
  const activeContent = document.getElementById(`tab-content-${tabId}`);
  if (activeContent) {
    activeContent.classList.remove('hidden');
  }

  if (tabId === 'map' && map) {
    setTimeout(() => map.invalidateSize(), 150);
  }
}

// -------------------------------------------------------------
// Helper UI: Toasts & Modals
// -------------------------------------------------------------
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const bg = type === 'error' ? 'bg-red-600' : (type === 'success' ? 'bg-emerald-600' : (type === 'warning' ? 'bg-amber-600' : 'bg-slate-800'));
  toast.className = `${bg} text-white px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center justify-between gap-3 animate-fade-in transition-all`;
  toast.innerHTML = `
    <span>${msg}</span>
    <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200 font-bold ml-2">×</button>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

function openModal(id) {
  document.getElementById(id)?.classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id)?.classList.add('hidden');
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

