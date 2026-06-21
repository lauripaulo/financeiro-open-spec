from django.urls import path

from lancamentos import views

app_name = "lancamentos"

urlpatterns = [
    path("novo/", views.criar_lancamento, name="criar"),
    path("<int:pk>/pagar/", views.marcar_pago, name="marcar_pago"),
    path("<int:pk>/editar/", views.editar_lancamento, name="editar"),
    path("<int:pk>/excluir/", views.excluir_lancamento, name="excluir"),
    path("parcelado/", views.criar_compra_parcelada, name="compra_parcelada"),
]
