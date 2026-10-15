/**
 * SmartSheet AI — App moduli.
 *
 * Bu modul:
 * - Sidebar bilan bog'lanadi
 * - Chat view'ni boshqaradi
 * - Xabarlar va jadvalni yuklaydi
 * - Xabar yuboradi (AI generate)
 * - Jadvalni tahrirlaydi (Undo/Redo, qator)
 * - Excel eksport
 */

'use strict';

// ============================================
// SOZLAMALAR
// ============================================
const MAX_PROMPT_LENGTH = 2000;
const MAX_HISTORY_SIZE = 20;

// ============================================
// DOM ELEMENTLAR
// ============================================
const el = {
    // Main panels
    emptyState: document.getElementById('empty-state'),
    chatView: document.getElementById('chat-view'),

    // Chat header
    chatTitle: document.getElementById('chat-title'),
    deleteChatBtn: document.getElementById('delete-chat-btn'),
    downloadExcelBtn: document.getElementById('download-excel-btn'),

    // Chat body
    chatBody: document.getElementById('chat-body'),
    messagesList: document.getElementById('messages-list'),
    loading: document.getElementById('loading'),

    // Table
    tableSection: document.getElementById('table-section'),
    tableTitle: document.getElementById('table-title'),
    tableMeta: document.getElementById('table-meta'),
    tableEditedIndicator: document.getElementById('table-edited-indicator'),
    tableHead: document.getElementById('data-table-head'),
    tableBody: document.getElementById('data-table-body'),
    undoBtn: document.getElementById('undo-btn'),
    redoBtn: document.getElementById('redo-btn'),
    addRowBtn: document.getElementById('add-row-btn'),

    // Chat footer
    promptInput: document.getElementById('prompt-input'),
    generateBtn: document.getElementById('generate-btn'),
    charCounter: document.getElementById('char-counter'),

    // Alert
    alert: document.getElementById('alert'),
    alertMessage: document.getElementById('alert-message'),
    alertClose: document.getElementById('alert-close'),
    deleteConfirmDialog: document.getElementById('delete-confirm-dialog'),
    deleteConfirmMessage: document.getElementById('delete-confirm-message'),
    deleteConfirmCancel: document.getElementById('delete-confirm-cancel'),
    deleteConfirmAccept: document.getElementById('delete-confirm-accept'),
};

// ============================================
// STATE
// ============================================
const state = {
    /** @type {number|null} Joriy chat ID */
    chatId: null,

    /** @type {object|null} Chat ma'lumotlari */
    chat: null,

    /** @type {object|null} Jadval */
    table: null,

    /** @type {object|null} Asl jadval (o'zgarishni aniqlash) */
    originalTable: null,

    /** @type {Array<object>} Xabarlar */
    messages: [],

    /** Undo stack */
    history: [],

    /** Redo stack */
    redoHistory: [],

    /** Yuklanmoqda */
    isLoading: false,

    deleteConfirmationResolve: null,
    deleteConfirmationPreviousFocus: null,
};

// ============================================
// YORDAMCHI
// ============================================

function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

function isFormula(value) {
    return (
        typeof value === 'string' &&
        value.startsWith('=') &&
        value.length > 1
    );
}

function countFormulas(rows) {
    if (!rows) return 0;
    let count = 0;
    for (const row of rows) {
        for (const cell of row) {
            if (isFormula(cell)) count++;
        }
    }
    return count;
}

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

// ============================================
// ALERT
// ============================================
function showAlert(message, type = 'error') {
    const icons = { error: '⚠️', success: '✓', info: 'ℹ️' };
    el.alert.querySelector('.alert__icon').textContent = icons[type] || icons.error;

    el.alertMessage.textContent = message;
    el.alert.classList.remove('alert--error', 'alert--success', 'alert--info');
    el.alert.classList.add(`alert--${type}`);
    el.alert.hidden = false;

    clearTimeout(showAlert._timer);
    showAlert._timer = setTimeout(() => hideAlert(), 5000);
}

function hideAlert() {
    el.alert.hidden = true;
}

function confirmDeleteChat(title) {
    if (state.deleteConfirmationResolve) return Promise.resolve(false);

    el.deleteConfirmMessage.textContent =
        `"${title}" chatini rostdan ham o'chirmoqchimisiz?`;
    state.deleteConfirmationPreviousFocus = document.activeElement;
    el.deleteConfirmDialog.hidden = false;
    el.deleteConfirmAccept.focus();

    return new Promise((resolve) => {
        state.deleteConfirmationResolve = resolve;
    });
}

function finishDeleteConfirmation(confirmed) {
    if (!state.deleteConfirmationResolve) return;

    const resolve = state.deleteConfirmationResolve;
    const previousFocus = state.deleteConfirmationPreviousFocus;
    state.deleteConfirmationResolve = null;
    state.deleteConfirmationPreviousFocus = null;
    el.deleteConfirmDialog.hidden = true;
    resolve(confirmed);

    if (previousFocus instanceof HTMLElement && previousFocus.isConnected) {
        previousFocus.focus();
    }
}

function handleDeleteDialogKeydown(event) {
    if (event.key === 'Escape') {
        event.preventDefault();
        finishDeleteConfirmation(false);
        return;
    }

    if (event.key !== 'Tab') return;

    const buttons = [el.deleteConfirmCancel, el.deleteConfirmAccept];
    const firstButton = buttons[0];
    const lastButton = buttons[buttons.length - 1];

    if (event.shiftKey && document.activeElement === firstButton) {
        event.preventDefault();
        lastButton.focus();
    } else if (!event.shiftKey && document.activeElement === lastButton) {
        event.preventDefault();
        firstButton.focus();
    }
}

// ============================================
// LOADING
// ============================================
function setLoading(isLoading) {
    state.isLoading = isLoading;
    el.loading.hidden = !isLoading;
    el.generateBtn.disabled = isLoading;
}

// ============================================
// CHAT VIEW — KO'RSATISH/YASHIRISH
// ============================================
function showEmptyState() {
    el.emptyState.hidden = false;
    el.chatView.hidden = true;
    state.chatId = null;
    state.chat = null;
    state.table = null;
    state.messages = [];
}

function showChatView() {
    el.emptyState.hidden = true;
    el.chatView.hidden = false;
}

// ============================================
// CHAT YUKLASH
// ============================================
async function loadChat(chatId) {
    if (!chatId) {
        showEmptyState();
        return;
    }

    state.chatId = chatId;
    showChatView();
    setLoading(true);

    try {
        // Parallel yuklash
        const [chat, messagesData, tableData] = await Promise.all([
            window.API.Chats.get(chatId),
            window.API.Messages.list(chatId).catch(() => ({ messages: [], total: 0 })),
            window.API.Table.get(chatId).catch(() => null),
        ]);

        state.chat = chat;
        state.messages = messagesData.messages || [];
        state.table = tableData;

        // Chat title
        el.chatTitle.value = chat.title || '';

        // Xabarlarni chizish
        renderMessages();

        // Jadvalni chizish
        if (tableData) {
            renderTable(tableData);
            el.tableSection.hidden = false;
        } else {
            el.tableSection.hidden = true;
        }

        // Scroll pastga
        scrollToBottom();
    } catch (err) {
        console.error('Chat yuklanmadi:', err);
        showAlert(err.message || 'Chat yuklanmadi', 'error');
        showEmptyState();
    } finally {
        setLoading(false);
    }
}

// ============================================
// XABARLAR
// ============================================
function renderMessages() {
    el.messagesList.innerHTML = '';

    if (state.messages.length === 0) {
        // Bo'sh chat — ko'rsatma
        const hint = document.createElement('div');
        hint.className = 'messages-empty';
        hint.innerHTML = `
            <p>👇 Jadval yaratish uchun quyida xabar yozing</p>
            <p class="messages-empty__example">
                Misol: "5 ta xodim uchun jadval yarat, ism va maosh ustunlari bilan"
            </p>
        `;
        el.messagesList.appendChild(hint);
        return;
    }

    state.messages.forEach((msg) => {
        el.messagesList.appendChild(createMessageEl(msg));
    });
}

function createMessageEl(message) {
    const div = document.createElement('div');
    div.className = `message message--${message.role === 'user' ? 'user' : 'ai'}`;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'message__avatar';
    avatar.textContent = message.role === 'user' ? '👤' : '🤖';
    div.appendChild(avatar);

    // Content wrapper
    const wrapper = document.createElement('div');

    // Content
    const content = document.createElement('div');
    content.className = 'message__content';
    content.textContent = message.content;
    wrapper.appendChild(content);

    // Time
    const time = document.createElement('div');
    time.className = 'message__time';
    time.textContent = formatTime(message.created_at);
    wrapper.appendChild(time);

    div.appendChild(wrapper);
    return div;
}

function formatTime(isoString) {
    if (!isoString) return '';
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString('uz-UZ', {
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch (_) {
        return '';
    }
}

function scrollToBottom() {
    if (el.messagesList) {
        el.messagesList.scrollTop = el.messagesList.scrollHeight;
    }
}

// ============================================
// JADVAL
// ============================================
function renderTable(tableData, { preserveHistory = false } = {}) {
    state.table = tableData;
    if (!preserveHistory) {
        state.originalTable = deepClone(tableData);
        state.history = [];
        state.redoHistory = [];
    }

    // Title
    el.tableTitle.textContent = tableData.title || 'Jadval';
    updateTableMeta();
    updateEditedIndicator();
    updateHistoryButtons();

    // Thead
    el.tableHead.innerHTML = '';
    const headerRow = document.createElement('tr');
    (tableData.columns || []).forEach((col) => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    const thActions = document.createElement('th');
    thActions.className = 'col-actions';
    headerRow.appendChild(thActions);
    el.tableHead.appendChild(headerRow);

    // Tbody
    el.tableBody.innerHTML = '';
    (tableData.rows || []).forEach((row, rowIndex) => {
        const tr = document.createElement('tr');
        tr.dataset.rowIndex = String(rowIndex);

        row.forEach((cell, colIndex) => {
            const td = createEditableCell(cell, rowIndex, colIndex);
            tr.appendChild(td);
        });

        // Delete button
        const tdActions = document.createElement('td');
        tdActions.className = 'col-actions';
        tdActions.appendChild(createDeleteButton(rowIndex));
        tr.appendChild(tdActions);

        el.tableBody.appendChild(tr);
    });

    el.tableSection.hidden = false;
}

function createEditableCell(value, rowIndex, colIndex) {
    const td = document.createElement('td');
    td.contentEditable = 'true';
    td.spellcheck = false;
    td.dataset.rowIndex = String(rowIndex);
    td.dataset.colIndex = String(colIndex);

    const textValue = value === null || value === undefined ? '' : String(value);

    if (isFormula(textValue)) {
        const displayValue = window.evaluateFormula
            ? window.evaluateFormula(textValue, state.table.rows, rowIndex, colIndex)
            : textValue;
        td.textContent = displayValue;
        td.classList.add('cell--formula');
        td.dataset.isFormula = 'true';
        td.dataset.formula = textValue;
        td.title = `Formula: ${textValue}`;
    } else {
        td.textContent = textValue;
    }

    return td;
}

function createDeleteButton(rowIndex) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'row-delete-btn';
    btn.title = 'Qatorni o\'chirish';
    btn.dataset.rowIndex = String(rowIndex);
    btn.textContent = '🗑';
    return btn;
}

function updateTableMeta() {
    if (!state.table) return;
    const t = state.table;
    const formulaCount = countFormulas(t.rows);

    let meta = `${t.rows.length} qator × ${t.columns.length} ustun`;
    if (formulaCount > 0) {
        meta += ` — ${formulaCount} formula`;
    }
    el.tableMeta.textContent = meta;
}

function updateEditedIndicator() {
    if (!state.table || !state.originalTable) {
        el.tableEditedIndicator.hidden = true;
        return;
    }
    const isEdited = !tablesAreEqual(state.table, state.originalTable);
    el.tableEditedIndicator.hidden = !isEdited;
}

function updateHistoryButtons() {
    if (el.undoBtn) el.undoBtn.disabled = state.history.length === 0;
    if (el.redoBtn) el.redoBtn.disabled = state.redoHistory.length === 0;
}

// ============================================
// HISTORY
// ============================================
function createTableSnapshot() {
    return {
        title: state.table.title,
        columns: [...state.table.columns],
        rows: state.table.rows.map((row) => [...row]),
    };
}

function pushToHistory() {
    if (!state.table) return;
    state.history.push(createTableSnapshot());
    state.redoHistory = [];
    if (state.history.length > MAX_HISTORY_SIZE) state.history.shift();
    updateHistoryButtons();
}

function restoreTableSnapshot(snapshot) {
    state.table.title = snapshot.title;
    state.table.columns = snapshot.columns;
    state.table.rows = snapshot.rows;
    renderTable(state.table, { preserveHistory: true });
}

function undo() {
    if (state.history.length === 0) return;
    state.redoHistory.push(createTableSnapshot());
    restoreTableSnapshot(state.history.pop());
    updateHistoryButtons();
}

function redo() {
    if (state.redoHistory.length === 0) return;
    state.history.push(createTableSnapshot());
    restoreTableSnapshot(state.redoHistory.pop());
    updateHistoryButtons();
}

// ============================================
// TAHRIRLASH — EVENT HANDLERS
// ============================================
function handleCellBlur(event) {
    const td = event.target;
    if (!td.dataset.rowIndex) return;

    const rowIndex = parseInt(td.dataset.rowIndex, 10);
    const colIndex = parseInt(td.dataset.colIndex, 10);
    if (!state.table || !state.table.rows[rowIndex]) return;

    const trimmed = td.textContent.trim();
    if (trimmed !== td.textContent) td.textContent = trimmed;

    const newValue = td.textContent;
    const storedValue = state.table.rows[rowIndex][colIndex];
    const oldValue = String(storedValue ?? '');

    if (
        isFormula(storedValue) &&
        window.evaluateFormula &&
        String(window.evaluateFormula(
            storedValue,
            state.table.rows,
            rowIndex,
            colIndex
        )) === newValue
    ) {
        return;
    }

    if (newValue === oldValue) return;

    pushToHistory();
    state.table.rows[rowIndex][colIndex] = newValue;

    // Formula holatini yangilash
    if (isFormula(newValue)) {
        td.classList.add('cell--formula');
        td.dataset.isFormula = 'true';
        td.dataset.formula = newValue;
    } else {
        td.classList.remove('cell--formula');
        delete td.dataset.isFormula;
        delete td.dataset.formula;
    }

    updateEditedIndicator();
    updateTableMeta();
}

function handleCellKeydown(event) {
    const td = event.target;
    if (!td.dataset.rowIndex) return;

    if (event.key === 'Enter' && !event.shiftKey) {
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

function handleAddRow() {
    if (!state.table) return;

    pushToHistory();
    const emptyRow = state.table.columns.map(() => '');
    state.table.rows.push(emptyRow);

    renderTable(state.table, { preserveHistory: true });
    updateEditedIndicator();
    updateTableMeta();

    // Scroll pastga
    const lastRow = el.tableBody.lastElementChild;
    if (lastRow) lastRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleDeleteRow(event) {
    const btn = event.target.closest('.row-delete-btn');
    if (!btn) return;

    const rowIndex = parseInt(btn.dataset.rowIndex, 10);
    if (!state.table || !state.table.rows[rowIndex]) return;

    if (state.table.rows.length <= 1) {
        showAlert('Kamida bitta qator bo\'lishi kerak.', 'error');
        return;
    }

    if (!confirm(`${rowIndex + 1}-qatorni o'chirishni tasdiqlaysizmi?`)) return;

    pushToHistory();
    state.table.rows.splice(rowIndex, 1);

    renderTable(state.table, { preserveHistory: true });
    updateEditedIndicator();
    updateTableMeta();
}

// ============================================
// XABAR YUBORISH (AI generate)
// ============================================
async function handleGenerate() {
    if (!state.chatId) {
        showAlert('Avval chat tanlang.', 'error');
        return;
    }

    const prompt = el.promptInput.value.trim();
    if (!prompt) {
        showAlert('Xabar bo\'sh.', 'error');
        el.promptInput.focus();
        return;
    }
    if (prompt.length < 3) {
        showAlert('Xabar juda qisqa.', 'error');
        el.promptInput.focus();
        return;
    }

    // Optimistic: userni darhol ko'rsatish
    const tempUserMsg = {
        id: 'temp-user',
        role: 'user',
        content: prompt,
        created_at: new Date().toISOString(),
    };
    state.messages.push(tempUserMsg);
    renderMessages();
    scrollToBottom();

    // Input tozalash
    el.promptInput.value = '';
    updateCharCounter();

    setLoading(true);

    try {
        const result = await window.API.AIGenerate.generate(state.chatId, prompt);

        // Userni almashtirish (haqiqiy)
        state.messages = state.messages.filter((m) => m.id !== 'temp-user');
        state.messages.push(result.user_message);
        state.messages.push(result.ai_message);
        renderMessages();
        scrollToBottom();

        // Jadvalni yangilash
        if (result.table) {
            renderTable(result.table);
            el.tableSection.hidden = false;
        }

        if (result.chat) {
            state.chat = result.chat;
            el.chatTitle.value = result.chat.title;
        }

        // Sidebar'ni yangilash
        if (window.Sidebar) {
            window.Sidebar.updateChat({
                id: state.chatId,
                ...(result.chat || {}),
                id: state.chatId,
                title: result.chat?.title || result.table?.title || state.chat?.title,
                message_count: result.chat?.message_count ?? state.messages.length,
                has_table: result.chat?.has_table ?? !!result.table,
            });
        }
    } catch (err) {
        console.error('Generate xatosi:', err);
        showAlert(err.message || 'AI xatosi', 'error');

        // Temp userni olib tashlash
        state.messages = state.messages.filter((m) => m.id !== 'temp-user');
        renderMessages();
    } finally {
        setLoading(false);
    }
}

function updateCharCounter() {
    const length = el.promptInput.value.length;
    el.charCounter.textContent = `${length} / ${MAX_PROMPT_LENGTH}`;
}

// ============================================
// CHAT TITLE
// ============================================
async function handleChatTitleBlur() {
    if (!state.chatId) return;
    const newTitle = el.chatTitle.value.trim() || 'Yangi chat';
    if (newTitle === state.chat?.title) return;

    try {
        const updated = await window.API.Chats.update(state.chatId, newTitle);
        state.chat = updated;
        el.chatTitle.value = updated.title;

        if (window.Sidebar) {
            window.Sidebar.updateChat(updated);
        }
    } catch (err) {
        console.error('Title update xatosi:', err);
        showAlert('Nomni o\'zgartirishda xato', 'error');
    }
}

// ============================================
// CHAT O'CHIRISH
// ============================================
async function handleDeleteChat() {
    const chatId = state.chatId;
    if (!chatId) return;
    const title = state.chat?.title || 'Chat';

    if (!(await confirmDeleteChat(title))) return;

    try {
        await window.API.Chats.delete(chatId);

        if (window.Sidebar) {
            window.Sidebar.removeChat(chatId);
        }

        if (state.chatId === chatId) {
            showEmptyState();
        }
        showAlert('Chat o\'chirildi', 'info');
    } catch (err) {
        console.error('Chat delete xatosi:', err);
        showAlert(err.message || 'Chatni o\'chirishda xato', 'error');
    }
}

// ============================================
// EXCEL EXPORT
// ============================================
async function handleDownloadExcel() {
    if (!state.table) {
        showAlert('Avval jadval yarating.', 'error');
        return;
    }

    const btn = el.downloadExcelBtn;
    const labelEl = btn.querySelector('.btn__label');
    const originalLabel = labelEl ? labelEl.textContent : '';

    btn.disabled = true;
    if (labelEl) labelEl.textContent = '...';

    try {
        const blob = await window.API.Excel.export({
            title: state.table.title,
            columns: state.table.columns,
            rows: state.table.rows,
        });

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'smartsheet.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showAlert('Excel yuklab olindi!', 'success');
    } catch (err) {
        console.error('Excel xatosi:', err);
        showAlert(err.message || 'Excel xatosi', 'error');
    } finally {
        btn.disabled = false;
        if (labelEl) labelEl.textContent = originalLabel;
    }
}

// ============================================
// GLOBAL KEYBOARD
// ============================================
function handleGlobalKeydown(event) {
    // Ctrl+Enter — yuborish
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        if (event.target === el.promptInput) {
            event.preventDefault();
            handleGenerate();
            return;
        }
    }

    const modifierKey = event.ctrlKey || event.metaKey;
    const key = event.key.toLowerCase();
    const isUndo = modifierKey && !event.shiftKey && key === 'z';
    const isRedo = modifierKey && (
        key === 'y' || (event.shiftKey && key === 'z')
    );

    if (!isUndo && !isRedo) return;
    if (!state.table) return;

    const tag = (event.target.tagName || '').toLowerCase();
    const isTableCell = event.target.isContentEditable &&
        event.target.dataset.rowIndex !== undefined;
    if ((tag === 'input' || tag === 'textarea') && !isTableCell) return;

    event.preventDefault();
    if (isTableCell) event.target.blur();
    if (isUndo) undo();
    else redo();
}

// ============================================
// EVENT LISTENERS
// ============================================
function bindEvents() {
    // Chat
    el.generateBtn.addEventListener('click', handleGenerate);
    el.promptInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleGenerate();
        }
    });
    el.promptInput.addEventListener('input', updateCharCounter);
    el.chatTitle.addEventListener('blur', handleChatTitleBlur);
    el.deleteChatBtn.addEventListener('click', handleDeleteChat);
    el.downloadExcelBtn.addEventListener('click', handleDownloadExcel);

    // Table
    el.tableBody.addEventListener('blur', handleCellBlur, true);
    el.tableBody.addEventListener('keydown', handleCellKeydown);
    el.tableBody.addEventListener('click', handleDeleteRow);
    el.addRowBtn.addEventListener('click', handleAddRow);
    el.undoBtn.addEventListener('click', undo);
    el.redoBtn.addEventListener('click', redo);

    // Alert
    el.alertClose.addEventListener('click', hideAlert);
    el.deleteConfirmCancel.addEventListener('click', () => {
        finishDeleteConfirmation(false);
    });
    el.deleteConfirmAccept.addEventListener('click', () => {
        finishDeleteConfirmation(true);
    });
    el.deleteConfirmDialog.addEventListener('click', (event) => {
        if (event.target === el.deleteConfirmDialog) {
            finishDeleteConfirmation(false);
        }
    });
    el.deleteConfirmDialog.addEventListener('keydown', handleDeleteDialogKeydown);

    // Global
    document.addEventListener('keydown', handleGlobalKeydown);

    // Sidebar callback
    window.Sidebar.onChatSelect = (chatId) => {
        if (chatId) {
            loadChat(chatId);
        } else {
            showEmptyState();
        }
    };
}

// ============================================
// INIT
// ============================================
function init() {
    bindEvents();
    updateCharCounter();
    showEmptyState();
    console.log('✅ SmartSheet AI app tayyor (12.8-bosqich)');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Eksport
window.App = {
    showAlert,
    loadChat,
    showEmptyState,
    confirmDeleteChat,
};