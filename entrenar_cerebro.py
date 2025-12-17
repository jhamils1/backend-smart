"""
Script para entrenar el modelo (cerebro) y guardarlo en un archivo
Este archivo debe ejecutarse cada vez que se actualicen los datos de ventas
"""
import os
import django
import pickle
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas
from analitica.ml_model import ModeloPrediccionVentas, ModeloPrediccionProductos

def entrenar_modelo_ventas():
    """Entrena y guarda el modelo de predicción de ventas"""
    print("=" * 80)
    print("ENTRENANDO CEREBRO - MODELO DE PREDICCIÓN DE VENTAS")
    print("=" * 80)
    
    # Obtener datos históricos
    print("\n1. Obteniendo datos históricos de ventas...")
    ventas_mensuales = ListadoHistoricoVentas.objects.filter(
        estado_pago='completado'
    ).annotate(
        mes=TruncMonth('fecha_venta')
    ).values('mes').annotate(
        total_ventas=Count('nota_venta', distinct=True),
        total_ingresos=Sum('total')
    ).order_by('mes')
    
    if not ventas_mensuales or len(ventas_mensuales) < 3:
        print("❌ Error: No hay suficientes datos históricos (mínimo 3 meses)")
        return False
    
    # Preparar datos
    datos_historicos = []
    for venta in ventas_mensuales:
        datos_historicos.append({
            'mes': venta['mes'].strftime('%Y-%m'),
            'ventas': venta['total_ventas'],
            'ingresos': float(venta['total_ingresos'] or 0)
        })
    
    print(f"✓ Se encontraron {len(datos_historicos)} meses de datos históricos")
    print(f"  Periodo: {datos_historicos[0]['mes']} a {datos_historicos[-1]['mes']}")
    
    # Crear y entrenar modelo
    print("\n2. Entrenando modelo Random Forest...")
    modelo = ModeloPrediccionVentas()
    modelo.entrenar(datos_historicos)
    print("✓ Modelo entrenado exitosamente")
    
    # Mostrar importancia de características
    print("\n3. Importancia de características:")
    importancia = modelo.obtener_importancia_features()
    for feature in importancia:
        print(f"  - {feature['feature']}: {feature['importancia']}%")
    
    # Guardar modelo
    print("\n4. Guardando cerebro en archivo...")
    ruta_modelo = os.path.join('analitica', 'cerebro_ventas.pkl')
    with open(ruta_modelo, 'wb') as f:
        pickle.dump({
            'modelo': modelo,
            'fecha_entrenamiento': datetime.now().isoformat(),
            'meses_entrenamiento': len(datos_historicos),
            'ultimo_mes': datos_historicos[-1]['mes'],
            'importancia_features': importancia
        }, f)
    
    print(f"✓ Cerebro guardado en: {ruta_modelo}")
    print(f"  Tamaño: {os.path.getsize(ruta_modelo) / 1024:.2f} KB")
    
    # Validar modelo
    print("\n5. Validando modelo...")
    predicciones_test = modelo.predecir(3, datos_historicos[-1]['mes'])
    print("✓ Predicciones de prueba (próximos 3 meses):")
    for pred in predicciones_test:
        print(f"  - {pred['mes']}: {pred['ventas_predichas']} ventas, "
             f"${pred['ingresos_predichos']:,.2f}")
    
    return True

def entrenar_modelo_productos():
    """Entrena y guarda el modelo de productos (opcional para futuro)"""
    print("\n" + "=" * 80)
    print("ENTRENANDO CEREBRO - MODELO DE DEMANDA DE PRODUCTOS")
    print("=" * 80)
    print("(Por implementar en futuras versiones)")
    return True

def main():
    """Función principal"""
    print("\n🧠 SISTEMA DE ENTRENAMIENTO DEL CEREBRO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Entrenar modelo de ventas
    exito_ventas = entrenar_modelo_ventas()
    
    if exito_ventas:
        print("\n" + "=" * 80)
        print("✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print("\nEl cerebro está listo para ser usado.")
        print("Ahora puedes iniciar el servidor: python manage.py runserver")
    else:
        print("\n" + "=" * 80)
        print("❌ ERROR EN EL ENTRENAMIENTO")
        print("=" * 80)
        print("\nVerifica que tienes suficientes datos en la base de datos.")

if __name__ == '__main__':
    main()
