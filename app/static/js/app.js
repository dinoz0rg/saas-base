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

// --- Fetch helpers ---
async function api(url, opts = {}) {
    opts.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (opts.body && typeof opts.body === 'object') opts.body = JSON.stringify(opts.body);
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(await res.text());
    if (res.status === 204) return null;
    return res.json();
}
