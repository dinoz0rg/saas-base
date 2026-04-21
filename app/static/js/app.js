/**
 * Shared utilities: animation helpers, toast, API fetch, dropdown animations.
 * Included by base.html — available on every page.
 */

// --- Animated overlay helpers ---
function animateOpen(wrapper, backdropCls, contentCls) {
    wrapper.classList.remove('hidden');
    const backdrop = wrapper.querySelector(backdropCls);
    const content = wrapper.querySelector(contentCls);
    if (backdrop) { backdrop.classList.remove('anim-backdrop-out'); backdrop.classList.add('anim-backdrop-in'); }
    if (content) { content.className = content.className.replace(/anim-\S+-out/g, ''); }
    return { backdrop, content };
}
function animateClose(wrapper, backdropCls, contentCls, outClass) {
    if (wrapper.classList.contains('hidden')) return;
    const backdrop = wrapper.querySelector(backdropCls);
    const content = wrapper.querySelector(contentCls);
    if (backdrop) { backdrop.classList.remove('anim-backdrop-in'); backdrop.classList.add('anim-backdrop-out'); }
    if (content) { content.classList.add(outClass); }
    const duration = 200;
    setTimeout(() => {
        wrapper.classList.add('hidden');
        if (backdrop) backdrop.classList.remove('anim-backdrop-out');
        if (content) content.classList.remove(outClass);
    }, duration);
}

// --- Dropdown animation helpers ---
function animateDropdownOpen(menu) {
    menu.classList.remove('hidden', 'anim-dropdown-out');
    menu.classList.add('anim-dropdown-in');
}
function animateDropdownClose(menu) {
    if (menu.classList.contains('hidden')) return;
    menu.classList.remove('anim-dropdown-in');
    menu.classList.add('anim-dropdown-out');
    setTimeout(() => { menu.classList.add('hidden'); menu.classList.remove('anim-dropdown-out'); }, 120);
}

/**
 * Shared dropdown manager.
 * Registers trigger→panel pairs, handles toggle, outside-click, and Escape.
 *
 * Usage:
 *   const dm = new DropdownManager();
 *   dm.register('my-btn', 'my-menu');          // by element id
 *   dm.register(btnEl, menuEl);                // by element reference
 *   dm.register('my-btn', 'my-menu', { onOpen, onClose, closeOthers: true });
 *
 * The panel element should have class="hidden dropdown-panel ..." (or any
 * element — the animation classes are added automatically).
 */
class DropdownManager {
    constructor() {
        this._entries = [];
        this._listening = false;
    }
    _el(ref) { return typeof ref === 'string' ? document.getElementById(ref) : ref; }
    register(trigger, panel, opts = {}) {
        const entry = { trigger: this._el(trigger), panel: this._el(panel), opts };
        if (!entry.trigger || !entry.panel) return;
        entry.trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle(entry);
        });
        this._entries.push(entry);
        if (!this._listening) {
            this._listening = true;
            document.addEventListener('click', (e) => this._outsideClick(e));
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') this.closeAll();
            });
        }
    }
    toggle(entry) {
        const isHidden = entry.panel.classList.contains('hidden');
        // Close others first (default: true)
        if (entry.opts.closeOthers !== false) {
            this._entries.forEach(en => { if (en !== entry) this._close(en); });
        }
        if (isHidden) { this._open(entry); } else { this._close(entry); }
    }
    _open(entry) {
        animateDropdownOpen(entry.panel);
        if (entry.opts.onOpen) entry.opts.onOpen(entry.panel);
    }
    _close(entry) {
        animateDropdownClose(entry.panel);
        if (entry.opts.onClose) entry.opts.onClose(entry.panel);
    }
    closeAll() {
        this._entries.forEach(en => this._close(en));
    }
    _outsideClick(e) {
        this._entries.forEach(entry => {
            if (!entry.panel.classList.contains('hidden') &&
                !entry.panel.contains(e.target) &&
                !entry.trigger.contains(e.target)) {
                this._close(entry);
            }
        });
    }
}

// --- Toast ---
let toastTimer;
function showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.querySelector('div').textContent = msg;
    clearTimeout(toastTimer);
    t.classList.remove('hidden', 'anim-toast-out');
    t.classList.add('anim-toast-in');
    toastTimer = setTimeout(() => {
        t.classList.remove('anim-toast-in');
        t.classList.add('anim-toast-out');
        setTimeout(() => { t.classList.add('hidden'); t.classList.remove('anim-toast-out'); }, 200);
    }, 2000);
}

// --- Responsive sidebar toggle ---
function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;
    const isOpen = sidebar.classList.contains('sidebar-open');
    if (isOpen) {
        sidebar.classList.remove('sidebar-open');
        if (overlay) overlay.classList.remove('active');
    } else {
        sidebar.classList.add('sidebar-open');
        if (overlay) overlay.classList.add('active');
    }
}

// --- Search modal ---
function openSearchModal() {
    const modal = document.getElementById('search-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    const input = document.getElementById('search-input');
    if (input) { input.value = ''; input.focus(); }
    handleSearch('');
}
function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    if (!modal || modal.classList.contains('hidden')) return;
    modal.classList.add('hidden');
}
function handleSearch(query) {
    const results = document.getElementById('search-results');
    if (!results) return;
    const items = results.querySelectorAll('.search-result-item');
    const q = query.toLowerCase().trim();
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = (!q || text.includes(q)) ? '' : 'none';
    });
}

// --- Workspace dropdown (auto-init) ---
document.addEventListener('DOMContentLoaded', function() {
    const trigger = document.getElementById('workspace-trigger');
    const menu = document.getElementById('workspace-menu');
    if (trigger && menu) {
        const dm = new DropdownManager();
        dm.register(trigger, menu);
    }
});

// --- Keyboard shortcuts (global) ---
document.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openSearchModal();
    }
    if (e.key === 'Escape') {
        closeSearchModal();
    }
});

/**
 * Shared CustomSelect — beautiful dropdown replacement for <select>.
 * Uses .dropdown-panel / .dropdown-item / .dropdown-item.active CSS.
 *
 * Usage:
 *   const cs = new CustomSelect(container, {
 *     options: [ { value: 'v', label: 'Label', icon: '<svg>...' }, ... ],
 *     value: 'v',                // initial value
 *     placeholder: 'Choose...',
 *     onChange: (value, option) => { ... }
 *   });
 *   cs.getValue();        // current value
 *   cs.setValue('v');      // programmatic set (no onChange fired)
 */
class CustomSelect {
    constructor(container, opts = {}) {
        this._container = typeof container === 'string' ? document.getElementById(container) : container;
        this._opts = opts;
        this._options = opts.options || [];
        this._value = opts.value ?? '';
        this._open = false;
        this._build();
    }
    _build() {
        const c = this._container;
        c.classList.add('relative');
        c.innerHTML = '';
        // Hidden input
        this._input = document.createElement('input');
        this._input.type = 'hidden';
        this._input.name = this._opts.name || '';
        this._input.value = this._value;
        c.appendChild(this._input);
        // Trigger button
        this._trigger = document.createElement('button');
        this._trigger.type = 'button';
        this._trigger.className = 'custom-select-trigger';
        this._trigger.innerHTML = this._renderTrigger();
        c.appendChild(this._trigger);
        // Dropdown panel
        this._panel = document.createElement('div');
        this._panel.className = 'hidden dropdown-panel w-full';
        this._panel.style.maxHeight = '200px';
        this._panel.style.overflowY = 'auto';
        this._renderOptions();
        c.appendChild(this._panel);
        // Events
        this._trigger.addEventListener('click', (e) => { e.stopPropagation(); this._toggle(); });
        document.addEventListener('click', (e) => {
            if (this._open && !c.contains(e.target)) this._close();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this._open) this._close();
        });
    }
    _renderTrigger() {
        const opt = this._options.find(o => o.value === this._value);
        const icon = opt?.icon || '';
        const label = opt?.label || this._opts.placeholder || 'Select...';
        const chevron = '<svg class="cs-chevron w-3 h-3 text-neutral-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/></svg>';
        return `${icon ? `<span class="shrink-0 flex items-center">${icon}</span>` : ''}<span class="flex-1 text-left truncate">${label}</span>${chevron}`;
    }
    _renderOptions() {
        this._panel.innerHTML = '<div class="py-1">' + this._options.map(o => {
            const active = o.value === this._value;
            const check = '<svg class="cs-check w-3.5 h-3.5 text-blue-500 ml-auto shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>';
            return `<button type="button" class="dropdown-item gap-2${active ? ' active' : ''}" data-value="${o.value}">
                ${o.icon ? `<span class="shrink-0 flex items-center">${o.icon}</span>` : ''}
                <span class="flex-1 text-left">${o.label}</span>
                ${active ? check : '<span class="w-3.5 h-3.5 ml-auto shrink-0"></span>'}
            </button>`;
        }).join('') + '</div>';
        this._panel.querySelectorAll('.dropdown-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const v = btn.dataset.value;
                if (v !== this._value) {
                    this._value = v;
                    this._input.value = v;
                    this._trigger.innerHTML = this._renderTrigger();
                    this._renderOptions();
                    if (this._opts.onChange) this._opts.onChange(v, this._options.find(o => o.value === v));
                }
                this._close();
            });
        });
    }
    _toggle() {
        this._open ? this._close() : this._openPanel();
    }
    _openPanel() {
        this._open = true;
        this._trigger.classList.add('open');
        animateDropdownOpen(this._panel);
    }
    _close() {
        if (!this._open) return;
        this._open = false;
        this._trigger.classList.remove('open');
        animateDropdownClose(this._panel);
    }
    getValue() { return this._value; }
    setValue(v) {
        this._value = v;
        this._input.value = v;
        this._trigger.innerHTML = this._renderTrigger();
        this._renderOptions();
    }
}

// --- Fetch helpers ---
async function api(url, opts = {}) {
    opts.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (opts.body && typeof opts.body === 'object') opts.body = JSON.stringify(opts.body);
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(await res.text());
    if (res.status === 204) return null;
    return res.json();
}
