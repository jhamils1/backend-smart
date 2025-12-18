import os
import django
import csv
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from perfiles.models import Cliente
from inventario.modelsProducto import Producto
from transacciones.modelsNotaDeVenta import NotaDeVenta
from transacciones.modelsDetalleNotaDeVenta import DetalleNotaDeVenta
from transacciones.modelsPago import Pago
from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas


def leer_clientes_csv():
    """Lee clientes del CSV"""
    clientes = []
    with open('clientes_usuarios.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            clientes.append(row['username'])
    return clientes


def generar_fecha_aleatoria(inicio, fin):
    """Genera una fecha aleatoria entre dos fechas con timezone"""
    delta = fin - inicio
    dias_aleatorios = random.randint(0, delta.days)
    horas_aleatorias = random.randint(0, 23)
    minutos_aleatorios = random.randint(0, 59)
    segundos_aleatorios = random.randint(0, 59)
    
    fecha = inicio + timedelta(
        days=dias_aleatorios,
        hours=horas_aleatorias,
        minutes=minutos_aleatorios,
        seconds=segundos_aleatorios
    )
    # Hacer la fecha "aware" con timezone
    return timezone.make_aware(fecha)


def crear_ventas():
    """Crea 1000 notas de venta con sus detalles y pagos"""
    
    print(" Leyendo clientes del CSV...")
    clientes_usernames = leer_clientes_csv()
    
    print("🔍 Obteniendo productos y clientes de la BD...")
    productos_db = list(Producto.objects.all())
    clientes_db = list(Cliente.objects.filter(usuario__username__in=clientes_usernames))
    
    if not productos_db:
        print("❌ No hay productos en la base de datos")
        return
    
    if not clientes_db:
        print("❌ No hay clientes en la base de datos")
        return
    
    print(f"✅ {len(productos_db)} productos encontrados")
    print(f"✅ {len(clientes_db)} clientes encontrados\n")
    
    # Fechas límite (naive, serán convertidas a aware en generar_fecha_aleatoria)
    fecha_inicio = datetime(2022, 1, 1)
    fecha_fin = datetime(2025, 12, 15, 23, 59, 59)
    
    # Contadores
    ventas_creadas = 0
    detalles_creados = 0
    pagos_creados = 0
    historicos_creados = 0
    errores = []
    
    print("🚀 Creando 1000 ventas...\n")
    
    for i in range(1, 1001):
        try:
            # Generar fecha aleatoria
            fecha_venta = generar_fecha_aleatoria(fecha_inicio, fecha_fin)
            
            # Cliente aleatorio
            cliente = random.choice(clientes_db)
            
            # Generar número de comprobante único
            numero_comprobante = f"NV-{fecha_venta.year}-{str(i).zfill(6)}"
            
            # Crear nota de venta
            nota_venta = NotaDeVenta.objects.create(
                cliente=cliente,
                numero_comprobante=numero_comprobante,
                estado='pagada',
                subtotal=0,
                total=0
            )
            
            # Sobrescribir la fecha (auto_now_add no permite modificar)
            NotaDeVenta.objects.filter(id=nota_venta.id).update(fecha=fecha_venta)
            nota_venta.refresh_from_db()
            
            ventas_creadas += 1
            
            # Cantidad aleatoria de productos (1 a 5 productos por venta)
            num_productos = random.randint(1, 5)
            productos_seleccionados = random.sample(productos_db, min(num_productos, len(productos_db)))
            
            total_venta = Decimal('0.00')
            
            for producto in productos_seleccionados:
                # Cantidad aleatoria (1 a 3 unidades por producto)
                cantidad = random.randint(1, 3)
                
                # Crear detalle
                detalle = DetalleNotaDeVenta(
                    nota_venta=nota_venta,
                    producto=producto,
                    cantidad=cantidad,
                    codigo=producto.codigo
                )
                
                # Calcular totales
                detalle.calcular_totales()
                detalle.save()
                
                total_venta += detalle.total
                detalles_creados += 1
            
            # Actualizar totales de la nota de venta
            nota_venta.subtotal = total_venta
            nota_venta.total = total_venta
            nota_venta.save()
            
            # Crear pago único
            pago = Pago.objects.create(
                nota_venta=nota_venta,
                monto=total_venta,
                moneda='USD',
                total_stripe=f"pi_{fecha_venta.year}_{str(i).zfill(6)}_{random.randint(1000, 9999)}"
            )
            
            # Sobrescribir la fecha del pago
            Pago.objects.filter(nota_venta_id=nota_venta.id).update(fecha=fecha_venta)
            
            pagos_creados += 1
            
            # Crear registro en ListadoHistoricoVentas
            historico = ListadoHistoricoVentas.objects.create(
                nota_venta=nota_venta,
                cliente_nombre=f"{cliente.nombre} {cliente.apellido}",
                cliente_ci=cliente.ci,
                cliente_email=cliente.usuario.email if cliente.usuario else None,
                numero_venta=numero_comprobante,
                fecha_venta=fecha_venta,
                subtotal=total_venta,
                total=total_venta,
                metodo_pago='Stripe',
                estado_pago='completado',
                fecha_pago=fecha_venta,
                referencia_pago=pago.total_stripe
            )
            
            historicos_creados += 1
            
            # Mostrar progreso cada 50 ventas
            if i % 50 == 0:
                print(f"✅ {i} ventas creadas...")
                
        except Exception as e:
            error_msg = f"Error en venta {i}: {str(e)}"
            errores.append(error_msg)
            print(f"❌ {error_msg}")
            continue
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE CREACIÓN DE VENTAS")
    print("="*60)
    print(f"✅ Notas de venta creadas: {ventas_creadas}")
    print(f"✅ Detalles creados: {detalles_creados}")
    print(f"✅ Pagos creados: {pagos_creados}")
    print(f"✅ Históricos creados: {historicos_creados}")
    if errores:
        print(f"❌ Errores: {len(errores)}")
        for error in errores[:10]:  # Mostrar solo los primeros 10 errores
            print(f"   - {error}")
    print("="*60)


if __name__ == "__main__":
    print("🚀 Iniciando creación de 1000 notas de venta...\n")
    crear_ventas()
    print("\n✅ Proceso completado.")
