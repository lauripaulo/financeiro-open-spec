## Context

The app is a Django 5.2.15 personal-finance tool rendered entirely with server-side
templates — no npm/package.json, no bundler (webpack/vite), no Sass, static files
served directly via `django.contrib.staticfiles`. The only client-side library is
htmx 1.9.12 (CDN script tag), used for progressive-enhancement form posts that swap
server-rendered HTML fragments into `#flash-area` (pay/delete/transfer/keep actions,
delete-confirmation dialogs). One small vanilla-JS file, `static/js/money-mask.js`,
wraps `input.money-input` elements in a `.money-field`/`.money-prefix` DOM structure
by selecting those exact class names.

There are ~12 page templates across `contas/`, `lancamentos/`, and `visualizacao/`,
all extending a single `templates/base.html` that currently carries ~90 lines of
hand-written inline `<style>` (dark header, custom card/table/alert/status/money-field
CSS, teal accent `#0f766e`). No icon set is in use today. The Django admin has zero
template overrides, so it is unaffected by any change here.

## Goals / Non-Goals

**Goals:**
- Apply Google's Material Design 3 (M3) visual language consistently across every
  non-admin, user-facing page: color roles, typography scale, shape, elevation,
  state layers, and core components (buttons, filled text fields, cards, data
  tables, chips, banners, top app bar).
- Keep the project's existing "no framework" philosophy: no new build tooling, no JS
  framework, no bundler.
- Preserve all existing behavior: htmx swap targets/attributes, form field
  names/ids (for `request.POST` parsing), and `money-mask.js`'s masking logic.
- Meet baseline accessibility expectations under M3 (touch targets, contrast, focus
  states, reduced motion).

**Non-Goals:**
- Touching the Django admin site in any way.
- Introducing a JS framework, custom elements/web components, or a build pipeline
  (npm, webpack, vite, Sass).
- Automated visual-regression testing (none exists today; not being added).
- A guaranteed pixel-perfect dark theme in v1 (see Decisions below — treated as a
  stretch addition, not a blocking requirement).
- Converting existing native `<table>`-based listings into a different information
  architecture (e.g., card-per-row on mobile) beyond horizontal-scroll wrapping.

## Decisions

### 1. Hand-written CSS with M3 design tokens, not `@material/web` web components
`@material/web` ships M3 as real custom elements but is meant to be bundled/tree-shaken;
importing it unbundled via CDN ES modules would ship a large, un-tree-shaken JS graph
for a 12-template app. More importantly, its form-associated custom elements
(text fields, selects, checkboxes) would need to replace this app's native
`<input>`/`<select>` elements that `request.POST` parsing and `money-mask.js` rely on
directly — extra integration risk for no UX gain. **Decision:** implement M3 as plain
CSS files under `static/css/` (design tokens as CSS custom properties, plus
hand-written component classes), loaded via `<link>` tags with no bundler, keeping
htmx and native form elements exactly as they are.

Alternative considered: Bootstrap/Tailwind reskinned to look M3-ish — rejected because
neither natively implements M3's token system or component set, and would add a
sizeable new CSS dependency for a job hand-written CSS already does well at this
project's scale.

### 2. CSS architecture: three static files, one class-rename mapping
- `static/css/m3-tokens.css` — `:root` custom properties for color roles (primary,
  on-primary, primary-container, on-primary-container, secondary, tertiary,
  tertiary-container, on-tertiary-container, surface, surface-container(-low/-high),
  surface-variant, on-surface, on-surface-variant, outline, outline-variant, error,
  on-error, error-container, on-error-container, background, on-background),
  typography scale (display/headline/title/body/label × large/medium/small), shape
  corner tokens, elevation levels 0-5, and state-layer opacity tokens (hover 0.08,
  focus/pressed 0.12). Values derived from Material Theme Builder using seed color
  `#0f766e` (the app's current teal accent) for WCAG-AA-audited contrast pairs.
- `static/css/m3-base.css` — reset/normalize and base typography wiring to tokens.
- `static/css/m3-components.css` — component classes: `.m3-button--{filled,outlined,text}`,
  `.m3-field--filled` (+ `__prefix` for the money affix), `.m3-card`,
  `.m3-data-table`(+ `-wrapper` for `overflow-x:auto`), `.m3-chip` (status tonal
  variants), `.m3-banner`(+ variants), `.m3-top-app-bar`, `.m3-nav-link`,
  `.m3-checkbox`.
- Class rename mapping applied across templates: `.card`→`.m3-card`; `.alert`/`.warn`/
  `.info`→`.m3-banner`/`--error`/`--info`; `table`/`th`/`td`→`.m3-data-table`;
  `.status.*`→`.m3-chip` tonal variants; `button`/`a.button`→`.m3-button--filled`;
  `button.secondary`/`a.button.secondary`→`.m3-button--outlined`; `.money-field`/
  `.money-prefix`→`.m3-field--filled`/`.m3-field__prefix` (requires updating the two
  class-name strings `money-mask.js` injects to match).
- Fonts/icons: Google Fonts CDN links for Roboto (400/500) and Material Symbols
  Outlined, added in `base.html` alongside the existing htmx CDN `<script>` tag (same
  external-dependency pattern already in use, not a new category of risk).

### 3. Shared field-rendering partial
A new `templates/_partials/field.html` renders the M3 filled-text-field DOM
(input → label → helper/error text) for any Django form field, preserving
Django's auto-generated `id`/`name` attributes so view-level `request.POST` handling
is untouched. Used by the 4 existing form templates instead of ad-hoc/`.as_p`
rendering, with a checkbox-specific branch for the two boolean fields in the app
(`confirmar_edicao_mes_encerrado`, status filter checkboxes).

### 4. Light theme required, dark theme as a later addition
M3 tokens naturally support both, but only light theme is required to ship in this
change. A dark token block gated by `@media (prefers-color-scheme: dark)` (generated
from the same seed color) is a documented follow-up, not a blocker — this avoids
doubling the contrast-audit and QA surface for the initial migration.

### 5. Deliberate, documented deviations from strict M3 guidance
- **No native `<dialog>` for delete confirmation.** `_confirmar_excluir_par.html` is
  swapped into `#flash-area` via htmx `innerHTML`; calling `.showModal()` on a
  swapped-in fragment would require new JS. Instead it's styled as an M3 error-toned
  confirmation banner with two inline actions. This keeps zero new JS, at the cost of
  not matching M3's modal-dialog pattern exactly.
- **No page-corner FAB.** "Novo lançamento"/"Nova compra parcelada" stay inline
  filled/tonal buttons rather than a fixed FAB, since the dashboard's stacked-card
  layout would risk the FAB overlapping content on mobile scroll.
- **Icons are ligature text next to visible labels for primary page-level actions, but icon-only buttons are used for table actions.** Primary actions (e.g. "Nova conta") use visible text labels. However, the action cells ("Ações" column) in tables (`consolidada.html` and `lista.html`) are migrated to icon-only buttons (`.m3-button--icon-only`) with explicit `aria-label` and `title` attributes. This preserves touch targets (48x48dp) and accessibility while preventing cramped horizontal scroll behavior on narrower viewports.

## Risks / Trade-offs

- [Risk] Renaming CSS classes referenced by `money-mask.js` breaks the currency input
  UI if the JS and templates fall out of sync. → Mitigation: rename the JS selector
  strings in the same change/commit as the template migration; verify manually per
  form page (see tasks.md verification step).
- [Risk] No automated visual-regression tooling exists, so styling regressions could
  slip through. → Mitigation: manual walk of every route in tasks.md, plus Lighthouse
  accessibility + DevTools contrast spot checks.
- [Risk] Deviating from strict M3 dialog/FAB patterns could read as "incomplete" M3
  adoption. → Mitigation: deviations are documented above with rationale, tied to
  concrete constraints (no new JS, mobile layout), not oversight.
- [Risk] Hand-derived token values (vs. a maintained library) could drift from future
  M3 spec updates. → Mitigation: centralizing all values in `m3-tokens.css` makes any
  future re-derivation (e.g., re-running Material Theme Builder) a single-file change.

## Migration Plan

1. Foundation: add `m3-tokens.css`, `m3-base.css`, `m3-components.css`.
2. Rewrite `base.html` (drop inline `<style>`, add links, restructure header/flash
   area) and update `money-mask.js` class-name selectors.
3. Build the shared `_partials/field.html` and wire it into the 4 form templates.
4. Migrate page templates in order: `contas/*` → `lancamentos/*` (incl.
   `_confirmar_excluir_par.html`) → `visualizacao/mes_nao_criado.html` →
   `visualizacao/resolver_pendentes.html` → `visualizacao/consolidada.html` →
   `visualizacao/comparativo.html` → `visualizacao/patrimonio.html`.
5. Manual verification pass across all routes (see tasks.md).

No database/data migration is involved; this is a template/static-asset-only change,
so rollback is a plain revert of the affected files if issues surface.

## Open Questions

- Should dark-theme support be scheduled as an immediate follow-up change, or left
  unscheduled until requested?
