# Project Conventions

## Frontend Asset Organization

**All JavaScript and CSS must live in their own files under `app/static/`.**

- **JavaScript** → `app/static/js/<name>.js`
- **CSS** → `app/static/css/<name>.css`

### Rules

1. **No inline `<script>` blocks in HTML templates.** Extract all JS into separate `.js` files and load them via `<script src="/static/js/...">`.
2. **No inline `<style>` blocks in HTML templates.** Extract all CSS into separate `.css` files and load them via `<link rel="stylesheet" href="/static/css/...">`.
3. **Tiny page-specific config constants** (e.g. `const BOARD_URL = "/dashboard/board"`) are acceptable as inline `<script>` if they are 1-3 lines and provide server-side data to an external JS file.
4. **Inline event handlers** (`onclick`, `onchange`, etc.) in HTML attributes are acceptable — they are not the same as inline script blocks.
5. Use the `{% block scripts %}` Jinja2 block in templates to load page-specific JS files.

### File naming

- Page-specific JS: name matches the page (e.g. `profile.js` for `profile.html`, `board.js` for `board.html`).
- Shared utilities: `app.js` (global), `navigator.js` (AI assistant), `dashboard.js` (dashboard page).
- Config: `tailwind.config.js` (Tailwind theme customization).

### Current JS files

| File | Purpose |
|------|---------|
| `app.js` | Shared utilities: sidebar toggle, `api()` helper, `showToast()`, `Modal` |
| `navigator.js` | Ask Navigator AI command palette/chat |
| `board.js` | Kanban board logic |
| `dashboard.js` | Dashboard page interactivity |
| `profile.js` | Profile page: avatar upload, forms, 2FA, sessions |
| `tailwind.config.js` | Tailwind CSS theme configuration |
