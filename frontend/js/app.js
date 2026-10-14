'use strict';

// ============================================
// SOZLAMALAR
// ============================================
const API_BASE_URL = '/api/v1';
const MAX_PROMPT_LENGTH = 2000;
const MAX_HISTORY_SIZE = 20;

// ============================================
// DOM ELEMENTLAR
// ============================================
const el = {
    promptInput: document.getElementById('prompt-input'),
    charCounter: document.getElementById('char-counter'),
    generateBtn: document.getElementById('generate-btn'),

    alert: document.getElementById('alert'),
    alertMessage: document.getElementById('alert-message'),
    alertClose: document.getElementById('alert-close'),

    loading: document.getElementById('loading'),
    emptyState: document.getElementById('empty-state'),

    tableSection: document.getElementById('table-section'),
    tableTitle: document.getElementById('table-title'),
    tableMeta: document.getElementById('table-meta'),
    tableEditedIndicator: document.getElementById('table-edited-indicator'),
    tableHead: document.getElementById('data-table-head'),
    tableBody: document.getElementById('data-table-body'),

    undoBtn: document.getElementById('undo-btn'),
    addRowBtn: document.getElementById('add-row-btn'),
    downloadExcelBtn: document.getElementById('download-excel-btn'),
};

// ============================================
// STATE
// ============================================
const state = {
    /** @type {null | object} */
    table: null,

    /** @type {null | object} */
    originalTable: null,

    isLoading: false,

    /**
     * Tarix stack (snapshot'lar).
     * @type {Array<{title: string, columns: string[], rows: any[][]}>}
     */
    history: [],

    /**
     * Har bir katak uchun oxirgi commit qilingan qiymat.
     * @type {Map<string, string>}
     */
    cellCommitted: new Map(),
};

// ============================================
// YORDAMCHI FUNKSIYALAR
// ============================================

/**
 * XSS himoyasi.
 */
function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Chuqur nusxa olish.
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Alert ko'rsatish.
 */
function showAlert(message, type = 'error') {
    const icons = { error: '⚠️', success: '✓', info: 'ℹ️' };
    el.alert.querySelector('.alert__icon').textContent = icons[type] || icons.error;

    el.alertMessage.textContent = message;
    el.alert.classList.remove('alert--error', 'alert--success');
    el.alert.classList.add(`alert--${type}`);
    el.alert.hidden = false;

    clearTimeout(showAlert._timer);
    showAlert._timer = setTimeout(() => hideAlert(), 6000);
}

function hideAlert() {
    el.alert.hidden = true;
}

/**
 * Loading holati.
 */
function setLoading(isLoading) {
    state.isLoading = isLoading;
    el.loading.hidden = !isLoading;
    el.generateBtn.disabled = isLoading;

    if (isLoading) {
        el.emptyState.hidden = true;
        el.tableSection.hidden = true;
    } else {
        if (state.table) {
            el.tableSection.hidden = false;
            el.emptyState.hidden = true;
        } else {
            el.tableSection.hidden = true;
            el.emptyState.hidden = false;
        }
    }
}

/**
 * Character counter.
 */
function updateCharCounter() {
    const length = el.promptInput.value.length;
    el.charCounter.textContent = `${length} / ${MAX_PROMPT_LENGTH}`;
    el.charCounter.classList.toggle(
        'char-counter--warning',
        length > MAX_PROMPT_LENGTH * 0.9
    );
}

/**
 * Ikkita jadval tengligini tekshirish.
 */
function tablesAreEqual(a, b) {
    if (!a || !b) return false;
    if (a.title !== b.title) return false;
    if (a.columns.length !== b.columns.length) return false;
    if (a.rows.length !== b.rows.length) return false;

    for (let i = 0; i < a.columns.length; i++) {
        if (a.columns[i] !== b.columns[i]) return false;
    }
    for (let i = 0; i < a.rows.length; i++) {
        if (a.rows[i].length !== b.rows[i].length) return false;
        for (let j = 0; j < a.rows[i].length; j++) {
            if (String(a.rows[i][j]) !== String(b.rows[i][j])) return false;
        }
    }
    return true;
}

/**
 * "O'zgartirilgan" belgisini yangilash.
 */
function updateEditedIndicator() {
    if (!state.table || !state.originalTable) {
        el.tableEditedIndicator.hidden = true;
        return;
    }
    const isEdited = !tablesAreEqual(state.table, state.originalTable);
    el.tableEditedIndicator.hidden = !isEdited;
}

/**
 * Meta ma'lumotlarni yangilash.
 */
function updateTableMeta() {
    if (!state.table) return;
    const t = state.table;
    el.tableMeta.textContent =
        `${t.row_count} qator × ${t.column_count} ustun — ` +
        `manba: ${t.source === 'ai' ? 'AI' : 'demo'}`;
}

/**
 * Undo tugmasining holatini yangilash.
 */
function updateUndoButton() {
    el.undoBtn.disabled = state.history.length === 0;
}

// ============================================
// HISTORY (TARIX) BOSHQARUVI
// ============================================

/**
 * Joriy holatni tarixga yozish.
 * Har bir O'ZGARISHDAN OLDIN chaqiriladi.
 */
function pushToHistory() {
    if (!state.table) return;

    const snapshot = {
        title: state.table.title,
        columns: [...state.table.columns],
        rows: state.table.rows.map((row) => [...row]),
    };

    state.history.push(snapshot);

    if (state.history.length > MAX_HISTORY_SIZE) {
        state.history.shift();
    }

    updateUndoButton();
}

/**
 * Undo — oxirgi amalni bekor qilish.
 * FAQAT BITTA snapshot'ni orqaga qaytaradi.
 */
function undo() {
    if (state.history.length === 0) {
        showAlert('Bekor qilish uchun amal yo\'q.', 'info');
        return;
    }

    const snapshot = state.history.pop();

    state.table.title = snapshot.title;
    state.table.columns = snapshot.columns;
    state.table.rows = snapshot.rows;
    state.table.row_count = snapshot.rows.length;
    state.table.column_count = snapshot.columns.length;

    renderTable(state.table, { keepHistory: true });

    updateUndoButton();
    showAlert('Oxirgi amal bekor qilindi.', 'info');
}

// ============================================
// API
// ============================================

async function requestTableGeneration(prompt) {
    const response = await fetch(`${API_BASE_URL}/tables/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
        let detail = `Server xatosi (${response.status})`;
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    detail = errorData.detail
                        .map((e) => `${e.loc?.join('.') || ''}: ${e.msg}`)
                        .join('; ');
                } else {
                    detail = errorData.detail;
                }
            }
        } catch (_) {
            // ignore
        }
        throw new Error(detail);
    }

    return response.json();
}

// ============================================
// RENDER
// ============================================

/**
 * Katakni tahrirlanadigan qilib yaratish.
 */
function createEditableCell(value, rowIndex, colIndex) {
    const td = document.createElement('td');
    td.contentEditable = 'true';
    td.spellcheck = false;
    td.dataset.rowIndex = String(rowIndex);
    td.dataset.colIndex = String(colIndex);

    const textValue = value === null || value === undefined ? '' : String(value);
    td.textContent = textValue;

    return td;
}

/**
 * Qator uchun o'chirish tugmasini yaratish.
 */
function createDeleteButton(rowIndex) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'row-delete-btn';
    btn.title = 'Qatorni o\'chirish';
    btn.setAttribute('aria-label', 'Delete row');
    btn.dataset.rowIndex = String(rowIndex);
    btn.textContent = '🗑';
    return btn;
}

/**
 * Jadvalni DOM'ga chizish.
 */
function renderTable(tableData, options = {}) {
    const { keepHistory = false } = options;

    state.table = tableData;

    if (!keepHistory) {
        state.originalTable = deepClone(tableData);
        state.history = [];
        updateUndoButton();
    }

    el.tableTitle.value = tableData.title;

    updateTableMeta();
    updateEditedIndicator();

    // Thead
    el.tableHead.innerHTML = '';
    const headerRow = document.createElement('tr');

    tableData.columns.forEach((col) => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });

    const thActions = document.createElement('th');
    thActions.className = 'col-actions';
    thActions.setAttribute('aria-label', 'Actions');
    headerRow.appendChild(thActions);

    el.tableHead.appendChild(headerRow);

    // Tbody
    el.tableBody.innerHTML = '';
    tableData.rows.forEach((row, rowIndex) => {
        const tr = document.createElement('tr');
        tr.dataset.rowIndex = String(rowIndex);

        row.forEach((cell, colIndex) => {
            const td = createEditableCell(cell, rowIndex, colIndex);
            tr.appendChild(td);
        });

        const tdActions = document.createElement('td');
        tdActions.className = 'col-actions';
        tdActions.appendChild(createDeleteButton(rowIndex));
        tr.appendChild(tdActions);

        el.tableBody.appendChild(tr);
    });

    el.emptyState.hidden = true;
    el.tableSection.hidden = false;
}

// ============================================
// TAHRIRLASH — EVENT HANDLERS
// ============================================

/**
 * Katak tahriri tugaganda (blur).
 */
function handleCellBlur(event) {
    const td = event.target;
    if (!td.dataset.rowIndex) return;

    const rowIndex = parseInt(td.dataset.rowIndex, 10);
    const colIndex = parseInt(td.dataset.colIndex, 10);
    if (!state.table || !state.table.rows[rowIndex]) return;

    const trimmed = td.textContent.trim();
    if (trimmed !== td.textContent) {
        td.textContent = trimmed;
    }

    const newValue = td.textContent;
    const oldValue = String(state.table.rows[rowIndex][colIndex] ?? '');

    if (newValue === oldValue) {
        return;
    }

    pushToHistory();

    state.table.rows[rowIndex][colIndex] = newValue;

    updateEditedIndicator();
    updateTableMeta();
}

/**
 * Enter / Escape.
 */
function handleCellKeydown(event) {
    const td = event.target;
    if (!td.dataset.rowIndex) return;

    if (event.key === 'Enter') {
        event.preventDefault();
        td.blur();
    }

    if (event.key === 'Escape') {
        event.preventDefault();
        const rowIndex = parseInt(td.dataset.rowIndex, 10);
        const colIndex = parseInt(td.dataset.colIndex, 10);
        if (state.table && state.table.rows[rowIndex]) {
            const original = state.table.rows[rowIndex][colIndex];
            td.textContent = original === null || original === undefined
                ? ''
                : String(original);
        }
        td.blur();
    }
}

/**
 * Jadval nomi o'zgarganda.
 */
function handleTitleBlur() {
    if (!state.table) return;

    const newTitle = el.tableTitle.value.trim() || 'Untitled table';
    if (newTitle === state.table.title) return;

    pushToHistory();
    state.table.title = newTitle;
    el.tableTitle.value = newTitle;
    updateEditedIndicator();
}

// ============================================
// ADD ROW / DELETE ROW
// ============================================

/**
 * Yangi bo'sh qator qo'shish.
 */
function handleAddRow() {
    if (!state.table) return;

    pushToHistory();

    const emptyRow = state.table.columns.map(() => '');
    state.table.rows.push(emptyRow);
    state.table.row_count = state.table.rows.length;

    renderTable(state.table, { keepHistory: true });
    updateEditedIndicator();
    updateTableMeta();

    const lastRow = el.tableBody.lastElementChild;
    if (lastRow) {
        lastRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    showAlert('Yangi qator qo\'shildi.', 'success');
}

/**
 * Qatorni o'chirish.
 */
function handleDeleteRow(event) {
    const btn = event.target.closest('.row-delete-btn');
    if (!btn) return;

    const rowIndex = parseInt(btn.dataset.rowIndex, 10);
    if (!state.table || !state.table.rows[rowIndex]) return;

    if (state.table.rows.length <= 1) {
        showAlert('Kamida bitta qator bo\'lishi kerak.', 'error');
        return;
    }

    if (!confirm(`${rowIndex + 1}-qatorni o'chirishni tasdiqlaysizmi?`)) {
        return;
    }

    pushToHistory();

    state.table.rows.splice(rowIndex, 1);
    state.table.row_count = state.table.rows.length;

    renderTable(state.table, { keepHistory: true });
    updateEditedIndicator();
    updateTableMeta();

    showAlert('Qator o\'chirildi.', 'info');
}

// ============================================
// EXCEL EKSPORT
// ============================================

/**
 * Excel fayl yuklab olish.
 */
async function handleDownloadExcel() {
    if (!state.table) {
        showAlert('Avval jadval yarating.', 'error');
        return;
    }

    const btn = el.downloadExcelBtn;
    const labelEl = btn.querySelector('.btn__label');
    const originalLabel = labelEl.textContent;

    btn.classList.add('btn--loading');
    btn.disabled = true;
    labelEl.textContent = 'Preparing...';

    try {
        const response = await fetch(`${API_BASE_URL}/excel/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: state.table.title,
                columns: state.table.columns,
                rows: state.table.rows,
            }),
        });

        if (!response.ok) {
            let detail = `Server xatosi (${response.status})`;
            try {
                const err = await response.json();
                if (err.detail) detail = err.detail;
            } catch (_) { /* ignore */ }
            throw new Error(detail);
        }

        const blob = await response.blob();
        const filename = 'smartsheet.xlsx';

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showAlert('Excel fayl yuklab olindi!', 'success');
    } catch (error) {
        console.error('Excel export error:', error);
        showAlert(error.message || 'Excel yuklab olishda xatolik.', 'error');
    } finally {
        btn.classList.remove('btn--loading');
        btn.disabled = false;
        labelEl.textContent = originalLabel;
    }
}

// ============================================
// CTRL+Z — GLOBAL KEYBOARD
// ============================================

/**
 * Ctrl+Z / Cmd+Z ni ushlash.
 */
function handleGlobalKeydown(event) {
    const isUndo = (event.ctrlKey || event.metaKey) &&
                   !event.shiftKey &&
                   event.key.toLowerCase() === 'z';

    if (!isUndo) return;
    if (!state.table) return;

    const tag = (event.target.tagName || '').toLowerCase();
    const isEditable = event.target.isContentEditable;

    if (tag === 'input' || tag === 'textarea') {
        return;
    }
    if (isEditable && event.target.dataset.rowIndex) {
        event.preventDefault();
        document.execCommand('undo');
        return;
    }

    event.preventDefault();
    undo();
}

// ============================================
// ASOSIY OQIM
// ============================================

async function handleGenerate() {
    const prompt = el.promptInput.value.trim();

    if (!prompt) {
        showAlert('Iltimos, jadval tavsifini kiriting.');
        el.promptInput.focus();
        return;
    }
    if (prompt.length < 3) {
        showAlert('Prompt juda qisqa. Iltimos, batafsilroq yozing.');
        el.promptInput.focus();
        return;
    }
    if (prompt.length > MAX_PROMPT_LENGTH) {
        showAlert(`Prompt ${MAX_PROMPT_LENGTH} belgidan oshmasligi kerak.`);
        return;
    }

    hideAlert();
    setLoading(true);

    try {
        const tableData = await requestTableGeneration(prompt);
        renderTable(tableData);
        showAlert('Jadval muvaffaqiyatli yaratildi!', 'success');
    } catch (error) {
        console.error('Generate error:', error);
        showAlert(error.message || 'Jadval yaratishda xatolik yuz berdi.');

        if (!state.table) {
            el.emptyState.hidden = false;
        } else {
            el.tableSection.hidden = false;
        }
    } finally {
        setLoading(false);
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

function bindEvents() {
    el.generateBtn.addEventListener('click', handleGenerate);

    el.promptInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleGenerate();
        }
    });

    el.promptInput.addEventListener('input', updateCharCounter);
    el.alertClose.addEventListener('click', hideAlert);

    // Tahrirlash
    el.tableBody.addEventListener('blur', handleCellBlur, true);
    el.tableBody.addEventListener('keydown', handleCellKeydown);
    el.tableTitle.addEventListener('blur', handleTitleBlur);

    // Action panel
    el.undoBtn.addEventListener('click', undo);
    el.addRowBtn.addEventListener('click', handleAddRow);
    el.downloadExcelBtn.addEventListener('click', handleDownloadExcel);

    // Delete Row
    el.tableBody.addEventListener('click', handleDeleteRow);

    // Ctrl+Z
    document.addEventListener('keydown', handleGlobalKeydown);
}

// ============================================
// INIT
// ============================================

function init() {
    bindEvents();
    updateCharCounter();
    updateUndoButton();
    console.log('✅ SmartSheet AI frontend tayyor (7-bosqich)');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}