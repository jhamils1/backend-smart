"""
Modelo de Machine Learning con Random Forest para predicciones de ventas
Este archivo actúa como el "cerebro" del sistema de predicciones
"""
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class ModeloPrediccionVentas:
    """
    Modelo de Random Forest para predecir ventas futuras
    """
    
    def __init__(self):
        self.modelo_ventas = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.modelo_ingresos = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.entrenado = False
    
    def entrenar(self, datos_historicos):
        """
        Entrena el modelo con datos históricos.
        
        Args:
            datos_historicos: Lista de diccionarios con 'mes', 'ventas', 'ingresos'
        """
        if len(datos_historicos) < 3:
            raise ValueError("Se necesitan al menos 3 meses de datos históricos")
        
        # Preparar características (features)
        X = []
        y_ventas = []
        y_ingresos = []
        
        for i, dato in enumerate(datos_historicos):
            # Features: índice temporal, mes del año, ventas previas
            mes_del_anio = datetime.strptime(dato['mes'], '%Y-%m').month
            
            # Características temporales
            features = [
                i,  # Índice temporal
                mes_del_anio,  # Mes del año (1-12)
                np.sin(2 * np.pi * mes_del_anio / 12),  # Estacionalidad (seno)
                np.cos(2 * np.pi * mes_del_anio / 12),  # Estacionalidad (coseno)
            ]
            
            # Agregar ventas de meses anteriores como features (lag features)
            if i > 0:
                features.append(datos_historicos[i-1]['ventas'])  # Mes anterior
                features.append(datos_historicos[i-1]['ingresos'])
            else:
                features.append(0)
                features.append(0)
            
            if i > 1:
                features.append(datos_historicos[i-2]['ventas'])  # 2 meses atrás
            else:
                features.append(0)
            
            X.append(features)
            y_ventas.append(dato['ventas'])
            y_ingresos.append(dato['ingresos'])
        
        X = np.array(X)
        y_ventas = np.array(y_ventas)
        y_ingresos = np.array(y_ingresos)
        
        # Normalizar características
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar modelos
        self.modelo_ventas.fit(X_scaled, y_ventas)
        self.modelo_ingresos.fit(X_scaled, y_ingresos)
        
        self.entrenado = True
        self.ultimo_indice = len(datos_historicos) - 1
        self.ultimas_ventas = datos_historicos[-2:] if len(datos_historicos) >= 2 else datos_historicos
    
    def predecir(self, n_meses, ultimo_mes_str):
        """
        Predice ventas e ingresos para los próximos n meses.
        
        Args:
            n_meses: Número de meses a predecir
            ultimo_mes_str: Fecha del último mes en formato 'YYYY-MM'
        
        Returns:
            Lista de predicciones con formato: {'mes', 'ventas_predichas', 'ingresos_predichos', 'confianza'}
        """
        if not self.entrenado:
            raise ValueError("El modelo debe ser entrenado antes de predecir")
        
        predicciones = []
        ultimo_mes = datetime.strptime(ultimo_mes_str, '%Y-%m')
        
        # Mantener historial de predicciones recientes para features
        ventas_recientes = [v['ventas'] for v in self.ultimas_ventas]
        ingresos_recientes = [v['ingresos'] for v in self.ultimas_ventas]
        
        for i in range(n_meses):
            # Calcular fecha futura
            fecha_futura = ultimo_mes + timedelta(days=32 * (i + 1))
            fecha_futura = fecha_futura.replace(day=1)
            mes_del_anio = fecha_futura.month
            
            # Construir features para predicción
            indice_temporal = self.ultimo_indice + i + 1
            
            features = [
                indice_temporal,
                mes_del_anio,
                np.sin(2 * np.pi * mes_del_anio / 12),
                np.cos(2 * np.pi * mes_del_anio / 12),
                ventas_recientes[-1] if ventas_recientes else 0,
                ingresos_recientes[-1] if ingresos_recientes else 0,
                ventas_recientes[-2] if len(ventas_recientes) >= 2 else 0
            ]
            
            X_pred = np.array([features])
            X_pred_scaled = self.scaler.transform(X_pred)
            
            # Realizar predicción
            venta_predicha = max(0, self.modelo_ventas.predict(X_pred_scaled)[0])
            ingreso_predicho = max(0, self.modelo_ingresos.predict(X_pred_scaled)[0])
            
            # Actualizar historial reciente para siguiente predicción
            ventas_recientes.append(venta_predicha)
            ingresos_recientes.append(ingreso_predicho)
            if len(ventas_recientes) > 2:
                ventas_recientes.pop(0)
                ingresos_recientes.pop(0)
            
            predicciones.append({
                'mes': fecha_futura.strftime('%Y-%m'),
                'mes_nombre': fecha_futura.strftime('%B %Y'),
                'ventas_predichas': round(venta_predicha),
                'ingresos_predichos': round(ingreso_predicho, 2),
                'confianza': self._calcular_confianza_rf(i)
            })
        
        return predicciones
    
    def obtener_importancia_features(self):
        """
        Retorna la importancia de cada característica en el modelo.
        """
        if not self.entrenado:
            return None
        
        feature_names = [
            'Índice Temporal',
            'Mes del Año',
            'Estacionalidad (Seno)',
            'Estacionalidad (Coseno)',
            'Ventas Mes Anterior',
            'Ingresos Mes Anterior',
            'Ventas 2 Meses Atrás'
        ]
        
        importancias = self.modelo_ventas.feature_importances_
        
        return [
            {
                'feature': nombre,
                'importancia': round(float(imp) * 100, 2)
            }
            for nombre, imp in zip(feature_names, importancias)
        ]
    
    def evaluar_precision(self, datos_test):
        """
        Evalúa la precisión del modelo con datos de prueba.
        
        Args:
            datos_test: Lista de datos reales para comparar
        
        Returns:
            Métricas de evaluación (MAE, RMSE)
        """
        if not self.entrenado or len(datos_test) == 0:
            return None
        
        errores_ventas = []
        errores_ingresos = []
        
        for i, dato_real in enumerate(datos_test):
            # Construir features similares al entrenamiento
            mes_del_anio = datetime.strptime(dato_real['mes'], '%Y-%m').month
            indice = self.ultimo_indice + i + 1
            
            features = [
                indice,
                mes_del_anio,
                np.sin(2 * np.pi * mes_del_anio / 12),
                np.cos(2 * np.pi * mes_del_anio / 12),
                0, 0, 0  # Simplificado para evaluación
            ]
            
            X_test = np.array([features])
            X_test_scaled = self.scaler.transform(X_test)
            
            venta_pred = self.modelo_ventas.predict(X_test_scaled)[0]
            ingreso_pred = self.modelo_ingresos.predict(X_test_scaled)[0]
            
            errores_ventas.append(abs(dato_real['ventas'] - venta_pred))
            errores_ingresos.append(abs(dato_real['ingresos'] - ingreso_pred))
        
        mae_ventas = np.mean(errores_ventas)
        mae_ingresos = np.mean(errores_ingresos)
        rmse_ventas = np.sqrt(np.mean(np.square(errores_ventas)))
        rmse_ingresos = np.sqrt(np.mean(np.square(errores_ingresos)))
        
        return {
            'ventas': {
                'mae': round(mae_ventas, 2),
                'rmse': round(rmse_ventas, 2)
            },
            'ingresos': {
                'mae': round(mae_ingresos, 2),
                'rmse': round(rmse_ingresos, 2)
            }
        }
    
    def _calcular_confianza_rf(self, indice_prediccion):
        """
        Calcula el nivel de confianza basado en la distancia de la predicción.
        """
        if indice_prediccion < 3:
            return 'alta'
        elif indice_prediccion < 6:
            return 'media'
        else:
            return 'baja'


class ModeloPrediccionProductos:
    """
    Modelo de Random Forest para predecir demanda de productos
    """
    
    def __init__(self):
        self.modelo = RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            random_state=42
        )
        self.entrenado = False
    
    def entrenar(self, datos_productos):
        """
        Entrena el modelo con datos históricos de productos.
        
        Args:
            datos_productos: Lista de diccionarios con datos de ventas por producto
        """
        if len(datos_productos) < 5:
            raise ValueError("Se necesitan al menos 5 productos con datos")
        
        X = []
        y = []
        
        for producto in datos_productos:
            features = [
                producto['total_vendido'],
                producto['frecuencia_ventas'],
                producto['ingreso_total'] / 1000,  # Normalizado
                producto['dias_en_catalogo'] if 'dias_en_catalogo' in producto else 365
            ]
            
            X.append(features)
            y.append(producto['total_vendido'])  # Predecir ventas futuras
        
        X = np.array(X)
        y = np.array(y)
        
        self.modelo.fit(X, y)
        self.entrenado = True
    
    def predecir_demanda(self, producto_features):
        """
        Predice la demanda futura de un producto.
        """
        if not self.entrenado:
            raise ValueError("El modelo debe ser entrenado antes de predecir")
        
        X_pred = np.array([producto_features])
        demanda_predicha = self.modelo.predict(X_pred)[0]
        
        return max(0, round(demanda_predicha))
