/**
 * Fast Search — lightweight client-side command palette for navigation.
 * Indexes the sidebar links + a few static destinations and filters them
 * instantly as the user types. No AI, no network calls.
 */

const Search = (() => {
    let modal, backdrop, dialog, inputEl, listEl, emptyEl;
    let isOpen = false;
    let entries = [];
    let filtered = [];
    let activeIndex = 0;

    function buildIndex() {
        // Pull every sidebar link as a navigable target.
        const sidebar = document.querySelector('aside');
        const items = [];
        if (sidebar) {
            sidebar.querySelectorAll('a[href]').forEach(a => {
                const href = a.getAttribute('href');
                if (!href || href.startsWith('#')) return;
                const label = (a.textContent || '').trim().replace(/\s+/g, ' ');
                if (!label) return;
                // Section is the nearest preceding "uppercase tracking-wider" heading.
                let section = '';
                const sectionEl = a.closest('div')?.previousElementSibling;
                if (sectionEl && sectionEl.classList?.contains('uppercase')) {
                    section = sectionEl.textContent.trim();
                }
                items.push({ label, href, section, kind: 'page' });
            });
        }
        // De-duplicate by href+label.
        const seen = new Set();
        entries = items.filter(i => {
            const k = i.href + '|' + i.label;
            if (seen.has(k)) return false;
            seen.add(k);
            return true;
        });
    }

    function init() {
        modal = document.getElementById('search-modal');
        if (!modal) return;
        backdrop = modal.querySelector('.search-backdrop');
        dialog = modal.querySelector('.search-dialog');
        inputEl = document.getElementById('search-input');
        listEl = document.getElementById('search-results');
        emptyEl = document.getElementById('search-empty');

        backdrop.addEventListener('click', close);
        dialog.addEventListener('click', e => { if (e.target === dialog) close(); });
        inputEl.addEventListener('input', onInput);
        inputEl.addEventListener('keydown', onKeyDown);

        const closeBtn = document.getElementById('search-close-btn');
        if (closeBtn) closeBtn.addEventListener('click', close);

        // Global shortcut: "/" focuses search (when not already in an input)
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !isOpen) {
                const t = e.target;
                if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
                e.preventDefault();
                open();
            } else if (e.key === 'Escape' && isOpen) {
                close();
            }
        });
    }

    function open() {
        if (!modal) init();
        if (!modal) return;
        buildIndex();
        isOpen = true;
        modal.classList.remove('hidden');
        requestAnimationFrame(() => {
            backdrop.classList.add('active');
            dialog.classList.add('active');
        });
        inputEl.value = '';
        activeIndex = 0;
        render('');
        inputEl.focus();
    }

    function close() {
        if (!modal || !isOpen) return;
        isOpen = false;
        backdrop.classList.remove('active');
        dialog.classList.remove('active');
        setTimeout(() => modal.classList.add('hidden'), 150);
    }

    function toggle() { isOpen ? close() : open(); }

    function onInput(e) {
        activeIndex = 0;
        render(e.target.value);
    }

    function onKeyDown(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, Math.max(filtered.length - 1, 0));
            updateActive();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, 0);
            updateActive();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            const item = filtered[activeIndex];
            if (item) {
                window.location.href = item.href;
            }
        } else if (e.key === 'Escape') {
            e.preventDefault();
            close();
        }
    }

    function score(item, q) {
        const label = item.label.toLowerCase();
        if (label === q) return 1000;
        if (label.startsWith(q)) return 500;
        if (label.includes(q)) return 200;
        if (item.href.toLowerCase().includes(q)) return 100;
        if (item.section.toLowerCase().includes(q)) return 50;
        return 0;
    }

    function render(query) {
        const q = query.trim().toLowerCase();
        if (!q) {
            filtered = entries.slice(0, 12);
        } else {
            filtered = entries
                .map(e => ({ e, s: score(e, q) }))
                .filter(x => x.s > 0)
                .sort((a, b) => b.s - a.s)
                .slice(0, 20)
                .map(x => x.e);
        }

        if (filtered.length === 0) {
            listEl.innerHTML = '';
            emptyEl.classList.remove('hidden');
            return;
        }
        emptyEl.classList.add('hidden');

        listEl.innerHTML = filtered.map((item, i) => `
            <a href="${escapeAttr(item.href)}" data-idx="${i}" class="search-result flex items-center gap-3 px-3 py-2 rounded-lg ${i === activeIndex ? 'bg-neutral-100' : 'hover:bg-neutral-50'} transition-colors">
                <svg class="w-4 h-4 text-neutral-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/></svg>
                <div class="flex-1 min-w-0">
                    <div class="text-sm text-neutral-900 truncate">${escapeHtml(item.label)}</div>
                    ${item.section ? `<div class="text-2xs text-neutral-400 truncate">${escapeHtml(item.section)}</div>` : ''}
                </div>
                <span class="text-2xs text-neutral-400 font-mono shrink-0">${escapeHtml(item.href)}</span>
            </a>
        `).join('');

        listEl.querySelectorAll('.search-result').forEach(el => {
            el.addEventListener('mouseenter', () => {
                activeIndex = parseInt(el.dataset.idx, 10);
                updateActive();
            });
        });
    }

    function updateActive() {
        listEl.querySelectorAll('.search-result').forEach((el, i) => {
            if (i === activeIndex) {
                el.classList.add('bg-neutral-100');
                el.classList.remove('hover:bg-neutral-50');
                el.scrollIntoView({ block: 'nearest' });
            } else {
                el.classList.remove('bg-neutral-100');
                el.classList.add('hover:bg-neutral-50');
            }
        });
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }
    function escapeAttr(str) { return escapeHtml(str).replace(/"/g, '&quot;'); }

    return { open, close, toggle, init };
})();

document.addEventListener('DOMContentLoaded', () => Search.init());
