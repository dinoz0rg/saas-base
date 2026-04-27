/**
 * Ask Navigator — AI-powered command palette / chat assistant.
 * Supports persistent chat history via /api/chats endpoints.
 */

const Navigator = (() => {
    let messages = [];
    let isLoading = false;
    let isOpen = false;
    let currentChatId = null;
    let chatSessions = [];
    let historyVisible = false;

    // DOM refs (resolved on first open)
    let modal, backdrop, dialog, messagesArea, inputEl, sendBtn, welcomeScreen, chatScreen, msgContainer;
    let historyPanel, historyList;

    function init() {
        modal = document.getElementById('navigator-modal');
        if (!modal) return;
        backdrop = modal.querySelector('.nav-backdrop');
        dialog = modal.querySelector('.nav-dialog');
        messagesArea = document.getElementById('nav-messages-area');
        inputEl = document.getElementById('nav-input');
        sendBtn = document.getElementById('nav-send-btn');
        welcomeScreen = document.getElementById('nav-welcome');
        chatScreen = document.getElementById('nav-chat');
        msgContainer = document.getElementById('nav-msg-container');
        historyPanel = document.getElementById('nav-history-panel');
        historyList = document.getElementById('nav-history-list');

        // Events
        sendBtn.addEventListener('click', handleSubmit);
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
            }
        });
        inputEl.addEventListener('input', autoResize);
        backdrop.addEventListener('click', close);
        dialog.addEventListener('click', (e) => { if (e.target === dialog) close(); });

        // New chat button
        const newChatBtn = document.getElementById('nav-new-chat');
        if (newChatBtn) newChatBtn.addEventListener('click', newChat);

        // Close button
        const closeBtn = document.getElementById('nav-close-btn');
        if (closeBtn) closeBtn.addEventListener('click', close);

        // History toggle
        const historyBtn = document.getElementById('nav-history-btn');
        if (historyBtn) historyBtn.addEventListener('click', toggleHistory);

        // Example prompts
        document.querySelectorAll('[data-nav-prompt]').forEach(btn => {
            btn.addEventListener('click', () => {
                inputEl.value = btn.dataset.navPrompt;
                inputEl.focus();
                autoResize({ target: inputEl });
            });
        });
    }

    function open() {
        if (!modal) init();
        if (!modal) return;
        isOpen = true;
        modal.classList.remove('hidden');
        requestAnimationFrame(() => {
            backdrop.classList.add('active');
            dialog.classList.add('active');
        });
        inputEl.value = '';
        inputEl.focus();
        autoResize({ target: inputEl });
        loadHistory();
    }

    function close() {
        if (!modal || !isOpen) return;
        isOpen = false;
        backdrop.classList.remove('active');
        dialog.classList.remove('active');
        setTimeout(() => {
            modal.classList.add('hidden');
            hideHistory();
        }, 200);
    }

    function toggle() {
        isOpen ? close() : open();
    }

    function newChat() {
        // Save current chat before starting new one
        saveCurrentChat();
        currentChatId = null;
        messages = [];
        isLoading = false;
        renderView();
        inputEl.value = '';
        inputEl.focus();
    }

    // ── History ─────────────────────────────────────────────────

    async function loadHistory() {
        try {
            const resp = await fetch('/api/chats');
            if (resp.ok) {
                chatSessions = await resp.json();
                renderHistory();
            }
        } catch (e) { /* silent */ }
    }

    function toggleHistory() {
        historyVisible ? hideHistory() : showHistory();
    }

    function showHistory() {
        if (!historyPanel) return;
        historyVisible = true;
        historyPanel.style.display = 'flex';
        requestAnimationFrame(() => historyPanel.classList.add('active'));
        loadHistory();
    }

    function hideHistory() {
        if (!historyPanel) return;
        historyVisible = false;
        historyPanel.classList.remove('active');
        setTimeout(() => { historyPanel.style.display = 'none'; }, 200);
    }

    function renderHistory() {
        if (!historyList) return;
        if (chatSessions.length === 0) {
            historyList.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12 text-center">
                    <svg class="w-8 h-8 text-neutral-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155"/>
                    </svg>
                    <p class="text-xs text-neutral-400">No previous chats</p>
                </div>`;
            return;
        }

        const grouped = groupByDate(chatSessions);
        historyList.innerHTML = Object.entries(grouped).map(([label, sessions]) => `
            <div class="mb-3">
                <div class="px-3 py-1.5 text-2xs font-medium text-neutral-400 uppercase tracking-wider">${escapeHtml(label)}</div>
                ${sessions.map(s => `
                    <div onclick="Navigator.loadChat('${s.id}')" class="w-full text-left px-3 py-2 rounded-lg hover:bg-neutral-100 transition-colors group flex items-center gap-2 cursor-pointer ${s.id === currentChatId ? 'bg-neutral-100' : ''}">
                        <svg class="w-3.5 h-3.5 text-neutral-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 011.037-.443 48.282 48.282 0 005.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"/>
                        </svg>
                        <span class="text-xs text-neutral-700 truncate flex-1">${escapeHtml(s.title)}</span>
                        <button onclick="event.stopPropagation(); Navigator.deleteChat('${s.id}')" class="hidden group-hover:flex w-5 h-5 items-center justify-center rounded text-neutral-400 hover:text-red-500 hover:bg-red-50 shrink-0 transition-colors" title="Delete chat">
                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>
                        </button>
                    </div>
                `).join('')}
            </div>
        `).join('');
    }

    function groupByDate(sessions) {
        const groups = {};
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
        const weekAgo = new Date(today); weekAgo.setDate(today.getDate() - 7);

        sessions.forEach(s => {
            const d = new Date(s.updated_at);
            let label;
            if (d >= today) label = 'Today';
            else if (d >= yesterday) label = 'Yesterday';
            else if (d >= weekAgo) label = 'This Week';
            else label = 'Older';
            if (!groups[label]) groups[label] = [];
            groups[label].push(s);
        });
        return groups;
    }

    async function loadChat(chatId) {
        try {
            const resp = await fetch(`/api/chats/${chatId}`);
            if (!resp.ok) return;
            const data = await resp.json();
            currentChatId = data.id;
            messages = data.messages || [];
            renderView();
            renderHistory();
            inputEl.focus();
        } catch (e) { /* silent */ }
    }

    async function deleteChat(chatId) {
        try {
            await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
            chatSessions = chatSessions.filter(s => s.id !== chatId);
            if (currentChatId === chatId) {
                currentChatId = null;
                messages = [];
                renderView();
            }
            renderHistory();
        } catch (e) { /* silent */ }
    }

    async function saveCurrentChat() {
        if (messages.length === 0) return;
        // Only save messages with content (skip loading placeholders)
        const toSave = messages.filter(m => m.content);
        if (toSave.length === 0) return;

        try {
            if (currentChatId) {
                await fetch(`/api/chats/${currentChatId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: toSave }),
                });
            } else {
                const resp = await fetch('/api/chats', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: toSave }),
                });
                if (resp.ok) {
                    const data = await resp.json();
                    currentChatId = data.id;
                }
            }
        } catch (e) { /* silent */ }
    }

    // ── View ────────────────────────────────────────────────────

    function renderView() {
        if (messages.length === 0) {
            welcomeScreen.classList.remove('hidden');
            chatScreen.classList.add('hidden');
        } else {
            welcomeScreen.classList.add('hidden');
            chatScreen.classList.remove('hidden');
            renderMessages();
        }
        // Show/hide new chat button
        const newChatBtn = document.getElementById('nav-new-chat');
        if (newChatBtn) newChatBtn.style.display = messages.length > 0 ? '' : 'none';
    }

    function renderMessages() {
        msgContainer.innerHTML = messages.map((msg, i) => {
            if (msg.role === 'user') return renderUserMsg(msg);
            return renderAssistantMsg(msg, i);
        }).join('');
        requestAnimationFrame(() => {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        });
    }

    function renderUserMsg(msg) {
        return `
        <div class="flex gap-3 justify-end anim-card" style="animation-delay:0ms">
            <div class="max-w-[85%] rounded-2xl bg-neutral-900 text-white px-4 py-3">
                <p class="text-sm whitespace-pre-wrap">${escapeHtml(msg.content)}</p>
            </div>
            <div class="w-9 h-9 rounded-xl bg-neutral-100 flex items-center justify-center shrink-0">
                <svg class="w-4 h-4 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/></svg>
            </div>
        </div>`;
    }

    function renderAssistantMsg(msg, index) {
        const toolsHtml = msg.tools && msg.tools.length > 0 ? `
        <div class="rounded-xl border border-blue-100 bg-blue-50/50 p-3 mb-3">
            <div class="flex items-center gap-2 mb-2">
                <svg class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125v-3.75"/></svg>
                <span class="text-xs font-medium text-blue-700">Data sources used</span>
            </div>
            <div class="space-y-1">
                ${msg.tools.map(t => `
                <div class="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/60">
                    <div class="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                        <svg class="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/></svg>
                    </div>
                    <span class="text-xs text-neutral-600">${escapeHtml(t)}</span>
                </div>`).join('')}
            </div>
        </div>` : '';

        const loadingHtml = msg.loading ? `
        <div class="flex items-center gap-2 px-2 py-1.5">
            <div class="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center">
                <svg class="w-3 h-3 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
            </div>
            <span class="text-xs text-neutral-500">Thinking...</span>
        </div>` : '';

        return `
        <div class="flex gap-3 justify-start anim-card" style="animation-delay:${index * 30}ms">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shrink-0 shadow-sm">
                <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/></svg>
            </div>
            <div class="max-w-[85%] rounded-2xl bg-white border border-neutral-200 shadow-sm px-4 py-3">
                ${toolsHtml}
                ${loadingHtml}
                ${msg.content ? `<div class="text-sm text-neutral-700 leading-relaxed nav-markdown">${formatMarkdown(msg.content)}</div>` : ''}
            </div>
        </div>`;
    }

    async function handleSubmit() {
        const text = inputEl.value.trim();
        if (!text || isLoading) return;

        messages.push({ role: 'user', content: text });
        inputEl.value = '';
        autoResize({ target: inputEl });

        const assistantMsg = { role: 'assistant', content: '', loading: true };
        messages.push(assistantMsg);
        isLoading = true;
        renderView();

        try {
            const history = messages
                .filter(m => m.content || m.role === 'user')
                .map(m => ({ role: m.role, content: m.content }))
                .filter(m => m.content);
            const resp = await fetch('/api/ai/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: history }),
            });
            if (!resp.ok) {
                const errText = await resp.text().catch(() => '');
                assistantMsg.content = `**Error:** ${resp.status} ${resp.statusText}${errText ? `\n\n\`${errText.slice(0, 300)}\`` : ''}`;
            } else {
                const data = await resp.json();
                assistantMsg.content = data.content || '';
            }
        } catch (err) {
            assistantMsg.content = `**Error:** ${err.message || 'Network error'}`;
        }

        assistantMsg.loading = false;
        isLoading = false;
        renderView();

        // Auto-save after each exchange
        await saveCurrentChat();
        loadHistory();
    }

    // ── Utilities ───────────────────────────────────────────────

    function formatMarkdown(text) {
        let html = escapeHtml(text);
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-neutral-900">$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/`(.+?)`/g, '<code class="px-1 py-0.5 rounded bg-neutral-100 font-mono text-xs">$1</code>');

        html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/gm, (match, header, sep, body) => {
            const headers = header.split('|').filter(c => c.trim()).map(c => `<th class="px-3 py-1.5 text-left text-xs font-semibold text-neutral-700">${c.trim()}</th>`).join('');
            const rows = body.trim().split('\n').map(row => {
                const cells = row.split('|').filter(c => c.trim()).map(c => `<td class="px-3 py-1.5 text-xs text-neutral-600">${c.trim()}</td>`).join('');
                return `<tr class="border-t border-neutral-100">${cells}</tr>`;
            }).join('');
            return `<div class="overflow-x-auto my-2 rounded-lg border border-neutral-200"><table class="min-w-full"><thead class="bg-neutral-50"><tr>${headers}</tr></thead><tbody>${rows}</tbody></table></div>`;
        });

        html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="text-sm pl-1 leading-relaxed">$2</li>');
        html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, (match) => `<ol class="list-decimal pl-4 space-y-1 my-2">${match}</ol>`);

        html = html.replace(/^- (.+)$/gm, '<li class="text-sm pl-1 leading-relaxed">$1</li>');
        html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, (match) => {
            if (match.includes('<ol')) return match;
            return `<ul class="list-disc pl-4 space-y-1 my-2">${match}</ul>`;
        });

        html = html.replace(/\n\n/g, '</p><p class="mb-2">');
        html = '<p class="mb-2">' + html + '</p>';
        html = html.replace(/\n/g, '<br>');
        html = html.replace(/<p class="mb-2"><\/p>/g, '');

        return html;
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function autoResize(e) {
        const el = e.target;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 150) + 'px';
    }

    function delay(ms) {
        return new Promise(r => setTimeout(r, ms));
    }

    return { open, close, toggle, init, loadChat, deleteChat, newChat };
})();

// Auto-init when DOM is ready
document.addEventListener('DOMContentLoaded', () => Navigator.init());
