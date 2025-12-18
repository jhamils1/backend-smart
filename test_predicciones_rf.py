"""
Script de prueba para verificar las predicciones con Random Forest
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

import requests
from datetime import datetime

# URL base de la API
BASE_URL = 'http://localhost:8000/api/analitica'

def probar_predicciones():
    """Prueba el endpoint de predicciones con Random Forest"""
    print("=" * 80)
    print("PROBANDO PREDICCIONES CON RANDOM FOREST")
    print("=" * 80)
    
    # 1. Ventas futuras
    print("\n1. Predicción de ventas futuras (6 meses):")
    print("-" * 80)
    try:
        response = requests.get(f'{BASE_URL}/predicciones/ventas-futuras/?meses=6')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Modelo: {data.get('modelo_info', {}).get('tipo', 'N/A')}")
            print(f"✓ Algoritmo: {data.get('modelo_info', {}).get('algoritmo', 'N/A')}")
            print(f"✓ Meses de entrenamiento: {data.get('modelo_info', {}).get('meses_entrenamiento', 'N/A')}")
            
            print("\nÚltimos 3 meses históricos:")
            for mes in data.get('historico', [])[-3:]:
                print(f"  - {mes['mes']}: {mes['ventas']} ventas, ${mes['ingresos']:,.2f}")
            
            print("\nPredicciones (primeros 3 meses):")
            for pred in data.get('predicciones', [])[:3]:
                print(f"  - {pred['mes_nombre']}: {pred['ventas_predichas']} ventas, "
                      f"${pred['ingresos_predichos']:,.2f} (Confianza: {pred['confianza']})")
            
            print("\nImportancia de características:")
            for feature in data.get('modelo_info', {}).get('importancia_features', []):
                print(f"  - {feature['feature']}: {feature['importancia']}%")
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # 2. Tendencias de productos
    print("\n\n2. Análisis de tendencias de productos:")
    print("-" * 80)
    try:
        response = requests.get(f'{BASE_URL}/predicciones/tendencias/')
        if response.status_code == 200:
            data = response.json()
            resumen = data.get('resumen', {})
            print(f"✓ Productos analizados: {resumen.get('total_productos_analizados', 0)}")
            print(f"✓ En crecimiento: {resumen.get('productos_crecimiento', 0)}")
            print(f"✓ En declive: {resumen.get('productos_declive', 0)}")
            
            print("\nTop 3 productos en alza:")
            for i, prod in enumerate(data.get('productos_en_alza', [])[:3], 1):
                print(f"  {i}. {prod['nombre']} ({prod['codigo']})")
                print(f"     Cambio: +{prod['cambio_porcentual']}% - Ventas: {prod['cantidad_reciente']}")
            
            if data.get('productos_en_baja'):
                print("\nTop 3 productos en baja:")
                for i, prod in enumerate(data.get('productos_en_baja', [])[:3], 1):
                    print(f"  {i}. {prod['nombre']} ({prod['codigo']})")
                    print(f"     Cambio: {prod['cambio_porcentual']}% - Ventas: {prod['cantidad_reciente']}")
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # 3. Productos más demandados
    print("\n\n3. Productos con mayor demanda predicha:")
    print("-" * 80)
    try:
        response = requests.get(f'{BASE_URL}/predicciones/productos-demandados/?limite=5')
        if response.status_code == 200:
            data = response.json()
            modelo_info = data.get('modelo_info', {})
            print(f"✓ Modelo: {modelo_info.get('tipo', 'N/A')}")
            print(f"✓ Productos analizados: {modelo_info.get('productos_analizados', 0)}")
            
            print("\nTop 5 productos de alta demanda:")
            for i, prod in enumerate(data.get('productos_alta_demanda', [])[:5], 1):
                print(f"\n  {i}. {prod['nombre']} ({prod['codigo']})")
                print(f"     Score prioridad: {prod['score_prioridad']}")
                print(f"     Ventas históricas: {prod['ventas_historicas']}")
                print(f"     Demanda predicha (90 días): {prod['demanda_predicha_90dias']}")
                print(f"     Stock actual: {prod['stock_actual']}")
                recom = prod.get('recomendacion', {})
                print(f"     Recomendación: {recom.get('mensaje', 'N/A')} "
                      f"({recom.get('cantidad_sugerida', 0)} unidades)")
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # 4. Métricas del modelo
    print("\n\n4. Métricas de precisión del modelo:")
    print("-" * 80)
    try:
        response = requests.get(f'{BASE_URL}/predicciones/metricas-modelo/')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Modelo: {data.get('modelo', 'N/A')}")
            print(f"✓ Datos entrenamiento: {data.get('datos_entrenamiento', 0)} meses")
            print(f"✓ Datos prueba: {data.get('datos_prueba', 0)} meses")
            
            metricas = data.get('metricas_precision', {})
            if metricas:
                print("\nPrecisión de ventas:")
                print(f"  - MAE (Error Absoluto Medio): {metricas.get('ventas', {}).get('mae', 'N/A')}")
                print(f"  - RMSE (Raíz del Error Cuadrático): {metricas.get('ventas', {}).get('rmse', 'N/A')}")
                
                print("\nPrecisión de ingresos:")
                print(f"  - MAE: {metricas.get('ingresos', {}).get('mae', 'N/A')}")
                print(f"  - RMSE: {metricas.get('ingresos', {}).get('rmse', 'N/A')}")
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("PRUEBAS COMPLETADAS")
    print("=" * 80)

if __name__ == '__main__':
    probar_predicciones()
