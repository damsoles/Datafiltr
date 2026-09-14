const API_BASE = '/api';

const elements = {
  uploadBtn: document.getElementById('uploadBtn'),
  viewDataBtn: document.getElementById('viewDataBtn'),
  detectBtn: document.getElementById('detectBtn'),
  updateBtn: document.getElementById('updateBtn'),
  missingReportBtn: document.getElementById('missingReportBtn'),
  downloadDataBtn: document.getElementById('downloadDataBtn'),
  settingsBtn: document.getElementById('settingsBtn'),
  settingsModal: document.getElementById('settingsModal'),
  closeSettingsBtn: document.getElementById('closeSettingsBtn'),
  cancelSettingsBtn: document.getElementById('cancelSettingsBtn'),
  clearSessionBtn: document.getElementById('clearSessionBtn'),
  sessionInfo: document.getElementById('sessionInfo'),
  excelFileInput: document.getElementById('excelFileInput'),
  statusMessage: document.getElementById('statusMessage'),
  mainTable: document.getElementById('mainTable'),
  missingTable: document.getElementById('missingTable')
};

const views = {
  data: {
    panel: document.getElementById('mainDataPanel'),
    button: elements.viewDataBtn
  },
  missing: {
    panel: document.getElementById('missingDataPanel'),
    button: elements.detectBtn
  }
};

const state = {
  data: [],
  missing: []
};

function setStatus(message, isError = false) {
  elements.statusMessage.textContent = message;
  elements.statusMessage.style.background = isError ? '#fee2e2' : '#e2e8f0';
  elements.statusMessage.style.color = isError ? '#991b1b' : '#1f2937';
}

function showView(viewName) {
  const view = views[viewName] ? viewName : 'data';
  Object.entries(views).forEach(([name, config]) => {
    config.panel.hidden = name !== view;
    config.button.classList.toggle('active', name === view);
  });
  window.history.replaceState(null, '', `#${view}`);
}

function showViewFromUrl() {
  const requestedView = window.location.hash.slice(1);
  showView(requestedView === 'faltantes' ? 'missing' : 'data');
}

function renderSummary(summary) {
  document.getElementById('totalRecords').textContent = summary.total || 0;
  document.getElementById('completeRecords').textContent = summary.complete || 0;
  document.getElementById('missingRecordsCount').textContent = summary.missing || 0;
  document.getElementById('missingFieldsTotal').textContent = summary.fields || 0;
  document.getElementById('completenessRate').textContent = summary.rate || '0%';
}

function clearLoadedData() {
  state.data = [];
  state.missing = [];
  renderMainTable([]);
  renderMissingTable([]);
  renderSummary({ total: 0, complete: 0, missing: 0, fields: 0, rate: '0%' });
}

function closeSettings() {
  elements.settingsModal.hidden = true;
}

function renderSessionInfo(session) {
  const active = session.active_file;
  const history = session.file_history || [];
  const activeText = active
    ? `<strong>Archivo activo:</strong> ${active.file_name} (${active.rows} registros)`
    : '<strong>Archivo activo:</strong> No hay ninguno';
  const historyItems = history.length
    ? `<ul>${history.map((item) => `<li>${item.file_name} - ${item.rows} registros - ${item.loaded_at}</li>`).join('')}</ul>`
    : '<p>No hay documentos cargados durante esta sesión.</p>';
  elements.sessionInfo.innerHTML = `${activeText}<h3>Historial de sesión</h3>${historyItems}`;
}

async function openSettings() {
  elements.settingsModal.hidden = false;
  try {
    const session = await fetchJson(`${API_BASE}/session`);
    renderSessionInfo(session);
  } catch (error) {
    elements.sessionInfo.textContent = error.message;
  }
}

async function clearSession() {
  if (!window.confirm('¿Eliminar la carga activa y el historial de esta sesión?')) return;
  try {
    const result = await fetchJson(`${API_BASE}/session`, { method: 'DELETE' });
    clearLoadedData();
    showView('data');
    closeSettings();
    setStatus(result.message);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Error en la solicitud');
  }
  return data;
}

function renderMainTable(rows) {
  if (!rows.length) {
    elements.mainTable.innerHTML = '<thead><tr><th>No hay datos</th></tr></thead>';
    return;
  }

  const columns = Object.keys(rows[0]);
  const thead = document.createElement('thead');
  const trHead = document.createElement('tr');
  columns.forEach((column) => {
    const th = document.createElement('th');
    th.textContent = column;
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);

  const tbody = document.createElement('tbody');
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    columns.forEach((column) => {
      const td = document.createElement('td');
      const value = row[column];
      td.textContent = value === null || value === undefined ? '' : value;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  elements.mainTable.innerHTML = '';
  elements.mainTable.appendChild(thead);
  elements.mainTable.appendChild(tbody);
}

function renderMissingTable(rows) {
  if (!rows.length) {
    elements.missingTable.innerHTML = '<thead><tr><th>No hay registros incompletos</th></tr></thead>';
    return;
  }

  const columns = ['empresa', 'ruc', 'año', 'campos_faltantes', 'cantidad'];
  const thead = document.createElement('thead');
  const trHead = document.createElement('tr');
  columns.forEach((column) => {
    const th = document.createElement('th');
    th.textContent = column;
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);

  const tbody = document.createElement('tbody');
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.classList.add('incomplete');
    columns.forEach((column) => {
      const td = document.createElement('td');
      const value = row[column];
      td.textContent = Array.isArray(value) ? value.join(', ') : (value ?? '');
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  elements.missingTable.innerHTML = '';
  elements.missingTable.appendChild(thead);
  elements.missingTable.appendChild(tbody);
}

async function loadData() {
  try {
    const data = await fetchJson(`${API_BASE}/data`);
    state.data = data;
    renderMainTable(data);
    const summary = {
      total: data.length,
      complete: data.filter((row) => !Object.values(row).some((value) => value === null || value === undefined || value === '')).length,
      missing: data.filter((row) => Object.values(row).some((value) => value === null || value === undefined || value === '')).length,
      fields: 0,
      rate: '0%'
    };
    summary.fields = data.reduce((acc, row) => {
      const emptyValues = Object.values(row).filter((value) => value === null || value === undefined || value === '').length;
      return acc + emptyValues;
    }, 0);
    const totalRecords = Math.max(summary.total, 1);
    summary.rate = `${Math.round(((summary.complete / totalRecords) * 100))}%`;
    renderSummary(summary);
    showView('data');
  } catch (error) {
    clearLoadedData();
    setStatus(error.message, true);
  }
}

async function detectMissing() {
  try {
    const result = await fetchJson(`${API_BASE}/detect-missing`, { method: 'POST' });
    const missing = await fetchJson(`${API_BASE}/missing`);
    state.missing = missing;
    renderMissingTable(missing);
    showView('missing');
    setStatus(`Se detectaron ${result.missing_records} registros con faltantes.`);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function uploadExcel(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);

  try {
    const result = await fetchJson(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData
    });

    setStatus(`${result.message} | Registros: ${result.rows_found}`);
    state.data = await fetchJson(`${API_BASE}/data`);
    renderMainTable(state.data);

    const missing = await fetchJson(`${API_BASE}/missing`);
    state.missing = missing;
    renderMissingTable(missing);

    const summary = {
      total: result.rows_found,
      complete: result.complete_records,
      missing: result.missing_records,
      fields: result.missing_fields_total,
      rate: `${Math.round((result.complete_records / Math.max(result.rows_found, 1)) * 100)}%`
    };
    renderSummary(summary);
    showView('data');
    if (result.duplicate_warning) {
      setStatus(`${result.message} | ${result.duplicate_warning}`, true);
    }
  } catch (error) {
    clearLoadedData();
    setStatus(error.message, true);
  }
}

function bindEvents() {
  elements.uploadBtn.addEventListener('click', () => elements.excelFileInput.click());
  elements.excelFileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    uploadExcel(file);
  });

  elements.viewDataBtn.addEventListener('click', async () => {
    showView('data');
    await loadData();
  });
  elements.detectBtn.addEventListener('click', detectMissing);
  window.addEventListener('hashchange', showViewFromUrl);
  elements.settingsBtn.addEventListener('click', openSettings);
  elements.closeSettingsBtn.addEventListener('click', closeSettings);
  elements.cancelSettingsBtn.addEventListener('click', closeSettings);
  elements.clearSessionBtn.addEventListener('click', clearSession);
  elements.settingsModal.addEventListener('click', (event) => {
    if (event.target === elements.settingsModal) closeSettings();
  });

  elements.missingReportBtn.addEventListener('click', async () => {
    try {
      const response = await fetch(`${API_BASE}/missing-report`);
      if (!response.ok) {
        throw new Error('No se pudo generar el reporte');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'REPORTE_FALTANTES.xlsx';
      a.click();
      window.URL.revokeObjectURL(url);
      setStatus('Reporte exportado correctamente.');
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  elements.downloadDataBtn.addEventListener('click', async () => {
    try {
      const response = await fetch(`${API_BASE}/download-updated`);
      if (!response.ok) {
        throw new Error('No se pudo descargar el archivo actualizado');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'BASE_EMPRESAS_ACTUALIZADA.xlsx';
      a.click();
      window.URL.revokeObjectURL(url);
      setStatus('Archivo actualizado descargado.');
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  elements.updateBtn.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx,.xls';
    input.onchange = async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);

      try {
        const result = await fetchJson(`${API_BASE}/update`, {
          method: 'POST',
          body: formData
        });
        setStatus(result.message);
        const data = await fetchJson(`${API_BASE}/data`);
        state.data = data;
        renderMainTable(data);
        const missing = await fetchJson(`${API_BASE}/missing`);
        state.missing = missing;
        renderMissingTable(missing);
        if (missing.length === 0) {
          renderSummary({ total: data.length, complete: data.length, missing: 0, fields: 0, rate: '100%' });
        }
      } catch (error) {
        setStatus(error.message, true);
      }
    };
    input.click();
  });
}

showViewFromUrl();
bindEvents();
