import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.contrib.auth.models import User
from perfiles.models_device_token import DeviceToken

print("🔓 Activando token del administrador...")

try:
    user = User.objects.get(username='jha')
    tokens = DeviceToken.objects.filter(user=user)
    
    if tokens.exists():
        token = tokens.first()
        token.is_active = True
        token.save()
        
        print(f"✅ Token activado para: {user.username}")
        print(f"   Token: {token.token[:60]}...")
        print(f"   Platform: {token.platform}")
        print(f"   Activo: {token.is_active}")
    else:
        print(f"❌ No hay tokens registrados para {user.username}")
        print("   El administrador debe iniciar sesión en la app móvil primero")
        
except User.DoesNotExist:
    print("❌ Usuario 'jha' no encontrado")
except Exception as e:
    print(f"❌ Error: {e}")
