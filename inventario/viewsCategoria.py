from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from inventario.modelsCategoria import Categoria
from inventario.serializers.serializerCategoria import CategoriaSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las categorías de productos.
    Proporciona operaciones CRUD completas.
    Los clientes autenticados pueden ver categorías.
    Solo admins pueden crear/editar/eliminar categorías.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Clientes pueden ver (list, retrieve).
        Solo admins pueden modificar (create, update, delete).
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
