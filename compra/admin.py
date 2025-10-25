from django.contrib import admin, messages
from django.http import HttpResponse
from .models import Compra, CompraItem


class CompraItemInline(admin.TabularInline):
    model = CompraItem
    extra = 0


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'total', 'pagado_en', 'stripe_payment_intent')
    list_filter = ('fecha',)
    search_fields = ('cliente__nombre', 'observaciones')
    date_hierarchy = 'fecha'
    inlines = [CompraItemInline]
    actions = ['exportar_excel', 'exportar_pdf', 'comprobante_pdf']

    def exportar_excel(self, request, queryset):
        try:
            from openpyxl import Workbook
        except ImportError:
            self.message_user(request, 'Instala openpyxl para exportar a Excel: pip install openpyxl', level=messages.ERROR)
            return
        wb = Workbook()
        ws = wb.active
        ws.title = 'Compras'
        headers = ['ID', 'Cliente', 'Fecha', 'Total', 'Pagado en', 'Referencia', '# Items']
        ws.append(headers)
        qs = queryset.select_related('cliente')
        for c in qs:
            ws.append([
                c.id,
                str(c.cliente),
                c.fecha.replace(tzinfo=None) if hasattr(c.fecha, 'tzinfo') else c.fecha,
                float(c.total),
                (c.pagado_en.replace(tzinfo=None) if c.pagado_en and hasattr(c.pagado_en, 'tzinfo') else c.pagado_en),
                c.pago_referencia,
                c.items.count(),
            ])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="compras.xlsx"'
        wb.save(response)
        return response

    exportar_excel.short_description = 'Exportar seleccionadas a Excel'

    def exportar_pdf(self, request, queryset):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            self.message_user(request, 'Instala reportlab para exportar a PDF: pip install reportlab', level=messages.ERROR)
            return
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="compras.pdf"'
        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40
        p.setFont('Helvetica-Bold', 12)
        p.drawString(40, y, 'Reporte de Compras')
        y -= 20
        p.setFont('Helvetica', 9)
        headers = ['ID', 'Cliente', 'Fecha', 'Total', 'Pagado en', 'Ref', 'Items']
        p.drawString(40, y, ' | '.join(headers))
        y -= 15
        qs = queryset.select_related('cliente')
        for c in qs:
            row = [
                str(c.id),
                str(c.cliente)[:20],
                c.fecha.strftime('%Y-%m-%d %H:%M'),
                f"{c.total}",
                (c.pagado_en.strftime('%Y-%m-%d %H:%M') if c.pagado_en else ''),
                (c.pago_referencia or '')[:12],
                str(c.items.count()),
            ]
            p.drawString(40, y, ' | '.join(row))
            y -= 12
            if y < 40:
                p.showPage()
                y = height - 40
        p.showPage()
        p.save()
        return response

    exportar_pdf.short_description = 'Exportar seleccionadas a PDF'

    def comprobante_pdf(self, request, queryset):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            self.message_user(request, 'Instala reportlab para exportar a PDF: pip install reportlab', level=messages.ERROR)
            return
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="comprobantes.pdf"'
        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        for c in queryset.select_related('cliente'):
            y = height - 40
            p.setFont('Helvetica-Bold', 14)
            p.drawString(40, y, 'Nota de Venta')
            y -= 20
            p.setFont('Helvetica', 10)
            p.drawString(40, y, f'Compra ID: {c.id}   Fecha: {c.fecha.strftime("%Y-%m-%d %H:%M")}')
            y -= 14
            p.drawString(40, y, f'Cliente: {c.cliente}')
            y -= 20
            p.setFont('Helvetica-Bold', 10)
            p.drawString(40, y, 'Cant.')
            p.drawString(90, y, 'Producto')
            p.drawString(300, y, 'P. Unit.')
            p.drawString(380, y, 'Subtotal')
            y -= 12
            p.setFont('Helvetica', 10)
            for it in c.items.select_related('producto'):
                if y < 60:
                    p.showPage(); y = height - 40
                p.drawString(40, y, str(it.cantidad))
                p.drawString(90, y, (it.producto.nombre[:36] if it.producto and it.producto.nombre else ''))
                p.drawRightString(360, y, f"{it.precio_unitario}")
                p.drawRightString(450, y, f"{it.subtotal}")
                y -= 12
            y -= 10
            p.setFont('Helvetica-Bold', 11)
            p.drawRightString(450, y, f"TOTAL: {c.total}")
            y -= 16
            p.setFont('Helvetica', 9)
            estado_pago = f"Pagado: {c.pagado_en.strftime('%Y-%m-%d %H:%M')}" if c.pagado_en else 'Pendiente de pago'
            p.drawString(40, y, estado_pago)
            p.showPage()
        p.save()
        return response

    comprobante_pdf.short_description = 'Descargar comprobante(s) PDF'


@admin.register(CompraItem)
class CompraItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'compra', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('producto__nombre',)
