# Hexi Docs Theme (`hexi_docs`)

This repository uses a custom MkDocs theme located at:

- `docs_theme/hexi_docs/`

It is designed to match Hexi branding (typography, palette, spacing rhythm, and light/dark behavior).

## Run locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Theme structure

- `docs_theme/hexi_docs/main.html`: page layout shell
- `docs_theme/hexi_docs/partials/header.html`: top bar, search, toggles
- `docs_theme/hexi_docs/partials/sidebar.html`: recursive nav tree
- `docs_theme/hexi_docs/partials/footer.html`: footer block
- `docs_theme/hexi_docs/assets/css/theme.css`: full tokenized design system + component styles
- `docs_theme/hexi_docs/assets/js/theme-init.js`: early theme boot (prevents flash)
- `docs_theme/hexi_docs/assets/js/theme.js`: toggle behavior, mobile nav, code copy buttons

## Token overrides

Edit token sets in `theme.css`:

- Light tokens: `:root, :root[data-theme="light"]`
- Dark tokens: `:root[data-theme="dark"]`

Semantic tokens to tune first:

- `--background`
- `--foreground`
- `--primary`
- `--link`
- `--border`
- `--code-bg`
- `--code-fg`

## Typography

- Sans: `Gabarito`
- Mono: `Victor Mono`

Configured in `main.html` font imports and `theme.css` font stacks.

## Layout/component editing guide

- Header behavior/search/toggles: `partials/header.html`
- Sidebar nav rendering: `partials/sidebar.html`
- Main content/toc/pagination placement: `main.html`
- Code block look/copy button: `theme.css` + `theme.js`
- Motion behavior/background orbs: `theme.css`

## Accessibility and motion

- Focus-visible rings are enabled globally.
- Skip-link is present for keyboard users.
- `prefers-reduced-motion` disables non-essential animation.

## Future extraction

If this theme becomes shared across projects, package it as a standalone MkDocs theme repo and reference it by theme name.
