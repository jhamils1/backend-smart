import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.contrib.auth.models import User, Group

def asignar_grupo_a_clientes():
    """
    Asigna el grupo 'cliente' (id=2) a todos los usuarios que empiezan con 'cliente'
    """
    try:
        # Obtener el grupo de cliente (id=2)
        grupo_cliente = Group.objects.get(id=2)
        print(f"✅ Grupo encontrado: {grupo_cliente.name}\n")
        
        # Obtener todos los usuarios que empiezan con 'cliente'
        usuarios_cliente = User.objects.filter(username__startswith='cliente')
        total_usuarios = usuarios_cliente.count()
        
        print(f"📊 Total de usuarios encontrados: {total_usuarios}\n")
        
        actualizados = 0
        ya_tenian_grupo = 0
        
        for usuario in usuarios_cliente:
            # Verificar si ya tiene el grupo
            if grupo_cliente in usuario.groups.all():
                print(f"⚠️  {usuario.username} ya tiene el grupo '{grupo_cliente.name}'")
                ya_tenian_grupo += 1
            else:
                # Asignar el grupo
                usuario.groups.add(grupo_cliente)
                print(f"✅ {usuario.username} asignado al grupo '{grupo_cliente.name}'")
                actualizados += 1
        
        # Resumen
        print("\n" + "="*60)
        print("RESUMEN DE ACTUALIZACIÓN")
        print("="*60)
        print(f"📊 Total usuarios procesados: {total_usuarios}")
        print(f"✅ Usuarios actualizados: {actualizados}")
        print(f"⚠️  Ya tenían el grupo: {ya_tenian_grupo}")
        print("="*60)
        
    except Group.DoesNotExist:
        print("❌ Error: No se encontró el grupo con id=2 (cliente)")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando asignación de grupo a clientes...\n")
    asignar_grupo_a_clientes()
    print("\n✅ Proceso completado.")
