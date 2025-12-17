# Script para instalar las dependencias de Machine Learning
import subprocess
import sys

def instalar_dependencias():
    """Instala las dependencias necesarias para el modelo de predicción"""
    dependencias = [
        'scikit-learn',
        'numpy'
    ]
    
    print("Instalando dependencias de Machine Learning...")
    for paquete in dependencias:
        print(f"\nInstalando {paquete}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', paquete])
            print(f"✓ {paquete} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error al instalar {paquete}: {e}")
            return False
    
    print("\n¡Todas las dependencias instaladas correctamente!")
    return True

if __name__ == '__main__':
    instalar_dependencias()
