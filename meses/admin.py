from django.contrib import admin

from meses.models import MesAberto, SaldoMensalConta


@admin.register(MesAberto)
class MesAbertoAdmin(admin.ModelAdmin):
    list_display = ("mes", "ano", "criado_em")
    list_filter = ("ano",)


@admin.register(SaldoMensalConta)
class SaldoMensalContaAdmin(admin.ModelAdmin):
    list_display = ("conta", "mes", "ano", "saldo_inicial")
    list_filter = ("ano", "mes", "conta")
