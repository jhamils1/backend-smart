from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReporteViewSet
from .viewsDashboard import DashboardViewSet
from .viewsPredicciones import PrediccionViewSet

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'predicciones', PrediccionViewSet, basename='prediccion')

urlpatterns = [
    path('', include(router.urls)),
]
