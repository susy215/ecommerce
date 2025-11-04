"""
Comando para poblar toda la base de datos con datos de prueba
Usuarios: admin/admin, vendedor1/vendedor1, cliente1/cliente1, cliente2/cliente2
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de prueba completos y coherentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los datos antes de poblar',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('⚠️  Eliminando datos existentes...'))
            self.clear_data()

        self.stdout.write(self.style.HTTP_INFO('🌱 Poblando base de datos...\n'))

        try:
            with transaction.atomic():
                # 1. Crear usuarios
                self.stdout.write('👥 Creando usuarios...')
                usuarios = self.crear_usuarios()
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(usuarios)} usuarios creados'))

                # 2. Crear categorías
                self.stdout.write('\n📁 Creando categorías...')
                categorias = self.crear_categorias()
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(categorias)} categorías creadas'))

                # 3. Crear productos
                self.stdout.write('\n📦 Creando productos...')
                productos = self.crear_productos(categorias)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(productos)} productos creados'))

                # 4. Crear clientes
                self.stdout.write('\n👤 Creando clientes...')
                clientes = self.crear_clientes(usuarios)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(clientes)} clientes creados'))

                # 5. Crear promociones
                self.stdout.write('\n🎁 Creando promociones...')
                promociones = self.crear_promociones()
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(promociones)} promociones creadas'))

                # 6. Crear compras
                self.stdout.write('\n🛒 Creando compras...')
                compras = self.crear_compras(clientes, productos, promociones)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {len(compras)} compras creadas'))

                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.SUCCESS('\n✅ Base de datos poblada exitosamente!\n'))
                self.mostrar_credenciales()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
            raise

    def clear_data(self):
        """Elimina todos los datos de prueba"""
        from compra.models import Compra, CompraItem
        from clientes.models import Cliente
        from productos.models import Producto, Categoria
        
        CompraItem.objects.all().delete()
        Compra.objects.all().delete()
        Cliente.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        Usuario.objects.filter(is_superuser=False).delete()

    def crear_usuarios(self):
        """Crea usuarios de prueba con credenciales fáciles"""
        usuarios = []

        # Admin
        admin, created = Usuario.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartsales.com',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'rol': 'admin',
                'telefono': '555-0000',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin')
            admin.save()
        usuarios.append(admin)

        # Vendedores
        for i in range(1, 3):
            vendedor, created = Usuario.objects.get_or_create(
                username=f'vendedor{i}',
                defaults={
                    'email': f'vendedor{i}@smartsales.com',
                    'first_name': f'Vendedor',
                    'last_name': f'Número {i}',
                    'rol': 'vendedor',
                    'telefono': f'555-100{i}',
                    'is_staff': True,
                }
            )
            if created:
                vendedor.set_password(f'vendedor{i}')
                vendedor.save()
            usuarios.append(vendedor)

        # Clientes
        clientes_data = [
            ('cliente1', 'Juan', 'Pérez', '555-2001'),
            ('cliente2', 'María', 'García', '555-2002'),
            ('cliente3', 'Pedro', 'López', '555-2003'),
            ('cliente4', 'Ana', 'Martínez', '555-2004'),
            ('cliente5', 'Carlos', 'Rodríguez', '555-2005'),
        ]

        for username, nombre, apellido, telefono in clientes_data:
            cliente, created = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@email.com',
                    'first_name': nombre,
                    'last_name': apellido,
                    'rol': 'cliente',
                    'telefono': telefono,
                }
            )
            if created:
                cliente.set_password(username)
                cliente.save()
            usuarios.append(cliente)

        return usuarios

    def crear_categorias(self):
        """Crea categorías de productos"""
        from productos.models import Categoria

        categorias_data = [
            ('Electrónica', 'electronica'),
            ('Ropa', 'ropa'),
            ('Hogar', 'hogar'),
            ('Deportes', 'deportes'),
            ('Libros', 'libros'),
            ('Juguetes', 'juguetes'),
            ('Alimentos', 'alimentos'),
        ]

        categorias = []
        for nombre, slug in categorias_data:
            cat, _ = Categoria.objects.get_or_create(
                slug=slug,
                defaults={'nombre': nombre}
            )
            categorias.append(cat)

        return categorias

    def crear_productos(self, categorias):
        """Crea productos de prueba"""
        from productos.models import Producto

        productos_data = [
            # Electrónica
            ('LAPTOP001', 'Laptop HP 15"', 'Laptop HP con 8GB RAM y 256GB SSD', 850.00, 15, 'electronica'),
            ('MOUSE001', 'Mouse Inalámbrico', 'Mouse ergonómico inalámbrico', 25.00, 50, 'electronica'),
            ('TECLADO001', 'Teclado Mecánico', 'Teclado mecánico RGB', 75.00, 30, 'electronica'),
            ('AUDIFONOS001', 'Audífonos Bluetooth', 'Audífonos con cancelación de ruido', 120.00, 25, 'electronica'),
            
            # Ropa
            ('CAMISA001', 'Camisa Casual', 'Camisa de algodón talla M', 35.00, 40, 'ropa'),
            ('PANTALON001', 'Pantalón Jean', 'Pantalón jean azul talla 32', 45.00, 35, 'ropa'),
            ('ZAPATOS001', 'Zapatos Deportivos', 'Zapatos para correr talla 42', 80.00, 20, 'ropa'),
            
            # Hogar
            ('SILLA001', 'Silla Oficina', 'Silla ergonómica para oficina', 150.00, 10, 'hogar'),
            ('LAMPARA001', 'Lámpara LED', 'Lámpara de escritorio LED', 30.00, 25, 'hogar'),
            ('ESCRITORIO001', 'Escritorio Moderno', 'Escritorio de madera 120x60cm', 200.00, 8, 'hogar'),
            
            # Deportes
            ('BALON001', 'Balón Fútbol', 'Balón profesional No. 5', 25.00, 30, 'deportes'),
            ('PESAS001', 'Set de Pesas', 'Pesas ajustables 5-20kg', 85.00, 15, 'deportes'),
            ('YOGA001', 'Mat de Yoga', 'Colchoneta antideslizante', 20.00, 40, 'deportes'),
            
            # Libros
            ('LIBRO001', 'Python para Todos', 'Libro de programación en Python', 35.00, 50, 'libros'),
            ('LIBRO002', 'Django Avanzado', 'Desarrollo web con Django', 45.00, 30, 'libros'),
            
            # Juguetes
            ('JUGUETE001', 'LEGO Classic', 'Set de construcción 500 piezas', 50.00, 20, 'juguetes'),
            ('JUGUETE002', 'Puzzle 1000 pzs', 'Puzzle de paisaje', 20.00, 25, 'juguetes'),
            
            # Alimentos
            ('CAFE001', 'Café Premium', 'Café molido 500g', 12.00, 100, 'alimentos'),
            ('TE001', 'Té Verde Orgánico', 'Caja con 25 sobres', 8.00, 80, 'alimentos'),
            ('SNACK001', 'Mix de Frutos Secos', 'Mezcla 250g', 6.00, 60, 'alimentos'),
        ]

        # Crear diccionario de categorías por slug
        cats_dict = {cat.slug: cat for cat in categorias}

        productos = []
        for sku, nombre, desc, precio, stock, cat_slug in productos_data:
            prod, _ = Producto.objects.get_or_create(
                sku=sku,
                defaults={
                    'nombre': nombre,
                    'descripcion': desc,
                    'precio': Decimal(str(precio)),
                    'stock': stock,
                    'activo': True,
                    'categoria': cats_dict.get(cat_slug),
                }
            )
            productos.append(prod)

        return productos

    def crear_clientes(self, usuarios):
        """Crea perfiles de clientes"""
        from clientes.models import Cliente

        clientes = []
        clientes_usuarios = Usuario.objects.filter(rol='cliente')
        vendedores = Usuario.objects.filter(rol='vendedor')

        direcciones = [
            'Av. Principal 123, Ciudad',
            'Calle Comercio 456, Centro',
            'Av. Libertad 789, Norte',
            'Calle 10 #234, Sur',
            'Av. Central 567, Este',
        ]

        for i, usuario in enumerate(clientes_usuarios):
            vendedor_asignado = vendedores[i % len(vendedores)] if vendedores else None
            
            cliente, _ = Cliente.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'nombre': usuario.get_full_name(),
                    'email': usuario.email,
                    'telefono': usuario.telefono,
                    'direccion': direcciones[i % len(direcciones)],
                    'asignado_a': vendedor_asignado,
                }
            )
            clientes.append(cliente)

        return clientes

    def crear_promociones(self):
        """Crea promociones de prueba"""
        from promociones.models import Promocion
        
        promociones = []
        ahora = timezone.now()
        
        promociones_data = [
            {
                'codigo': 'VERANO2025',
                'nombre': 'Descuento de Verano',
                'descripcion': '20% de descuento en toda la tienda',
                'tipo_descuento': 'porcentaje',
                'valor_descuento': Decimal('20.00'),
                'descuento_maximo': Decimal('100.00'),
                'monto_minimo': Decimal('50.00'),
                'fecha_inicio': ahora - timedelta(days=10),
                'fecha_fin': ahora + timedelta(days=50),
                'usos_maximos': 100,
            },
            {
                'codigo': 'BIENVENIDA',
                'nombre': 'Bienvenida',
                'descripcion': '$15 de descuento en tu primera compra',
                'tipo_descuento': 'monto',
                'valor_descuento': Decimal('15.00'),
                'monto_minimo': Decimal('30.00'),
                'fecha_inicio': ahora - timedelta(days=30),
                'fecha_fin': None,
                'usos_maximos': None,
            },
            {
                'codigo': 'BLACK50',
                'nombre': 'Black Friday',
                'descripcion': '50% de descuento',
                'tipo_descuento': 'porcentaje',
                'valor_descuento': Decimal('50.00'),
                'descuento_maximo': Decimal('200.00'),
                'monto_minimo': Decimal('100.00'),
                'fecha_inicio': ahora - timedelta(days=5),
                'fecha_fin': ahora + timedelta(days=2),
                'usos_maximos': 50,
            },
            {
                'codigo': 'ENVIOGRATIS',
                'nombre': 'Envío Gratis',
                'descripcion': '$10 de descuento en envío',
                'tipo_descuento': 'monto',
                'valor_descuento': Decimal('10.00'),
                'monto_minimo': Decimal('25.00'),
                'fecha_inicio': ahora - timedelta(days=15),
                'fecha_fin': ahora + timedelta(days=30),
                'usos_maximos': 200,
            },
        ]
        
        for data in promociones_data:
            promo, _ = Promocion.objects.get_or_create(
                codigo=data['codigo'],
                defaults=data
            )
            promociones.append(promo)
        
        return promociones

    def crear_compras(self, clientes, productos, promociones):
        """Crea compras de prueba con diferentes estados"""
        from compra.models import Compra, CompraItem

        compras = []
        
        # Crear 10 compras variadas
        for i in range(10):
            # Seleccionar cliente aleatorio
            cliente = random.choice(clientes)
            
            # Crear compra
            fecha = timezone.now() - timedelta(days=random.randint(0, 30))
            compra = Compra.objects.create(
                cliente=cliente,
                observaciones=f'Pedido de prueba #{i+1}',
            )
            compra.fecha = fecha
            compra.save()

            # Agregar items (2-5 productos aleatorios)
            num_items = random.randint(2, 5)
            productos_compra = random.sample(productos, min(num_items, len(productos)))

            for producto in productos_compra:
                cantidad = random.randint(1, 3)
                # Verificar si hay stock
                if producto.stock >= cantidad:
                    CompraItem.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                        subtotal=producto.precio * cantidad
                    )
                    # Reducir stock
                    producto.stock -= cantidad
                    producto.save()

            # Recalcular total
            compra.recalc_total()
            
            # 30% de las compras tienen promoción
            if random.random() < 0.3 and promociones:
                promo = random.choice(promociones)
                if promo.esta_vigente():
                    compra.aplicar_promocion(promo)

            # 70% de las compras están pagadas
            if random.random() < 0.7:
                compra.pagado_en = fecha + timedelta(hours=random.randint(1, 48))
                compra.pago_referencia = f'PAY-{random.randint(1000, 9999)}'
                compra.save()

            compras.append(compra)

        return compras

    def mostrar_credenciales(self):
        """Muestra las credenciales de acceso"""
        self.stdout.write(self.style.HTTP_INFO('🔑 CREDENCIALES DE ACCESO:\n'))
        
        credenciales = [
            ('Admin', 'admin', 'admin', 'Acceso total al sistema'),
            ('Vendedor 1', 'vendedor1', 'vendedor1', 'Gestión de ventas'),
            ('Vendedor 2', 'vendedor2', 'vendedor2', 'Gestión de ventas'),
            ('Cliente 1', 'cliente1', 'cliente1', 'Compras'),
            ('Cliente 2', 'cliente2', 'cliente2', 'Compras'),
            ('Cliente 3', 'cliente3', 'cliente3', 'Compras'),
            ('Cliente 4', 'cliente4', 'cliente4', 'Compras'),
            ('Cliente 5', 'cliente5', 'cliente5', 'Compras'),
        ]

        self.stdout.write('  ' + '-'*70)
        self.stdout.write(f'  {"Rol":<15} {"Usuario":<15} {"Contraseña":<15} {"Permisos":<20}')
        self.stdout.write('  ' + '-'*70)
        
        for rol, usuario, password, permisos in credenciales:
            self.stdout.write(f'  {rol:<15} {usuario:<15} {password:<15} {permisos:<20}')
        
        self.stdout.write('  ' + '-'*70)
        self.stdout.write('\n💡 Usa: python manage.py seed_all --clear  para reiniciar datos\n')
