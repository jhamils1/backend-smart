import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from transacciones.modelsNotaDeVenta import NotaDeVenta
from transacciones.modelsPago import Pago
from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas


def crear_historicos_para_ventas_existentes():
    """
    Crea registros de ListadoHistoricoVentas para todas las notas de venta que no lo tengan
    """
    print("🔍 Buscando notas de venta sin registro histórico...\n")
    
    # Obtener todas las notas de venta que no tienen registro histórico
    notas_sin_historico = NotaDeVenta.objects.filter(historial_venta__isnull=True)
    total = notas_sin_historico.count()
    
    print(f"📊 Encontradas {total} notas de venta sin registro histórico\n")
    
    if total == 0:
        print("✅ Todas las notas de venta ya tienen su registro histórico")
        return
    
    creados = 0
    errores = []
    
    print("🚀 Creando registros históricos...\n")
    
    for i, nota_venta in enumerate(notas_sin_historico, 1):
        try:
            # Obtener el pago asociado
            try:
                pago = nota_venta.pago
            except Pago.DoesNotExist:
                print(f"⚠️  Nota {nota_venta.numero_comprobante} no tiene pago, omitiendo...")
                continue
            
            # Obtener información del cliente
            cliente = nota_venta.cliente
            
            # Crear registro histórico
            ListadoHistoricoVentas.objects.create(
                nota_venta=nota_venta,
                cliente_nombre=f"{cliente.nombre} {cliente.apellido}",
                cliente_ci=cliente.ci,
                cliente_email=cliente.usuario.email if cliente.usuario else None,
                numero_venta=nota_venta.numero_comprobante,
                fecha_venta=nota_venta.fecha,
                subtotal=nota_venta.subtotal,
                total=nota_venta.total,
                metodo_pago='Stripe',
                estado_pago='completado',
                fecha_pago=pago.fecha,
                referencia_pago=pago.total_stripe
            )
            
            creados += 1
            
            # Mostrar progreso cada 50 registros
            if i % 50 == 0:
                print(f"✅ {i}/{total} registros históricos creados...")
                
        except Exception as e:
            error_msg = f"Error en nota {nota_venta.numero_comprobante}: {str(e)}"
            errores.append(error_msg)
            print(f"❌ {error_msg}")
            continue
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE CREACIÓN DE HISTÓRICOS")
    print("="*60)
    print(f"✅ Registros históricos creados: {creados}")
    if errores:
        print(f"❌ Errores: {len(errores)}")
        for error in errores[:10]:
            print(f"   - {error}")
    print("="*60)


if __name__ == "__main__":
    print("🚀 Iniciando creación de registros históricos...\n")
    crear_historicos_para_ventas_existentes()
    print("\n✅ Proceso completado.")
