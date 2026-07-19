from django.contrib import admin

from importacao.models import ItemImportado


@admin.register(ItemImportado)
class ItemImportadoAdmin(admin.ModelAdmin):
    list_display = ("fitid", "conta", "lancamento", "compra", "importado_em")
    list_filter = ("conta",)
    search_fields = ("fitid", "chave_dedup")
