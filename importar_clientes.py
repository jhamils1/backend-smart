import os
import django
import csv
from django.contrib.auth.hashers import make_password

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_exa2.settings')
django.setup()

from django.contrib.auth.models import User, Group
from perfiles.models import Cliente

def importar_clientes_desde_csv(archivo_csv):
    """
    Importa usuarios y clientes desde un archivo CSV
    """
    usuarios_creados = 0
    clientes_creados = 0
    errores = []
    
    # Obtener el grupo de cliente (id=2)
    try:
        grupo_cliente = Group.objects.get(id=2)
        print(f"✅ Grupo encontrado: {grupo_cliente.name}\n")
    except Group.DoesNotExist:
        print("❌ Error: No se encontró el grupo con id=2 (cliente)")
        return

    try:
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Verificar si el usuario ya existe
                    if User.objects.filter(username=row['username']).exists():
                        print(f"⚠️  Usuario {row['username']} ya existe, omitiendo...")
                        continue
                    
                    # Crear el usuario
                    usuario = User.objects.create(
                        username=row['username'],
                        email=row['email'],
                        password=make_password(row['password']),
                        first_name=row['nombre'],
                        last_name=row['apellido']
                    )
                    
                    # Asignar al grupo de cliente
                    usuario.groups.add(grupo_cliente)
                    
                    usuarios_creados += 1
                    print(f"✅ Usuario creado: {usuario.username} (grupo: {grupo_cliente.name})")
                    
                    # Crear el cliente relacionado
                    cliente = Cliente.objects.create(
                        usuario=usuario,
                        nombre=row['nombre'],
                        apellido=row['apellido'],
                        ci=row['ci'],
                        direccion=row['direccion'],
                        sexo=row['sexo'],
                        telefono=row['telefono'],
                        estado='activo'
                    )
                    clientes_creados += 1
                    print(f"✅ Cliente creado: {cliente.nombre} {cliente.apellido}")
                    
                except Exception as e:
                    error_msg = f"Error al procesar {row.get('username', 'desconocido')}: {str(e)}"
                    errores.append(error_msg)
                    print(f"❌ {error_msg}")
                    continue
        
        # Resumen
        print("\n" + "="*60)
        print("RESUMEN DE IMPORTACIÓN")
        print("="*60)
        print(f"✅ Usuarios creados: {usuarios_creados}")
        print(f"✅ Clientes creados: {clientes_creados}")
        if errores:
            print(f"❌ Errores: {len(errores)}")
            for error in errores:
                print(f"   - {error}")
        print("="*60)
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {archivo_csv}")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    archivo = 'clientes_usuarios.csv'
    print(f"🚀 Iniciando importación desde {archivo}...\n")
    importar_clientes_desde_csv(archivo)
    print("\n✅ Proceso completado.")
