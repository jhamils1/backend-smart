import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas

total = ListadoHistoricoVentas.objects.count()
completadas = ListadoHistoricoVentas.objects.filter(estado_pago='completado').count()
estados = list(ListadoHistoricoVentas.objects.values_list('estado_pago', flat=True).distinct())

print(f'Total ventas: {total}')
print(f'Ventas completadas: {completadas}')
print(f'Estados únicos: {estados}')

# Ver una muestra
if total > 0:
    muestra = ListadoHistoricoVentas.objects.first()
    print(f'\nMuestra de venta:')
    print(f'  - Número: {muestra.numero_venta}')
    print(f'  - Estado: {muestra.estado_pago}')
    print(f'  - Fecha: {muestra.fecha_venta}')
    print(f'  - Total: {muestra.total}')
