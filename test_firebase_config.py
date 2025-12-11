"""
Script para verificar si Firebase está configurado correctamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.conf import settings
import json

print("=" * 70)
print("🔍 VERIFICANDO CONFIGURACIÓN DE FIREBASE")
print("=" * 70)

# Verificar PROJECT_ID
print(f"\n📋 FIREBASE_PROJECT_ID: {settings.FIREBASE_PROJECT_ID}")

# Verificar JSON
if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
    print(f"\n✅ FIREBASE_SERVICE_ACCOUNT_JSON está configurado")
    print(f"   Longitud: {len(settings.FIREBASE_SERVICE_ACCOUNT_JSON)} caracteres")
    
    try:
        # Intentar parsear el JSON
        credentials = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        print(f"\n✅ JSON válido")
        print(f"   Project ID: {credentials.get('project_id')}")
        print(f"   Client Email: {credentials.get('client_email')}")
        print(f"   Private Key: {'Presente' if credentials.get('private_key') else 'FALTA'}")
        
        # Verificar que la private key tenga el formato correcto
        private_key = credentials.get('private_key', '')
        if private_key:
            if '-----BEGIN PRIVATE KEY-----' in private_key:
                print(f"   ✅ Private key tiene el formato correcto")
            else:
                print(f"   ❌ Private key NO tiene el formato correcto")
                print(f"   Primeros 50 caracteres: {private_key[:50]}")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Error parseando JSON: {e}")
        print(f"   Primeros 200 caracteres:")
        print(f"   {settings.FIREBASE_SERVICE_ACCOUNT_JSON[:200]}")
else:
    print(f"\n❌ FIREBASE_SERVICE_ACCOUNT_JSON NO está configurado")

# Intentar inicializar FCMService
print("\n" + "=" * 70)
print("🔥 PROBANDO INICIALIZACIÓN DE FCMService")
print("=" * 70)

try:
    from perfiles.fcm_service import FCMService
    fcm = FCMService()
    
    if fcm.credentials:
        print("\n✅ FCMService inicializado correctamente")
        print(f"   Project ID: {fcm.project_id}")
    else:
        print("\n❌ FCMService NO pudo inicializarse")
        print("   Verifica las credenciales de Firebase")
        
except Exception as e:
    print(f"\n❌ Error inicializando FCMService: {e}")

print("\n" + "=" * 70)
