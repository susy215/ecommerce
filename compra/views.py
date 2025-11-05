from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from .models import Compra, CompraItem
from .serializers import CompraSerializer
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite al dueño o admin acceder a la compra"""
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if isinstance(obj, Compra):
            return getattr(obj.cliente, 'usuario_id', None) == request.user.id
        if isinstance(obj, CompraItem):
            return getattr(obj.compra.cliente, 'usuario_id', None) == request.user.id
        return False


class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.select_related('cliente').prefetch_related('items__producto').all()
    serializer_class = CompraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'observaciones', 'pago_referencia']
    ordering_fields = ['fecha', 'total']

    def perform_create(self, serializer):
        """Crea automáticamente el perfil de cliente si no existe"""
        user = self.request.user
        cliente = getattr(user, 'perfil_cliente', None)
        if cliente is None:
            from clientes.models import Cliente
            cliente = Cliente.objects.create(
                usuario=user,
                nombre=user.get_full_name() or user.username,
                email=user.email or ''
            )
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
        """
        Crea una compra con items dados (el carrito vive en el frontend).
        Body esperado: {
            "items": [{"producto": ID, "cantidad": N}, ...],
            "observaciones": "...",
            "codigo_promocion": "VERANO2025" (opcional)
        }
        
        ✅ Valida stock disponible
        ✅ Reduce stock automáticamente
        ✅ Aplica promoción si existe
        ✅ Usa transacciones para atomicidad
        """
        items = request.data.get('items') or []
        if not isinstance(items, list) or not items:
            return Response(
                {'detail': 'Items requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        observaciones = request.data.get('observaciones', '')
        codigo_promocion = request.data.get('codigo_promocion', '').strip()

        user = request.user
        cliente = getattr(user, 'perfil_cliente', None)
        if cliente is None:
            from clientes.models import Cliente
            cliente = Cliente.objects.create(
                usuario=user,
                nombre=user.get_full_name() or user.username,
                email=user.email or ''
            )

        from productos.models import Producto
        from promociones.models import Promocion

        try:
            with transaction.atomic():
                # Validar promoción si existe
                promocion = None
                if codigo_promocion:
                    try:
                        promocion = Promocion.objects.get(codigo=codigo_promocion.upper())
                        if not promocion.esta_vigente():
                            return Response(
                                {'detail': 'La promoción no está vigente o ha alcanzado el límite de usos'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    except Promocion.DoesNotExist:
                        return Response(
                            {'detail': f'Código de promoción "{codigo_promocion}" inválido'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Validar todos los productos y stock ANTES de crear la compra
                productos_validados = []
                for it in items:
                    try:
                        prod_id = int(it.get('producto'))
                        cantidad = int(it.get('cantidad'))
                    except (ValueError, TypeError):
                        return Response(
                            {'detail': 'Formato de item inválido'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    if cantidad <= 0:
                        return Response(
                            {'detail': 'La cantidad debe ser mayor a 0'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Verificar producto existe y está activo
                    try:
                        producto = Producto.objects.select_for_update().get(
                            pk=prod_id,
                            activo=True
                        )
                    except Producto.DoesNotExist:
                        return Response(
                            {'detail': f'Producto {prod_id} no existe o está inactivo'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # ✅ Validar stock disponible
                    if not producto.tiene_stock(cantidad):
                        return Response(
                            {
                                'detail': f'Stock insuficiente para {producto.nombre}. '
                                         f'Disponible: {producto.stock}, Solicitado: {cantidad}'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    productos_validados.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio': producto.precio
                    })

                # Crear la compra
                compra = Compra.objects.create(
                    cliente=cliente,
                    observaciones=observaciones
                )

                # Crear items y reducir stock
                for item_data in productos_validados:
                    producto = item_data['producto']
                    cantidad = item_data['cantidad']
                    precio = item_data['precio']
                    
                    # Crear item (el subtotal se calcula automáticamente)
                    CompraItem.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=precio * cantidad
                    )
                    
                    # ✅ Reducir stock
                    producto.reducir_stock(cantidad)

                # Recalcular total
                compra.recalc_total()
                
                # ✅ Aplicar promoción si existe
                if promocion:
                    descuento = compra.aplicar_promocion(promocion)
                    logger.info(f'Promoción {promocion.codigo} aplicada a compra #{compra.id}. Descuento: ${descuento}')

            logger.info(f'Compra #{compra.id} creada exitosamente por usuario {user.username}')
            
            # ✅ Enviar notificación push de compra creada
            try:
                from notificaciones.push_service import push_service
                push_service.send_notification(
                    usuario=user,
                    titulo='🛒 Carrito confirmado',
                    mensaje=f'Tu pedido #{compra.id} ha sido creado. Procede al pago para completar tu compra.',
                    tipo='otro',
                    datos_extra={
                        'compra_id': compra.id,
                        'total': float(compra.total)
                    },
                    url=f'/mis-pedidos/{compra.id}'
                )
            except Exception as e:
                logger.warning(f'No se pudo enviar notificación push: {str(e)}')
            
            return Response(
                CompraSerializer(compra).data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            logger.error(f'Error en checkout: {str(e)}')
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f'Error inesperado en checkout: {str(e)}')
            return Response(
                {'detail': 'Error al procesar la compra'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def pay(self, request, pk=None):
        """
        Marca la compra como pagada.
        Body esperado: { "referencia": "..." }
        """
        compra = self.get_object()
        
        if compra.esta_pagada:
            return Response(
                {'detail': 'La compra ya está pagada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if compra.total <= 0:
            return Response(
                {'detail': 'El total debe ser mayor a 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ref = (request.data.get('referencia') or '').strip()
        if not ref:
            return Response(
                {'detail': 'Referencia de pago requerida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        compra.pago_referencia = ref
        compra.pagado_en = timezone.now()
        compra.save(update_fields=['pago_referencia', 'pagado_en'])
        
        logger.info(f'Compra #{compra.id} marcada como pagada')
        
        # ✅ Enviar notificación push de pago confirmado
        try:
            from notificaciones.push_service import push_service
            push_service.send_compra_exitosa(compra)
        except Exception as e:
            logger.warning(f'No se pudo enviar notificación push: {str(e)}')
        
        return Response(CompraSerializer(compra).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def stripe_session(self, request, pk=None):
        """
        Crea una Stripe Checkout Session para esta compra.
        Body opcional: { "success_url": "...", "cancel_url": "..." }
        """
        try:
            import stripe
        except ImportError:
            return Response(
                {'detail': 'La librería stripe no está instalada'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        compra = self.get_object()
        
        if compra.total <= 0 or compra.items.count() == 0:
            return Response(
                {'detail': 'La compra debe tener items y total > 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not stripe.api_key:
            return Response(
                {'detail': 'Falta configurar STRIPE_SECRET_KEY en el servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if stripe.api_key.startswith('pk_'):
            return Response(
                {
                    'detail': 'Configuración inválida: se está usando una clave '
                             'publicable (pk_...). Configura STRIPE_SECRET_KEY '
                             'con tu clave secreta (sk_...).'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        success_url = request.data.get('success_url') or f"{frontend_url}/checkout/success?compra={compra.id}"
        cancel_url = request.data.get('cancel_url') or f"{frontend_url}/checkout/cancel?compra={compra.id}"

        # Construir line items
        line_items = []
        for item in compra.items.select_related('producto'):
            line_items.append({
                'price_data': {
                    'currency': getattr(settings, 'STRIPE_CURRENCY', 'usd'),
                    'product_data': {
                        'name': item.producto.nombre,
                        'metadata': {'producto_id': str(item.producto_id)}
                    },
                    'unit_amount': int(float(item.precio_unitario) * 100),
                },
                'quantity': item.cantidad,
            })

        try:
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
            
            logger.info(f'Stripe session creada para compra #{compra.id}')
            return Response({'id': session.id, 'url': session.url})
            
        except stripe.error.StripeError as e:
            logger.error(f'Error de Stripe: {str(e)}')
            return Response(
                {'detail': f'Error al crear sesión de pago: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Procesa webhooks de Stripe para actualizar estado de pagos.
    
    Este endpoint debe estar exento de CSRF ya que Stripe envía las solicitudes directamente.
    No requiere autenticación, pero verifica la firma del webhook usando STRIPE_WEBHOOK_SECRET.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Procesa webhook de Stripe.
        
        Eventos soportados:
        - checkout.session.completed: Marca la compra como pagada
        """
        try:
            import stripe
        except ImportError:
            logger.error('Stripe no está instalado')
            return Response(
                {'detail': 'Stripe no instalado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not stripe.api_key:
            logger.error('STRIPE_SECRET_KEY no configurada')
            return Response(
                {'detail': 'Stripe no configurado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        payload = request.body

        # Log para debugging
        logger.info(f'Webhook recibido. Secret configurado: {bool(webhook_secret)}, Header presente: {bool(sig_header)}')
        if webhook_secret:
            logger.debug(f'Webhook secret (primeros 10 chars): {webhook_secret[:10]}...')
        else:
            logger.warning('⚠️ STRIPE_WEBHOOK_SECRET no está configurado en variables de entorno')

        # Verificar firma del webhook
        try:
            if webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
                logger.info(f'✅ Webhook verificado exitosamente: {event["type"]}')
            else:
                logger.error('❌ STRIPE_WEBHOOK_SECRET no configurado. No se puede verificar la firma.')
                logger.error('Por favor, agrega STRIPE_WEBHOOK_SECRET a tu archivo .env y reinicia el servidor.')
                return Response(
                    {'detail': 'Webhook secret no configurado'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except ValueError as e:
            logger.error(f'Webhook payload inválido: {str(e)}')
            return Response({'detail': 'Payload inválido'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f'Firma del webhook inválida: {str(e)}')
            return Response({'detail': 'Firma inválida'}, status=400)
        except Exception as e:
            logger.exception(f'Error procesando webhook: {str(e)}')
            return Response({'detail': 'Error procesando webhook'}, status=500)

        # Procesar evento checkout.session.completed
        if event.get('type') == 'checkout.session.completed':
            session = event['data']['object']
            compra_id = session.get('metadata', {}).get('compra_id')
            
            if not compra_id:
                logger.warning('Webhook checkout.session.completed sin compra_id en metadata')
                logger.debug(f'Session metadata: {session.get("metadata", {})}')
                return Response({'detail': 'No se encontró compra_id en metadata'}, status=400)
            
            try:
                compra = Compra.objects.select_related('cliente').get(id=int(compra_id))
                
                if compra.esta_pagada:
                    logger.info(f'Compra #{compra_id} ya estaba pagada, ignorando webhook')
                    return Response({'received': True, 'message': 'Compra ya pagada'})
                
                # Actualizar compra como pagada
                with transaction.atomic():
                    compra.pago_referencia = session.get('payment_intent') or session.get('id') or compra.pago_referencia
                    compra.pagado_en = timezone.now()
                    compra.stripe_session_id = session.get('id') or compra.stripe_session_id
                    compra.stripe_payment_intent = session.get('payment_intent') or compra.stripe_payment_intent
                    compra.save(update_fields=[
                        'pago_referencia',
                        'pagado_en',
                        'stripe_session_id',
                        'stripe_payment_intent'
                    ])
                    
                    logger.info(
                        f'✅ Compra #{compra_id} pagada via Stripe webhook. '
                        f'Payment Intent: {compra.stripe_payment_intent}, '
                        f'Total: ${compra.total}'
                    )
                    
                    # ✅ Enviar notificación push de pago confirmado vía Stripe
                    try:
                        from notificaciones.push_service import push_service
                        push_service.send_compra_exitosa(compra)
                        logger.info(f'Notificación push enviada para compra #{compra_id}')
                    except Exception as e:
                        logger.warning(f'No se pudo enviar notificación push para compra #{compra_id}: {str(e)}')
                
            except Compra.DoesNotExist:
                logger.error(f'Compra {compra_id} no encontrada en webhook')
                return Response({'detail': f'Compra {compra_id} no encontrada'}, status=404)
            except ValueError as e:
                logger.error(f'compra_id inválido: {compra_id}, error: {str(e)}')
                return Response({'detail': 'compra_id inválido'}, status=400)
            except Exception as e:
                logger.exception(f'Error procesando webhook para compra {compra_id}: {e}')
                return Response({'detail': 'Error procesando compra'}, status=500)
        
        else:
            # Evento no manejado (log pero no fallar)
            event_type = event.get('type', 'unknown')
            logger.info(f'ℹ️ Webhook recibido: {event_type} (evento no procesado, solo se procesa checkout.session.completed)')
            
            # Para eventos de charge, intentar obtener el checkout session
            if event_type == 'charge.updated' or event_type == 'charge.succeeded':
                charge = event.get('data', {}).get('object', {})
                payment_intent_id = charge.get('payment_intent')
                if payment_intent_id:
                    logger.info(f'Charge detectado para payment_intent: {payment_intent_id}')
                    # Buscar compra por payment_intent
                    try:
                        compra = Compra.objects.filter(stripe_payment_intent=payment_intent_id).first()
                        if compra and not compra.esta_pagada:
                            logger.info(f'Compra #{compra.id} encontrada por payment_intent, marcando como pagada')
                            compra.pagado_en = timezone.now()
                            compra.pago_referencia = payment_intent_id
                            compra.save(update_fields=['pagado_en', 'pago_referencia'])
                            
                            # Enviar notificación push
                            try:
                                from notificaciones.push_service import push_service
                                push_service.send_compra_exitosa(compra)
                                logger.info(f'Notificación push enviada para compra #{compra.id}')
                            except Exception as e:
                                logger.warning(f'No se pudo enviar notificación push: {str(e)}')
                    except Exception as e:
                        logger.warning(f'Error procesando charge para payment_intent {payment_intent_id}: {str(e)}')

        return Response({'received': True})


class CompraReceiptView(APIView):
    """Genera un comprobante PDF de la compra"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int):
        try:
            compra = Compra.objects.select_related('cliente').prefetch_related(
                'items__producto'
            ).get(pk=pk)
        except Compra.DoesNotExist:
            return Response({'detail': 'Compra no encontrada'}, status=404)

        user = request.user
        if not (user.is_staff or getattr(compra.cliente, 'usuario_id', None) == user.id):
            return Response({'detail': 'No autorizado'}, status=403)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            return Response(
                {'detail': 'reportlab no instalado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{compra.id}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40

        # Encabezado
        p.setFont('Helvetica-Bold', 16)
        p.drawString(40, y, 'SmartSales365 - Comprobante de Compra')
        y -= 30

        # Información de la compra
        p.setFont('Helvetica', 11)
        p.drawString(40, y, f'Compra ID: {compra.id}')
        y -= 16
        p.drawString(40, y, f'Fecha: {compra.fecha.strftime("%Y-%m-%d %H:%M")}')
        y -= 16
        p.drawString(40, y, f'Cliente: {compra.cliente.nombre}')
        y -= 16
        estado = 'Pagado' if compra.esta_pagada else 'Pendiente'
        p.drawString(40, y, f'Estado: {estado}')
        y -= 30

        # Tabla de items
        p.setFont('Helvetica-Bold', 10)
        p.drawString(40, y, 'Cant.')
        p.drawString(90, y, 'Producto')
        p.drawString(350, y, 'P. Unit.')
        p.drawString(450, y, 'Subtotal')
        y -= 14
        p.line(40, y, 550, y)
        y -= 10

        p.setFont('Helvetica', 10)
        for item in compra.items.all():
            if y < 60:
                p.showPage()
                y = height - 40

            p.drawString(40, y, str(item.cantidad))
            nombre = item.producto.nombre[:40] if item.producto else 'N/A'
            p.drawString(90, y, nombre)
            p.drawRightString(420, y, f'${item.precio_unitario}')
            p.drawRightString(530, y, f'${item.subtotal}')
            y -= 14

        # Total
        y -= 10
        p.line(40, y, 550, y)
        y -= 20
        p.setFont('Helvetica-Bold', 12)
        p.drawRightString(530, y, f'TOTAL: ${compra.total}')

        # Información de pago
        if compra.esta_pagada:
            y -= 20
            p.setFont('Helvetica', 9)
            p.drawString(40, y, f'Pagado el: {compra.pagado_en.strftime("%Y-%m-%d %H:%M")}')
            if compra.pago_referencia:
                y -= 12
                p.drawString(40, y, f'Referencia: {compra.pago_referencia}')

        p.showPage()
        p.save()

        logger.info(f'Comprobante PDF generado para compra #{compra.id}')
        return response
