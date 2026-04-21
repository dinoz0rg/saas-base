/* Dashboard-specific JS */
(function() {
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Cmd/Ctrl+K → search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            if (typeof openSearchModal === 'function') openSearchModal();
        }
        // Escape → close modals
        if (e.key === 'Escape') {
            if (typeof closeSearchModal === 'function') closeSearchModal();
        }
    });
})();
