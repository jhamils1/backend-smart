from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, EmpleadoViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'empleados', EmpleadoViewSet, basename='empleado')

urlpatterns = router.urls
