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

// --- Fetch helpers ---
async function api(url, opts = {}) {
    opts.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (opts.body && typeof opts.body === 'object') opts.body = JSON.stringify(opts.body);
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}
