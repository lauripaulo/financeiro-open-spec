## 1. Pass month context to the compra-parcelada form

- [x] 1.1 Update the "Nova compra parcelada" link in `templates/visualizacao/consolidada.html` to include `?ano={{ ano }}&mes={{ mes }}`, matching the adjacent "Novo lancamento" link

## 2. Fix the view's response

- [x] 2.1 Call `_contexto_mes(request)` at the top of `criar_compra_parcelada` in `lancamentos/views.py` to read the origin `ano`/`mes`
- [x] 2.2 On successful form save, branch on `request.headers.get("HX-Request")`: return `HttpResponse(status=204)` if present, else `redirect(f"/?ano={ano}&mes={mes}")` — mirroring `criar_lancamento`

## 3. Verification

- [x] 3.1 Run `python manage.py test` and confirm all existing tests still pass
- [ ] 3.2 Manually verify in the dev server: from the consolidated view of a non-current month, click "Nova compra parcelada", submit with a purchase date in a different month, and confirm the app redirects back to the original (non-current) month, not today's month or the purchase month
- [ ] 3.3 Manually verify the parcelas appear correctly in the resulting consolidated view (or in the months where they actually land, per existing parcela-month logic)
