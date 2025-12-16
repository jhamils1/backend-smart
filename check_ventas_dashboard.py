import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas

# Verificar datos
total = ListadoHistoricoVentas.objects.count()
print(f'📊 Total ventas en histórico: {total}')

if total > 0:
    # Ver distribución de estados
    from django.db.models import Count
    estados_count = ListadoHistoricoVentas.objects.values('estado_pago').annotate(count=Count('estado_pago'))
    print(f'\n📈 Distribución por estado:')
    for estado in estados_count:
        print(f"  - {estado['estado_pago']}: {estado['count']}")
    
    # Ver una muestra
    muestra = ListadoHistoricoVentas.objects.first()
    print(f'\n🔍 Muestra de primera venta:')
    print(f'  - Número: {muestra.numero_venta}')
    print(f'  - Estado pago: "{muestra.estado_pago}"')
    print(f'  - Fecha: {muestra.fecha_venta}')
    print(f'  - Total: ${muestra.total}')
    print(f'  - Cliente: {muestra.cliente_nombre}')
else:
    print('❌ No hay ventas en el histórico')
