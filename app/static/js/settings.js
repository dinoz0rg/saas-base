/**
 * Settings page logic — tab switching, form submission, sessions list,
 * API keys CRUD, and account deletion.
 */
(function () {
    'use strict';

    // ── Tab switching (also reflects in URL hash for shareable links) ───────
    const tabs = document.querySelectorAll('.settings-tab');
    const panels = document.querySelectorAll('.settings-panel');

    function showTab(slug) {
        let found = false;
        panels.forEach(p => {
            const match = p.getAttribute('data-panel') === slug;
            p.style.display = match ? '' : 'none';
            if (match) found = true;
        });
        if (!found) {
            slug = 'general';
            panels.forEach(p => p.style.display = p.getAttribute('data-panel') === 'general' ? '' : 'none');
        }
        tabs.forEach(t => {
            const active = t.dataset.tab === slug;
            t.classList.toggle('bg-neutral-900', active);
            t.classList.toggle('text-white', active);
            t.classList.toggle('text-neutral-700', !active);
            t.classList.toggle('hover:bg-neutral-100', !active);
        });
        history.replaceState(null, '', '?tab=' + slug);
        if (slug === 'sessions') loadSessions();
    }
    tabs.forEach(t => t.addEventListener('click', () => showTab(t.dataset.tab)));

    const initial = (location.hash.startsWith('#') ? location.hash.slice(1) : null)
        || (window.__INITIAL_TAB__ || 'general');
    showTab(initial);

    // ── Form submit helper ──────────────────────────────────────────────────
    async function submitForm(form, url, method = 'POST') {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) { btn.disabled = true; btn.dataset._label = btn.textContent; btn.textContent = 'Saving…'; }
        try {
            const fd = new FormData(form);
            // Convert checkbox 'on' to truthy 'on' string already; nothing extra needed.
            const res = await fetch(url, { method, body: fd });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.ok) throw new Error(data.error || 'Request failed');
            return data;
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = btn.dataset._label || 'Save'; }
        }
    }

    function bindForm(formId, url, opts = {}) {
        const form = document.getElementById(formId);
        if (!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const data = await submitForm(form, url);
                showToast(opts.successMsg || 'Saved.', 'success');
                if (opts.onSuccess) opts.onSuccess(data, form);
            } catch (err) {
                showToast(err.message || 'Something went wrong.', 'destructive');
            }
        });
    }

    // ── General / Notifications / Password ──────────────────────────────────
    bindForm('form-general', '/dashboard/settings/general', { successMsg: 'Profile updated.' });
    bindForm('form-notifications', '/dashboard/settings/notifications', { successMsg: 'Preferences saved.' });
    bindForm('form-password', '/dashboard/settings/password', {
        successMsg: 'Password updated.',
        onSuccess: (_, form) => form.reset(),
    });

    // ── Appearance: select-card UX + live theme apply ───────────────────────
    function syncSelectedClasses(panel) {
        panel.querySelectorAll('.theme-option, .density-option, .accent-option').forEach(label => {
            const input = label.querySelector('input');
            label.classList.toggle('selected', !!input?.checked);
        });
    }
    const appearance = document.getElementById('form-appearance');
    if (appearance) {
        syncSelectedClasses(appearance);
        appearance.addEventListener('change', () => syncSelectedClasses(appearance));
        bindForm('form-appearance', '/dashboard/settings/appearance', {
            successMsg: 'Appearance updated.',
            onSuccess: (data) => applyTheme(data.theme, data.accent),
        });
    }

    function applyTheme(theme, accent) {
        const root = document.documentElement;
        const t = theme === 'system'
            ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
            : theme;
        root.dataset.theme = t;
        root.dataset.accent = accent;
        try {
            localStorage.setItem('app.theme', theme);
            localStorage.setItem('app.accent', accent);
        } catch (_) { /* ignore */ }
    }

    // ── Sessions ────────────────────────────────────────────────────────────
    const sessionsList = document.getElementById('sessions-list');

    async function loadSessions() {
        if (!sessionsList) return;
        sessionsList.innerHTML = '<div class="flex items-center justify-center py-6 text-sm text-neutral-500">Loading…</div>';
        try {
            const res = await fetch('/api/sessions');
            const data = await res.json();
            if (!data.ok) throw new Error('Failed');
            renderSessions(data.sessions || []);
        } catch (e) {
            sessionsList.innerHTML = '<div class="text-center py-6 text-sm text-red-600">Failed to load sessions.</div>';
        }
    }

    function fmtDate(iso) {
        if (!iso) return '—';
        const d = new Date(iso);
        return d.toLocaleString();
    }

    function renderSessions(items) {
        if (!items.length) {
            sessionsList.innerHTML = '<div class="text-center py-6 text-sm text-muted">No active sessions.</div>';
            return;
        }
        sessionsList.innerHTML = '<div class="space-y-2">' + items.map(s => `
            <div class="flex items-center justify-between gap-4 rounded-lg border border-neutral-200 bg-neutral-50/50 p-3">
                <div class="flex items-start gap-3 min-w-0">
                    <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white border border-neutral-200 text-neutral-600">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                    </div>
                    <div class="min-w-0">
                        <div class="text-sm font-medium text-neutral-900 truncate">
                            ${esc(s.browser)} · ${esc(s.os)}
                            ${s.is_current ? '<span class="ml-2 rounded-full bg-emerald-100 text-emerald-700 px-1.5 py-0.5 text-2xs font-medium">This device</span>' : ''}
                        </div>
                        <div class="text-xs text-muted mt-0.5">${esc(s.ip_address)} · last active ${fmtDate(s.last_active)}</div>
                    </div>
                </div>
                ${s.is_current ? '' :
                    `<button data-id="${esc(s.id)}" class="session-revoke shrink-0 rounded-lg border border-red-200 bg-white text-red-600 hover:bg-red-50 px-3 py-1.5 text-xs font-medium transition">Sign out</button>`
                }
            </div>
        `).join('') + '</div>';
    }

    function esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }

    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.session-revoke');
        if (!btn) return;
        if (!confirm('Sign out this session?')) return;
        try {
            const res = await fetch('/api/sessions/' + encodeURIComponent(btn.dataset.id), { method: 'DELETE' });
            const data = await res.json();
            if (!data.ok) throw new Error(data.error || 'Failed');
            showToast('Session signed out.', 'success');
            loadSessions();
        } catch (err) {
            showToast(err.message, 'destructive');
        }
    });

    const revokeOthers = document.getElementById('sessions-revoke-others');
    if (revokeOthers) {
        revokeOthers.addEventListener('click', async () => {
            if (!confirm('Sign out all other sessions? You\'ll stay signed in here.')) return;
            try {
                const res = await fetch('/api/sessions/revoke-others', { method: 'POST' });
                const data = await res.json();
                if (!data.ok) throw new Error(data.error || 'Failed');
                showToast('Other sessions signed out.', 'success');
                loadSessions();
            } catch (err) { showToast(err.message, 'destructive'); }
        });
    }

    // ── API keys ────────────────────────────────────────────────────────────
    const apikeyCreateBtn = document.getElementById('apikey-create-btn');
    const apikeyForm = document.getElementById('apikey-form');
    const apikeyList = document.getElementById('apikey-list');

    if (apikeyCreateBtn) {
        apikeyCreateBtn.addEventListener('click', () => Modal.open('apikey-modal'));
    }
    if (apikeyForm) {
        apikeyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const data = await submitForm(apikeyForm, '/dashboard/settings/api-keys');
                Modal.close('apikey-modal');
                apikeyForm.reset();
                addApiKeyRow(data);
                document.getElementById('apikey-reveal-value').textContent = data.key;
                Modal.open('apikey-reveal-modal');
            } catch (err) {
                showToast(err.message, 'destructive');
            }
        });
    }

    function addApiKeyRow(k) {
        const empty = document.getElementById('apikey-empty');
        if (empty) empty.remove();
        const created = new Date(k.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' });
        const row = document.createElement('div');
        row.className = 'apikey-row flex items-center justify-between gap-4 rounded-lg border border-neutral-200 bg-neutral-50/50 p-3';
        row.dataset.id = k.id;
        row.innerHTML = `
            <div class="min-w-0">
                <div class="text-sm font-medium text-neutral-900 truncate">${esc(k.name)}</div>
                <div class="text-xs text-muted mt-0.5 font-mono">${esc(k.prefix)}••••••••••••••••</div>
                <div class="text-2xs text-muted mt-1">Created ${created}</div>
            </div>
            <button class="apikey-revoke shrink-0 rounded-lg border border-red-200 bg-white text-red-600 hover:bg-red-50 px-3 py-1.5 text-xs font-medium transition">Revoke</button>`;
        apikeyList.prepend(row);
    }

    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.apikey-revoke');
        if (!btn) return;
        const row = btn.closest('.apikey-row');
        if (!confirm('Revoke this API key? Apps using it will stop working immediately.')) return;
        try {
            const res = await fetch('/dashboard/settings/api-keys/' + encodeURIComponent(row.dataset.id), { method: 'DELETE' });
            const data = await res.json();
            if (!data.ok) throw new Error(data.error || 'Failed');
            row.remove();
            showToast('API key revoked.', 'success');
            if (!apikeyList.querySelector('.apikey-row')) {
                apikeyList.innerHTML = '<div id="apikey-empty" class="text-center py-10 text-sm text-muted">No API keys yet. Create one to get started.</div>';
            }
        } catch (err) {
            showToast(err.message, 'destructive');
        }
    });

    const copyBtn = document.getElementById('apikey-copy');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const v = document.getElementById('apikey-reveal-value').textContent;
            try {
                await navigator.clipboard.writeText(v);
                copyBtn.textContent = 'Copied';
                setTimeout(() => copyBtn.textContent = 'Copy', 1500);
            } catch (_) {
                showToast('Copy failed.', 'destructive');
            }
        });
    }


    // ── Avatar upload ───────────────────────────────────────────────────────
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) {
        avatarInput.addEventListener('change', async () => {
            const file = avatarInput.files && avatarInput.files[0];
            if (!file) return;
            if (file.size > 2 * 1024 * 1024) {
                showToast('Image must be 2MB or smaller.', 'destructive');
                avatarInput.value = '';
                return;
            }
            const fd = new FormData();
            fd.append('avatar', file);
            try {
                const res = await fetch('/profile/avatar', { method: 'POST', body: fd });
                const data = await res.json();
                if (!data.ok) throw new Error(data.error || 'Upload failed');
                const preview = document.getElementById('avatar-preview');
                const fallback = document.getElementById('avatar-preview-fallback');
                if (preview) {
                    preview.src = data.avatar_url + '?t=' + Date.now();
                    preview.classList.remove('hidden');
                }
                if (fallback) fallback.classList.add('hidden');
                const sidebarAv = document.getElementById('sidebar-avatar');
                if (sidebarAv) sidebarAv.src = data.avatar_url + '?t=' + Date.now();
                showToast('Profile photo updated.', 'success');
            } catch (err) {
                showToast(err.message, 'destructive');
            } finally {
                avatarInput.value = '';
            }
        });
    }

    // ── 2FA ─────────────────────────────────────────────────────────────────
    const twofaEnableBtn = document.getElementById('twofa-enable-btn');
    const twofaSetup = document.getElementById('twofa-setup');
    const twofaCancel = document.getElementById('twofa-cancel');
    const twofaVerifyForm = document.getElementById('twofa-verify-form');
    const twofaDisableBtn = document.getElementById('twofa-disable-btn');
    const twofaDisableForm = document.getElementById('twofa-disable-form');
    const twofaDisableCancel = document.getElementById('twofa-disable-cancel');

    if (twofaEnableBtn) {
        twofaEnableBtn.addEventListener('click', async () => {
            twofaEnableBtn.disabled = true;
            try {
                const res = await fetch('/profile/2fa/setup', { method: 'POST' });
                const data = await res.json();
                if (!data.ok) throw new Error(data.error || 'Failed');
                document.getElementById('twofa-qr').src = data.qr_code;
                document.getElementById('twofa-secret').textContent = data.secret;
                twofaSetup.classList.remove('hidden');
                twofaSetup.querySelector('input[name="code"]').focus();
            } catch (err) {
                showToast(err.message, 'destructive');
            } finally {
                twofaEnableBtn.disabled = false;
            }
        });
    }
    if (twofaCancel) twofaCancel.addEventListener('click', () => twofaSetup.classList.add('hidden'));
    if (twofaVerifyForm) {
        twofaVerifyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await submitForm(twofaVerifyForm, '/profile/2fa/verify');
                showToast('Two-factor authentication enabled.', 'success');
                setTimeout(() => location.reload(), 500);
            } catch (err) {
                showToast(err.message, 'destructive');
            }
        });
    }
    if (twofaDisableBtn) twofaDisableBtn.addEventListener('click', () => {
        twofaDisableForm.classList.remove('hidden');
        twofaDisableForm.querySelector('input[name="password"]').focus();
    });
    if (twofaDisableCancel) twofaDisableCancel.addEventListener('click', () => twofaDisableForm.classList.add('hidden'));
    if (twofaDisableForm) {
        twofaDisableForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await submitForm(twofaDisableForm, '/profile/2fa/disable');
                showToast('Two-factor authentication disabled.', 'success');
                setTimeout(() => location.reload(), 500);
            } catch (err) {
                showToast(err.message, 'destructive');
            }
        });
    }

    // ── Danger zone ─────────────────────────────────────────────────────────
    const deleteBtn = document.getElementById('danger-delete-btn');
    const dangerForm = document.getElementById('danger-form');
    if (deleteBtn) deleteBtn.addEventListener('click', () => Modal.open('danger-modal'));
    if (dangerForm) {
        dangerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const data = await submitForm(dangerForm, '/dashboard/settings/danger/delete');
                showToast('Account deleted.', 'success');
                setTimeout(() => location.href = data.redirect || '/', 600);
            } catch (err) {
                showToast(err.message, 'destructive');
            }
        });
    }
})();
