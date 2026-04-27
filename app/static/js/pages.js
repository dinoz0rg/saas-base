/**
 * Pages list + editor logic.
 */
(function () {
    'use strict';

    // ── Editor (page-form) ──────────────────────────────────────────────────
    const form = document.getElementById('page-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const mode = form.dataset.mode;
            const id = form.dataset.id;
            const url = mode === 'edit' ? '/dashboard/pages/' + encodeURIComponent(id) : '/dashboard/pages';
            const btn = form.querySelector('button[type="submit"]');
            const original = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Saving…';
            try {
                const res = await fetch(url, { method: 'POST', body: new FormData(form) });
                const data = await res.json();
                if (!res.ok || !data.ok) throw new Error(data.error || 'Save failed.');
                showToast(mode === 'edit' ? 'Page updated.' : 'Page created.', 'success');
                if (data.redirect) setTimeout(() => location.href = data.redirect, 400);
            } catch (err) {
                showToast(err.message, 'destructive');
            } finally {
                btn.disabled = false;
                btn.textContent = original;
            }
        });

        const delBtn = document.getElementById('page-delete-btn');
        if (delBtn) {
            delBtn.addEventListener('click', async () => {
                if (!confirm('Delete this page? This cannot be undone.')) return;
                try {
                    const res = await fetch('/dashboard/pages/' + encodeURIComponent(form.dataset.id) + '/delete', { method: 'POST' });
                    const data = await res.json();
                    if (!data.ok) throw new Error(data.error || 'Failed');
                    showToast('Page deleted.', 'success');
                    setTimeout(() => location.href = '/dashboard/pages', 400);
                } catch (err) { showToast(err.message, 'destructive'); }
            });
        }
    }

    // ── List page actions ───────────────────────────────────────────────────
    document.addEventListener('click', async (e) => {
        const pubBtn = e.target.closest('.page-publish');
        if (pubBtn) {
            const row = pubBtn.closest('.page-row');
            try {
                const res = await fetch('/dashboard/pages/' + encodeURIComponent(row.dataset.id) + '/publish', { method: 'POST' });
                const data = await res.json();
                if (!data.ok) throw new Error(data.error || 'Failed');
                const status = row.querySelector('.page-status');
                if (data.is_published) {
                    pubBtn.textContent = 'Unpublish';
                    status.textContent = 'Published';
                    status.className = 'page-status text-2xs px-2 py-1 rounded-full font-medium shrink-0 bg-emerald-50 text-emerald-700';
                    showToast('Page published.', 'success');
                } else {
                    pubBtn.textContent = 'Publish';
                    status.textContent = 'Draft';
                    status.className = 'page-status text-2xs px-2 py-1 rounded-full font-medium shrink-0 bg-neutral-100 text-neutral-600';
                    showToast('Page unpublished.', 'success');
                }
            } catch (err) { showToast(err.message, 'destructive'); }
            return;
        }

        const delBtn = e.target.closest('.page-delete');
        if (delBtn) {
            const row = delBtn.closest('.page-row');
            if (!confirm('Delete this page? This cannot be undone.')) return;
            try {
                const res = await fetch('/dashboard/pages/' + encodeURIComponent(row.dataset.id) + '/delete', { method: 'POST' });
                const data = await res.json();
                if (!data.ok) throw new Error(data.error || 'Failed');
                row.style.transition = 'opacity .25s';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 250);
                showToast('Page deleted.', 'success');
            } catch (err) { showToast(err.message, 'destructive'); }
        }
    });
})();
