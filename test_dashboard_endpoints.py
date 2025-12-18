import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from analitica.viewsDashboard import DashboardViewSet
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

# Crear factory
factory = APIRequestFactory()

# Obtener o crear un usuario para la petición
user, created = User.objects.get_or_create(username='testuser', defaults={'password': 'test123'})

# Probar endpoint de ventas históricas
print('🧪 Probando endpoint: ventas-historicas')
print('='*60)

request = factory.get('/api/analitica/dashboard/ventas-historicas/', {'periodo': 'mes'})
request.user = user

view = DashboardViewSet.as_view({'get': 'ventas_historicas'})
response = view(request)

print(f'Status: {response.status_code}')
print(f'Periodo: {response.data.get("periodo")}')
print(f'Total registros: {response.data.get("total_registros")}')

if response.data.get("datos"):
    print(f'\n📊 Primeros 3 registros:')
    for dato in response.data["datos"][:3]:
        print(f'  {dato}')
else:
    print('⚠️  No hay datos en la respuesta')

# Probar productos ranking
print('\n\n🧪 Probando endpoint: productos-ranking')
print('='*60)

request2 = factory.get('/api/analitica/dashboard/productos-ranking/', {'tipo': 'top', 'limite': 5})
request2.user = user

view2 = DashboardViewSet.as_view({'get': 'productos_ranking'})
response2 = view2(request2)

print(f'Status: {response2.status_code}')
print(f'Total registros: {response2.data.get("total_registros")}')

if response2.data.get("datos"):
    print(f'\n🏆 Top productos:')
    for dato in response2.data["datos"]:
        print(f'  - {dato["producto_nombre"]}: {dato["total_vendido"]} unidades')
else:
    print('⚠️  No hay datos en la respuesta')

# Probar clientes ranking
print('\n\n🧪 Probando endpoint: clientes-ranking')
print('='*60)

request3 = factory.get('/api/analitica/dashboard/clientes-ranking/', {'tipo': 'top', 'limite': 5})
request3.user = user

view3 = DashboardViewSet.as_view({'get': 'clientes_ranking'})
response3 = view3(request3)

print(f'Status: {response3.status_code}')
print(f'Total registros: {response3.data.get("total_registros")}')

if response3.data.get("datos"):
    print(f'\n👥 Top clientes:')
    for dato in response3.data["datos"]:
        print(f'  - {dato["cliente_nombre"]}: {dato["total_compras"]} compras')
else:
    print('⚠️  No hay datos en la respuesta')
