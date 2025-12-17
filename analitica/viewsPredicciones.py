"""
Vista para predicciones y análisis predictivo del dashboard usando Random Forest
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import pickle
import os

from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas
from transacciones.modelsDetalleNotaDeVenta import DetalleNotaDeVenta


def cargar_cerebro():
    """Carga el modelo pre-entrenado (cerebro) desde archivo"""
    ruta_modelo = os.path.join(os.path.dirname(__file__), 'cerebro_ventas.pkl')
    try:
        with open(ruta_modelo, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


class PrediccionViewSet(viewsets.ViewSet):
    """
    ViewSet para predicciones y análisis predictivo usando Random Forest
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], url_path='ventas-futuras')
    def ventas_futuras(self, request):
        """
        Predice las ventas de los próximos meses usando Random Forest.
        
        Parámetros:
        - meses: Número de meses a predecir (por defecto: 6)
        
        Ejemplo: /api/analitica/predicciones/ventas-futuras/?meses=6
        """
        try:
            meses_predecir = int(request.query_params.get('meses', 6))
            
            # Cargar cerebro pre-entrenado
            cerebro = cargar_cerebro()
            
            if cerebro is None:
                return Response({
                    'error': 'El cerebro no ha sido entrenado. Ejecuta: python entrenar_cerebro.py'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            modelo = cerebro['modelo']
            ultimo_mes = cerebro['ultimo_mes']
            
            # Obtener datos históricos para mostrar
            ventas_mensuales = ListadoHistoricoVentas.objects.filter(
                estado_pago='completado'
            ).annotate(
                mes=TruncMonth('fecha_venta')
            ).values('mes').annotate(
                total_ventas=Count('nota_venta', distinct=True),
                total_ingresos=Sum('total')
            ).order_by('mes')
            
            datos_historicos = []
            for venta in ventas_mensuales:
                datos_historicos.append({
                    'mes': venta['mes'].strftime('%Y-%m'),
                    'ventas': venta['total_ventas'],
                    'ingresos': float(venta['total_ingresos'] or 0)
                })
            
            # Realizar predicciones con el cerebro
            predicciones = modelo.predecir(meses_predecir, ultimo_mes)
            
            return Response({
                'historico': datos_historicos[-12:],  # Últimos 12 meses
                'predicciones': predicciones,
                'cerebro_info': {
                    'tipo': 'Random Forest Regressor',
                    'algoritmo': 'Ensemble Learning',
                    'n_estimators': 100,
                    'fecha_entrenamiento': cerebro['fecha_entrenamiento'],
                    'importancia_features': cerebro['importancia_features'],
                    'meses_entrenamiento': cerebro['meses_entrenamiento']
                },
                'meses_predichos': meses_predecir
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al generar predicciones: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='tendencias')
    def tendencias(self, request):
        """
        Analiza las tendencias de productos usando análisis temporal.
        
        Ejemplo: /api/analitica/predicciones/tendencias/
        """
        try:
            # Obtener fechas de análisis
            ahora = timezone.now()
            hace_90_dias = ahora - timedelta(days=90)
            hace_180_dias = ahora - timedelta(days=180)
            
            # Productos con más ventas en últimos 90 días
            productos_periodo_reciente = DetalleNotaDeVenta.objects.filter(
                nota_venta__estado='pagada',
                nota_venta__fecha__gte=hace_90_dias
            ).values(
                'producto__id',
                'producto__nombre',
                'producto__codigo',
                'producto__precio_venta'
            ).annotate(
                cantidad_reciente=Sum('cantidad'),
                ingresos_recientes=Sum(F('cantidad') * F('producto__precio_venta'))
            )
            
            # Productos en periodo anterior (90-180 días atrás)
            productos_periodo_anterior = DetalleNotaDeVenta.objects.filter(
                nota_venta__estado='pagada',
                nota_venta__fecha__gte=hace_180_dias,
                nota_venta__fecha__lt=hace_90_dias
            ).values(
                'producto__id'
            ).annotate(
                cantidad_anterior=Sum('cantidad')
            )
            
            # Crear diccionario de periodo anterior
            dict_anterior = {
                p['producto__id']: p['cantidad_anterior'] 
                for p in productos_periodo_anterior
            }
            
            # Analizar tendencias
            productos_en_alza = []
            productos_en_baja = []
            
            for producto in productos_periodo_reciente:
                producto_id = producto['producto__id']
                cantidad_reciente = producto['cantidad_reciente']
                cantidad_anterior = dict_anterior.get(producto_id, 0)
                
                # Calcular cambio porcentual
                if cantidad_anterior > 0:
                    cambio_porcentual = ((cantidad_reciente - cantidad_anterior) / cantidad_anterior) * 100
                else:
                    cambio_porcentual = 100 if cantidad_reciente > 0 else 0
                
                producto_info = {
                    'producto_id': producto_id,
                    'nombre': producto['producto__nombre'],
                    'codigo': producto['producto__codigo'],
                    'cantidad_reciente': cantidad_reciente,
                    'cantidad_anterior': cantidad_anterior,
                    'cambio_porcentual': round(cambio_porcentual, 2),
                    'ingresos': round(float(producto['ingresos_recientes'] or 0), 2)
                }
                
                # Clasificar tendencia
                if cambio_porcentual >= 20:
                    producto_info['tendencia'] = 'alto_crecimiento'
                    productos_en_alza.append(producto_info)
                elif cambio_porcentual >= 5:
                    producto_info['tendencia'] = 'crecimiento_moderado'
                    productos_en_alza.append(producto_info)
                elif cambio_porcentual <= -20:
                    producto_info['tendencia'] = 'fuerte_declive'
                    productos_en_baja.append(producto_info)
                elif cambio_porcentual <= -5:
                    producto_info['tendencia'] = 'declive_moderado'
                    productos_en_baja.append(producto_info)
            
            # Ordenar por cambio porcentual
            productos_en_alza.sort(key=lambda x: x['cambio_porcentual'], reverse=True)
            productos_en_baja.sort(key=lambda x: x['cambio_porcentual'])
            
            return Response({
                'periodo_analisis': {
                    'inicio': hace_180_dias.strftime('%Y-%m-%d'),
                    'fin': ahora.strftime('%Y-%m-%d'),
                    'dias_periodo_reciente': 90,
                    'dias_periodo_anterior': 90
                },
                'productos_en_alza': productos_en_alza[:10],
                'productos_en_baja': productos_en_baja[:10],
                'resumen': {
                    'total_productos_analizados': len(productos_periodo_reciente),
                    'productos_crecimiento': len(productos_en_alza),
                    'productos_declive': len(productos_en_baja)
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al analizar tendencias: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='productos-demandados')
    def productos_demandados(self, request):
        """
        Predice qué productos tendrán mayor demanda usando Random Forest.
        
        Parámetros:
        - limite: Número de productos a retornar (por defecto: 10)
        
        Ejemplo: /api/analitica/predicciones/productos-demandados/?limite=15
        """
        try:
            limite = int(request.query_params.get('limite', 10))
            
            # Obtener datos de productos de los últimos 90 días
            hace_90_dias = timezone.now() - timedelta(days=90)
            
            productos_data = DetalleNotaDeVenta.objects.filter(
                nota_venta__estado='pagada',
                nota_venta__fecha__gte=hace_90_dias
            ).values(
                'producto__id',
                'producto__nombre',
                'producto__codigo',
                'producto__precio_venta',
                'producto__stock'
            ).annotate(
                total_vendido=Sum('cantidad'),
                frecuencia_ventas=Count('nota_venta', distinct=True),
                ingreso_total=Sum(F('cantidad') * F('producto__precio_venta'))
            ).order_by('-total_vendido')
            
            if not productos_data or len(productos_data) < 5:
                return Response({
                    'error': 'No hay suficientes datos de productos (mínimo 5 productos requeridos)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calcular score de demanda basado en datos históricos
            # (Sin entrenar modelo - usamos algoritmo de scoring directo)
            productos_con_prediccion = []
            for producto in productos_data:
                total_vendido = producto['total_vendido']
                frecuencia = producto['frecuencia_ventas']
                ingresos = float(producto['ingreso_total'] or 0)
                stock_actual = producto['producto__stock'] or 0
                
                # Predicción simple: proyección lineal basada en promedio diario
                demanda_predicha = round((total_vendido / 90) * 90)  # Próximos 90 días
                
                # Calcular score de prioridad
                score = self._calcular_score_demanda(
                    total_vendido,
                    frecuencia,
                    ingresos,
                    demanda_predicha
                )
                
                productos_con_prediccion.append({
                    'producto_id': producto['producto__id'],
                    'nombre': producto['producto__nombre'],
                    'codigo': producto['producto__codigo'],
                    'precio': float(producto['producto__precio_venta'] or 0),
                    'stock_actual': stock_actual,
                    'ventas_historicas': total_vendido,
                    'demanda_predicha_90dias': demanda_predicha,
                    'frecuencia_compras': frecuencia,
                    'ingresos_generados': round(ingresos, 2),
                    'score_prioridad': round(score, 2),
                    'recomendacion': self._generar_recomendacion(
                        stock_actual,
                        demanda_predicha
                    )
                })
            
            # Ordenar por score de prioridad
            productos_con_prediccion.sort(key=lambda x: x['score_prioridad'], reverse=True)
            
            return Response({
                'productos_alta_demanda': productos_con_prediccion[:limite],
                'modelo_info': {
                    'tipo': 'Análisis estadístico + proyección lineal',
                    'productos_analizados': len(productos_data),
                    'periodo_datos': '90 días',
                    'metodo': 'Score ponderado (ventas 30%, frecuencia 20%, ingresos 20%, predicción 30%)'
                },
                'fecha_analisis': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al predecir demanda de productos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calcular_score_demanda(self, ventas_historicas, frecuencia, ingresos, demanda_predicha):
        """
        Calcula un score de prioridad basado en múltiples factores.
        """
        # Normalizar valores
        score_ventas = min(ventas_historicas / 10, 100)  # Máximo 100 puntos
        score_frecuencia = min(frecuencia / 2, 50)  # Máximo 50 puntos
        score_ingresos = min(ingresos / 1000, 50)  # Máximo 50 puntos
        score_prediccion = min(demanda_predicha / 10, 100)  # Máximo 100 puntos
        
        # Peso: 30% ventas, 20% frecuencia, 20% ingresos, 30% predicción
        score_total = (
            score_ventas * 0.30 +
            score_frecuencia * 0.20 +
            score_ingresos * 0.20 +
            score_prediccion * 0.30
        )
        
        return score_total
    
    def _generar_recomendacion(self, stock_actual, demanda_predicha):
        """
        Genera recomendación de reabastecimiento.
        """
        if stock_actual < demanda_predicha * 0.3:
            return {
                'nivel': 'urgente',
                'mensaje': 'Stock crítico - Reabastecer inmediatamente',
                'cantidad_sugerida': round(demanda_predicha * 1.5)
            }
        elif stock_actual < demanda_predicha * 0.6:
            return {
                'nivel': 'moderado',
                'mensaje': 'Stock bajo - Planificar reabastecimiento',
                'cantidad_sugerida': round(demanda_predicha * 1.2)
            }
        else:
            return {
                'nivel': 'normal',
                'mensaje': 'Stock adecuado',
                'cantidad_sugerida': round(demanda_predicha * 0.5)
            }
    
    @action(detail=False, methods=['get'], url_path='metricas-modelo')
    def metricas_modelo(self, request):
        """
        Retorna información del cerebro pre-entrenado.
        """
        try:
            # Cargar cerebro
            cerebro = cargar_cerebro()
            
            if cerebro is None:
                return Response({
                    'error': 'El cerebro no ha sido entrenado. Ejecuta: python entrenar_cerebro.py'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'modelo': 'Random Forest Regressor',
                'estado': 'Pre-entrenado y listo',
                'fecha_entrenamiento': cerebro['fecha_entrenamiento'],
                'meses_entrenamiento': cerebro['meses_entrenamiento'],
                'ultimo_mes_datos': cerebro['ultimo_mes'],
                'importancia_features': cerebro['importancia_features'],
                'configuracion': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'algoritmo': 'Ensemble Learning - Random Forest'
                },
                'nota': 'Para re-entrenar el modelo con datos actualizados, ejecuta: python entrenar_cerebro.py'
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al obtener información del cerebro: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
