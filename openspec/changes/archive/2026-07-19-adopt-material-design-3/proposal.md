## Why

The frontend currently uses ad-hoc inline CSS in `templates/base.html` (dark header, plain
tables, unstyled inputs) with no consistent design system, typography scale, color
tokens, or accessibility baseline. Adopting Google's Material Design 3 (M3) gives the
app a modern, coherent, accessible visual language across every user-facing page
without requiring a JS framework or build pipeline.

## What Changes

- Introduce an M3 design-token foundation (color roles, typography scale, shape,
  elevation, state-layer opacity) as plain CSS custom properties, derived from a seed
  color close to the current teal accent (`#0f766e`).
- Rewrite `templates/base.html`: remove the existing inline `<style>` block, add M3
  stylesheets and Google Fonts (Roboto + Material Symbols Outlined) links, restructure
  the header into an M3 top app bar, restyle flash messages as M3 banners.
- Add reusable M3 component CSS (buttons, filled text fields, cards, data tables,
  chips, banners, checkboxes) and a shared Django template partial for form fields.
- Migrate every page template in `contas/`, `lancamentos/`, and `visualizacao/` to the
  new M3 classes/components, including htmx-swapped fragments
  (`_confirmar_excluir_par.html`) restyled as inline M3 confirmation banners.
- Update `static/js/money-mask.js` selectors to match renamed field classes.
- **BREAKING**: none for end users of behavior; existing CSS class names used in
  templates are renamed/removed, so any undocumented external references to the old
  class names (e.g. `.card`, `.alert`, `.money-field`) would break.
- Explicitly **out of scope**: the Django admin site (`/admin/`) is not touched — the
  project has no `templates/admin/` override, so admin styling is unaffected by
  construction.

## Capabilities

### New Capabilities
- `frontend-design-system`: Defines the M3 design-token foundation and the
  requirement that all non-admin, user-facing pages consistently use it (color,
  typography, shape, elevation, components, accessibility, responsiveness), and that
  the Django admin remains untouched.

### Modified Capabilities
(none — no existing behavioral requirements in `contas`, `lancamentos`, or
`visualizacao` specs change; this is a presentation-layer restyling of pages whose
functional requirements are already captured in those specs.)

## Impact

- **Affected code**: `templates/base.html`, all templates under `templates/contas/`,
  `templates/lancamentos/`, `templates/visualizacao/`, `static/js/money-mask.js`.
- **New static assets**: `static/css/m3-tokens.css`, `static/css/m3-base.css`,
  `static/css/m3-components.css`, new shared partial `templates/_partials/field.html`.
- **Dependencies**: adds Google Fonts CDN links (Roboto, Material Symbols Outlined);
  no new build tooling, no npm/bundler, no JS framework.
- **Not affected**: Django admin, URLs/views/models, htmx usage patterns, business
  logic in `contas`, `lancamentos`, `meses`, `parcelas`, `financeiro` apps.
