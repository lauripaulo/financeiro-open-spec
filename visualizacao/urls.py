from django.urls import path

from visualizacao import views

app_name = "visualizacao"

urlpatterns = [
    path("", views.visao_consolidada, name="consolidada"),
    path("patrimonio/", views.visao_patrimonio, name="patrimonio"),
    path("comparativo/", views.comparativo_meses, name="comparativo"),
    path("criar-mes/", views.criar_mes_view, name="criar_mes"),
    path("pendentes/<int:pk>/transferir/", views.transferir_pendente, name="transferir_pendente"),
    path("pendentes/<int:pk>/manter/", views.manter_pendente, name="manter_pendente"),
    path("contas/<int:conta_id>/ajustar-saldo/", views.ajustar_saldo, name="ajustar_saldo"),
]
