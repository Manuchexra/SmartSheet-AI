/**
 * SmartSheet AI — API moduli.
 *
 * Barcha backend so'rovlar shu yerda.
 */

'use strict';

const API_BASE_URL = '/api/v1';
const CLIENT_ID_STORAGE_KEY = 'smartsheet_client_id';

function getClientId() {
    let clientId = localStorage.getItem(CLIENT_ID_STORAGE_KEY);
    if (!clientId) {
        clientId = crypto.randomUUID();
        localStorage.setItem(CLIENT_ID_STORAGE_KEY, clientId);
    }
    return clientId;
}

/**
 * Umumiy fetch wrapper.
 */
async function apiFetch(path, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': getClientId(),
            ...(options.headers || {}),
        },
    };

    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    const response = await fetch(url, config);

    // 204 No Content
    if (response.status === 204) {
        return null;
    }

    // Xato
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
        } catch (_) { /* ignore */ }
        const err = new Error(detail);
        err.status = response.status;
        throw err;
    }

    return response.json();
}

// ============================================
// CHATS API
// ============================================
const ChatsAPI = {
    /** Chatlar ro'yxati */
    async list() {
        return apiFetch('/chats');
    },

    /** Bitta chat */
    async get(chatId) {
        return apiFetch(`/chats/${chatId}`);
    },

    /** Yangi chat */
    async create(title = 'Yangi chat') {
        return apiFetch('/chats', {
            method: 'POST',
            body: { title },
        });
    },

    /** Tahrirlash */
    async update(chatId, title) {
        return apiFetch(`/chats/${chatId}`, {
            method: 'PATCH',
            body: { title },
        });
    },

    /** O'chirish */
    async delete(chatId) {
        return apiFetch(`/chats/${chatId}`, {
            method: 'DELETE',
        });
    },
};

// ============================================
// MESSAGES API
// ============================================
const MessagesAPI = {
    /** Xabarlar ro'yxati */
    async list(chatId) {
        return apiFetch(`/chats/${chatId}/messages`);
    },

    /** Yangi xabar */
    async create(chatId, role, content) {
        return apiFetch(`/chats/${chatId}/messages`, {
            method: 'POST',
            body: { role, content },
        });
    },

    /** O'chirish */
    async delete(chatId, messageId) {
        return apiFetch(`/chats/${chatId}/messages/${messageId}`, {
            method: 'DELETE',
        });
    },
};

// ============================================
// TABLE API
// ============================================
const TableAPI = {
    /** Jadvalni olish */
    async get(chatId) {
        return apiFetch(`/chats/${chatId}/table`);
    },

    /** Jadval yaratish/yangilash */
    async upsert(chatId, table) {
        return apiFetch(`/chats/${chatId}/table`, {
            method: 'PUT',
            body: table,
        });
    },

    /** Tahrirlash */
    async update(chatId, changes) {
        return apiFetch(`/chats/${chatId}/table`, {
            method: 'PATCH',
            body: changes,
        });
    },

    /** Excel yoki CSV faylini chat jadvali sifatida import qilish */
    async upload(chatId, file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/chats/${chatId}/table/upload`, {
            method: 'POST',
            headers: { 'X-Client-ID': getClientId() },
            body: formData,
        });
        if (!response.ok) {
            let detail = `Fayl yuklashda xato (${response.status})`;
            try {
                const errorData = await response.json();
                if (errorData.detail) detail = errorData.detail;
            } catch (_) { /* non-JSON errors retain the status message */ }
            throw new Error(detail);
        }
        return response.json();
    },

    /** O'chirish */
    async delete(chatId) {
        return apiFetch(`/chats/${chatId}/table`, {
            method: 'DELETE',
        });
    },
};

// ============================================
// AI GENERATE API
// ============================================
const AIGenerateAPI = {
    /** Chat ichida AI'ga so'rov */
    async generate(chatId, prompt) {
        return apiFetch(`/chats/${chatId}/generate`, {
            method: 'POST',
            body: { prompt },
        });
    },
};

// ============================================
// EXCEL API
// ============================================
const ExcelAPI = {
    /** Excel yuklab olish */
    async export(table) {
        const response = await fetch(`${API_BASE_URL}/excel/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-ID': getClientId(),
            },
            body: JSON.stringify(table),
        });

        if (!response.ok) {
            throw new Error(`Excel xatosi (${response.status})`);
        }

        return response.blob();
    },
};

// Global eksport
window.API = {
    Chats: ChatsAPI,
    Messages: MessagesAPI,
    Table: TableAPI,
    AIGenerate: AIGenerateAPI,
    Excel: ExcelAPI,
};