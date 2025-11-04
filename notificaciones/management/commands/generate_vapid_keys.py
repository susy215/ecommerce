"""
Management command para generar claves VAPID para notificaciones push.
Uso: python manage.py generate_vapid_keys
"""
from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import base64


class Command(BaseCommand):
    help = 'Genera claves VAPID para notificaciones push (Web Push)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email para las claims VAPID (ej: admin@tudominio.com)'
        )
    
    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write('Generando claves VAPID...\n')
        
        try:
            # Generar clave privada usando curva elíptica P-256 (SECP256R1)
            private_key = ec.generate_private_key(
                ec.SECP256R1(),  # ← Paréntesis necesarios para instanciar
                default_backend()
            )
            
            # Obtener clave pública
            public_key = private_key.public_key()
            
            # Serializar claves en formato raw (sin comprimir para la pública)
            private_bytes = private_key.private_numbers().private_value.to_bytes(32, byteorder='big')
            
            # Para la clave pública: X e Y coordinates (32 bytes cada una)
            public_numbers = public_key.public_numbers()
            x = public_numbers.x.to_bytes(32, byteorder='big')
            y = public_numbers.y.to_bytes(32, byteorder='big')
            
            # Formato: 0x04 + X + Y (uncompressed point)
            public_bytes = b'\x04' + x + y
            
            # Convertir a base64 URL-safe (VAPID usa este formato)
            private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
            public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
            
            self.stdout.write(self.style.SUCCESS('\n✅ Claves VAPID generadas exitosamente!\n'))
            self.stdout.write('Agrega estas líneas a tu archivo .env:\n')
            self.stdout.write('-' * 80 + '\n')
            self.stdout.write(f'VAPID_PRIVATE_KEY={private_key_b64}\n')
            self.stdout.write(f'VAPID_PUBLIC_KEY={public_key_b64}\n')
            self.stdout.write(f'VAPID_ADMIN_EMAIL={email}\n')
            self.stdout.write('-' * 80 + '\n')
            
            self.stdout.write('\n📝 Configuración en settings.py (ya está lista):\n')
            self.stdout.write('''
# Notificaciones Push (VAPID)
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {
    "sub": f"mailto:{os.environ.get('VAPID_ADMIN_EMAIL', 'admin@smartsales365.com')}"
}
            ''')
            
            self.stdout.write('\n⚠️  IMPORTANTE:')
            self.stdout.write('  - La clave PRIVADA debe mantenerse SECRETA')
            self.stdout.write('  - La clave PÚBLICA se comparte con el frontend')
            self.stdout.write('  - NUNCA subas las claves a Git (usa .env)')
            self.stdout.write('  - En producción, usa claves diferentes\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error al generar claves: {str(e)}\n'))
            raise

