"""
Comando para poblar la base de datos con datos de prueba de una tienda de electrodomésticos.
Incluye categorías, productos, usuarios, clientes y compras históricas.

Uso:
    python manage.py poblar_datos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import timedelta
import random

from productos.models import Categoria, Producto
from usuarios.models import Usuario
from clientes.models import Cliente
from compra.models import Compra, CompraItem
from promociones.models import Promocion


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba de electrodomésticos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina todos los datos existentes antes de poblar',
        )
        parser.add_argument(
            '--compras',
            type=int,
            default=100,
            help='Número de compras a generar (default: 100)',
        )
        parser.add_argument(
            '--meses',
            type=int,
            default=12,
            help='Número de meses de histórico (default: 12)',
        )
        parser.add_argument(
            '--desde',
            type=str,
            help='Fecha inicio en formato YYYY-MM-DD (opcional)',
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            # Eliminar en orden para evitar problemas de foreign keys
            from promociones.models import DevolucionProducto
            DevolucionProducto.objects.all().delete()
            CompraItem.objects.all().delete()
            Compra.objects.all().delete()
            Cliente.objects.all().delete()
            Producto.objects.all().delete()
            Categoria.objects.all().delete()
            Promocion.objects.all().delete()
            # No eliminamos usuarios para evitar problemas con el admin
            Usuario.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS('Iniciando población de datos...'))

        with transaction.atomic():
            # 1. Crear categorías
            categorias = self.crear_categorias()
            
            # 2. Crear productos
            productos = self.crear_productos(categorias)
            
            # 3. Crear usuarios
            usuarios = self.crear_usuarios()
            
            # 4. Crear clientes
            clientes = self.crear_clientes(usuarios)
            
            # 5. Crear promociones
            promociones = self.crear_promociones()
            
            # 6. Crear compras históricas
            self.crear_compras_historicas(
                clientes, 
                productos, 
                promociones,
                num_compras=options['compras'],
                meses_historico=options['meses'],
                fecha_desde=options.get('desde')
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Datos poblados exitosamente!'))
        self.stdout.write(self.style.SUCCESS('\n📋 Resumen:'))
        self.stdout.write(f'  - Categorías: {Categoria.objects.count()}')
        self.stdout.write(f'  - Productos: {Producto.objects.count()}')
        self.stdout.write(f'  - Usuarios: {Usuario.objects.count()}')
        self.stdout.write(f'  - Clientes: {Cliente.objects.count()}')
        self.stdout.write(f'  - Compras: {Compra.objects.count()}')
        self.stdout.write(f'  - Promociones: {Promocion.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n🔑 Credenciales:'))
        self.stdout.write(self.style.SUCCESS('  - Admin: admin / admin'))
        self.stdout.write(self.style.SUCCESS('  - Cliente: cliente1 / cliente1'))

    def crear_categorias(self):
        """Crea categorías de electrodomésticos"""
        self.stdout.write('Creando categorías...')
        
        categorias_data = [
            {'nombre': 'Refrigeradores', 'slug': 'refrigeradores'},
            {'nombre': 'Lavadoras', 'slug': 'lavadoras'},
            {'nombre': 'Microondas', 'slug': 'microondas'},
            {'nombre': 'Hornos', 'slug': 'hornos'},
            {'nombre': 'Televisores', 'slug': 'televisores'},
            {'nombre': 'Aires Acondicionados', 'slug': 'aires-acondicionados'},
            {'nombre': 'Aspiradoras', 'slug': 'aspiradoras'},
            {'nombre': 'Planchas', 'slug': 'planchas'},
            {'nombre': 'Licuadoras', 'slug': 'licuadoras'},
            {'nombre': 'Cafeteras', 'slug': 'cafeteras'},
        ]
        
        categorias = []
        for cat_data in categorias_data:
            categoria, created = Categoria.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'nombre': cat_data['nombre']}
            )
            categorias.append(categoria)
        
        return categorias

    def crear_productos(self, categorias):
        """Crea productos de electrodomésticos"""
        self.stdout.write('Creando productos...')
        
        productos_data = [
            # Refrigeradores
            {'sku': 'REF-001', 'nombre': 'Refrigerador Samsung 2 Puertas 500L', 'precio': 899.99, 'stock': 15, 'categoria': 'Refrigeradores', 'descripcion': 'Refrigerador de dos puertas con tecnología No Frost, capacidad de 500 litros, color plateado.'},
            {'sku': 'REF-002', 'nombre': 'Refrigerador LG Side by Side 600L', 'precio': 1299.99, 'stock': 8, 'categoria': 'Refrigeradores', 'descripcion': 'Refrigerador Side by Side con dispensador de agua y hielo, pantalla táctil.'},
            {'sku': 'REF-003', 'nombre': 'Refrigerador Mabe Compacto 280L', 'precio': 549.99, 'stock': 25, 'categoria': 'Refrigeradores', 'descripcion': 'Refrigerador compacto ideal para espacios pequeños, bajo consumo energético.'},
            
            # Lavadoras
            {'sku': 'LAV-001', 'nombre': 'Lavadora Samsung 18kg Carga Superior', 'precio': 699.99, 'stock': 12, 'categoria': 'Lavadoras', 'descripcion': 'Lavadora de carga superior con tecnología EcoBubble, 18kg de capacidad.'},
            {'sku': 'LAV-002', 'nombre': 'Lavadora LG Carga Frontal 15kg', 'precio': 899.99, 'stock': 10, 'categoria': 'Lavadoras', 'descripcion': 'Lavadora de carga frontal con motor Inverter, múltiples programas de lavado.'},
            {'sku': 'LAV-003', 'nombre': 'Lavadora Mabe Automática 12kg', 'precio': 499.99, 'stock': 20, 'categoria': 'Lavadoras', 'descripcion': 'Lavadora automática con sistema de lavado eficiente, panel digital.'},
            
            # Microondas
            {'sku': 'MIC-001', 'nombre': 'Microondas Samsung 30L con Grill', 'precio': 199.99, 'stock': 30, 'categoria': 'Microondas', 'descripcion': 'Microondas con función grill, panel digital, capacidad 30 litros.'},
            {'sku': 'MIC-002', 'nombre': 'Microondas LG 42L Inverter', 'precio': 349.99, 'stock': 18, 'categoria': 'Microondas', 'descripcion': 'Microondas con tecnología Inverter para calentamiento uniforme, 42 litros.'},
            {'sku': 'MIC-003', 'nombre': 'Microondas Panasonic 25L Básico', 'precio': 149.99, 'stock': 35, 'categoria': 'Microondas', 'descripcion': 'Microondas básico de 25 litros, fácil de usar, diseño compacto.'},
            
            # Hornos
            {'sku': 'HOR-001', 'nombre': 'Horno Eléctrico Mabe 60cm', 'precio': 599.99, 'stock': 10, 'categoria': 'Hornos', 'descripcion': 'Horno eléctrico empotrable de 60cm, función pirolítica, panel táctil.'},
            {'sku': 'HOR-002', 'nombre': 'Horno a Gas Mabe 5 Quemadores', 'precio': 449.99, 'stock': 15, 'categoria': 'Hornos', 'descripcion': 'Horno a gas con 5 quemadores, encendido automático, parrilla integrada.'},
            
            # Televisores
            {'sku': 'TV-001', 'nombre': 'Smart TV Samsung 55" 4K UHD', 'precio': 899.99, 'stock': 25, 'categoria': 'Televisores', 'descripcion': 'Smart TV 55 pulgadas con resolución 4K UHD, sistema Tizen, HDR.'},
            {'sku': 'TV-002', 'nombre': 'Smart TV LG 65" OLED', 'precio': 1599.99, 'stock': 12, 'categoria': 'Televisores', 'descripcion': 'Smart TV OLED de 65 pulgadas, tecnología OLED para negros perfectos.'},
            {'sku': 'TV-003', 'nombre': 'Smart TV Sony 43" Full HD', 'precio': 599.99, 'stock': 20, 'categoria': 'Televisores', 'descripcion': 'Smart TV 43 pulgadas Full HD, Android TV integrado, HDR.'},
            
            # Aires Acondicionados
            {'sku': 'AC-001', 'nombre': 'Aire Acondicionado Split Samsung 1.5 Ton', 'precio': 699.99, 'stock': 15, 'categoria': 'Aires Acondicionados', 'descripcion': 'Aire acondicionado split de 1.5 toneladas, tecnología Digital Inverter.'},
            {'sku': 'AC-002', 'nombre': 'Aire Acondicionado LG 2 Ton Inverter', 'precio': 899.99, 'stock': 10, 'categoria': 'Aires Acondicionados', 'descripcion': 'Aire acondicionado de 2 toneladas con compresor Inverter, bajo consumo.'},
            
            # Aspiradoras
            {'sku': 'ASP-001', 'nombre': 'Aspiradora Robot Samsung', 'precio': 399.99, 'stock': 22, 'categoria': 'Aspiradoras', 'descripcion': 'Aspiradora robot con navegación inteligente, control por app.'},
            {'sku': 'ASP-002', 'nombre': 'Aspiradora LG Sin Bolsa 5L', 'precio': 199.99, 'stock': 30, 'categoria': 'Aspiradoras', 'descripcion': 'Aspiradora sin bolsa con capacidad de 5 litros, filtro HEPA.'},
            
            # Planchas
            {'sku': 'PLA-001', 'nombre': 'Plancha a Vapor Philips', 'precio': 79.99, 'stock': 50, 'categoria': 'Planchas', 'descripcion': 'Plancha a vapor con sistema de vapor continuo, panel digital.'},
            {'sku': 'PLA-002', 'nombre': 'Plancha a Vapor Rowenta', 'precio': 99.99, 'stock': 40, 'categoria': 'Planchas', 'descripcion': 'Plancha a vapor con tecnología de microvapor, suela cerámica.'},
            
            # Licuadoras
            {'sku': 'LIC-001', 'nombre': 'Licuadora Oster 600W', 'precio': 89.99, 'stock': 45, 'categoria': 'Licuadoras', 'descripcion': 'Licuadora de 600W con vaso de vidrio, múltiples velocidades.'},
            {'sku': 'LIC-002', 'nombre': 'Licuadora Ninja Professional', 'precio': 149.99, 'stock': 25, 'categoria': 'Licuadoras', 'descripcion': 'Licuadora profesional de alta potencia, vaso de plástico resistente.'},
            
            # Cafeteras
            {'sku': 'CAF-001', 'nombre': 'Cafetera Express Oster', 'precio': 299.99, 'stock': 18, 'categoria': 'Cafeteras', 'descripcion': 'Cafetera express con sistema de vapor, espumador de leche integrado.'},
            {'sku': 'CAF-002', 'nombre': 'Cafetera Nespresso Vertuo', 'precio': 249.99, 'stock': 20, 'categoria': 'Cafeteras', 'descripcion': 'Cafetera de cápsulas con tecnología centrifusión, espuma cremosa.'},
        ]
        
        productos = []
        categoria_map = {cat.nombre: cat for cat in categorias}
        
        for prod_data in productos_data:
            categoria = categoria_map.get(prod_data['categoria'])
            producto, created = Producto.objects.get_or_create(
                sku=prod_data['sku'],
                defaults={
                    'nombre': prod_data['nombre'],
                    'precio': Decimal(str(prod_data['precio'])),
                    'stock': prod_data['stock'],
                    'categoria': categoria,
                    'descripcion': prod_data.get('descripcion', ''),
                    'activo': True,
                }
            )
            productos.append(producto)
        
        return productos

    def crear_usuarios(self):
        """Crea usuarios de prueba"""
        self.stdout.write('Creando usuarios...')
        
        usuarios_data = [
            {
                'username': 'admin',
                'email': 'admin@smartsales365.com',
                'password': 'admin',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_superuser': True,
                'is_staff': True,
                'rol': 'admin',
            },
            {
                'username': 'cliente1',
                'email': 'cliente1@example.com',
                'password': 'cliente1',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'is_superuser': False,
                'is_staff': False,
                'rol': 'cliente',
            },
            {
                'username': 'maria_garcia',
                'email': 'maria@example.com',
                'password': 'cliente123',
                'first_name': 'María',
                'last_name': 'García',
                'is_superuser': False,
                'is_staff': False,
                'rol': 'cliente',
            },
            {
                'username': 'carlos_rodriguez',
                'email': 'carlos@example.com',
                'password': 'cliente123',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'is_superuser': False,
                'is_staff': False,
                'rol': 'cliente',
            },
        ]
        
        usuarios = []
        for user_data in usuarios_data:
            usuario, created = Usuario.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_superuser': user_data['is_superuser'],
                    'is_staff': user_data['is_staff'],
                    'rol': user_data['rol'],
                }
            )
            if created:
                usuario.set_password(user_data['password'])
                usuario.save()
            usuarios.append(usuario)
        
        return usuarios

    def crear_clientes(self, usuarios):
        """Crea clientes asociados a usuarios"""
        self.stdout.write('Creando clientes...')
        
        clientes_data = [
            {
                'usuario': 'cliente1',
                'nombre': 'Juan Pérez',
                'email': 'cliente1@example.com',
                'telefono': '+1 234 567 8900',
                'direccion': 'Av. Principal 123, Ciudad',
            },
            {
                'usuario': 'maria_garcia',
                'nombre': 'María García',
                'email': 'maria@example.com',
                'telefono': '+1 234 567 8901',
                'direccion': 'Calle Secundaria 456, Ciudad',
            },
            {
                'usuario': 'carlos_rodriguez',
                'nombre': 'Carlos Rodríguez',
                'email': 'carlos@example.com',
                'telefono': '+1 234 567 8902',
                'direccion': 'Boulevard Norte 789, Ciudad',
            },
            # Clientes sin usuario (compras de invitados)
            {
                'usuario': None,
                'nombre': 'Ana López',
                'email': 'ana@example.com',
                'telefono': '+1 234 567 8903',
                'direccion': 'Plaza Central 321, Ciudad',
            },
            {
                'usuario': None,
                'nombre': 'Pedro Martínez',
                'email': 'pedro@example.com',
                'telefono': '+1 234 567 8904',
                'direccion': 'Avenida Sur 654, Ciudad',
            },
        ]
        
        clientes = []
        usuario_map = {u.username: u for u in usuarios}
        
        for cliente_data in clientes_data:
            usuario = usuario_map.get(cliente_data['usuario']) if cliente_data['usuario'] else None
            
            # Si tiene usuario, buscar por usuario primero
            if usuario:
                cliente = Cliente.objects.filter(usuario=usuario).first()
                if cliente:
                    # Actualizar datos si es necesario
                    cliente.nombre = cliente_data['nombre']
                    cliente.email = cliente_data['email']
                    cliente.telefono = cliente_data['telefono']
                    cliente.direccion = cliente_data['direccion']
                    cliente.save()
                    clientes.append(cliente)
                    continue
            
            # Si no tiene usuario o no existe, buscar por email
            cliente = Cliente.objects.filter(email=cliente_data['email']).first()
            if cliente:
                # Actualizar usuario si no lo tiene
                if not cliente.usuario and usuario:
                    cliente.usuario = usuario
                    cliente.save()
                clientes.append(cliente)
            else:
                # Crear nuevo cliente
                cliente = Cliente.objects.create(
                    usuario=usuario,
                    nombre=cliente_data['nombre'],
                    email=cliente_data['email'],
                    telefono=cliente_data['telefono'],
                    direccion=cliente_data['direccion'],
                )
                clientes.append(cliente)
        
        return clientes

    def crear_promociones(self):
        """Crea promociones de prueba"""
        self.stdout.write('Creando promociones...')
        
        ahora = timezone.now()
        
        promociones_data = [
            {
                'codigo': 'VERANO2025',
                'nombre': 'Descuento de Verano',
                'descripcion': '20% de descuento en compras mayores a $500',
                'tipo_descuento': 'porcentaje',
                'valor_descuento': Decimal('20.00'),
                'monto_minimo': Decimal('500.00'),
                'fecha_inicio': ahora - timedelta(days=30),
                'fecha_fin': ahora + timedelta(days=60),
                'activa': True,
            },
            {
                'codigo': 'BIENVENIDA50',
                'nombre': 'Cupón de Bienvenida',
                'descripcion': '$50 de descuento en tu primera compra',
                'tipo_descuento': 'monto',
                'valor_descuento': Decimal('50.00'),
                'monto_minimo': Decimal('200.00'),
                'fecha_inicio': ahora - timedelta(days=15),
                'fecha_fin': None,
                'activa': True,
            },
            {
                'codigo': 'BLACKFRIDAY',
                'nombre': 'Black Friday',
                'descripcion': '30% de descuento hasta $200 máximo',
                'tipo_descuento': 'porcentaje',
                'valor_descuento': Decimal('30.00'),
                'descuento_maximo': Decimal('200.00'),
                'monto_minimo': Decimal('300.00'),
                'fecha_inicio': ahora - timedelta(days=10),
                'fecha_fin': ahora + timedelta(days=5),
                'activa': True,
            },
        ]
        
        promociones = []
        for prom_data in promociones_data:
            promocion, created = Promocion.objects.get_or_create(
                codigo=prom_data['codigo'],
                defaults=prom_data
            )
            promociones.append(promocion)
        
        return promociones

    def crear_compras_historicas(self, clientes, productos, promociones, num_compras=100, meses_historico=12, fecha_desde=None):
        """
        Crea compras históricas distribuidas inteligentemente en el tiempo
        
        Args:
            clientes: Lista de clientes
            productos: Lista de productos
            promociones: Lista de promociones
            num_compras: Número total de compras a crear
            meses_historico: Número de meses hacia atrás para generar datos
            fecha_desde: Fecha de inicio opcional (formato YYYY-MM-DD)
        """
        self.stdout.write(f'Creando {num_compras} compras históricas en {meses_historico} meses...')
        
        ahora = timezone.now()
        
        # Determinar fecha de inicio
        if fecha_desde:
            from datetime import datetime
            fecha_inicio = timezone.make_aware(datetime.strptime(fecha_desde, '%Y-%m-%d'))
        else:
            fecha_inicio = ahora - timedelta(days=meses_historico * 30)
        
        dias_totales = (ahora - fecha_inicio).days
        
        # Distribuir compras por mes para mejor análisis
        compras_por_mes = {}
        compras_creadas = 0
        compras_pagadas = 0
        total_ventas = Decimal('0')
        
        # Mapeo de compras y sus fechas para actualizar al final
        compras_fechas_map = {}  # {compra_id: fecha_compra}
        
        # Generar distribución temporal más realista
        # Más ventas en meses recientes, menos en meses antiguos
        pesos_mensuales = []
        for i in range(meses_historico):
            # Peso aumenta en meses más recientes (último mes tiene más peso)
            peso = 1.0 + (i * 0.2)  # Incremento progresivo
            # Añadir variabilidad (temporada alta/baja)
            if i % 3 == 0:  # Cada 3 meses, temporada alta
                peso *= 1.5
            pesos_mensuales.append(peso)
        
        suma_pesos = sum(pesos_mensuales)
        compras_por_peso = [int((peso / suma_pesos) * num_compras) for peso in pesos_mensuales]
        
        # Ajustar para que sume exactamente num_compras
        diferencia = num_compras - sum(compras_por_peso)
        if diferencia > 0:
            compras_por_peso[-1] += diferencia
        
        observaciones_posibles = [
            'Entregar en horario de oficina',
            'Llamar antes de entregar',
            'Dejar en recepción',
            'Entregar en la mañana',
            'Entregar en la tarde',
            '',
            '',  # Más probabilidad de sin observaciones
            'Factura requerida',
            'Paquete frágil - manejar con cuidado',
            'Regalo - incluir tarjeta',
        ]
        
        # Crear compras mes por mes
        for mes_idx, compras_en_mes in enumerate(compras_por_peso):
            if compras_en_mes == 0:
                continue
                
            # Determinar rango de fechas para este mes
            mes_inicio = fecha_inicio + timedelta(days=mes_idx * 30)
            mes_fin = mes_inicio + timedelta(days=30)
            
            if mes_fin > ahora:
                mes_fin = ahora
            
            # Crear compras para este mes
            for _ in range(compras_en_mes):
                # Fecha aleatoria dentro del mes, con más probabilidad en días laborales
                dias_en_mes = (mes_fin - mes_inicio).days
                if dias_en_mes < 1:
                    continue
                    
                # 70% probabilidad de ser día laboral (lun-vie)
                intentos = 0
                while intentos < 10:
                    dia_aleatorio = random.randint(0, dias_en_mes - 1)
                    fecha_compra = mes_inicio + timedelta(
                        days=dia_aleatorio,
                        hours=random.randint(8, 20),  # Horas de trabajo
                        minutes=random.randint(0, 59)
                    )
                    
                    # Aceptar más fácilmente días laborales
                    dia_semana = fecha_compra.weekday()
                    if dia_semana < 5 or random.random() > 0.7:  # Lun-Vie o 30% fin de semana
                        break
                    intentos += 1
                
                # Cliente aleatorio (algunos clientes compran más)
                # 20% de clientes son "frecuentes" y aparecen más
                if random.random() < 0.3 and len(clientes) > 5:
                    # Cliente frecuente (de los primeros)
                    cliente = random.choice(clientes[:max(1, len(clientes) // 3)])
                else:
                    cliente = random.choice(clientes)
                
                # Número de productos (distribución más realista)
                if random.random() < 0.4:  # 40% compra 1 producto
                    num_productos = 1
                elif random.random() < 0.7:  # 30% compra 2-3 productos
                    num_productos = random.randint(2, 3)
                else:  # 30% compra 4-7 productos
                    num_productos = random.randint(4, 7)
                
                productos_compra = random.sample(
                    productos, 
                    min(num_productos, len(productos))
                )
                
                # Crear compra
                compra = Compra.objects.create(
                    cliente=cliente,
                    observaciones=random.choice(observaciones_posibles),
                )
                
                # Guardar fecha para actualizar al final
                compras_fechas_map[compra.id] = fecha_compra
                
                # Agregar items
                subtotal = Decimal('0')
                for producto in productos_compra:
                    # Cantidad varía según precio (productos caros: menos cantidad)
                    if producto.precio > 500:
                        cantidad = 1
                    elif producto.precio > 200:
                        cantidad = random.randint(1, 2)
                    else:
                        cantidad = random.randint(1, 4)
                    
                    precio = producto.precio
                    
                    # Pequeña variación de precio histórico (±5%)
                    if random.random() < 0.2:  # 20% tiene precio histórico diferente
                        variacion = Decimal(str(random.uniform(0.95, 1.05)))
                        precio = precio * variacion
                        precio = precio.quantize(Decimal('0.01'))
                    
                    item = CompraItem.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                    )
                    subtotal += item.subtotal
                
                # Aplicar promoción (30% de probabilidad)
                descuento_aplicado = Decimal('0')
                if random.random() < 0.3 and promociones:
                    # Buscar promoción válida para esta fecha y monto
                    promociones_validas = [
                        p for p in promociones 
                        if p.monto_minimo <= subtotal
                    ]
                    
                    if promociones_validas:
                        promocion = random.choice(promociones_validas)
                        try:
                            compra.aplicar_promocion(promocion)
                            descuento_aplicado = subtotal - compra.total
                        except:
                            compra.total = subtotal
                            compra.save()
                    else:
                        compra.total = subtotal
                        compra.save()
                else:
                    compra.total = subtotal
                    compra.save()
                
                # Estado de pago (85% pagadas, 15% pendientes)
                # Compras más antiguas tienen mayor probabilidad de estar pagadas
                dias_desde_compra = (ahora - fecha_compra).days
                prob_pago = 0.85 + (dias_desde_compra / dias_totales) * 0.10  # Hasta 95%
                
                if random.random() < prob_pago:
                    # Pagar entre 0 y 3 días después de la compra
                    dias_pago = random.randint(0, 3)
                    horas_pago = random.randint(1, 47)
                    
                    fecha_pago = fecha_compra + timedelta(days=dias_pago, hours=horas_pago)
                    
                    # No puede ser en el futuro
                    if fecha_pago > ahora:
                        fecha_pago = ahora - timedelta(hours=random.randint(1, 24))
                    
                    # Actualizar pagado_en y referencia
                    pago_ref = f'PAY-{random.randint(10000, 99999)}-{compra.id}'
                    Compra.objects.filter(id=compra.id).update(
                        pagado_en=fecha_pago,
                        pago_referencia=pago_ref
                    )
                    
                    compras_pagadas += 1
                    # Recargar compra para obtener el total actualizado
                    compra.refresh_from_db()
                    total_ventas += compra.total
                
                compras_creadas += 1
                
                # Registrar estadísticas por mes
                mes_nombre = fecha_compra.strftime('%Y-%m')
                if mes_nombre not in compras_por_mes:
                    compras_por_mes[mes_nombre] = {'count': 0, 'total': Decimal('0')}
                compras_por_mes[mes_nombre]['count'] += 1
                compras_por_mes[mes_nombre]['total'] += compra.total
        
        # Actualizar todas las fechas al final (bypass auto_now_add)
        self.stdout.write('\n  🔄 Actualizando fechas históricas...')
        for compra_id, fecha_historica in compras_fechas_map.items():
            Compra.objects.filter(id=compra_id).update(fecha=fecha_historica)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(compras_fechas_map)} fechas actualizadas'))
        
        # Mostrar estadísticas
        self.stdout.write(self.style.SUCCESS(f'\n  ✓ Creadas {compras_creadas} compras históricas'))
        self.stdout.write(f'  ✓ Compras pagadas: {compras_pagadas} ({compras_pagadas/compras_creadas*100:.1f}%)')
        self.stdout.write(f'  ✓ Total en ventas pagadas: ${total_ventas:,.2f}')
        self.stdout.write(f'\n  📊 Distribución mensual:')
        
        for mes in sorted(compras_por_mes.keys()):
            stats = compras_por_mes[mes]
            promedio = stats['total'] / stats['count'] if stats['count'] > 0 else 0
            self.stdout.write(
                f'     {mes}: {stats["count"]:3d} compras | '
                f'Total: ${stats["total"]:8,.2f} | '
                f'Promedio: ${promedio:6,.2f}'
            )

