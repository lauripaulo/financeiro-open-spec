from django.contrib import admin

from contas.models import Conta


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "saldo_atual", "limite_negativo", "dia_vencimento")
    list_filter = ("tipo",)
    search_fields = ("nome",)
