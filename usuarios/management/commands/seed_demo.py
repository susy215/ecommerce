import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from clientes.models import Cliente
from productos.models import Categoria, Producto
from compra.models import Compra, CompraItem


class Command(BaseCommand):
    help = "Puebla la base de datos con datos de demostración: usuarios, clientes, categorías, productos y compras."

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Cantidad de usuarios cliente a crear')
        parser.add_argument('--categories', type=int, default=5, help='Cantidad de categorías a crear')
        parser.add_argument('--products-per-category', type=int, default=5, help='Productos por categoría')
        parser.add_argument('--purchases-per-user', type=int, default=2, help='Compras por usuario a generar')
        parser.add_argument('--no-purchases', action='store_true', help='No generar compras')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        users_count = options['users']
        cat_count = options['categories']
        ppc = options['products_per_category']
        purchases_per_user = options['purchases_per_user']
        no_purchases = options['no_purchases']

        self.stdout.write(self.style.MIGRATE_HEADING('=> Creando usuario administrador...'))
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'rol': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
            self.stdout.write(self.style.SUCCESS('   Admin creado: admin / admin12345'))
        else:
            self.stdout.write('   Admin ya existía')

        self.stdout.write(self.style.MIGRATE_HEADING('=> Creando usuarios cliente...'))
        demo_users = []
        for i in range(1, users_count + 1):
            username = f'user{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'User{i}',
                    'last_name': 'Demo',
                    'rol': 'cliente',
                }
            )
            if created:
                user.set_password('user12345')
                user.save()
            demo_users.append(user)
        self.stdout.write(self.style.SUCCESS(f'   Usuarios cliente: {len(demo_users)}'))

        self.stdout.write(self.style.MIGRATE_HEADING('=> Creando perfiles Cliente...'))
        for u in demo_users:
            Cliente.objects.get_or_create(
                usuario=u,
                defaults={
                    'nombre': f'{u.first_name} {u.last_name}'.strip() or u.username,
                    'email': u.email,
                    'telefono': '999-999',
                    'direccion': 'Calle Falsa 123',
                }
            )
        self.stdout.write(self.style.SUCCESS('   Perfiles Cliente listos'))

        self.stdout.write(self.style.MIGRATE_HEADING('=> Creando categorías y productos...'))
        productos_creados = 0
        for ci in range(1, cat_count + 1):
            nombre = f'Categoria {ci}'
            slug = f'categoria-{ci}'
            categoria, _ = Categoria.objects.get_or_create(slug=slug, defaults={'nombre': nombre})
            for pi in range(1, ppc + 1):
                sku = f'SKU-{ci:02d}-{pi:03d}'
                defaults = {
                    'nombre': f'Producto {ci}-{pi}',
                    'descripcion': 'Producto de demostración',
                    'precio': round(random.uniform(5, 200), 2),
                    'stock': random.randint(5, 200),
                    'activo': True,
                    'categoria': categoria,
                }
                Producto.objects.get_or_create(sku=sku, defaults=defaults)
                productos_creados += 1
        self.stdout.write(self.style.SUCCESS(f'   Productos listos (~{productos_creados})'))

        if no_purchases:
            self.stdout.write(self.style.WARNING('=> Saltando generación de compras (--no-purchases)'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING('=> Generando compras de ejemplo...'))
        productos_ids = list(Producto.objects.filter(activo=True).values_list('id', flat=True))
        if not productos_ids:
            self.stdout.write(self.style.WARNING('   No hay productos activos; no se generarán compras'))
            return

        compras_creadas = 0
        items_creados = 0
        for u in demo_users:
            cliente = getattr(u, 'perfil_cliente', None)
            if not cliente:
                cliente, _ = Cliente.objects.get_or_create(usuario=u, defaults={'nombre': u.username, 'email': u.email})
            for _ in range(purchases_per_user):
                compra = Compra.objects.create(cliente=cliente, observaciones='Compra demo')
                # 1 a 3 items
                for _ in range(random.randint(1, 3)):
                    pid = random.choice(productos_ids)
                    p = Producto.objects.get(id=pid)
                    cant = random.randint(1, 3)
                    CompraItem.objects.create(
                        compra=compra,
                        producto=p,
                        cantidad=cant,
                        precio_unitario=p.precio,
                        subtotal=p.precio * cant,
                    )
                    items_creados += 1
                compra.recalc_total()
                # Marcar pagado a la mitad
                if random.random() < 0.5 and compra.total > 0:
                    compra.pago_referencia = f'SEED-{compra.id}'
                    compra.pagado_en = timezone.now() - timedelta(days=random.randint(0, 30))
                    compra.save(update_fields=['pago_referencia', 'pagado_en'])
                compras_creadas += 1

        self.stdout.write(self.style.SUCCESS(f'   Compras: {compras_creadas}, Items: {items_creados}'))
        self.stdout.write(self.style.SUCCESS('=> Seed completado'))
