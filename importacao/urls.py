from django.urls import path

from importacao import views

app_name = "importacao"

urlpatterns = [
    path("", views.index, name="index"),
    path("nubank-cartao/", views.importar_nubank_cartao, name="nubank_cartao"),
    path("nubank-conta/", views.importar_nubank_conta, name="nubank_conta"),
    path("resultado/", views.resultado, name="resultado"),
]
