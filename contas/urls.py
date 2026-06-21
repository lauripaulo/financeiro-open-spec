from django.urls import path

from contas import views

app_name = "contas"

urlpatterns = [
    path("", views.listar_contas, name="listar"),
    path("novo/", views.criar_conta, name="criar"),
    path("<int:pk>/editar/", views.editar_conta, name="editar"),
    path("<int:pk>/excluir/", views.excluir_conta, name="excluir"),
]
