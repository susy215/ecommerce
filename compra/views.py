from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from .models import Compra, CompraItem
from .serializers import CompraSerializer
from django.http import HttpResponse


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if isinstance(obj, Compra):
            return getattr(obj.cliente, 'usuario_id', None) == request.user.id
        if isinstance(obj, CompraItem):
            return getattr(obj.compra.cliente, 'usuario_id', None) == request.user.id
        return False


class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.select_related('cliente').all()
    serializer_class = CompraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'observaciones']
    ordering_fields = ['fecha', 'total']

    def perform_create(self, serializer):
        # Para clientes: vincular/crear perfil Cliente y no asignar vendedor
        user = self.request.user
        cliente = getattr(user, 'perfil_cliente', None)
        if cliente is None:
            from clientes.models import Cliente
            cliente = Cliente.objects.create(usuario=user, nombre=user.get_full_name() or user.username, email=user.email or '')
        serializer.save(cliente=cliente)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(cliente__usuario=self.request.user)

    def get_permissions(self):
        if self.action in ['list', 'create']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def checkout(self, request):
        """Crea una compra con items dados (el carrito vive en el frontend).
        Body esperado: { "items": [{"producto": ID, "cantidad": N}, ...], "observaciones": "..." }
        Setea el precio_unitario desde el producto en servidor y calcula totales.
        """
        items = request.data.get('items') or []
        if not isinstance(items, list) or not items:
            return Response({'detail': 'Items requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        observaciones = request.data.get('observaciones', '')

        user = request.user
        cliente = getattr(user, 'perfil_cliente', None)
        if cliente is None:
            from clientes.models import Cliente
            cliente = Cliente.objects.create(usuario=user, nombre=user.get_full_name() or user.username, email=user.email or '')
        from productos.models import Producto

        with transaction.atomic():
            compra = Compra.objects.create(cliente=cliente, observaciones=observaciones)
            for it in items:
                try:
                    prod_id = int(it.get('producto'))
                    cantidad = int(it.get('cantidad'))
                except Exception:
                    return Response({'detail': 'Formato de item inválido'}, status=status.HTTP_400_BAD_REQUEST)
                if cantidad <= 0:
                    return Response({'detail': 'Cantidad debe ser mayor a 0'}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    p = Producto.objects.get(pk=prod_id, activo=True)
                except Producto.DoesNotExist:
                    return Response({'detail': f'Producto {prod_id} no existe o inactivo'}, status=status.HTTP_400_BAD_REQUEST)
                precio = p.precio
                CompraItem.objects.create(compra=compra, producto=p, cantidad=cantidad, precio_unitario=precio, subtotal=precio * cantidad)
            compra.recalc_total()
        return Response(CompraSerializer(compra).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def pay(self, request, pk=None):
        """Marca la compra como pagada, guarda referencia y fecha de pago.
        Espera body: { "referencia": "..." }
        """
        compra = self.get_object()
        if compra.total <= 0:
            return Response({'detail': 'El total debe ser mayor a 0'}, status=status.HTTP_400_BAD_REQUEST)
        if compra.pagado_en:
            return Response({'detail': 'La compra ya está pagada'}, status=status.HTTP_400_BAD_REQUEST)
        ref = (request.data.get('referencia') or '').strip()
        if not ref:
            return Response({'detail': 'Referencia de pago requerida'}, status=status.HTTP_400_BAD_REQUEST)
        compra.pago_referencia = ref
        from django.utils import timezone
        compra.pagado_en = timezone.now()
        compra.save(update_fields=['pago_referencia', 'pagado_en'])
        return Response(CompraSerializer(compra).data)


    # Not exposing per-item CRUD to keep backend simple; carrito vive en frontend.

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def stripe_session(self, request, pk=None):
        """Crea una Stripe Checkout Session para esta compra y devuelve url y session id.
        Body opcional: { success_url, cancel_url }
        """
        try:
            import stripe
        except Exception:
            return Response({'detail': 'Instala la librería stripe'}, status=500)

        compra = self.get_object()
        if compra.total <= 0 or compra.items.count() == 0:
            return Response({'detail': 'La compra debe tener items y total > 0'}, status=400)

        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not stripe.api_key:
            return Response({'detail': 'Falta STRIPE_SECRET_KEY en el servidor (clave secreta sk_...)'}, status=500)
        if stripe.api_key.startswith('pk_'):
            return Response({'detail': 'Clave inválida: estás usando una publishable key (pk_...). Configura STRIPE_SECRET_KEY con tu clave secreta (sk_...).'}, status=500)

        success_url = request.data.get('success_url') or f"{getattr(settings, 'FRONTEND_URL', '')}/checkout/success?compra={compra.id}"
        cancel_url = request.data.get('cancel_url') or f"{getattr(settings, 'FRONTEND_URL', '')}/checkout/cancel?compra={compra.id}"

        line_items = []
        for it in compra.items.select_related('producto'):
            line_items.append({
                'price_data': {
                    'currency': getattr(settings, 'STRIPE_CURRENCY', 'usd'),
                    'product_data': {
                        'name': it.producto.nombre,
                        'metadata': {'producto_id': it.producto_id}
                    },
                    'unit_amount': int(float(it.precio_unitario) * 100),
                },
                'quantity': it.cantidad,
            })

        session = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=line_items,
            metadata={'compra_id': str(compra.id)},
            payment_intent_data={'metadata': {'compra_id': str(compra.id)}},
        )
        compra.stripe_session_id = session.get('id') or ''
        compra.stripe_payment_intent = session.get('payment_intent') or ''
        compra.save(update_fields=['stripe_session_id', 'stripe_payment_intent'])
        return Response({'id': session.id, 'url': session.url})


class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            import stripe
        except Exception:
            return Response({'detail': 'Stripe no instalado'}, status=500)
        # Asegura que la API key esté configurada (no necesaria para verificar firma, pero útil si se consulta a Stripe)
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        payload = request.body
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret) if webhook_secret else stripe.Event.construct_from(request.data, stripe.api_key)
        except Exception as e:
            return Response({'detail': f'Webhook inválido: {e}'}, status=400)

        # Procesar eventos relevantes
        if event['type'] in ('checkout.session.completed',):
            session = event['data']['object']
            compra_id = session.get('metadata', {}).get('compra_id')
            if compra_id:
                try:
                    compra = Compra.objects.get(id=int(compra_id))
                    if not compra.pagado_en:
                        from django.utils import timezone
                        compra.pago_referencia = session.get('payment_intent') or compra.pago_referencia
                        compra.pagado_en = timezone.now()
                        compra.stripe_session_id = session.get('id') or compra.stripe_session_id
                        compra.stripe_payment_intent = session.get('payment_intent') or compra.stripe_payment_intent
                        compra.save(update_fields=['pago_referencia', 'pagado_en', 'stripe_session_id', 'stripe_payment_intent'])
                except Compra.DoesNotExist:
                    pass

        return Response({'received': True})


class CompraReceiptView(APIView):
    """Devuelve un comprobante PDF de la compra para el dueño o admin."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int):
        try:
            compra = Compra.objects.select_related('cliente').get(pk=pk)
        except Compra.DoesNotExist:
            return Response(status=404)
        user = request.user
        if not (user.is_staff or getattr(compra.cliente, 'usuario_id', None) == user.id):
            return Response(status=403)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            return Response({'detail': 'reportlab no instalado'}, status=500)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{compra.id}.pdf"'
        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40
        p.setFont('Helvetica-Bold', 14)
        p.drawString(40, y, 'Nota de Venta')
        y -= 20
        p.setFont('Helvetica', 10)
        p.drawString(40, y, f'Compra ID: {compra.id}   Fecha: {compra.fecha.strftime("%Y-%m-%d %H:%M")}')
        y -= 14
        p.drawString(40, y, f'Cliente: {compra.cliente}')
        y -= 20
        p.setFont('Helvetica-Bold', 10)
        p.drawString(40, y, 'Cant.')
        p.drawString(90, y, 'Producto')
        p.drawString(300, y, 'P. Unit.')
        p.drawString(380, y, 'Subtotal')
        y -= 12
        p.setFont('Helvetica', 10)
        for it in compra.items.select_related('producto'):
            if y < 60:
                p.showPage(); y = height - 40
            p.drawString(40, y, str(it.cantidad))
            p.drawString(90, y, (it.producto.nombre[:36] if it.producto and it.producto.nombre else ''))
            p.drawRightString(360, y, f"{it.precio_unitario}")
            p.drawRightString(450, y, f"{it.subtotal}")
            y -= 12
        y -= 10
        p.setFont('Helvetica-Bold', 11)
        p.drawRightString(450, y, f"TOTAL: {compra.total}")
        y -= 16
        p.setFont('Helvetica', 9)
        estado_pago = f"Pagado: {compra.pagado_en.strftime('%Y-%m-%d %H:%M')}" if compra.pagado_en else 'Pendiente de pago'
        p.drawString(40, y, estado_pago)
        p.showPage()
        p.save()
        return response
