from django.contrib import admin
from .models import Venta, VentaItem


class VentaItemInline(admin.TabularInline):
	model = VentaItem
	extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
	list_display = ('id', 'cliente', 'vendedor', 'fecha', 'total')
	list_filter = ('fecha',)
	search_fields = ('cliente__nombre', 'vendedor__username')
	inlines = [VentaItemInline]


@admin.register(VentaItem)
class VentaItemAdmin(admin.ModelAdmin):
	list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
