"""
Script rápido para enviar notificación a superadmin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.contrib.auth.models import User
from perfiles.fcm_service import send_push_to_user
from perfiles.models_device_token import DeviceToken

print("🔔 Enviando notificación a superadmin...")

try:
    user = User.objects.get(username='jha')
    tokens = DeviceToken.objects.filter(user=user, is_active=True)
    
    print(f"📱 Dispositivos: {tokens.count()}")
    for token in tokens:
        print(f"   - {token.platform}: {token.token[:50]}...")
    
    resultado = send_push_to_user(
        user=user,
        title="🎉 ¡Prueba de notificación!",
        body="Si ves esto, las notificaciones están funcionando perfectamente 🚀",
        data={
            'type': 'test',
            'screen': '/perfil'
        }
    )
    
    print(f"\n📊 Resultados:")
    print(f"   Total: {resultado['total']}")
    print(f"   ✅ Exitosos: {resultado['successful']}")
    print(f"   ❌ Fallidos: {resultado['failed']}")
    
    if resultado['errors']:
        print(f"\n⚠️ Errores:")
        for error in resultado['errors']:
            print(f"   - {error}")
    
    if resultado['successful'] > 0:
        print("\n✅ ¡NOTIFICACIÓN ENVIADA! Revisa tu dispositivo 📱")
    else:
        print("\n❌ No se pudo enviar")
        
except User.DoesNotExist:
    print("❌ Usuario 'superadmin' no encontrado")
except Exception as e:
    print(f"❌ Error: {e}")
