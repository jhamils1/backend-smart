from django.contrib import admin
from inventario.models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio_compra', 'precio_venta', 'stock', 'fecha_creacion')
    list_filter = ('categoria', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'imagen')
        }),
        ('Precios', {
            'fields': ('precio_compra', 'precio_compra_anterior', 'precio_venta', 'costo_promedio')
        }),
        ('Inventario', {
            'fields': ('stock', 'fecha_creacion')
        }),
    )
