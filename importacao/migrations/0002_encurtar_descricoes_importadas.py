from django.db import migrations

# Logica duplicada de importacao.services.resumir_memo de proposito:
# migracao nao deve depender de codigo vivo do app.
DESCRICAO_MAX = 180


def _resumir(memo):
    partes = [parte.strip() for parte in memo.split(" - ")]
    if len(partes) < 3:
        return None
    descricao = " - ".join(partes[:2])
    if len(descricao) > DESCRICAO_MAX:
        descricao = descricao[: DESCRICAO_MAX - 1] + "…"
    return descricao


def encurtar_descricoes(apps, schema_editor):
    ItemImportado = apps.get_model("importacao", "ItemImportado")
    Lancamento = apps.get_model("lancamentos", "Lancamento")

    itens = ItemImportado.objects.filter(
        conta__tipo="BANCO", lancamento__isnull=False
    ).select_related("lancamento")
    for item in itens:
        memo = item.lancamento.descricao
        descricao = _resumir(memo)
        if descricao is None or item.lancamento.detalhes:
            continue
        Lancamento.objects.filter(pk=item.lancamento_id).update(
            descricao=descricao, detalhes=memo
        )


def reverter(apps, schema_editor):
    ItemImportado = apps.get_model("importacao", "ItemImportado")
    Lancamento = apps.get_model("lancamentos", "Lancamento")

    itens = ItemImportado.objects.filter(
        conta__tipo="BANCO", lancamento__isnull=False
    ).select_related("lancamento")
    for item in itens:
        if item.lancamento.detalhes:
            Lancamento.objects.filter(pk=item.lancamento_id).update(
                descricao=item.lancamento.detalhes[:DESCRICAO_MAX], detalhes=""
            )


class Migration(migrations.Migration):
    dependencies = [
        ("importacao", "0001_initial"),
        ("lancamentos", "0004_lancamento_detalhes"),
    ]

    operations = [
        migrations.RunPython(encurtar_descricoes, reverter),
    ]
