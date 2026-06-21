from django.contrib import admin

from lancamentos.models import Lancamento


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "tipo",
        "conta",
        "competencia_mes",
        "competencia_ano",
        "valor",
        "status",
    )
    list_filter = ("tipo", "conta", "competencia_ano", "competencia_mes")
    search_fields = ("descricao",)
