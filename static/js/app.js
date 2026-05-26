// ═══════════════════════════════════════════════════════════════
//  Coloproctología — Registro Quirúrgico  |  app.js
// ═══════════════════════════════════════════════════════════════

// ── State ────────────────────────────────────────────────────
let token = localStorage.getItem('token') || null;
let currentUser = null;
let currentStep = 1;
let editMode = false;
let editId = null;
let editTipo = null;
let dbCurrentPage = 1;
let dbCurrentTab = 'todos';
let dbTotalPages = 1;
let charts = {};

// ── Listas dinámicas ─────────────────────────────────────────
const DIAGNOSTICOS = {
  colorrectal: [
    'Neoplasia de Colon Derecho','Neoplasia de Colon Transverso','Neoplasia de Colon Izquierdo',
    'Neoplasia de Sigma','Neoplasia de Recto','Neoplasia de Ano','Neoplasia de Intestino Delgado',
    'Diverticulitis','Enfermedad Inflamatoria Intestinal','Colitis Isquémica','Colostomía','Ileostomía'
  ],
  proctologia: [
    'Fístula Perianal','Fístula Sacrococcígea','Absceso Perianal','Hemorroides','Fisura Anal',
    'Crohn Perianal','Prolapso Rectal','Cuerpo Extraño Anorrectal','Condilomas Anales','Gangrena de Fournier'
  ],
  funcionales: ['Incontinencia Fecal','Rectocele'],
  general: [
    'Hernia Inguinal','Hernia Umbilical','Eventración','Colelitiasis','Colecistitis',
    'Obstrucción Intestinal','Perforación Gastroduodenal','Apendicitis','Hernia Paraostomal'
  ]
};

const INTERVENCIONES = {
  'Neoplasia de Colon Derecho': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Neoplasia de Colon Transverso': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Neoplasia de Colon Izquierdo': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Neoplasia de Sigma': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Neoplasia de Recto': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Neoplasia de Ano': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Neoplasia de Intestino Delgado': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Diverticulitis': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Enfermedad Inflamatoria Intestinal': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Colitis Isquémica': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Colostomía': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Ileostomía': ['Resección Intestino Delgado','Resección Ileocecal','Hemicolectomía Derecha','Hemicolectomía Derecha Ampliada','Resección Segmentaria Ángulo Esplénico','Hemicolectomía Izquierda','Sigmoidectomía','Colectomía Subtotal','Colectomía Total','Panproctocolectomía','Resección Anterior + EPM','Resección Anterior + ETM','Amputación Abdominoperineal','Hartmann','Resección Endoanal','TAMIS','Estoma Derivativo','Reconstrucción de Tránsito','Cierre de Ileostomía'],
  'Fístula Perianal': ['Fistulotomía','Fistulectomía','Drenaje + Setón','Colgajo de Avance','LIFT','TROPIS','Esfinteroplastia','Láser'],
  'Crohn Perianal': ['Fistulotomía','Fistulectomía','Drenaje + Setón','Colgajo de Avance','LIFT','TROPIS','Esfinteroplastia','Láser'],
  'Hemorroides': ['Milligan-Morgan','Láser','Desarterialización Doppler'],
  'Absceso Perianal': ['Drenaje Simple','Drenaje + Setón'],
  'Fisura Anal': ['Esfinterotomía Lateral Interna','Toxina Botulínica'],
  'Fístula Sacrococcígea': ['Exéresis + Cierre Primario','Exéresis','Marsupialización','Colgajo Cutáneo','Láser'],
  'Prolapso Rectal': ['Rectopexia Ventral','Rectopexia + Sigmoidectomía','Delorme','Altemeier'],
  'Cuerpo Extraño Anorrectal': ['Extracción','Extracción + Estoma'],
  'Condilomas Anales': ['Exéresis'],
  'Gangrena de Fournier': ['Drenaje + Necrosectomía'],
  'Incontinencia Fecal': ['NMIS Primer Tiempo','NMIS Segundo Tiempo','Esfinteroplastia'],
  'Rectocele': ['Reparación Transanal','Reparación Perineal','Rectopexia'],
  'Hernia Inguinal': ['Hernioplastia','Herniorrafia','TAPP','TEP'],
  'Hernia Umbilical': ['Hernioplastia','Herniorrafia'],
  'Eventración': ['Eventroplastia'],
  'Colelitiasis': ['Colecistectomía'],
  'Colecistitis': ['Colecistectomía','Colecistostomía','Conservador'],
  'Obstrucción Intestinal': ['Adhesiolisis','Resección Intestinal','Conservador'],
  'Perforación Gastroduodenal': ['Sutura','Gastrectomía','Exclusión Duodenal'],
  'Apendicitis': ['Apendicectomía','Conservador'],
  'Hernia Paraostomal': ['Sugarbaker','Keyhole','Pauli','Eventroplastia']
};

// ── API helper ───────────────────────────────────────────────
async function api(method, url, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (res.status === 401) { doLogout(); return null; }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error en la solicitud');
  }
  if (res.status === 204) return null;
  return res.json();
}

// ── Toast ────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `fixed bottom-6 right-6 px-5 py-3 rounded-xl text-white font-medium shadow-lg z-50 text-sm transition-all ${
    type === 'error' ? 'bg-red-600' : type === 'warn' ? 'bg-yellow-600' : 'bg-green-700'
  }`;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 3500);
}

// ── Auth ─────────────────────────────────────────────────────
async function doLogin() {
  const user = document.getElementById('login-user').value;
  const pass = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  errEl.classList.add('hidden');
  try {
    const fd = new FormData();
    fd.append('username', user);
    fd.append('password', pass);
    const res = await fetch('/api/auth/token', { method: 'POST', body: fd });
    if (!res.ok) throw new Error('Credenciales incorrectas');
    const data = await res.json();
    token = data.access_token;
    localStorage.setItem('token', token);
    currentUser = data;
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('user-badge').textContent = data.nombre_completo || data.username;
    document.getElementById('btn-own-password').classList.remove('hidden');
    if (data.es_admin) {
      document.getElementById('nav-admin').classList.remove('hidden');
      document.getElementById('security-panel').classList.remove('hidden');
    }
    initApp();
  } catch (e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
  }
}

function doLogout() {
  token = null;
  localStorage.removeItem('token');
  location.reload();
}

// ── Init ─────────────────────────────────────────────────────
async function initApp() {
  buildRecidivaTable();
  await loadNextId();
  showSection('formulario');
  // Check login on enter key
  document.getElementById('login-pass').addEventListener('keyup', e => { if (e.key === 'Enter') doLogin(); });
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('login-pass').addEventListener('keyup', e => { if (e.key === 'Enter') doLogin(); });
  if (token) {
    api('GET', '/api/auth/me').then(data => {
      if (data) {
        currentUser = data;
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('user-badge').textContent = data.nombre_completo || data.username;
        document.getElementById('btn-own-password').classList.remove('hidden');
        if (data.es_admin) {
          document.getElementById('nav-admin').classList.remove('hidden');
          document.getElementById('security-panel').classList.remove('hidden');
        }
        initApp();
      }
    }).catch(() => {});
  }
});

// ── Sidebar ──────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('expanded');
}

// ── Section navigation ───────────────────────────────────────
const TITLES = { formulario: 'Nuevo Registro', database: 'Base de Datos', dashboard: 'Dashboard', export: 'Exportación', admin: 'Gestión de Usuarios' };

function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`section-${name}`).classList.add('active');
  document.querySelector(`[data-section="${name}"]`)?.classList.add('active');
  document.getElementById('page-title').textContent = TITLES[name] || name;

  if (name === 'database') { dbCurrentPage = 1; loadDbTable(); }
  if (name === 'dashboard') { loadDashboard('global'); }
  if (name === 'admin') loadAdminUsers();
}

// ── WIZARD logic ─────────────────────────────────────────────
async function loadNextId() {
  const tipo = document.getElementById('f-tipo-cirugia').value || 'colorrectal';
  const endpoint = { colorrectal: '/api/colorrectal', proctologia: '/api/proctologia', funcionales: '/api/funcionales', general: '/api/general' }[tipo] || '/api/colorrectal';
  try {
    const data = await api('GET', `${endpoint}/next-id`);
    if (data && !editMode) document.getElementById('f-id').value = data.next_id;
  } catch {}
}

function goToStep(n) {
  document.getElementById(`form-step-${currentStep}`).classList.add('hidden');
  currentStep = n;
  document.getElementById(`form-step-${currentStep}`).classList.remove('hidden');
  updateStepUI();
}

function updateStepUI() {
  for (let i = 1; i <= 4; i++) {
    const circ = document.getElementById(`step-circle-${i}`);
    circ.className = 'step-circle ' + (i < currentStep ? 'step-done' : i === currentStep ? 'step-active' : 'step-pending');
    if (i < 4) {
      const line = document.getElementById(`step-line-${i}`);
      line.className = 'step-line ' + (i < currentStep ? 'done' : '');
    }
  }
  document.getElementById('btn-prev').classList.toggle('hidden', currentStep === 1);
  document.getElementById('btn-next').classList.toggle('hidden', currentStep === 4);
  document.getElementById('btn-save').classList.toggle('hidden', currentStep !== 4);
}

function validateStep(n) {
  const required = {
    1: [['f-nhc', 'NHC'], ['f-fecha-intervencion', 'Fecha Intervención'], ['f-sexo', 'Sexo'], ['f-asa', 'ASA'], ['f-cirujano', 'Cirujano']],
    2: [['f-tipo-cirugia', 'Tipo Cirugía'], ['f-diagnostico', 'Diagnóstico'], ['f-intervencion', 'Intervención']],
    3: [], 4: []
  };
  for (const [id, label] of (required[n] || [])) {
    if (!document.getElementById(id)?.value) {
      showToast(`${label} es obligatorio`, 'error');
      document.getElementById(id)?.focus();
      return false;
    }
  }
  return true;
}

function nextStep() {
  if (!validateStep(currentStep)) return;
  if (currentStep < 4) goToStep(currentStep + 1);
}

function prevStep() {
  if (currentStep > 1) goToStep(currentStep - 1);
}

// ── Dynamic selects ──────────────────────────────────────────
function onTipoCirugia() {
  const tipo = document.getElementById('f-tipo-cirugia').value;
  const diagSel = document.getElementById('f-diagnostico');
  diagSel.innerHTML = '<option value="">— Seleccionar —</option>';
  (DIAGNOSTICOS[tipo] || []).forEach(d => {
    const o = document.createElement('option'); o.value = d; o.textContent = d; diagSel.appendChild(o);
  });
  document.getElementById('f-intervencion').innerHTML = '<option value="">— Seleccione diagnóstico —</option>';
  document.getElementById('wrap-estoma').classList.toggle('hidden', tipo !== 'colorrectal');
  // Paso 4: etiqueta dinámica según tipo
  const isColorrectal = tipo === 'colorrectal';
  const lbl = document.getElementById('step4-label');
  const ttl = document.getElementById('step4-title');
  if (lbl) lbl.textContent = isColorrectal ? 'Oncológico' : 'Seguimiento';
  if (ttl) ttl.textContent = isColorrectal
    ? 'Paso 4 — Oncológico · Seguimiento · Observaciones'
    : 'Paso 4 — Seguimiento · Observaciones';
  loadNextId();
}

function onDiagnostico() {
  const diag = document.getElementById('f-diagnostico').value;
  const sel = document.getElementById('f-intervencion');
  sel.innerHTML = '<option value="">— Seleccionar —</option>';
  (INTERVENCIONES[diag] || []).forEach(i => {
    const o = document.createElement('option'); o.value = i; o.textContent = i; sel.appendChild(o);
  });
  updateOncologicoVisibility();
}

function onAbordaje() {
  const ab = document.getElementById('f-abordaje').value;
  document.getElementById('wrap-conversion').classList.toggle('hidden', !['Laparoscopia','Robótico'].includes(ab));
}

function onDehiscencia() {
  const v = document.getElementById('f-dehiscencia').value;
  document.getElementById('wrap-tipo-dehiscencia').classList.toggle('hidden', v !== 'Si');
}

function onReintervencion() {
  document.getElementById('wrap-tipo-reintervencion').classList.toggle('hidden', document.getElementById('f-reintervencion').value !== 'Si');
}

function onMortalidad() {
  document.getElementById('wrap-causa-mortalidad').classList.toggle('hidden', document.getElementById('f-mortalidad').value !== 'Si');
}

function onLocalizacion() {
  document.getElementById('wrap-dist-margen').classList.toggle('hidden', document.getElementById('f-localizacion').value !== 'Recto');
}

function onNeoadyuvancia() {
  const v = document.getElementById('f-neoadyuvancia').value;
  document.getElementById('wrap-tipo-neo').classList.toggle('hidden', v !== 'Si');
  document.getElementById('wrap-pcr').classList.toggle('hidden', v !== 'Si');
}

function onAdyuvancia() {
  document.getElementById('wrap-tipo-adyuvancia').classList.toggle('hidden', document.getElementById('f-adyuvancia').value !== 'Si');
}

function updateOncologicoVisibility() {
  const tipo = document.getElementById('f-tipo-cirugia').value;
  const diag = document.getElementById('f-diagnostico').value;
  const isColorrectal = tipo === 'colorrectal';
  const showOnco = isColorrectal && diag.startsWith('Neoplasia');
  document.getElementById('wrap-oncologico').classList.toggle('hidden', !showOnco);
  document.getElementById('wrap-dehiscencia').classList.toggle('hidden', !isColorrectal);
  // Sync step 4 labels when called from populateForm
  const lbl = document.getElementById('step4-label');
  const ttl = document.getElementById('step4-title');
  if (lbl) lbl.textContent = isColorrectal ? 'Oncológico' : 'Seguimiento';
  if (ttl) ttl.textContent = isColorrectal
    ? 'Paso 4 — Oncológico · Seguimiento · Observaciones'
    : 'Paso 4 — Seguimiento · Observaciones';
}

// ── Calculated fields ────────────────────────────────────────
function calcEdad() {
  const fi = document.getElementById('f-fecha-intervencion').value;
  const fn = document.getElementById('f-fecha-nacimiento').value;
  if (fi && fn) {
    const d1 = new Date(fi), d2 = new Date(fn);
    let age = d1.getFullYear() - d2.getFullYear();
    const m = d1.getMonth() - d2.getMonth();
    if (m < 0 || (m === 0 && d1.getDate() < d2.getDate())) age--;
    document.getElementById('f-edad').value = age >= 0 ? age : '';
  } else {
    document.getElementById('f-edad').value = '';
  }
}

function calcEstancia() {
  const fi = document.getElementById('f-fecha-intervencion').value;
  const fa = document.getElementById('f-fecha-alta').value;
  if (fi && fa) {
    const diff = Math.round((new Date(fa) - new Date(fi)) / 86400000);
    document.getElementById('f-estancia').value = diff >= 0 ? diff : '';
  } else {
    document.getElementById('f-estancia').value = '';
  }
}

// ── TNM staging AJCC 8th ─────────────────────────────────────
function calcEstadioTNM() {
  const T = document.getElementById('f-t-tnm').value;
  const N = document.getElementById('f-n-tnm').value;
  const M = document.getElementById('f-m-tnm').value;
  if (!T || !N || !M) { document.getElementById('f-estadio-tnm').value = ''; return; }
  let estadio = '';
  if (M === 'M1a') estadio = 'IVA';
  else if (M === 'M1b') estadio = 'IVB';
  else if (M === 'M1c') estadio = 'IVC';
  else if (N === 'N0') {
    if (T === 'Tis') estadio = '0';
    else if (['T1','T2'].includes(T)) estadio = 'I';
    else if (T === 'T3') estadio = 'IIA';
    else if (T === 'T4a') estadio = 'IIB';
    else if (T === 'T4b') estadio = 'IIC';
  } else if (['N1','N1a','N1b','N1c'].includes(N)) {
    if (['T1','T2'].includes(T)) estadio = 'IIIA';
    else if (['T3','T4a'].includes(T)) estadio = 'IIIB';
    else if (T === 'T4b') estadio = 'IIIC';
  } else if (N === 'N2a') {
    if (T === 'T1') estadio = 'IIIA';
    else if (['T2','T3','T4a'].includes(T)) estadio = 'IIIB';
    else if (T === 'T4b') estadio = 'IIIC';
  } else if (N === 'N2b') {
    if (['T1','T2','T3'].includes(T)) estadio = 'IIIB';
    else if (['T4a','T4b'].includes(T)) estadio = 'IIIC';
  }
  document.getElementById('f-estadio-tnm').value = estadio;
}

// ── Recidiva table ───────────────────────────────────────────
const INTERVALOS = [3,6,12,18,24,36,48,60];

function buildRecidivaTable() {
  const tbody = document.getElementById('recidiva-table');
  tbody.innerHTML = '';
  INTERVALOS.forEach(m => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="font-medium text-gray-600">${m} meses</td>
      <td>
        <select id="f-recidiva-${m}m" class="input text-sm py-1" onchange="onRecidiva(${m})">
          <option value="">—</option><option>Si</option><option>No</option>
        </select>
      </td>
      <td>
        <select id="f-tipo-recidiva-${m}m" class="input text-sm py-1 hidden">
          <option value="">—</option>
          <option>Local</option><option>A distancia</option><option>Local + distancia</option>
        </select>
      </td>`;
    tbody.appendChild(tr);
  });
}

function onRecidiva(m) {
  const v = document.getElementById(`f-recidiva-${m}m`).value;
  document.getElementById(`f-tipo-recidiva-${m}m`).classList.toggle('hidden', v !== 'Si');
}

// ── Form collect / populate ──────────────────────────────────
function collectFormData() {
  const g = id => document.getElementById(id)?.value || null;
  const data = {
    nhc: g('f-nhc'), fecha_intervencion: g('f-fecha-intervencion'),
    fecha_nacimiento: g('f-fecha-nacimiento') || null,
    edad: g('f-edad') ? parseInt(g('f-edad')) : null,
    sexo: g('f-sexo'), asa: g('f-asa'), cirujano: g('f-cirujano'),
    ingreso_cma: g('f-ingreso-cma'), diagnostico: g('f-diagnostico'),
    intervencion: g('f-intervencion'), urgencia: g('f-urgencia'),
    abordaje: g('f-abordaje'), conversion: g('f-conversion') || null,
    tiempo_quirurgico: g('f-tiempo-quirurgico') ? parseInt(g('f-tiempo-quirurgico')) : null,
    clavien_dindo: g('f-clavien-dindo'), tipo_complicacion: g('f-tipo-complicacion') || null,
    intervencionismo: g('f-intervencionismo') || null,
    reintervencion: g('f-reintervencion') || null,
    tipo_reintervencion: g('f-tipo-reintervencion') || null,
    mortalidad: g('f-mortalidad') || null,
    causa_mortalidad: g('f-causa-mortalidad') || null,
    fecha_alta: g('f-fecha-alta') || null,
    estancia: g('f-estancia') ? parseInt(g('f-estancia')) : null,
    reingreso_30d: g('f-reingreso-30d') || null,
    observaciones: g('f-observaciones') || null,
  };

  const tipo = g('f-tipo-cirugia');
  if (tipo === 'colorrectal') {
    Object.assign(data, {
      estoma_proteccion: g('f-estoma-proteccion') || null,
      dehiscencia: g('f-dehiscencia') || null,
      tipo_dehiscencia: g('f-tipo-dehiscencia') || null,
      t_tnm: g('f-t-tnm') || null, n_tnm: g('f-n-tnm') || null,
      m_tnm: g('f-m-tnm') || null, estadio_tnm: g('f-estadio-tnm') || null,
      localizacion: g('f-localizacion') || null,
      distancia_margen_anal: g('f-distancia-margen-anal') ? parseFloat(g('f-distancia-margen-anal')) : null,
      neoadyuvancia: g('f-neoadyuvancia') || null,
      tipo_neoadyuvancia: g('f-tipo-neoadyuvancia') || null,
      pcr: g('f-pcr') || null,
      tipo_histologico: g('f-tipo-histologico') || null,
      grado: g('f-grado') || null,
      margenes_libres: g('f-margenes-libres') || null,
      ganglios_analizados: g('f-ganglios-analizados') ? parseInt(g('f-ganglios-analizados')) : null,
      ganglios_positivos: g('f-ganglios-positivos') ? parseInt(g('f-ganglios-positivos')) : null,
      invasion_linfovascular: g('f-invasion-linfovascular') || null,
      invasion_perineural: g('f-invasion-perineural') || null,
      msi: g('f-msi') || null,
      adyuvancia: g('f-adyuvancia') || null,
      tipo_adyuvancia: g('f-tipo-adyuvancia') || null,
      fecha_exitus: g('f-fecha-exitus') || null,
    });
    INTERVALOS.forEach(m => {
      data[`recidiva_${m}m`] = g(`f-recidiva-${m}m`) || null;
      data[`tipo_recidiva_${m}m`] = g(`f-tipo-recidiva-${m}m`) || null;
    });
  }
  return { tipo, data };
}

function populateForm(tipo, record) {
  const s = (id, val) => { const el = document.getElementById(id); if (el && val != null) el.value = val; };
  s('f-nhc', record.nhc); s('f-fecha-intervencion', record.fecha_intervencion);
  s('f-fecha-nacimiento', record.fecha_nacimiento); s('f-edad', record.edad);
  s('f-sexo', record.sexo); s('f-asa', record.asa); s('f-cirujano', record.cirujano);
  s('f-ingreso-cma', record.ingreso_cma);
  s('f-urgencia', record.urgencia); s('f-abordaje', record.abordaje);
  s('f-conversion', record.conversion); s('f-tiempo-quirurgico', record.tiempo_quirurgico);
  s('f-clavien-dindo', record.clavien_dindo); s('f-tipo-complicacion', record.tipo_complicacion);
  s('f-intervencionismo', record.intervencionismo); s('f-reintervencion', record.reintervencion);
  s('f-tipo-reintervencion', record.tipo_reintervencion); s('f-mortalidad', record.mortalidad);
  s('f-causa-mortalidad', record.causa_mortalidad); s('f-fecha-alta', record.fecha_alta);
  s('f-estancia', record.estancia); s('f-reingreso-30d', record.reingreso_30d);
  s('f-observaciones', record.observaciones);

  const tipoMap = { colorrectal: 'colorrectal', proctologia: 'proctologia', funcionales: 'funcionales', general: 'general' };
  s('f-tipo-cirugia', tipoMap[tipo] || tipo);
  onTipoCirugia();
  s('f-diagnostico', record.diagnostico);
  onDiagnostico();
  s('f-intervencion', record.intervencion);
  onAbordaje();

  if (tipo === 'colorrectal') {
    s('f-estoma-proteccion', record.estoma_proteccion);
    s('f-dehiscencia', record.dehiscencia); onDehiscencia();
    s('f-tipo-dehiscencia', record.tipo_dehiscencia);
    s('f-t-tnm', record.t_tnm); s('f-n-tnm', record.n_tnm); s('f-m-tnm', record.m_tnm);
    s('f-estadio-tnm', record.estadio_tnm);
    s('f-localizacion', record.localizacion); onLocalizacion();
    s('f-distancia-margen-anal', record.distancia_margen_anal);
    s('f-neoadyuvancia', record.neoadyuvancia); onNeoadyuvancia();
    s('f-tipo-neoadyuvancia', record.tipo_neoadyuvancia); s('f-pcr', record.pcr);
    s('f-tipo-histologico', record.tipo_histologico); s('f-grado', record.grado);
    s('f-margenes-libres', record.margenes_libres);
    s('f-ganglios-analizados', record.ganglios_analizados);
    s('f-ganglios-positivos', record.ganglios_positivos);
    s('f-invasion-linfovascular', record.invasion_linfovascular);
    s('f-invasion-perineural', record.invasion_perineural); s('f-msi', record.msi);
    s('f-adyuvancia', record.adyuvancia); onAdyuvancia();
    s('f-tipo-adyuvancia', record.tipo_adyuvancia);
    s('f-fecha-exitus', record.fecha_exitus);
    INTERVALOS.forEach(m => {
      s(`f-recidiva-${m}m`, record[`recidiva_${m}m`]);
      onRecidiva(m);
      s(`f-tipo-recidiva-${m}m`, record[`tipo_recidiva_${m}m`]);
    });
  }
  onReintervencion(); onMortalidad();
  updateOncologicoVisibility();
}

// ── Save / Edit ──────────────────────────────────────────────
async function saveRecord() {
  if (!validateStep(currentStep)) return;
  const { tipo, data } = collectFormData();
  const endpoint = { colorrectal: '/api/colorrectal', proctologia: '/api/proctologia', funcionales: '/api/funcionales', general: '/api/general' }[tipo];
  if (!endpoint) { showToast('Selecciona un tipo de cirugía', 'error'); return; }
  try {
    if (editMode && editId) {
      await api('PUT', `${endpoint}/${editId}`, data);
      showToast('Registro actualizado correctamente');
    } else {
      await api('POST', endpoint, data);
      showToast('Registro guardado correctamente');
    }
    clearForm();
    goToStep(1);
  } catch (e) {
    showToast(e.message, 'error');
  }
}

function clearForm() {
  editMode = false; editId = null; editTipo = null;
  document.querySelectorAll('#form-step-1 input, #form-step-1 select, #form-step-2 input, #form-step-2 select, #form-step-3 input, #form-step-3 select, #form-step-4 input, #form-step-4 select, #form-step-4 textarea').forEach(el => {
    if (el.type !== 'button') el.value = '';
  });
  buildRecidivaTable();
  loadNextId();
  document.querySelectorAll('.hidden-cond').forEach(el => el.classList.add('hidden'));
  ['wrap-conversion','wrap-estoma','wrap-dehiscencia','wrap-tipo-dehiscencia','wrap-tipo-reintervencion',
   'wrap-causa-mortalidad','wrap-oncologico','wrap-dist-margen','wrap-tipo-neo','wrap-pcr','wrap-tipo-adyuvancia'].forEach(id => {
    document.getElementById(id)?.classList.add('hidden');
  });
}

// ── DB Table ─────────────────────────────────────────────────
function buildFiltersQuery() {
  const fd = document.getElementById('db-filter-fecha-desde').value;
  const fh = document.getElementById('db-filter-fecha-hasta').value;
  const cir = document.getElementById('db-filter-cirujano').value;
  const asa = document.getElementById('db-filter-asa').value;
  const nhc = document.getElementById('db-search-nhc').value;
  const p = new URLSearchParams({ page: dbCurrentPage, page_size: 20 });
  if (fd) p.set('fecha_desde', fd);
  if (fh) p.set('fecha_hasta', fh);
  if (cir) p.set('cirujano', cir);
  if (asa) p.set('asa', asa);
  if (nhc) p.set('nhc', nhc);
  return p.toString();
}

const TYPE_COLORS = {
  colorrectal: 'bg-blue-100 text-blue-800',
  proctologia: 'bg-green-100 text-green-800',
  funcionales: 'bg-purple-100 text-purple-800',
  general: 'bg-orange-100 text-orange-800',
};
const TYPE_LABELS = { colorrectal: 'Colorrectal', proctologia: 'Proctología', funcionales: 'Funcionales', general: 'General' };

async function loadDbTable() {
  const tbody = document.getElementById('db-table-body');
  tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-gray-400">Cargando...</td></tr>';
  const q = buildFiltersQuery();

  try {
    let rows = [], total = 0;
    if (dbCurrentTab === 'todos') {
      const results = await Promise.all([
        api('GET', `/api/colorrectal?${q}`),
        api('GET', `/api/proctologia?${q}`),
        api('GET', `/api/funcionales?${q}`),
        api('GET', `/api/general?${q}`),
      ]);
      const types = ['colorrectal','proctologia','funcionales','general'];
      results.forEach((r, i) => {
        if (r?.items) r.items.forEach(item => rows.push({ ...item, _tipo: types[i] }));
        total += r?.total || 0;
      });
      rows.sort((a, b) => new Date(b.fecha_intervencion) - new Date(a.fecha_intervencion));
      rows = rows.slice(0, 20);
    } else {
      const r = await api('GET', `/api/${dbCurrentTab}?${q}`);
      rows = (r?.items || []).map(item => ({ ...item, _tipo: dbCurrentTab }));
      total = r?.total || 0;
    }

    tbody.innerHTML = '';
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center py-12 text-gray-400">No hay registros</td></tr>';
    } else {
      rows.forEach(row => {
        const tr = document.createElement('tr');
        const tipo = row._tipo;
        tr.innerHTML = `
          <td class="font-mono text-xs text-gray-500">${row.id}</td>
          <td class="font-medium">${row.nhc || '—'}</td>
          <td>${row.fecha_intervencion || '—'}</td>
          <td><span class="badge ${TYPE_COLORS[tipo]}">${TYPE_LABELS[tipo]}</span></td>
          <td class="max-w-xs truncate text-sm" title="${row.diagnostico||''}">${row.diagnostico || '—'}</td>
          <td class="max-w-xs truncate text-sm" title="${row.intervencion||''}">${row.intervencion || '—'}</td>
          <td class="text-sm">${row.cirujano || '—'}</td>
          <td><span class="font-semibold">${row.asa || '—'}</span></td>
          <td class="text-sm">${row.abordaje || '—'}</td>
          <td>${row.clavien_dindo || '—'}</td>
          <td>
            <div class="flex gap-1">
              <button onclick='viewDetail("${tipo}",${row.id})' class="btn btn-ghost p-1.5 text-blue-600 hover:bg-blue-50" title="Ver">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              </button>
              <button onclick='editRecord("${tipo}",${row.id})' class="btn btn-ghost p-1.5 text-green-600 hover:bg-green-50" title="Editar">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              </button>
              <button onclick='deleteRecord("${tipo}",${row.id})' class="btn btn-ghost p-1.5 text-red-600 hover:bg-red-50" title="Eliminar">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              </button>
            </div>
          </td>`;
        tbody.appendChild(tr);
      });
    }
    dbTotalPages = Math.ceil(total / 20) || 1;
    document.getElementById('db-info').textContent = `${total} registro${total !== 1 ? 's' : ''}`;
    document.getElementById('db-page-info').textContent = `Pág. ${dbCurrentPage} / ${dbTotalPages}`;
    document.getElementById('db-prev-btn').disabled = dbCurrentPage <= 1;
    document.getElementById('db-next-btn').disabled = dbCurrentPage >= dbTotalPages;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="11" class="text-center py-8 text-red-400">${e.message}</td></tr>`;
  }
}

function switchDbTab(tab) {
  dbCurrentTab = tab;
  dbCurrentPage = 1;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.tab-btn-${tab === 'todos' ? 'todos' : tab}`)?.classList.add('active');
  loadDbTable();
}

function dbChangePage(delta) {
  const newPage = dbCurrentPage + delta;
  if (newPage < 1 || newPage > dbTotalPages) return;
  dbCurrentPage = newPage;
  loadDbTable();
}

function applyFilters() { dbCurrentPage = 1; loadDbTable(); }
function clearFilters() {
  ['db-search-nhc','db-filter-fecha-desde','db-filter-fecha-hasta','db-filter-cirujano','db-filter-asa'].forEach(id => {
    document.getElementById(id).value = '';
  });
  applyFilters();
}

async function searchAllNHC() {
  const nhc = document.getElementById('db-search-nhc').value;
  if (!nhc) { loadDbTable(); return; }
  try {
    const res = await api('GET', `/api/search?nhc=${encodeURIComponent(nhc)}`);
    const tbody = document.getElementById('db-table-body');
    tbody.innerHTML = '';
    if (!res?.length) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center py-12 text-gray-400">Sin resultados</td></tr>';
      return;
    }
    res.forEach(row => {
      const tipo = row.tipo;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="font-mono text-xs text-gray-500">${row.id}</td>
        <td class="font-medium">${row.nhc}</td>
        <td>${row.fecha_intervencion||'—'}</td>
        <td><span class="badge ${TYPE_COLORS[tipo]}">${TYPE_LABELS[tipo]}</span></td>
        <td colspan="3" class="text-sm">${row.diagnostico||'—'} / ${row.intervencion||'—'}</td>
        <td colspan="3" class="text-sm">${row.cirujano||'—'}</td>
        <td>
          <div class="flex gap-1">
            <button onclick='viewDetail("${tipo}",${row.id})' class="btn btn-ghost p-1.5 text-blue-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
            </button>
            <button onclick='editRecord("${tipo}",${row.id})' class="btn btn-ghost p-1.5 text-green-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            </button>
            <button onclick='deleteRecord("${tipo}",${row.id})' class="btn btn-ghost p-1.5 text-red-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </td>`;
      tbody.appendChild(tr);
    });
    document.getElementById('db-info').textContent = `${res.length} resultado(s)`;
    document.getElementById('db-page-info').textContent = '';
  } catch (e) { showToast(e.message, 'error'); }
}

// ── View detail ──────────────────────────────────────────────
async function viewDetail(tipo, id) {
  try {
    const record = await api('GET', `/api/${tipo}/${id}`);
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');
    const rows = Object.entries(record)
      .filter(([k]) => !['created_at','created_by'].includes(k))
      .map(([k, v]) => `<tr><td class="py-1.5 pr-4 font-medium text-gray-500 text-sm whitespace-nowrap">${k.replace(/_/g,' ')}</td><td class="py-1.5 text-sm text-gray-900">${v ?? '—'}</td></tr>`)
      .join('');
    content.innerHTML = `<div class="mb-3"><span class="badge ${TYPE_COLORS[tipo]} text-sm">${TYPE_LABELS[tipo]}</span></div><table>${rows}</table>`;
    modal.classList.add('open');
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Edit record ──────────────────────────────────────────────
async function editRecord(tipo, id) {
  try {
    const record = await api('GET', `/api/${tipo}/${id}`);
    clearForm();                              // resets editMode → false primero
    editMode = true; editId = id; editTipo = tipo;  // luego fijamos modo edición
    goToStep(1);
    showSection('formulario');
    document.getElementById('f-id').value = id;
    populateForm(tipo, record);
    showToast('Editando registro — guarda para confirmar', 'warn');
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Delete record ────────────────────────────────────────────
async function deleteRecord(tipo, id) {
  if (!confirm(`¿Eliminar el registro ${id} de ${TYPE_LABELS[tipo]}? Esta acción no se puede deshacer.`)) return;
  try {
    await api('DELETE', `/api/${tipo}/${id}`);
    showToast('Registro eliminado');
    loadDbTable();
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Modal ────────────────────────────────────────────────────
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// ── Dashboard ────────────────────────────────────────────────
let dashCurrentTab = 'global';

function switchDashTab(tab) {
  dashCurrentTab = tab;
  ['global','colorrectal','proctologia','funcionales','general'].forEach(t => {
    document.getElementById(`dash-${t}`)?.classList.toggle('hidden', t !== tab);
  });
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const map = { global: 'todos', colorrectal: 'colorrectal', proctologia: 'proctologia', funcionales: 'funcionales', general: 'general' };
  document.querySelector(`.tab-btn-${map[tab]}`)?.classList.add('active');
  loadDashboard(tab);
}

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

function mkChart(id, type, labels, datasets, opts = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id)?.getContext('2d');
  if (!ctx) return;
  charts[id] = new Chart(ctx, { type, data: { labels, datasets }, options: { responsive: true, plugins: { legend: { position: 'bottom' } }, ...opts } });
}

const PALETTE = ['#1565C0','#2E7D32','#6A1B9A','#E65100','#C62828','#00838F','#AD1457','#558B2F','#4527A0','#0277BD'];
const DONUT_OPTS = { responsive: true, plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } } };
const BAR_NOLABEL = { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { font: { size: 11 } } } } };
const BAR_Y_NOLABEL = { responsive: true, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { y: { ticks: { font: { size: 11 } } } } };

function kpiCard(label, value, color, sub = '') {
  return `<div class="stat-card" style="border-color:${color}">
    <div class="text-xl font-bold leading-tight" style="color:${color}">${value}</div>
    <div class="text-xs font-semibold text-gray-700 mt-1">${label}</div>
    ${sub ? `<div class="text-xs text-gray-400 mt-1">${sub}</div>` : ''}
  </div>`;
}

function mkDonut(id, obj, colors) {
  const entries = Object.entries(obj || {}).filter(([,v]) => v > 0);
  if (!entries.length) return;
  mkChart(id, 'doughnut', entries.map(([k]) => k), [{
    data: entries.map(([,v]) => v),
    backgroundColor: colors || PALETTE,
  }], DONUT_OPTS);
}

function mkBarH(id, obj, color) {
  const entries = Object.entries(obj || {}).filter(([,v]) => v > 0).sort(([,a],[,b]) => b - a);
  if (!entries.length) return;
  mkChart(id, 'bar', entries.map(([k]) => k.replace(/^(Neoplasia de |DR[A]?\. )/, '')), [{
    label: 'Casos', data: entries.map(([,v]) => v), backgroundColor: color,
  }], BAR_Y_NOLABEL);
}

function mkBarV(id, labels, data, color) {
  mkChart(id, 'bar', labels, [{ label: 'Casos', data, backgroundColor: color }], BAR_NOLABEL);
}

function mkClavienBar(id, obj, color) {
  const keys = ['0','I','II','IIIa','IIIb','IVa','IVb','V'];
  mkBarV(id, keys, keys.map(k => obj[k] || 0), color);
}

async function loadDashboard(tab) {
  try {
    // ── GLOBAL ──────────────────────────────────────────────
    if (tab === 'global') {
      const d = await api('GET', '/api/stats/global');
      if (!d) return;
      document.getElementById('dash-kpis').innerHTML = `
        ${kpiCard('Total Casos', d.total, '#0D2B4E', `CR:${d.colorrectal} Pr:${d.proctologia} Fu:${d.funcionales} Ge:${d.general}`)}
        ${kpiCard('Edad Media', d.edad_media + ' a', '#1565C0', `Estancia: ${d.estancia_media} d`)}
        ${kpiCard('Laparoscopia', d.pct_laparoscopia + '%', '#2E7D32', `Conversión: ${d.pct_conversion}%`)}
        ${kpiCard('Clavien ≥ II', d.pct_clavien_ge2 + '%', '#6A1B9A', `Reintervención: ${d.pct_reintervencion}%`)}
        ${kpiCard('Mortalidad 30d', d.pct_mortalidad + '%', '#C62828', `Reingreso: ${d.pct_reingreso_30d}%`)}
      `;
      mkDonut('chart-tipo',
        { Colorrectal: d.colorrectal, Proctología: d.proctologia, Funcionales: d.funcionales, General: d.general },
        ['#1565C0','#2E7D32','#6A1B9A','#E65100']
      );
      mkDonut('chart-abordaje', d.abordaje || {});
      mkBarH('chart-cirujano', d.por_cirujano || {}, '#1565C0');
      const monthly = d.monthly || [];
      mkChart('chart-mensual', 'line',
        monthly.map(m => m.mes),
        [{ label: 'Casos', data: monthly.map(m => m.n), borderColor: '#1565C0', backgroundColor: 'rgba(21,101,192,.12)', fill: true, tension: 0.4 }],
        { responsive: true, plugins: { legend: { display: false } } }
      );

    // ── COLORRECTAL ─────────────────────────────────────────
    } else if (tab === 'colorrectal') {
      const d = await api('GET', '/api/stats/colorrectal');
      if (!d) return;
      document.getElementById('dash-kpis-cr').innerHTML = `
        ${kpiCard('Total', d.total, '#1565C0', `Edad: ${d.edad_media} a`)}
        ${kpiCard('TQ Medio', d.tq_medio + ' min', '#1565C0', `Estancia: ${d.estancia_media} d`)}
        ${kpiCard('Conversión', d.pct_conversion + '%', '#1565C0', `Estoma prot.: ${d.pct_estoma_proteccion}%`)}
        ${kpiCard('Dehiscencia', d.pct_dehiscencia + '%', '#C62828', `Reintervención: ${d.pct_reintervencion}%`)}
        ${kpiCard('Neoadyuvancia', d.pct_neoadyuvancia + '%', '#2E7D32', `pCR: ${d.pct_pcr}%`)}
        ${kpiCard('Adyuvancia', d.pct_adyuvancia + '%', '#2E7D32', `Márgenes libres: ${d.pct_margenes_libres}%`)}
        ${kpiCard('Mortalidad 30d', d.pct_mortalidad + '%', '#C62828', `Reingreso: ${d.pct_reingreso_30d}%`)}
        ${kpiCard('Ganglios med.', d.ganglios_media, '#6A1B9A', `Clavien ≥ II: ${d.pct_clavien_ge2}%`)}
      `;
      // Donuts
      mkDonut('cr-chart-sexo', d.por_sexo, ['#1565C0','#E91E63']);
      mkDonut('cr-chart-asa', d.por_asa, ['#43A047','#FDD835','#FB8C00','#E53935','#7B1FA2']);
      mkDonut('cr-chart-abordaje', d.por_abordaje);
      mkDonut('cr-chart-urgencia', d.por_urgencia, ['#2E7D32','#C62828']);
      mkDonut('cr-chart-neo', d.por_neoadyuvancia, ['#C62828','#E0E0E0']);
      mkDonut('cr-chart-ady', d.por_adyuvancia, ['#1565C0','#E0E0E0']);
      // Barras
      const estKeys = ['0','I','IIA','IIB','IIC','IIIA','IIIB','IIIC','IVA','IVB','IVC'];
      mkBarV('cr-chart-estadio', estKeys, estKeys.map(k => (d.estadios||{})[k]||0), '#1565C0');
      mkClavienBar('cr-chart-clavien', d.por_clavien || {}, '#6A1B9A');
      mkBarH('cr-chart-cirujano', d.por_cirujano || {}, '#1565C0');
      mkBarH('cr-chart-diag', d.por_diagnostico || {}, '#1565C0');
      mkBarH('cr-chart-interv', d.por_intervencion || {}, '#42A5F5');
      // Recidiva
      const ri = d.recidiva_intervalos || {};
      mkChart('cr-chart-recidiva', 'line',
        INTERVALOS.map(m => `${m}m`),
        [{ label: 'Casos con recidiva', data: INTERVALOS.map(m => ri[`${m}m`]||0), borderColor: '#C62828', backgroundColor: 'rgba(198,40,40,.1)', fill: true, tension: 0.4, pointRadius: 5 }],
        { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
      );

    // ── PROCTOLOGÍA / FUNCIONALES / GENERAL ─────────────────
    } else {
      const colorMap = { proctologia: '#2E7D32', funcionales: '#6A1B9A', general: '#E65100' };
      const kpiIdMap = { proctologia: 'dash-kpis-pr', funcionales: 'dash-kpis-fu', general: 'dash-kpis-ge' };
      const pfx = tab.substring(0,2);  // pr, fu, ge
      const color = colorMap[tab];
      const d = await api('GET', `/api/stats/${tab}`);
      if (!d) return;
      document.getElementById(kpiIdMap[tab]).innerHTML = `
        ${kpiCard('Total', d.total, color, `Edad: ${d.edad_media} a`)}
        ${kpiCard('Estancia Media', d.estancia_media + ' d', color, `TQ: ${d.tq_medio} min`)}
        ${kpiCard('Reintervención', d.pct_reintervencion + '%', color, `Clavien ≥ II: ${d.pct_clavien_ge2}%`)}
        ${kpiCard('Mortalidad 30d', d.pct_mortalidad + '%', '#C62828', `Reingreso: ${d.pct_reingreso_30d}%`)}
        ${kpiCard('Laparoscopia', d.pct_laparoscopia + '%', color, `Conversión: ${d.pct_conversion}%`)}
      `;
      // Donuts
      mkDonut(`${pfx}-chart-sexo`, d.por_sexo, ['#1565C0','#E91E63']);
      mkDonut(`${pfx}-chart-asa`, d.por_asa, ['#43A047','#FDD835','#FB8C00','#E53935','#7B1FA2']);
      mkDonut(`${pfx}-chart-urgencia`, d.por_urgencia, ['#2E7D32','#C62828']);
      // Barras
      mkBarH(`${pfx}-chart-cirujano`, d.por_cirujano || {}, color);
      mkBarH(`${pfx}-chart-diag`, d.por_diagnostico || {}, color);
      mkBarH(`${pfx}-chart-interv`, d.por_intervencion || {}, color);
      mkClavienBar(`${pfx}-chart-clavien`, d.por_clavien || {}, '#6A1B9A');
      mkBarH(`${pfx}-chart-complic`, d.por_tipo_complicacion || {}, '#FB8C00');
    }
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Export ───────────────────────────────────────────────────
function doExport(format) {
  const tabla = document.getElementById('exp-tabla').value;
  const desde = document.getElementById('exp-desde').value;
  const hasta = document.getElementById('exp-hasta').value;
  const p = new URLSearchParams({ tabla });
  if (desde) p.set('fecha_desde', desde);
  if (hasta) p.set('fecha_hasta', hasta);
  const url = `/api/export/${format}?${p.toString()}`;
  const a = document.createElement('a');
  a.href = url;
  a.setAttribute('download', '');
  // Add auth via hidden form trick for downloads
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob())
    .then(blob => {
      const burl = URL.createObjectURL(blob);
      a.href = burl;
      a.click();
      URL.revokeObjectURL(burl);
    })
    .catch(e => showToast(e.message, 'error'));
}

// ── Backup ───────────────────────────────────────────────────
async function doBackup() {
  try {
    const res = await fetch('/api/export/backup', {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Error al descargar backup');
    }
    const blob = await res.blob();
    const cd = res.headers.get('Content-Disposition') || '';
    const match = cd.match(/filename=(.+)/);
    const filename = match ? match[1] : 'backup_coloproctologia.db';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Backup descargado correctamente');
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Restore ──────────────────────────────────────────────────
async function doRestore() {
  const fileInput = document.getElementById('restore-file');
  const file = fileInput.files[0];
  if (!file) { showToast('Selecciona un archivo .db', 'warn'); return; }
  const ok = confirm(
    '⚠️ ATENCIÓN: Esta acción reemplazará TODA la base de datos actual con el archivo seleccionado.\n\n' +
    'Se perderán todos los registros que no estén incluidos en el backup.\n\n' +
    '¿Deseas continuar?'
  );
  if (!ok) return;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/export/restore', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(data.detail || 'Error al restaurar');
    showToast(data.message || 'Base de datos restaurada correctamente');
    fileInput.value = '';
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Import CSV ───────────────────────────────────────────────
async function doImportCsv() {
  const fileInput = document.getElementById('import-csv-file');
  const file = fileInput.files[0];
  if (!file) { showToast('Selecciona un archivo .csv', 'warn'); return; }
  const ok = confirm(
    'Se añadirán los registros del CSV a la base de datos sin borrar los existentes.\n\n¿Deseas continuar?'
  );
  if (!ok) return;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/export/import-csv', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(data.detail || 'Error al importar');
    let msg = `Importación completada: ${data.insertados} registros añadidos`;
    if (data.omitidos) msg += `, ${data.omitidos} omitidos`;
    showToast(msg);
    if (data.errores && data.errores.length) {
      console.warn('Errores de importación:', data.errores);
    }
    fileInput.value = '';
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Recovery panel (login screen) ────────────────────────────
function showRecoveryPanel() {
  document.getElementById('login-panel').classList.add('hidden');
  document.getElementById('recovery-panel').classList.remove('hidden');
  document.getElementById('recovery-error').classList.add('hidden');
  document.getElementById('recovery-code-sent').classList.add('hidden');
  ['recovery-user','recovery-code','recovery-newpass','recovery-newpass2'].forEach(id => {
    document.getElementById(id).value = '';
  });
}

function showLoginPanel() {
  document.getElementById('recovery-panel').classList.add('hidden');
  document.getElementById('login-panel').classList.remove('hidden');
  document.getElementById('login-error').classList.add('hidden');
}

async function requestRecoveryCode() {
  const username = document.getElementById('recovery-user').value.trim();
  if (!username) { showRecoveryError('Introduce tu nombre de usuario'); return; }
  try {
    await api('POST', '/api/auth/recovery-code', { username });
    document.getElementById('recovery-code-sent').classList.remove('hidden');
    document.getElementById('recovery-error').classList.add('hidden');
  } catch (e) { showRecoveryError(e.message); }
}

async function resetPasswordWithCode() {
  const code = document.getElementById('recovery-code').value.trim();
  const np  = document.getElementById('recovery-newpass').value;
  const np2 = document.getElementById('recovery-newpass2').value;
  if (!code) { showRecoveryError('Introduce el código de 6 dígitos'); return; }
  if (!np)   { showRecoveryError('Introduce la nueva contraseña'); return; }
  if (np.length < 6) { showRecoveryError('La contraseña debe tener al menos 6 caracteres'); return; }
  if (np !== np2) { showRecoveryError('Las contraseñas no coinciden'); return; }
  try {
    await api('POST', '/api/auth/reset-password', { code, new_password: np });
    showLoginPanel();
    showToast('Contraseña restablecida. Ya puedes iniciar sesión');
  } catch (e) { showRecoveryError(e.message); }
}

function showRecoveryError(msg) {
  const el = document.getElementById('recovery-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

// ── Own password change ──────────────────────────────────────
function openOwnPasswordModal() {
  ['own-pass-current','own-pass-new','own-pass-new2'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('own-pass-error').classList.add('hidden');
  document.getElementById('own-password-modal').classList.add('open');
}

async function changeOwnPassword() {
  const current = document.getElementById('own-pass-current').value;
  const np      = document.getElementById('own-pass-new').value;
  const np2     = document.getElementById('own-pass-new2').value;
  const errEl   = document.getElementById('own-pass-error');
  errEl.classList.add('hidden');
  if (!current) { errEl.textContent = 'Introduce tu contraseña actual'; errEl.classList.remove('hidden'); return; }
  if (np.length < 6) { errEl.textContent = 'La nueva contraseña debe tener al menos 6 caracteres'; errEl.classList.remove('hidden'); return; }
  if (np !== np2) { errEl.textContent = 'Las contraseñas no coinciden'; errEl.classList.remove('hidden'); return; }
  try {
    await api('POST', '/api/auth/change-password', { current_password: current, new_password: np });
    closeModal('own-password-modal');
    showToast('Contraseña actualizada correctamente');
  } catch (e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
  }
}

// ── Admin: change any user's password ───────────────────────
let _adminPassTargetId = null;

function openAdminPasswordModal(uid, username) {
  _adminPassTargetId = uid;
  document.getElementById('admin-pass-username-label').textContent = `Usuario: ${username}`;
  ['admin-pass-new','admin-pass-new2'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('admin-pass-error').classList.add('hidden');
  document.getElementById('admin-password-modal').classList.add('open');
}

async function changeAdminPassword() {
  const np    = document.getElementById('admin-pass-new').value;
  const np2   = document.getElementById('admin-pass-new2').value;
  const errEl = document.getElementById('admin-pass-error');
  errEl.classList.add('hidden');
  if (np.length < 6) { errEl.textContent = 'La contraseña debe tener al menos 6 caracteres'; errEl.classList.remove('hidden'); return; }
  if (np !== np2) { errEl.textContent = 'Las contraseñas no coinciden'; errEl.classList.remove('hidden'); return; }
  try {
    await api('PATCH', `/api/admin/usuarios/${_adminPassTargetId}/password`, { new_password: np });
    closeModal('admin-password-modal');
    showToast('Contraseña actualizada');
  } catch (e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
  }
}

// ── Admin users ──────────────────────────────────────────────
async function loadAdminUsers() {
  try {
    const users = await api('GET', '/api/admin/usuarios');
    const tbody = document.getElementById('admin-users-table');
    tbody.innerHTML = '';
    (users || []).forEach(u => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="font-mono font-medium">${u.username}</td>
        <td>${u.nombre_completo || '—'}</td>
        <td>${u.es_admin ? '<span class="badge bg-blue-100 text-blue-800">Admin</span>' : '—'}</td>
        <td>${u.activo ? '<span class="badge bg-green-100 text-green-800">Activo</span>' : '<span class="badge bg-red-100 text-red-800">Inactivo</span>'}</td>
        <td class="flex gap-1 flex-wrap">
          <button onclick="toggleUser(${u.id})" class="btn btn-ghost text-sm ${u.activo ? 'text-red-600' : 'text-green-600'}">
            ${u.activo ? 'Desactivar' : 'Activar'}
          </button>
          <button onclick="openAdminPasswordModal(${u.id}, '${u.username}')" class="btn btn-ghost text-sm text-blue-600">
            Contraseña
          </button>
        </td>`;
      tbody.appendChild(tr);
    });
  } catch (e) { showToast(e.message, 'error'); }
}

function openNewUserModal() { document.getElementById('user-modal').classList.add('open'); }

async function createUser() {
  const username = document.getElementById('new-username').value;
  const password = document.getElementById('new-password').value;
  const nombre = document.getElementById('new-nombre').value;
  const esAdmin = document.getElementById('new-admin').checked;
  if (!username || !password) { showToast('Usuario y contraseña son obligatorios', 'error'); return; }
  try {
    await api('POST', '/api/admin/usuarios', { username, password, nombre_completo: nombre, es_admin: esAdmin });
    closeModal('user-modal');
    showToast('Usuario creado');
    loadAdminUsers();
    ['new-username','new-password','new-nombre'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('new-admin').checked = false;
  } catch (e) { showToast(e.message, 'error'); }
}

async function toggleUser(uid) {
  try {
    const r = await api('PATCH', `/api/admin/usuarios/${uid}/toggle`);
    showToast(r.activo ? 'Usuario activado' : 'Usuario desactivado');
    loadAdminUsers();
  } catch (e) { showToast(e.message, 'error'); }
}
