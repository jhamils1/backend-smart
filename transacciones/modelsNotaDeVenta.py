from django.db import models
from decimal import Decimal
from perfiles.models import Cliente


class NotaDeVenta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)
    numero_comprobante = models.CharField(max_length=50, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notas_venta')

    def __str__(self):
        return f"Nota de Venta {self.numero_comprobante} - {self.cliente.nombre} ({self.estado})"

    class Meta:
        verbose_name = 'Nota de Venta'
        verbose_name_plural = 'Notas de Venta'
        ordering = ['-fecha']

    def calcular_totales(self):
        """Calcula el subtotal y total de la nota de venta"""
        # Calcular subtotal desde los detalles
        subtotal = sum(detalle.subtotal for detalle in self.detalles.all())
        self.subtotal = Decimal(str(subtotal)).quantize(Decimal('0.01'))
        
        # El total es igual al subtotal (sin impuestos ni descuentos)
        self.total = self.subtotal
        self.save()

    def anular(self):
        """Anula la nota de venta"""
        self.estado = 'anulada'
        self.save()

    def marcar_pagada(self):
        """Marca la nota de venta como pagada y envía notificación push"""
        self.estado = 'pagada'
        self.save()
        
        # Enviar notificación push al cliente y administradores
        self._enviar_notificacion_compra()
    
    def _enviar_notificacion_compra(self):
        """Envía notificación push al cliente y a los administradores sobre la compra"""
        try:
            from perfiles.fcm_service import FCMService
            from perfiles.models_device_token import DeviceToken
            from django.contrib.auth.models import User
            
            fcm_service = FCMService()
            
            # 1️⃣ NOTIFICACIÓN AL CLIENTE
            if self.cliente and self.cliente.usuario:
                # Obtener tokens activos del cliente
                tokens_cliente = DeviceToken.objects.filter(
                    user=self.cliente.usuario,
                    is_active=True
                )
                
                if tokens_cliente.exists():
                    # Preparar el mensaje para el cliente
                    titulo_cliente = "¡Compra Exitosa! 🎉"
                    mensaje_cliente = f"Tu orden {self.numero_comprobante} por ${self.total} ha sido procesada exitosamente."
                    
                    data_cliente = {
                        'tipo': 'compra_cliente',
                        'nota_venta_id': str(self.id),
                        'numero_comprobante': self.numero_comprobante,
                        'total': str(self.total),
                        'route': '/mis-comprobantes'
                    }
                    
                    # Enviar a cada token del cliente
                    for device_token in tokens_cliente:
                        try:
                            resultado = fcm_service.send_push_notification(
                                token=device_token.token,
                                title=titulo_cliente,
                                body=mensaje_cliente,
                                data=data_cliente
                            )
                            
                            if resultado.get('success'):
                                print(f"✅ Notificación enviada al cliente {self.cliente.usuario.username} ({device_token.platform})")
                            else:
                                print(f"❌ Error enviando notificación al cliente: {resultado.get('error')}")
                                
                                # Si el token es inválido, desactivarlo
                                if 'invalid' in resultado.get('error', '').lower() or 'not-registered' in resultado.get('error', '').lower():
                                    device_token.is_active = False
                                    device_token.save()
                                    print(f"⚠️ Token del cliente desactivado: {device_token.token[:20]}...")
                                    
                        except Exception as e:
                            print(f"❌ Error enviando notificación al cliente: {e}")
                else:
                    print(f"⚠️ No hay tokens FCM registrados para el cliente {self.cliente.usuario.username}")
            
            # 2️⃣ NOTIFICACIÓN A LOS ADMINISTRADORES
            # Obtener todos los usuarios administradores y superusuarios
            admins = User.objects.filter(
                models.Q(is_superuser=True) | models.Q(is_staff=True)
            ).distinct()
            
            if admins.exists():
                # Preparar el mensaje para administradores
                cliente_nombre = self.cliente.nombre if self.cliente else "Cliente desconocido"
                titulo_admin = "Nueva Compra Registrada 💰"
                mensaje_admin = f"{cliente_nombre} realizó una compra por ${self.total} (Orden: {self.numero_comprobante})"
                
                data_admin = {
                    'tipo': 'compra_admin',
                    'nota_venta_id': str(self.id),
                    'numero_comprobante': self.numero_comprobante,
                    'total': str(self.total),
                    'cliente': cliente_nombre,
                    'route': '/historial-ventas'
                }
                
                # Enviar a cada administrador
                for admin in admins:
                    tokens_admin = DeviceToken.objects.filter(
                        user=admin,
                        is_active=True
                    )
                    
                    for device_token in tokens_admin:
                        try:
                            resultado = fcm_service.send_push_notification(
                                token=device_token.token,
                                title=titulo_admin,
                                body=mensaje_admin,
                                data=data_admin
                            )
                            
                            if resultado.get('success'):
                                print(f"✅ Notificación enviada al administrador {admin.username} ({device_token.platform})")
                            else:
                                print(f"❌ Error enviando notificación al admin: {resultado.get('error')}")
                                
                                # Si el token es inválido, desactivarlo
                                if 'invalid' in resultado.get('error', '').lower() or 'not-registered' in resultado.get('error', '').lower():
                                    device_token.is_active = False
                                    device_token.save()
                                    print(f"⚠️ Token del admin desactivado: {device_token.token[:20]}...")
                                    
                        except Exception as e:
                            print(f"❌ Error enviando notificación al admin {admin.username}: {e}")
            else:
                print("⚠️ No hay administradores registrados en el sistema")
                    
        except Exception as e:
            print(f"❌ Error en _enviar_notificacion_compra: {e}")
    
    def validar_stock_disponible(self):
        """
        Valida que haya stock suficiente para todos los productos en la nota de venta.
        Retorna una tupla (es_valido, mensaje_error)
        """
        productos_sin_stock = []
        
        for detalle in self.detalles.all():
            if detalle.producto.stock < detalle.cantidad:
                productos_sin_stock.append({
                    'producto': detalle.producto.nombre,
                    'stock_actual': detalle.producto.stock,
                    'cantidad_requerida': detalle.cantidad
                })
        
        if productos_sin_stock:
            mensaje = "Stock insuficiente para los siguientes productos: "
            mensaje += ", ".join([
                f"{p['producto']} (disponible: {p['stock_actual']}, requerido: {p['cantidad_requerida']})"
                for p in productos_sin_stock
            ])
            return False, mensaje
        
        return True, "Stock suficiente para todos los productos"
