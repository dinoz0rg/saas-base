/**
 * Board page logic: CRUD, drag-drop, search, filters,
 * view tabs, display/column menus, hidden columns, keyboard shortcuts.
 *
 * Expects globals: BOARD_URL (set inline by board.html template).
 * Depends on: app.js (animateOpen/Close, animateDropdown*, showToast, api).
 */

let currentIssueId = null;

// --- Create Issue Modal ---
function openCreateModal(status) {
    const modal = document.getElementById('create-modal');
    const form = document.getElementById('create-form');
    form.reset();
    if (status) form.querySelector('[name=status]').value = status;
    const { content } = animateOpen(modal, '.modal-backdrop', '.modal-content');
    if (content) content.classList.add('anim-modal-in');
}
function closeCreateModal() {
    const modal = document.getElementById('create-modal');
    animateClose(modal, '.modal-backdrop', '.modal-content', 'anim-modal-out');
}

async function submitCreateIssue(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        title: form.title.value,
        description: form.description.value || null,
        status: form.status.value,
        priority: form.priority.value,
        assignee: form.assignee.value || null,
        label: form.label.value || null,
    };
    try {
        await api('/api/issues', { method: 'POST', body: data });
        closeCreateModal();
        showToast('Issue created');
        location.reload();
    } catch (err) { showToast('Error: ' + err.message); }
}

// --- Issue Detail ---
async function openIssueDetail(issueId) {
    currentIssueId = issueId;
    try {
        const issue = await api('/api/issues/' + issueId);
        document.getElementById('detail-identifier').textContent = issue.identifier;
        document.getElementById('detail-title').value = issue.title;
        document.getElementById('detail-description').value = issue.description || '';
        document.getElementById('detail-status').value = issue.status;
        document.getElementById('detail-priority').value = issue.priority;
        document.getElementById('detail-assignee').value = issue.assignee || '';
        document.getElementById('detail-label').value = issue.label || '';
        const panel = document.getElementById('detail-panel');
        const { content } = animateOpen(panel, '.panel-backdrop', '.panel-content');
        if (content) content.classList.add('anim-slide-in');
    } catch (err) { showToast('Error loading issue'); }
}
function closeDetailPanel() {
    const panel = document.getElementById('detail-panel');
    animateClose(panel, '.panel-backdrop', '.panel-content', 'anim-slide-out');
    currentIssueId = null;
}

async function updateCurrentIssue(fields) {
    if (!currentIssueId) return;
    try {
        await api('/api/issues/' + currentIssueId, { method: 'PATCH', body: fields });
        showToast('Updated');
        if (fields.status) location.reload();
    } catch (err) { showToast('Error: ' + err.message); }
}

async function deleteCurrentIssue() {
    if (!currentIssueId) return;
    if (!confirm('Delete this issue?')) return;
    try {
        await api('/api/issues/' + currentIssueId, { method: 'DELETE' });
        closeDetailPanel();
        showToast('Issue deleted');
        location.reload();
    } catch (err) { showToast('Error: ' + err.message); }
}

// --- Drag & Drop ---
let draggedCard = null;

document.addEventListener('dragstart', (e) => {
    const card = e.target.closest('.issue-card');
    if (!card) return;
    draggedCard = card;
    card.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', card.dataset.issueId);
});

document.addEventListener('dragend', (e) => {
    if (draggedCard) draggedCard.classList.remove('dragging');
    draggedCard = null;
    document.querySelectorAll('.drop-zone').forEach(z => z.classList.remove('drag-over'));
});

document.querySelectorAll('.drop-zone').forEach(zone => {
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });
    zone.addEventListener('drop', async (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const issueId = e.dataTransfer.getData('text/plain');
        const newStatus = zone.dataset.status;
        if (!issueId || !newStatus) return;
        if (draggedCard) {
            draggedCard.classList.remove('dragging');
            draggedCard.classList.add('anim-card');
            zone.appendChild(draggedCard);
        }
        try {
            await api('/api/issues/' + issueId, { method: 'PATCH', body: { status: newStatus } });
            showToast('Moved to ' + newStatus.replace('_', ' '));
            location.reload();
        } catch (err) {
            showToast('Error moving issue');
            location.reload();
        }
    });
});

// --- Search ---
function openSearchModal() {
    const modal = document.getElementById('search-modal');
    const { content } = animateOpen(modal, '.search-backdrop', '.search-content');
    if (content) content.classList.add('anim-search-in');
    document.getElementById('search-input').value = '';
    document.getElementById('search-input').focus();
    document.getElementById('search-results').innerHTML = '<div class="px-4 py-8 text-center text-sm text-neutral-400">Type to search issues...</div>';
}
function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    animateClose(modal, '.search-backdrop', '.search-content', 'anim-search-out');
}

let searchTimeout;
function handleSearch(query) {
    clearTimeout(searchTimeout);
    if (!query.trim()) {
        document.getElementById('search-results').innerHTML = '<div class="px-4 py-8 text-center text-sm text-neutral-400">Type to search issues...</div>';
        return;
    }
    searchTimeout = setTimeout(async () => {
        try {
            const issues = await api('/api/issues');
            const q = query.toLowerCase();
            const matches = issues.filter(i => i.title.toLowerCase().includes(q) || (i.description || '').toLowerCase().includes(q) || i.identifier.toLowerCase().includes(q));
            const container = document.getElementById('search-results');
            if (!matches.length) {
                container.innerHTML = '<div class="px-4 py-8 text-center text-sm text-neutral-400">No issues found</div>';
                return;
            }
            const statusColors = {backlog:'bg-neutral-200',todo:'bg-neutral-200',in_progress:'bg-amber-100',done:'bg-green-100',cancelled:'bg-neutral-200'};
            container.innerHTML = matches.slice(0, 20).map(i =>
                '<div class="flex items-center gap-3 px-4 py-2.5 hover:bg-neutral-50 cursor-pointer border-b border-neutral-50" onclick="closeSearchModal(); openIssueDetail(\'' + i.id + '\')">' +
                    '<span class="text-2xs text-muted font-mono w-14 shrink-0">' + i.identifier + '</span>' +
                    '<span class="text-sm text-neutral-800 truncate flex-1">' + i.title + '</span>' +
                    '<span class="text-2xs px-1.5 py-0.5 rounded ' + (statusColors[i.status] || 'bg-neutral-200') + '">' + i.status.replace('_',' ') + '</span>' +
                '</div>'
            ).join('');
        } catch (err) { console.error(err); }
    }, 200);
}

// --- View Tabs ---
function setViewTab(tab) {
    document.querySelectorAll('.board-tab').forEach(b => {
        b.className = b.className.replace(/bg-neutral-50 font-medium text-neutral-800/g, '').replace(/text-neutral-600/g, '');
        if (b.dataset.tab === tab) {
            b.classList.add('bg-neutral-50', 'font-medium', 'text-neutral-800');
        } else {
            b.classList.add('text-neutral-600');
        }
    });
    const cols = { all: ['backlog','todo','in_progress'], active: ['in_progress','todo'], backlog: ['backlog'] };
    const visible = cols[tab] || cols.all;
    document.querySelectorAll('.kanban-col').forEach(col => {
        col.style.display = visible.includes(col.dataset.status) ? '' : 'none';
    });
}

// --- Display Menu ---
function toggleDisplayMenu() {
    const m = document.getElementById('display-menu');
    if (m.classList.contains('hidden')) {
        animateDropdownOpen(m);
    } else {
        animateDropdownClose(m);
    }
    animateDropdownClose(document.getElementById('filter-menu'));
    closeAllColMenus();
}
function setGrouping(group) {
    document.querySelectorAll('.group-opt span').forEach(s => s.classList.add('hidden'));
    document.querySelector('.group-opt[data-group="' + group + '"] span').classList.remove('hidden');
    showToast('Grouped by ' + group);
    animateDropdownClose(document.getElementById('display-menu'));
}
function toggleLabels(show) {
    document.querySelectorAll('.issue-card .card-labels').forEach(el => el.style.display = show ? '' : 'none');
}
function toggleAssignees(show) {
    document.querySelectorAll('.issue-card .card-assignee').forEach(el => el.style.display = show ? '' : 'none');
}

// --- Filter Menu ---
let activeFilters = {};
function toggleFilterMenu() {
    const m = document.getElementById('filter-menu');
    if (m.classList.contains('hidden')) {
        animateDropdownOpen(m);
    } else {
        animateDropdownClose(m);
    }
    animateDropdownClose(document.getElementById('display-menu'));
    closeAllColMenus();
}
function applyFilter(type, value) {
    activeFilters[type] = value;
    animateDropdownClose(document.getElementById('filter-menu'));
    renderActiveFilters();
    applyAllFilters();
}
function removeFilter(type) {
    delete activeFilters[type];
    renderActiveFilters();
    applyAllFilters();
}
function clearFilters() {
    activeFilters = {};
    animateDropdownClose(document.getElementById('filter-menu'));
    renderActiveFilters();
    applyAllFilters();
}
function renderActiveFilters() {
    const container = document.getElementById('active-filters');
    container.innerHTML = Object.entries(activeFilters).map(([type, value]) =>
        '<span class="inline-flex items-center gap-1 px-2 py-0.5 text-2xs bg-blue-50 text-blue-700 rounded-md">' +
            type + ': ' + value +
            ' <button onclick="removeFilter(\'' + type + '\')" class="hover:text-blue-900 ml-0.5">&times;</button>' +
        '</span>'
    ).join('');
}
function applyAllFilters() {
    document.querySelectorAll('.issue-card').forEach(card => {
        let show = true;
        if (activeFilters.priority) {
            show = show && card.dataset.priority === activeFilters.priority;
        }
        if (activeFilters.label) {
            const cardLabel = (card.dataset.label || '').toLowerCase();
            show = show && cardLabel.includes(activeFilters.label.toLowerCase());
        }
        card.style.display = show ? '' : 'none';
    });
    document.querySelectorAll('.kanban-col').forEach(col => {
        const visible = col.querySelectorAll('.issue-card:not([style*="display: none"])').length;
        col.querySelector('.col-count').textContent = visible;
    });
}

// --- Column menus ---
function toggleColMenu(status) {
    const menu = document.getElementById('col-menu-' + status);
    const wasHidden = menu.classList.contains('hidden');
    closeAllColMenus();
    if (wasHidden) animateDropdownOpen(menu);
}
function closeAllColMenus() {
    document.querySelectorAll('[id^="col-menu-"]').forEach(m => animateDropdownClose(m));
}
function sortColumn(status, sortBy) {
    const zone = document.querySelector('.drop-zone[data-status="' + status + '"]');
    const cards = [...zone.querySelectorAll('.issue-card')];
    const priorityOrder = {urgent:0,high:1,medium:2,low:3,none:4};
    cards.sort((a, b) => {
        if (sortBy === 'priority') return (priorityOrder[a.dataset.priority] ?? 4) - (priorityOrder[b.dataset.priority] ?? 4);
        if (sortBy === 'title') return (a.dataset.title || '').localeCompare(b.dataset.title || '');
        if (sortBy === 'created') return (b.dataset.created || '').localeCompare(a.dataset.created || '');
        return 0;
    });
    cards.forEach(c => zone.appendChild(c));
    closeAllColMenus();
    showToast('Sorted by ' + sortBy);
}
function collapseColumn(status) {
    const col = document.getElementById('col-' + status);
    const zone = col.querySelector('.drop-zone');
    zone.classList.toggle('collapsed');
    closeAllColMenus();
}

// --- Hidden columns ---
function toggleHiddenList() {
    const list = document.getElementById('hidden-list');
    const chevron = document.getElementById('hidden-chevron');
    if (list.classList.contains('hidden')) {
        list.classList.remove('hidden');
        list.style.opacity = '0';
        list.style.transform = 'translateY(-8px)';
        requestAnimationFrame(() => {
            list.style.transition = 'opacity 200ms ease-out, transform 200ms ease-out';
            list.style.opacity = '1';
            list.style.transform = 'translateY(0)';
        });
        chevron.style.transform = 'rotate(0deg)';
    } else {
        list.style.transition = 'opacity 150ms ease-in, transform 150ms ease-in';
        list.style.opacity = '0';
        list.style.transform = 'translateY(-8px)';
        setTimeout(() => {
            list.classList.add('hidden');
            list.style.transition = '';
            list.style.opacity = '';
            list.style.transform = '';
        }, 150);
        chevron.style.transform = 'rotate(-90deg)';
    }
}
async function toggleHiddenColumn(status) {
    const container = document.getElementById('hidden-expanded-' + status);
    if (!container.classList.contains('hidden')) {
        container.style.transition = 'opacity 150ms ease-in, max-height 200ms ease-in';
        container.style.opacity = '0';
        container.style.maxHeight = '0';
        setTimeout(() => {
            container.classList.add('hidden');
            container.style.transition = '';
            container.style.opacity = '';
            container.style.maxHeight = '';
        }, 200);
        return;
    }
    try {
        const issues = await api('/api/issues?status=' + status);
        container.innerHTML = issues.slice(0, 15).map((i, idx) =>
            '<div class="flex items-center gap-2 px-2 py-1.5 text-xs text-neutral-600 hover:bg-neutral-50 rounded cursor-pointer" onclick="openIssueDetail(\'' + i.id + '\')" style="opacity:0;transform:translateY(-4px);animation:cardIn 200ms ease-out ' + (idx * 30) + 'ms forwards">' +
                '<span class="text-2xs text-muted font-mono">' + i.identifier + '</span>' +
                '<span class="truncate">' + i.title + '</span>' +
            '</div>'
        ).join('') || '<div class="px-2 py-1.5 text-2xs text-neutral-400">No issues</div>';
        if (issues.length > 15) {
            container.innerHTML += '<div class="px-2 py-1 text-2xs text-muted" style="opacity:0;animation:cardIn 200ms ease-out ' + (15 * 30) + 'ms forwards">... and ' + (issues.length - 15) + ' more</div>';
        }
        container.classList.remove('hidden');
        container.style.opacity = '0';
        container.style.maxHeight = '0';
        requestAnimationFrame(() => {
            container.style.transition = 'opacity 200ms ease-out, max-height 300ms ease-out';
            container.style.opacity = '1';
            container.style.maxHeight = container.scrollHeight + 'px';
            setTimeout(() => { container.style.maxHeight = 'none'; }, 300);
        });
    } catch (err) { showToast('Error loading issues'); }
}

// --- Close dropdowns on outside click ---
document.addEventListener('click', (e) => {
    if (!e.target.closest('#display-menu') && !e.target.closest('[onclick*="toggleDisplayMenu"]')) {
        animateDropdownClose(document.getElementById('display-menu'));
    }
    if (!e.target.closest('#filter-menu') && !e.target.closest('[onclick*="toggleFilterMenu"]')) {
        animateDropdownClose(document.getElementById('filter-menu'));
    }
    if (!e.target.closest('[id^="col-menu-"]') && !e.target.closest('[onclick*="toggleColMenu"]')) {
        closeAllColMenus();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeCreateModal();
        closeDetailPanel();
        closeSearchModal();
        animateDropdownClose(document.getElementById('display-menu'));
        animateDropdownClose(document.getElementById('filter-menu'));
        closeAllColMenus();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openSearchModal();
    }
    if (e.key === 'c' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName) &&
        document.getElementById('create-modal').classList.contains('hidden') &&
        document.getElementById('detail-panel').classList.contains('hidden') &&
        document.getElementById('search-modal').classList.contains('hidden')) {
        openCreateModal();
    }
});

// --- Staggered card entrance ---
document.querySelectorAll('.issue-card.anim-card').forEach((card, i) => {
    card.style.animationDelay = (i * 30) + 'ms';
});
