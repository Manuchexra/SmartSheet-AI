/**
 * Sidebar moduli.
 *
 * Vazifasi:
 * - Chatlar ro'yxatini yuklash va ko'rsatish
 * - Yangi chat yaratish
 * - Chatni tanlash
 * - Chatni o'chirish
 * - Chat nomini tahrirlash (sidebar ichida)
 * - Mobil uchun sidebar ochish/yopish
 *
 * Bu modul `window.Sidebar` orqali boshqa modullarga ochiq.
 */

'use strict';

// ============================================
// DOM ELEMENTLAR
// ============================================
const sidebarEl = {
    sidebar: document.getElementById('sidebar'),
    chatList: document.getElementById('chat-list'),
    chatListEmpty: document.getElementById('chat-list-empty'),
    newChatBtn: document.getElementById('new-chat-btn'),
    toggleBtn: document.getElementById('sidebar-toggle'),
};

// ============================================
// STATE
// ============================================
const sidebarState = {
    /** @type {Array} Chatlar ro'yxati */
    chats: [],

    /** @type {number|null} Faol chat ID */
    activeChatId: null,

    /** @type {Function|null} Chat tanlanganda chaqiriladi */
    onChatSelect: null,

    /** @type {boolean} Yuklanmoqda */
    isLoading: false,
};

// ============================================
// API
// ============================================

/**
 * Chatlar ro'yxatini backend'dan yuklash.
 */
async function loadChats() {
    if (sidebarState.isLoading) return;

    sidebarState.isLoading = true;

    try {
        const data = await window.API.Chats.list();
        sidebarState.chats = data.chats || [];
        renderChatList();
    } catch (err) {
        console.error('Chatlar yuklanmadi:', err);
        showSidebarError('Chatlar yuklanmadi');
    } finally {
        sidebarState.isLoading = false;
    }
}

/**
 * Sidebar'da xatolik ko'rsatish (oddiy).
 */
function showSidebarError(message) {
    if (!sidebarEl.chatList) return;

    // Eski xatoni o'chirish
    const old = sidebarEl.chatList.querySelector('.sidebar__error');
    if (old) old.remove();

    const errorEl = document.createElement('div');
    errorEl.className = 'sidebar__error';
    errorEl.textContent = message;
    sidebarEl.chatList.appendChild(errorEl);
}

// ============================================
// RENDER
// ============================================

/**
 * Chatlar ro'yxatini chizish.
 */
function renderChatList() {
    const list = sidebarEl.chatList;
    if (!list) return;

    // Eski chatlarni o'chirish (empty state va error'dan tashqari)
    Array.from(list.children).forEach((child) => {
        if (
            child.id !== 'chat-list-empty' &&
            !child.classList.contains('sidebar__error')
        ) {
            child.remove();
        }
    });

    // Bo'sh holat
    if (sidebarState.chats.length === 0) {
        sidebarEl.chatListEmpty.hidden = false;
        return;
    }

    sidebarEl.chatListEmpty.hidden = true;

    // Chatlarni chizish
    sidebarState.chats.forEach((chat) => {
        const item = createChatItem(chat);
        list.appendChild(item);
    });
}

/**
 * Bitta chat item yaratish.
 * @param {object} chat
 * @returns {HTMLDivElement}
 */
function createChatItem(chat) {
    const div = document.createElement('div');
    div.className = 'chat-item';
    div.dataset.chatId = String(chat.id);

    if (chat.id === sidebarState.activeChatId) {
        div.classList.add('chat-item--active');
    }

    // ============================================
    // ICON
    // ============================================
    const icon = document.createElement('span');
    icon.className = 'chat-item__icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = chat.has_table ? '📊' : '💬';
    div.appendChild(icon);

    // ============================================
    // CONTENT
    // ============================================
    const content = document.createElement('div');
    content.className = 'chat-item__content';

    const title = document.createElement('div');
    title.className = 'chat-item__title';
    title.textContent = chat.title || 'Untitled';
    title.title = chat.title || 'Untitled'; // tooltip
    content.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'chat-item__meta';
    const msgCount = chat.message_count || 0;
    meta.textContent = `${msgCount} xabar`;
    content.appendChild(meta);

    div.appendChild(content);

    // ============================================
    // DELETE BUTTON
    // ============================================
    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'chat-item__delete';
    delBtn.textContent = '🗑';
    delBtn.title = 'Chatni o\'chirish';
    delBtn.setAttribute('aria-label', 'Chatni o\'chirish');
    delBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleDeleteChat(chat.id, chat.title);
    });
    div.appendChild(delBtn);

    // ============================================
    // CLICK
    // ============================================
    div.addEventListener('click', () => {
        if (chat.id !== sidebarState.activeChatId) {
            selectChat(chat.id);
        }
    });

    return div;
}

// ============================================
// ACTIONS
// ============================================

/**
 * Chatni tanlash.
 * @param {number} chatId
 */
function selectChat(chatId) {
    sidebarState.activeChatId = chatId;

    // Active klassini yangilash
    document.querySelectorAll('.chat-item').forEach((el) => {
        const elId = parseInt(el.dataset.chatId, 10);
        el.classList.toggle('chat-item--active', elId === chatId);
    });

    // Mobil'da sidebar'ni yopish
    closeSidebar();

    // Callback
    if (typeof sidebarState.onChatSelect === 'function') {
        sidebarState.onChatSelect(chatId);
    }
}

/**
 * Yangi chat yaratish.
 */
async function handleNewChat() {
    if (sidebarState.isLoading) return;

    sidebarState.isLoading = true;
    sidebarEl.newChatBtn.disabled = true;

    try {
        const chat = await window.API.Chats.create('Yangi chat');

        // Ro'yxatga qo'shish (birinchi o'ringa)
        sidebarState.chats.unshift(chat);
        renderChatList();

        // Tanlash
        selectChat(chat.id);
    } catch (err) {
        console.error('Chat yaratilmadi:', err);
        window.App?.showAlert(err.message || 'Chat yaratishda xato', 'error');
    } finally {
        sidebarState.isLoading = false;
        sidebarEl.newChatBtn.disabled = false;
    }
}

/**
 * Chatni o'chirish.
 * @param {number} chatId
 * @param {string} chatTitle
 */
async function handleDeleteChat(chatId, chatTitle) {
    const title = chatTitle || 'Untitled';
    if (!(await window.App.confirmDeleteChat(title))) return;

    try {
        await window.API.Chats.delete(chatId);

        // Ro'yxatdan olib tashlash
        sidebarState.chats = sidebarState.chats.filter((c) => c.id !== chatId);

        // Active chat o'chirilgan bo'lsa
        const wasActive = sidebarState.activeChatId === chatId;
        if (wasActive) {
            sidebarState.activeChatId = null;
        }

        renderChatList();

        // Callback — bo'sh holatga qaytish
        if (wasActive && typeof sidebarState.onChatSelect === 'function') {
            sidebarState.onChatSelect(null);
        }

        window.App?.showAlert('Chat o\'chirildi', 'info');
    } catch (err) {
        console.error('Chat o\'chirilmadi:', err);
        window.App?.showAlert(err.message || 'Chatni o\'chirishda xato', 'error');
    }
}

// ============================================
// SIDEBAR'NI YANGILASH (tashqi modullar uchun)
// ============================================

/**
 * Sidebar'dagi chat ma'lumotlarini yangilash.
 * Chat generate/update/delete bo'lganda chaqiriladi.
 * @param {object} chatData
 */
function updateChatInSidebar(chatData) {
    if (!chatData || !chatData.id) return;

    const index = sidebarState.chats.findIndex((c) => c.id === chatData.id);
    if (index === -1) return;

    // Yangilash
    sidebarState.chats[index] = {
        ...sidebarState.chats[index],
        ...chatData,
    };

    // Faqat shu item'ni qayta chizish (yoki butun ro'yxatni)
    renderChatList();
}

/**
 * Chatni ro'yxatga qo'shish (agar mavjud bo'lmasa).
 * @param {object} chatData
 */
function addOrUpdateChat(chatData) {
    if (!chatData || !chatData.id) return;

    const index = sidebarState.chats.findIndex((c) => c.id === chatData.id);
    if (index === -1) {
        sidebarState.chats.unshift(chatData);
    } else {
        sidebarState.chats[index] = {
            ...sidebarState.chats[index],
            ...chatData,
        };
    }

    renderChatList();
}

/**
 * Chatni ro'yxatdan olib tashlash.
 * @param {number} chatId
 */
function removeChatFromSidebar(chatId) {
    sidebarState.chats = sidebarState.chats.filter((c) => c.id !== chatId);
    if (sidebarState.activeChatId === chatId) {
        sidebarState.activeChatId = null;
    }
    renderChatList();
}

// ============================================
// MOBIL — SIDEBAR OCHISH/YOPISH
// ============================================

function openSidebar() {
    sidebarEl.sidebar.classList.add('sidebar--open');
}

function closeSidebar() {
    sidebarEl.sidebar.classList.remove('sidebar--open');
}

function toggleSidebar() {
    sidebarEl.sidebar.classList.toggle('sidebar--open');
}

// ============================================
// EVENT LISTENERS
// ============================================

function bindSidebarEvents() {
    // Yangi chat
    if (sidebarEl.newChatBtn) {
        sidebarEl.newChatBtn.addEventListener('click', handleNewChat);
    }

    // Mobil toggle
    if (sidebarEl.toggleBtn) {
        sidebarEl.toggleBtn.addEventListener('click', toggleSidebar);
    }

    // Sidebar tashqarisiga bosilganda yopish (mobil)
    document.addEventListener('click', (e) => {
        if (window.innerWidth > 768) return;

        const isInsideSidebar = sidebarEl.sidebar.contains(e.target);
        const isToggle = sidebarEl.toggleBtn.contains(e.target);

        if (
            !isInsideSidebar &&
            !isToggle &&
            sidebarEl.sidebar.classList.contains('sidebar--open')
        ) {
            closeSidebar();
        }
    });
}

// ============================================
// INIT
// ============================================

function initSidebar() {
    bindSidebarEvents();
    loadChats();
}

// ============================================
// GLOBAL EKSPORT
// ============================================
window.Sidebar = {
    // State
    get chats() {
        return sidebarState.chats;
    },
    get activeChatId() {
        return sidebarState.activeChatId;
    },

    // Callbacks
    set onChatSelect(fn) {
        sidebarState.onChatSelect = fn;
    },

    // Metodlar
    init: initSidebar,
    load: loadChats,
    refresh: loadChats,
    select: selectChat,
    render: renderChatList,
    updateChat: updateChatInSidebar,
    addOrUpdateChat,
    removeChat: removeChatFromSidebar,
    open: openSidebar,
    close: closeSidebar,
    toggle: toggleSidebar,
    createChat: handleNewChat,
    deleteChat: handleDeleteChat,
};

// ============================================
// AUTO-INIT
// ============================================
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSidebar);
} else {
    initSidebar();
}