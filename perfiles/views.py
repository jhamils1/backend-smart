from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Cliente, Empleado
from .serializers import ClienteSerializer, EmpleadoSerializer

# Create your views here.

class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Clientes.
    - Listar con filtros y búsqueda
    - Borrado lógico
    """
    queryset = Cliente.objects.filter(estado='activo').order_by('nombre', 'apellido')
    serializer_class = ClienteSerializer

    def perform_destroy(self, instance):
        instance.estado = 'inactivo'
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmpleadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Empleados.
    - Listar con filtros y búsqueda
    - Borrado lógico
    """
    queryset = Empleado.objects.filter(estado='Activo').order_by('nombre', 'apellido')
    serializer_class = EmpleadoSerializer

    def perform_destroy(self, instance):
        instance.estado = 'Inactivo'
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
