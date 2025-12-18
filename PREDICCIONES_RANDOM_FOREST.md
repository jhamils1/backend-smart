# Sistema de Predicciones con Random Forest

## 📊 Descripción

Sistema de predicciones avanzado que utiliza **Random Forest** (Ensemble Learning) para predecir ventas futuras, analizar tendencias de productos y detectar productos de alta demanda.

## 🧠 Modelo de Machine Learning

### Archivo Cerebro: `ml_model.py`

Este archivo contiene dos modelos principales:

#### 1. **ModeloPrediccionVentas**
- **Algoritmo**: Random Forest Regressor
- **Estimadores**: 100 árboles de decisión
- **Features utilizados**:
  - Índice temporal
  - Mes del año
  - Estacionalidad (componentes seno/coseno)
  - Ventas del mes anterior
  - Ingresos del mes anterior
  - Ventas de 2 meses atrás

#### 2. **ModeloPrediccionProductos**
- **Algoritmo**: Random Forest Regressor
- **Estimadores**: 50 árboles de decisión
- **Features utilizados**:
  - Total vendido
  - Frecuencia de ventas
  - Ingresos generados
  - Días en catálogo

## 🎯 Endpoints Disponibles

### 1. Ventas Futuras
```
GET /api/analitica/predicciones/ventas-futuras/?meses=6
```

**Descripción**: Predice ventas e ingresos para los próximos N meses.

**Parámetros**:
- `meses` (opcional): Número de meses a predecir (default: 6)

**Respuesta**:
```json
{
  "historico": [
    {
      "mes": "2024-11",
      "ventas": 85,
      "ingresos": 45230.50
    }
  ],
  "predicciones": [
    {
      "mes": "2025-01",
      "mes_nombre": "January 2025",
      "ventas_predichas": 92,
      "ingresos_predichos": 48750.25,
      "confianza": "alta"
    }
  ],
  "modelo_info": {
    "tipo": "Random Forest Regressor",
    "algoritmo": "Ensemble Learning",
    "n_estimators": 100,
    "importancia_features": [
      {
        "feature": "Índice Temporal",
        "importancia": 35.5
      }
    ]
  }
}
```

### 2. Análisis de Tendencias
```
GET /api/analitica/predicciones/tendencias/
```

**Descripción**: Analiza productos en crecimiento o declive comparando últimos 90 días vs 90 días anteriores.

**Respuesta**:
```json
{
  "productos_en_alza": [
    {
      "nombre": "Laptop Dell XPS 15",
      "codigo": "LAP-001",
      "cantidad_reciente": 45,
      "cantidad_anterior": 30,
      "cambio_porcentual": 50.0,
      "tendencia": "alto_crecimiento"
    }
  ],
  "productos_en_baja": [...],
  "resumen": {
    "total_productos_analizados": 50,
    "productos_crecimiento": 25,
    "productos_declive": 10
  }
}
```

### 3. Productos de Alta Demanda
```
GET /api/analitica/predicciones/productos-demandados/?limite=10
```

**Descripción**: Predice qué productos tendrán mayor demanda e indica necesidad de reabastecimiento.

**Parámetros**:
- `limite` (opcional): Número de productos a retornar (default: 10)

**Respuesta**:
```json
{
  "productos_alta_demanda": [
    {
      "nombre": "iPhone 15 Pro",
      "codigo": "PHO-015",
      "stock_actual": 15,
      "ventas_historicas": 87,
      "demanda_predicha_90dias": 95,
      "score_prioridad": 92.5,
      "recomendacion": {
        "nivel": "urgente",
        "mensaje": "Stock crítico - Reabastecer inmediatamente",
        "cantidad_sugerida": 143
      }
    }
  ]
}
```

### 4. Métricas del Modelo
```
GET /api/analitica/predicciones/metricas-modelo/
```

**Descripción**: Evalúa la precisión del modelo usando validación 80-20.

**Respuesta**:
```json
{
  "metricas_precision": {
    "ventas": {
      "mae": 5.2,
      "rmse": 7.8
    },
    "ingresos": {
      "mae": 1250.45,
      "rmse": 1890.30
    }
  },
  "importancia_features": [...],
  "datos_entrenamiento": 40,
  "datos_prueba": 10
}
```

## 🚀 Instalación

### 1. Instalar dependencias
```bash
pip install scikit-learn numpy
```

O ejecutar el script:
```bash
python instalar_ml_dependencias.py
```

### 2. Verificar funcionamiento
```bash
python test_predicciones_rf.py
```

## 📈 Características del Sistema

### ✅ Ventajas del Random Forest
- **Alta precisión**: Combina múltiples árboles de decisión
- **Manejo de no-linealidad**: Captura patrones complejos
- **Resistente a outliers**: Menos sensible a datos atípicos
- **Importancia de features**: Identifica qué variables son más relevantes
- **No requiere normalización**: Funciona bien con datos sin preprocesar

### 🎯 Casos de Uso
1. **Planificación de inventario**: Saber qué productos reponer
2. **Proyección financiera**: Estimar ingresos futuros
3. **Detección de tendencias**: Identificar productos en alza/baja
4. **Optimización de stock**: Evitar quiebres o exceso de inventario

## 📊 Interpretación de Confianza

- **Alta**: Predicción a 1-3 meses (datos más confiables)
- **Media**: Predicción a 4-6 meses (buena precisión)
- **Baja**: Predicción a 6+ meses (más incertidumbre)

## 🔧 Configuración del Modelo

Los modelos pueden ajustarse modificando parámetros en `ml_model.py`:

```python
self.modelo_ventas = RandomForestRegressor(
    n_estimators=100,      # Número de árboles
    max_depth=10,          # Profundidad máxima
    random_state=42,       # Semilla para reproducibilidad
    n_jobs=-1             # Usar todos los cores del CPU
)
```

## 📝 Métricas de Evaluación

- **MAE (Mean Absolute Error)**: Error promedio absoluto
  - Interpretación: Si MAE=5, las predicciones se desvían en promedio 5 ventas
  
- **RMSE (Root Mean Squared Error)**: Penaliza errores grandes
  - Interpretación: Similar a MAE pero da más peso a errores mayores

## 🎨 Visualización Recomendada

Para el frontend, se recomienda crear:
1. **Gráfico de líneas**: Histórico vs Predicciones
2. **Gráfico de barras**: Top productos en alza/baja
3. **Tabla de recomendaciones**: Productos a reabastecer
4. **Indicadores KPI**: MAE, RMSE, precisión general

## 🔒 Seguridad

Actualmente los endpoints tienen `permission_classes = [AllowAny]` para facilitar el desarrollo.

**Para producción**, cambiar a:
```python
permission_classes = [IsAuthenticated]
```

## 📚 Referencias

- Scikit-learn RandomForestRegressor: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
- Ensemble Methods: https://scikit-learn.org/stable/modules/ensemble.html

## 🐛 Troubleshooting

### Error: "No hay suficientes datos históricos"
- Se requieren mínimo 3 meses de datos para entrenar el modelo

### Error: "No module named 'sklearn'"
- Ejecutar: `pip install scikit-learn`

### Predicciones muy diferentes a la realidad
- Verificar que hay suficientes datos históricos (mínimo 6 meses recomendado)
- Revisar métricas del modelo con `/metricas-modelo/`
- Considerar ajustar parámetros del Random Forest

## 👨‍💻 Autor

Sistema desarrollado para el proyecto backend-smart
Fecha: Diciembre 2025
