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

// --- Toast System ---
// Variants: 'default' | 'success' | 'destructive' | 'warning' | 'info'
const Toast = (() => {
    const MAX_VISIBLE = 10;
    const AUTO_DISMISS = 5000;
    const EXIT_DURATION = 400;
    let _id = 0;
    let _toasts = [];
    let _hovered = false;
    let _container = null;

    const icons = {
        default:     '<svg class="w-5 h-5 shrink-0 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
        success:     '<svg class="w-5 h-5 shrink-0 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/></svg>',
        destructive: '<svg class="w-5 h-5 shrink-0 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning:     '<svg class="w-5 h-5 shrink-0 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
        info:        '<svg class="w-5 h-5 shrink-0 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    };

    const variantStyles = {
        default:     'bg-white border border-neutral-200',
        success:     'border-l-4 border-l-green-500 border-y border-r border-green-200 bg-green-50 text-green-900',
        destructive: 'border-l-4 border-l-red-500 border-y border-r border-red-200 bg-red-50 text-red-900',
        warning:     'border-l-4 border-l-amber-500 border-y border-r border-amber-200 bg-amber-50 text-amber-900',
        info:        'border-l-4 border-l-blue-500 border-y border-r border-blue-200 bg-blue-50 text-blue-900',
    };

    const closeStyles = {
        default:     'text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100',
        success:     'text-green-600 hover:text-green-700 hover:bg-green-100',
        destructive: 'text-red-600 hover:text-red-700 hover:bg-red-100',
        warning:     'text-amber-600 hover:text-amber-700 hover:bg-amber-100',
        info:        'text-blue-600 hover:text-blue-700 hover:bg-blue-100',
    };

    function _ensureContainer() {
        if (_container) return _container;
        _container = document.createElement('div');
        _container.id = 'toast-container';
        _container.className = 'fixed bottom-0 right-0 z-[100] flex flex-col p-4 w-full sm:max-w-[420px] pointer-events-none';
        _container.innerHTML = '<div class="relative pointer-events-auto flex flex-col gap-2" id="toast-list"></div>';
        document.body.appendChild(_container);
        const list = _container.querySelector('#toast-list');
        list.addEventListener('mouseenter', () => { _hovered = true; _pauseAll(); });
        list.addEventListener('mouseleave', () => { _hovered = false; _resumeAll(); });
        return _container;
    }

    function _pauseAll() {
        _toasts.forEach(t => {
            if (t.timerId) {
                clearTimeout(t.timerId);
                t.remaining = Math.max(0, t.remaining - (Date.now() - t.startTime));
                t.timerId = null;
            }
        });
    }

    function _resumeAll() {
        _toasts.forEach(t => {
            if (!t.exiting && t.remaining > 0) {
                t.startTime = Date.now();
                t.timerId = setTimeout(() => _dismiss(t.id), t.remaining);
            }
        });
    }

    function _dismiss(id) {
        const t = _toasts.find(x => x.id === id);
        if (!t || t.exiting) return;
        t.exiting = true;
        if (t.timerId) clearTimeout(t.timerId);
        const el = t.el;
        el.style.transform = 'translateY(20px) scale(0.9)';
        el.style.opacity = '0';
        el.style.filter = 'blur(2px)';
        setTimeout(() => {
            _toasts = _toasts.filter(x => x.id !== id);
            el.remove();
            _updateVisibility();
        }, EXIT_DURATION);
    }

    function _updateVisibility() {
        const list = document.getElementById('toast-list');
        if (!list) return;
        const items = list.children;
        for (let i = 0; i < items.length; i++) {
            items[i].style.display = i < MAX_VISIBLE ? 'block' : 'none';
        }
    }

    function show(msg, variant) {
        if (!variant) variant = 'default';
        _ensureContainer();
        const id = ++_id;
        const v = variantStyles[variant] || variantStyles.default;
        const icon = icons[variant] || icons.default;
        const closeCls = closeStyles[variant] || closeStyles.default;

        const wrapper = document.createElement('div');
        wrapper.style.transition = `all ${EXIT_DURATION}ms ease-out`;
        wrapper.style.transform = 'translateY(100%) scale(0.9)';
        wrapper.style.opacity = '0';

        wrapper.innerHTML = `<div class="relative flex w-full items-center gap-3 overflow-hidden rounded-lg py-4 px-4 pr-10 shadow-lg ${v}" role="alert">
            <div class="flex items-start gap-3">
                ${icon}
                <div class="text-sm opacity-90">${_escHtml(msg)}</div>
            </div>
            <button type="button" class="absolute right-3 top-3 rounded-md p-1 opacity-70 transition-all duration-200 hover:opacity-100 ${closeCls}" aria-label="Dismiss">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
        </div>`;

        wrapper.querySelector('button').addEventListener('click', () => _dismiss(id));

        const list = document.getElementById('toast-list');
        list.insertBefore(wrapper, list.firstChild);

        // Enter animation
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                wrapper.style.transform = 'translateY(0) scale(1)';
                wrapper.style.opacity = '1';
            });
        });

        const entry = { id, el: wrapper, exiting: false, remaining: AUTO_DISMISS, startTime: Date.now(), timerId: null };
        _toasts.unshift(entry);

        if (!_hovered) {
            entry.timerId = setTimeout(() => _dismiss(id), AUTO_DISMISS);
        }

        _updateVisibility();
        return id;
    }

    function _escHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    return { show };
})();

function showToast(msg, variant) {
    Toast.show(msg, variant);
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

// --- Search / Navigator modal (delegates to Navigator if available) ---
function openSearchModal() { if (typeof Navigator !== 'undefined') Navigator.open(); }
function closeSearchModal() { if (typeof Navigator !== 'undefined') Navigator.close(); }

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
        if (typeof Navigator !== 'undefined') Navigator.toggle();
    }
    if (e.key === 'Escape') {
        if (typeof Navigator !== 'undefined') Navigator.close();
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
