from django.contrib import admin

from parcelas.models import CompraParcelada


@admin.register(CompraParcelada)
class CompraParceladaAdmin(admin.ModelAdmin):
    list_display = ("descricao", "conta", "valor_total", "total_parcelas", "data_compra")
    list_filter = ("conta", "data_compra")
