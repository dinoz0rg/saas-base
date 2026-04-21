// ── Avatar Upload ──
async function uploadAvatar(input) {
    const file = input.files[0];
    if (!file) return;

    // Validate size (2MB max)
    if (file.size > 2 * 1024 * 1024) {
        showToast('File too large. Maximum size is 2MB.', 'destructive');
        input.value = '';
        return;
    }

    const loading = document.getElementById('avatar-loading');
    const container = document.getElementById('avatar-container');
    loading.classList.remove('hidden');
    loading.classList.add('flex');

    const formData = new FormData();
    formData.append('avatar', file);

    try {
        const res = await fetch('/profile/avatar', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.ok) {
            // Replace avatar content
            const existing = container.querySelector('img, #avatar-fallback');
            if (existing) existing.remove();
            const img = document.createElement('img');
            img.id = 'avatar-img';
            img.src = data.avatar_url + '?t=' + Date.now();
            img.alt = 'Avatar';
            img.className = 'h-20 w-20 rounded-full object-cover transition-all duration-300';
            container.insertBefore(img, loading);
            // Update sidebar avatar too
            const sidebarAvatar = document.getElementById('sidebar-avatar');
            if (sidebarAvatar) {
                sidebarAvatar.src = data.avatar_url + '?t=' + Date.now();
            } else {
                // If sidebar had fallback letter, replace it with img
                const sidebarUser = document.querySelector('#sidebar-avatar, .sidebar-avatar-fallback');
                if (!sidebarUser) {
                    const fallback = document.querySelector('a[href="/profile"] .w-5.h-5.rounded-full');
                    if (fallback) {
                        const sImg = document.createElement('img');
                        sImg.id = 'sidebar-avatar';
                        sImg.src = data.avatar_url + '?t=' + Date.now();
                        sImg.alt = '';
                        sImg.className = 'w-5 h-5 rounded-full object-cover shrink-0';
                        fallback.replaceWith(sImg);
                    }
                }
            }
            showToast('Avatar updated', 'success');
        } else {
            showToast(data.error || 'Failed to upload avatar', 'destructive');
        }
    } catch (e) {
        showToast('Failed to upload avatar', 'destructive');
    } finally {
        loading.classList.add('hidden');
        loading.classList.remove('flex');
        input.value = '';
    }
}

// ── Profile Form (AJAX) ──
document.getElementById('profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const firstName = document.getElementById('first_name').value.trim();
    const lastName = document.getElementById('last_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const displayName = lastName ? firstName + ' ' + lastName : firstName;

    const formData = new URLSearchParams();
    formData.append('display_name', displayName);
    formData.append('email', email);

    try {
        const res = await fetch('/profile', {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: formData,
        });
        const data = await res.json();
        if (data.ok) {
            showToast('Profile updated', 'success');
        } else {
            showToast(data.error || 'Failed to update profile', 'destructive');
        }
    } catch (e) {
        showToast('Failed to update profile', 'destructive');
    }
});

// ── Password Form (AJAX) ──
document.getElementById('password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const current = document.getElementById('current_password').value;
    const newPw = document.getElementById('new_password').value;
    const confirm = document.getElementById('confirm_password').value;

    if (newPw !== confirm) {
        showToast('Passwords do not match', 'destructive');
        return;
    }

    const formData = new URLSearchParams();
    formData.append('current_password', current);
    formData.append('new_password', newPw);

    try {
        const res = await fetch('/profile/password', {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: formData,
        });
        const data = await res.json();
        if (data.ok) {
            showToast('Password updated', 'success');
            document.getElementById('password-form').reset();
        } else {
            showToast(data.error || 'Failed to update password', 'destructive');
        }
    } catch (e) {
        showToast('Failed to update password', 'destructive');
    }
});

// ── 2FA ──
async function start2FASetup() {
    const btn = document.getElementById('2fa-enable-btn');
    btn.disabled = true;
    btn.textContent = 'Setting up...';
    try {
        const res = await fetch('/profile/2fa/setup', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('2fa-qr-img').src = data.qr_code;
            document.getElementById('2fa-secret-code').textContent = data.secret;
            document.getElementById('2fa-setup-area').classList.add('hidden');
            document.getElementById('2fa-qr-area').classList.remove('hidden');
        } else {
            showToast(data.error || 'Failed to set up 2FA', 'destructive');
        }
    } catch (e) {
        showToast('Failed to set up 2FA', 'destructive');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Enable two-factor authentication';
    }
}

function cancel2FASetup() {
    document.getElementById('2fa-qr-area').classList.add('hidden');
    document.getElementById('2fa-setup-area').classList.remove('hidden');
    document.getElementById('2fa-verify-code').value = '';
}

async function verify2FA() {
    const code = document.getElementById('2fa-verify-code').value.trim();
    if (!code || code.length !== 6) {
        showToast('Please enter a 6-digit code', 'warning');
        return;
    }
    const formData = new URLSearchParams();
    formData.append('code', code);
    try {
        const res = await fetch('/profile/2fa/verify', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.ok) {
            showToast('Two-factor authentication enabled!', 'success');
            document.getElementById('2fa-qr-area').classList.add('hidden');
            document.getElementById('2fa-setup-area').classList.add('hidden');
            document.getElementById('2fa-disable-area').classList.remove('hidden');
            const badge = document.getElementById('2fa-badge');
            badge.className = 'inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700';
            badge.textContent = 'Enabled';
            const icon = document.getElementById('2fa-icon');
            icon.className = icon.className.replace('bg-neutral-100', 'bg-emerald-100');
            icon.querySelector('svg').className = icon.querySelector('svg').className.replace('text-neutral-600', 'text-emerald-600');
        } else {
            showToast(data.error || 'Invalid code', 'destructive');
        }
    } catch (e) {
        showToast('Failed to verify code', 'destructive');
    }
}

async function disable2FA() {
    const password = document.getElementById('2fa-disable-password').value;
    if (!password) {
        showToast('Please enter your password', 'warning');
        return;
    }
    const formData = new URLSearchParams();
    formData.append('password', password);
    try {
        const res = await fetch('/profile/2fa/disable', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.ok) {
            showToast('Two-factor authentication disabled', 'success');
            document.getElementById('2fa-disable-area').classList.add('hidden');
            document.getElementById('2fa-disable-confirm').classList.add('hidden');
            document.getElementById('2fa-disable-password').value = '';
            document.getElementById('2fa-setup-area').classList.remove('hidden');
            const badge = document.getElementById('2fa-badge');
            badge.className = 'inline-flex items-center rounded-full border border-neutral-200 bg-neutral-50 px-2.5 py-0.5 text-xs font-medium text-neutral-600';
            badge.textContent = 'Not enabled';
            const icon = document.getElementById('2fa-icon');
            icon.className = icon.className.replace('bg-emerald-100', 'bg-neutral-100');
            icon.querySelector('svg').className = icon.querySelector('svg').className.replace('text-emerald-600', 'text-neutral-600');
        } else {
            showToast(data.error || 'Failed to disable 2FA', 'destructive');
        }
    } catch (e) {
        showToast('Failed to disable 2FA', 'destructive');
    }
}

// ── Sessions ──
function timeAgo(isoStr) {
    if (!isoStr) return 'Unknown';
    const diff = Date.now() - new Date(isoStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return mins + 'm ago';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    const days = Math.floor(hrs / 24);
    return days + 'd ago';
}

function renderSessions(sessions) {
    const list = document.getElementById('sessions-list');
    if (!sessions.length) {
        list.innerHTML = '<p class="text-sm text-neutral-500 py-4 text-center">No active sessions</p>';
        return;
    }
    list.innerHTML = sessions.map(s => {
        const isCurrent = s.is_current;
        const borderCls = isCurrent ? 'border-emerald-200 bg-emerald-50/50' : 'border-neutral-200 bg-white';
        const iconBg = isCurrent ? 'bg-emerald-100' : 'bg-neutral-100';
        const iconText = isCurrent ? 'text-emerald-600' : 'text-neutral-600';
        const badge = isCurrent ? '<span class="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">Current</span>' : '';
        const revokeBtn = !isCurrent ? `<button onclick="revokeSession('${s.id}')" class="rounded-md border border-neutral-200 bg-white px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 transition">Revoke</button>` : '';
        return `<div class="flex items-center justify-between rounded-lg border ${borderCls} p-4">
            <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-lg ${iconBg}">
                    <svg class="h-5 w-5 ${iconText}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8m-4-4v4"/></svg>
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <p class="text-sm font-medium text-neutral-900">${s.browser} on ${s.os}</p>
                        ${badge}
                    </div>
                    <p class="text-xs text-neutral-500 mt-0.5">${s.ip_address} · Last active ${timeAgo(s.last_active)}</p>
                </div>
            </div>
            ${revokeBtn}
        </div>`;
    }).join('');
}

async function loadSessions() {
    try {
        const res = await fetch('/api/sessions');
        const data = await res.json();
        if (data.ok) renderSessions(data.sessions);
    } catch (e) {
        document.getElementById('sessions-list').innerHTML = '<p class="text-sm text-red-500 py-4 text-center">Failed to load sessions</p>';
    }
}

async function revokeSession(id) {
    try {
        const res = await fetch('/api/sessions/' + id, { method: 'DELETE' });
        const data = await res.json();
        if (data.ok) {
            showToast('Session revoked', 'success');
            loadSessions();
        } else {
            showToast(data.error || 'Failed to revoke session', 'destructive');
        }
    } catch (e) {
        showToast('Failed to revoke session', 'destructive');
    }
}

async function handleSignOutAll() {
    try {
        const res = await fetch('/api/sessions/revoke-others', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            showToast('All other sessions have been signed out', 'success');
            loadSessions();
        } else {
            showToast(data.error || 'Failed to sign out sessions', 'destructive');
        }
    } catch (e) {
        showToast('Failed to sign out sessions', 'destructive');
    }
}

// Load sessions on page load
loadSessions();
