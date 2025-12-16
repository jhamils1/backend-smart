"""
Vistas para el Dashboard con estadísticas y gráficos
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from transacciones.modelsListadoHistoricoVentas import ListadoHistoricoVentas
from transacciones.modelsDetalleNotaDeVenta import DetalleNotaDeVenta
from perfiles.models import Cliente


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para el dashboard con estadísticas y gráficos
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación para dashboard
    
    @action(detail=False, methods=['get'], url_path='ventas-historicas')
    def ventas_historicas(self, request):
        """
        Obtiene las ventas históricas agrupadas por período.
        
        Parámetros:
        - periodo: 'mes', 'semestre', 'anio' (por defecto: 'mes')
        - fecha_inicio: Fecha de inicio (opcional, formato: YYYY-MM-DD)
        - fecha_fin: Fecha de fin (opcional, formato: YYYY-MM-DD)
        
        Ejemplo: /api/analitica/dashboard/ventas-historicas/?periodo=mes
        """
        periodo = request.query_params.get('periodo', 'mes')
        fecha_inicio = request.query_params.get('fecha_inicio', None)
        fecha_fin = request.query_params.get('fecha_fin', None)
        
        # Validar período
        if periodo not in ['mes', 'semestre', 'anio']:
            return Response({
                'error': 'Período inválido. Use: mes, semestre o anio'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener todas las ventas completadas
        ventas = ListadoHistoricoVentas.objects.filter(estado_pago='completado')
        
        # Aplicar filtros de fecha si existen
        if fecha_inicio:
            ventas = ventas.filter(fecha_venta__gte=fecha_inicio)
        if fecha_fin:
            ventas = ventas.filter(fecha_venta__lte=fecha_fin)
        
        # Agrupar según el período
        if periodo == 'mes':
            datos = self._agrupar_por_mes(ventas)
        elif periodo == 'semestre':
            datos = self._agrupar_por_semestre(ventas)
        else:  # anio
            datos = self._agrupar_por_anio(ventas)
        
        return Response({
            'periodo': periodo,
            'datos': datos,
            'total_registros': len(datos)
        })
    
    def _agrupar_por_mes(self, ventas):
        """Agrupa ventas por mes"""
        from django.db.models.functions import TruncMonth
        
        ventas_por_mes = ventas.annotate(
            mes=TruncMonth('fecha_venta')
        ).values('mes').annotate(
            total_ventas=Count('nota_venta'),
            total_ingresos=Sum('total')
        ).order_by('mes')
        
        return [
            {
                'periodo': v['mes'].strftime('%Y-%m') if v['mes'] else 'N/A',
                'periodo_nombre': v['mes'].strftime('%B %Y') if v['mes'] else 'N/A',
                'total_ventas': v['total_ventas'],
                'total_ingresos': float(v['total_ingresos'] or 0)
            }
            for v in ventas_por_mes
        ]
    
    def _agrupar_por_semestre(self, ventas):
        """Agrupa ventas por semestre"""
        datos = []
        
        # Obtener rango de años
        primera_venta = ventas.order_by('fecha_venta').first()
        ultima_venta = ventas.order_by('-fecha_venta').first()
        
        if not primera_venta or not ultima_venta:
            return []
        
        anio_inicio = primera_venta.fecha_venta.year
        anio_fin = ultima_venta.fecha_venta.year
        
        for anio in range(anio_inicio, anio_fin + 1):
            # Primer semestre (enero - junio)
            semestre1 = ventas.filter(
                fecha_venta__year=anio,
                fecha_venta__month__lte=6
            ).aggregate(
                total_ventas=Count('nota_venta'),
                total_ingresos=Sum('total')
            )
            
            if semestre1['total_ventas'] > 0:
                datos.append({
                    'periodo': f'{anio}-S1',
                    'periodo_nombre': f'Primer Semestre {anio}',
                    'total_ventas': semestre1['total_ventas'],
                    'total_ingresos': float(semestre1['total_ingresos'] or 0)
                })
            
            # Segundo semestre (julio - diciembre)
            semestre2 = ventas.filter(
                fecha_venta__year=anio,
                fecha_venta__month__gt=6
            ).aggregate(
                total_ventas=Count('nota_venta'),
                total_ingresos=Sum('total')
            )
            
            if semestre2['total_ventas'] > 0:
                datos.append({
                    'periodo': f'{anio}-S2',
                    'periodo_nombre': f'Segundo Semestre {anio}',
                    'total_ventas': semestre2['total_ventas'],
                    'total_ingresos': float(semestre2['total_ingresos'] or 0)
                })
        
        return datos
    
    def _agrupar_por_anio(self, ventas):
        """Agrupa ventas por año"""
        from django.db.models.functions import TruncYear
        
        ventas_por_anio = ventas.annotate(
            anio=TruncYear('fecha_venta')
        ).values('anio').annotate(
            total_ventas=Count('nota_venta'),
            total_ingresos=Sum('total')
        ).order_by('anio')
        
        return [
            {
                'periodo': v['anio'].year if v['anio'] else 'N/A',
                'periodo_nombre': str(v['anio'].year) if v['anio'] else 'N/A',
                'total_ventas': v['total_ventas'],
                'total_ingresos': float(v['total_ingresos'] or 0)
            }
            for v in ventas_por_anio
        ]
    
    @action(detail=False, methods=['get'], url_path='clientes-ranking')
    def clientes_ranking(self, request):
        """
        Obtiene el ranking de clientes por cantidad de compras.
        
        Parámetros:
        - tipo: 'top' (más compras) o 'bottom' (menos compras) (por defecto: 'top')
        - limite: Cantidad de clientes a mostrar (por defecto: 10)
        
        Ejemplo: /api/analitica/dashboard/clientes-ranking/?tipo=top&limite=10
        """
        tipo = request.query_params.get('tipo', 'top')
        limite = int(request.query_params.get('limite', 10))
        
        # Validar tipo
        if tipo not in ['top', 'bottom']:
            return Response({
                'error': 'Tipo inválido. Use: top o bottom'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Agrupar ventas por cliente
        clientes_stats = ListadoHistoricoVentas.objects.filter(
            estado_pago='completado'
        ).values(
            'cliente_nombre',
            'cliente_ci',
            'cliente_email'
        ).annotate(
            total_compras=Count('nota_venta'),
            total_gastado=Sum('total')
        )
        
        # Ordenar según tipo
        if tipo == 'top':
            clientes_stats = clientes_stats.order_by('-total_compras')[:limite]
        else:  # bottom
            clientes_stats = clientes_stats.order_by('total_compras')[:limite]
        
        datos = []
        for c in clientes_stats:
            total_gastado = float(c['total_gastado'] or 0)
            total_compras = c['total_compras']
            compra_promedio = total_gastado / total_compras if total_compras > 0 else 0
            
            datos.append({
                'cliente_nombre': c['cliente_nombre'],
                'cliente_ci': c['cliente_ci'],
                'cliente_email': c['cliente_email'],
                'total_compras': total_compras,
                'total_gastado': total_gastado,
                'compra_promedio': round(compra_promedio, 2)
            })
        return Response({
            'tipo': tipo,
            'limite': limite,
            'datos': datos,
            'total_registros': len(datos)
        })
    
    @action(detail=False, methods=['get'], url_path='productos-ranking')
    def productos_ranking(self, request):
        """
        Obtiene el ranking de productos por ventas.
        
        Parámetros:
        - tipo: 'top' (más vendidos) o 'bottom' (menos vendidos) (por defecto: 'top')
        - limite: Cantidad de productos a mostrar (por defecto: 10)
        
        Ejemplo: /api/analitica/dashboard/productos-ranking/?tipo=top&limite=10
        """
        tipo = request.query_params.get('tipo', 'top')
        limite = int(request.query_params.get('limite', 10))
        
        # Validar tipo
        if tipo not in ['top', 'bottom']:
            return Response({
                'error': 'Tipo inválido. Use: top o bottom'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Agrupar detalles de ventas por producto
        # Solo incluir ventas completadas
        productos_stats = DetalleNotaDeVenta.objects.filter(
            nota_venta__estado='pagada'
        ).values(
            'producto__id',
            'producto__codigo',
            'producto__nombre',
            'producto__categoria__nombre'
        ).annotate(
            total_vendido=Sum('cantidad'),
            total_ingresos=Sum('total'),
            numero_ventas=Count('nota_venta', distinct=True)
        )
        
        # Ordenar según tipo
        if tipo == 'top':
            productos_stats = productos_stats.order_by('-total_vendido')[:limite]
        else:  # bottom
            productos_stats = productos_stats.order_by('total_vendido')[:limite]
        
        datos = [
            {
                'producto_id': p['producto__id'],
                'producto_codigo': p['producto__codigo'],
                'producto_nombre': p['producto__nombre'],
                'categoria': p['producto__categoria__nombre'],
                'total_vendido': p['total_vendido'],
                'total_ingresos': float(p['total_ingresos'] or 0),
                'numero_ventas': p['numero_ventas']
            }
            for p in productos_stats
        ]
        
        return Response({
            'tipo': tipo,
            'limite': limite,
            'datos': datos,
            'total_registros': len(datos)
        })
    
    @action(detail=False, methods=['get'], url_path='resumen-general')
    def resumen_general(self, request):
        """
        Obtiene un resumen general del dashboard con KPIs principales.
        
        Ejemplo: /api/analitica/dashboard/resumen-general/
        """
        # Estadísticas de ventas
        stats_ventas = ListadoHistoricoVentas.objects.filter(
            estado_pago='completado'
        ).aggregate(
            total_ventas=Count('nota_venta'),
            total_ingresos=Sum('total')
        )
        
        # Calcular ticket promedio en Python
        ticket_promedio = 0
        if stats_ventas['total_ventas'] and stats_ventas['total_ventas'] > 0:
            ticket_promedio = float(stats_ventas['total_ingresos'] or 0) / stats_ventas['total_ventas']
        
        # Cantidad de clientes únicos con compras
        clientes_activos = ListadoHistoricoVentas.objects.filter(
            estado_pago='completado'
        ).values('cliente_ci').distinct().count()
        
        # Total de productos vendidos (unidades)
        unidades_vendidas = DetalleNotaDeVenta.objects.filter(
            nota_venta__estado='pagada'
        ).aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        # Productos únicos vendidos
        productos_vendidos = DetalleNotaDeVenta.objects.filter(
            nota_venta__estado='pagada'
        ).values('producto__id').distinct().count()
        
        # Comparativa con mes anterior
        ahora = timezone.now()
        inicio_mes_actual = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        inicio_mes_anterior = (inicio_mes_actual - timedelta(days=1)).replace(day=1)
        
        ventas_mes_actual = ListadoHistoricoVentas.objects.filter(
            estado_pago='completado',
            fecha_venta__gte=inicio_mes_actual
        ).aggregate(
            total_ventas=Count('nota_venta'),
            total_ingresos=Sum('total')
        )
        
        ventas_mes_anterior = ListadoHistoricoVentas.objects.filter(
            estado_pago='completado',
            fecha_venta__gte=inicio_mes_anterior,
            fecha_venta__lt=inicio_mes_actual
        ).aggregate(
            total_ventas=Count('nota_venta'),
            total_ingresos=Sum('total')
        )
        
        # Calcular variación porcentual
        variacion_ventas = 0
        variacion_ingresos = 0
        
        if ventas_mes_anterior['total_ventas'] and ventas_mes_anterior['total_ventas'] > 0:
            variacion_ventas = ((ventas_mes_actual['total_ventas'] - ventas_mes_anterior['total_ventas']) / ventas_mes_anterior['total_ventas']) * 100
        
        if ventas_mes_anterior['total_ingresos'] and ventas_mes_anterior['total_ingresos'] > 0:
            variacion_ingresos = ((float(ventas_mes_actual['total_ingresos'] or 0) - float(ventas_mes_anterior['total_ingresos'])) / float(ventas_mes_anterior['total_ingresos'])) * 100
        
        return Response({
            'kpis': {
                'total_ventas': stats_ventas['total_ventas'] or 0,
                'total_ingresos': float(stats_ventas['total_ingresos'] or 0),
                'ticket_promedio': round(ticket_promedio, 2),
                'clientes_activos': clientes_activos,
                'unidades_vendidas': unidades_vendidas,
                'productos_vendidos': productos_vendidos
            },
            'comparativa_mensual': {
                'mes_actual': {
                    'ventas': ventas_mes_actual['total_ventas'] or 0,
                    'ingresos': float(ventas_mes_actual['total_ingresos'] or 0)
                },
                'mes_anterior': {
                    'ventas': ventas_mes_anterior['total_ventas'] or 0,
                    'ingresos': float(ventas_mes_anterior['total_ingresos'] or 0)
                },
                'variacion': {
                    'ventas_porcentaje': round(variacion_ventas, 2),
                    'ingresos_porcentaje': round(variacion_ingresos, 2)
                }
            }
        })
