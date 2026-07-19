## 1. Design tokens foundation

- [x] 1.1 Run seed color `#0f766e` through Material Theme Builder (or equivalent M3
      token generation) to derive light-theme color-role values
- [x] 1.2 Create `static/css/m3-tokens.css` with `:root` color-role custom
      properties (primary, on-primary, primary-container, on-primary-container,
      secondary, tertiary, tertiary-container, on-tertiary-container, surface,
      surface-container(-low/-high), surface-variant, on-surface,
      on-surface-variant, outline, outline-variant, error, on-error,
      error-container, on-error-container, background, on-background)
- [x] 1.3 Add typography scale tokens (display/headline/title/body/label x
      large/medium/small: font, size, line-height, weight, tracking)
- [x] 1.4 Add shape corner tokens (none/xs/sm/md/lg/xl/full) and elevation tokens
      (levels 0-5 as box-shadow values)
- [x] 1.5 Add state-layer opacity tokens (hover 0.08, focus/pressed 0.12)

## 2. Base and component stylesheets

- [x] 2.1 Create `static/css/m3-base.css` (reset/normalize, body/heading defaults
      wired to typography and color tokens, responsive `.container` margins)
- [x] 2.2 Create `static/css/m3-components.css` with: `.m3-button--filled`,
      `.m3-button--outlined`, `.m3-button--text`; `.m3-field--filled` and
      `.m3-field__prefix`; `.m3-card`; `.m3-data-table` + `.m3-data-table-wrapper`
      (`overflow-x: auto`); `.m3-chip` tonal variants; `.m3-banner` +
      error/info variants; `.m3-top-app-bar`; `.m3-nav-link`; `.m3-checkbox`
- [x] 2.3 Restyle native `<select>` via `appearance: none` plus a Material Symbols
      dropdown affordance
- [x] 2.4 Add 48x48dp minimum touch-target rules, visible `:focus-visible` rings,
      and `@media (prefers-reduced-motion: no-preference)` guards for new
      transitions

## 3. base.html rewrite

- [x] 3.1 Remove the existing inline `<style>` block from `templates/base.html`
- [x] 3.2 Add `<link>` tags for `m3-tokens.css`, `m3-base.css`, `m3-components.css`,
      and Google Fonts (Roboto 400/500, Material Symbols Outlined)
- [x] 3.3 Restructure `<header>` into `.m3-top-app-bar` markup; convert `nav a`
      links to `.m3-nav-link`, marking the active route via `request.path`
- [x] 3.4 Restyle the `#flash-area` messages loop to render `.m3-banner` /
      `.m3-banner--error` / `.m3-banner--info` instead of `.alert` classes
- [x] 3.5 Update `static/js/money-mask.js` to inject `m3-field--filled` and
      `m3-field__prefix` class names instead of `money-field`/`money-prefix`

## 4. Shared form field partial

- [x] 4.1 Create `templates/_partials/field.html` rendering the M3 filled-text-field
      DOM (input, label, helper/error text) while preserving Django's auto
      `id="id_<field>"` / `name` attributes
- [x] 4.2 Add a checkbox-specific rendering branch in the partial
- [x] 4.3 Wire the partial into `templates/contas/form.html`
- [x] 4.4 Wire the partial into `templates/lancamentos/form.html`,
      `form_edicao.html`, and `form_compra_parcelada.html`

## 5. Page migration: contas and lancamentos

- [x] 5.1 Migrate `templates/contas/lista.html` (data table -> `.m3-data-table`,
      row actions -> M3 text/outlined buttons, "Nova conta" -> filled button)
- [x] 5.2 Migrate `templates/contas/form.html` styling around the field partial
- [x] 5.3 Migrate `templates/lancamentos/form.html`,
      `templates/lancamentos/form_edicao.html`,
      `templates/lancamentos/form_compra_parcelada.html` (verify the existing
      parcelas-pagas clamping `<script>` still works unchanged, since it targets
      inputs by `id`, not by class)
- [x] 5.4 Migrate `templates/lancamentos/_confirmar_excluir_par.html` into an M3
      error-toned confirmation banner with two inline actions (no native
      `<dialog>`), preserving the existing confirm-before-delete flow

## 6. Page migration: visualizacao

- [x] 6.1 Migrate `templates/visualizacao/mes_nao_criado.html` to an M3 empty-state
      pattern (centered icon, headline, supporting text, filled-button CTA)
- [x] 6.2 Migrate `templates/visualizacao/resolver_pendentes.html` (list items ->
      `.m3-list-item` with outlined/text trailing actions)
- [x] 6.3 Migrate `templates/visualizacao/consolidada.html` filter section (status
      checkboxes -> M3 filter chips, conta `<select>` -> M3 outlined field)
- [x] 6.4 Migrate `templates/visualizacao/consolidada.html` month navigation
      (anterior/seguinte/Ir -> text buttons with chevron icons)
- [x] 6.5 Migrate `templates/visualizacao/consolidada.html` main table -> M3 data
      table in a scroll wrapper; action buttons keep icon + visible text
- [x] 6.6 Migrate `templates/visualizacao/consolidada.html` primary CTAs ("Novo
      lancamento", "Nova compra parcelada") to inline filled/tonal buttons with a
      leading `add` icon (no fixed FAB)
- [x] 6.7 Migrate `templates/visualizacao/consolidada.html` pendentes and
      ajuste-saldo inline forms to `.m3-field` / button classes
- [x] 6.8 Migrate `templates/visualizacao/comparativo.html` (number inputs ->
      `.m3-field`, table -> `.m3-data-table`)
- [x] 6.9 Migrate `templates/visualizacao/patrimonio.html` (outer/nested cards ->
      `.m3-card` with elevation, inner tables -> `.m3-data-table`)

## 7. Verification

- [x] 7.1 Walk every route via `python manage.py runserver`: contas (listar,
      criar, editar), lancamentos (criar, editar, compra_parcelada), visualizacao
      (consolidada populated and empty states, comparativo, patrimonio,
      mes_nao_criado, resolver_pendentes_abertura)
- [x] 7.2 Trigger and verify htmx-swapped fragments render with correct M3 styling:
      marcar_pago, excluir, excluir_par, transferir_pendente, manter_pendente,
      ajustar_saldo
- [x] 7.3 Confirm `/admin/` renders with stock Django styling, unaffected by the new
      `static/css` files or font links
- [x] 7.4 Check responsive behavior at mobile (360px), tablet, and desktop widths,
      including table horizontal scrolling and top-app-bar/nav wrapping
- [x] 7.5 Run a Lighthouse accessibility audit and a keyboard-only tab pass on each
      migrated page, confirming visible focus rings and no keyboard traps
- [x] 7.6 Spot-check color contrast (DevTools) on body text, status chips, button
      text/background, and banner text/background against the M3 tokens
- [x] 7.7 Regression-check `money-mask.js`: type into money fields on
      `contas/form.html`, `lancamentos/form.html`, and
      `lancamentos/form_compra_parcelada.html`, confirming the "R$" prefix still
      attaches correctly to the renamed `.m3-field--filled` container

## 8. Compact table action buttons (Option B)

- [x] 8.1 Add `.m3-button--icon-only` class to `static/css/m3-components.css`
- [x] 8.2 Migrate `templates/visualizacao/consolidada.html` action buttons to icon-only buttons with `aria-label` and `title` attributes
- [x] 8.3 Migrate `templates/contas/lista.html` action buttons to icon-only buttons with `aria-label` and `title` attributes
- [x] 8.4 Verify layout alignment and visual appearance of icon-only buttons across all viewport widths
- [x] 8.5 Harmonize pendente flow-action labels: `resolver_pendentes.html` uses the
      same short labels as `consolidada.html` ("Transferir"/"Manter", full phrase in
      `title`); flow decisions stay text-labeled per the amended design rule

> Verification note (2026-07-19): tasks 7.2 and 7.4–7.7 were performed manually
> (browser walk, DevTools contrast, Lighthouse, keyboard pass, money-mask typing)
> during the icon-only follow-up session and marked complete in batch at archive
> time. No evidence artifacts are stored in the repo.
