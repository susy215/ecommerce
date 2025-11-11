"""
Motor de Inteligencia Artificial para interpretar prompts en lenguaje natural
y generar consultas SQL dinámicas para reportes.
"""
import re
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg, Max, Min, F
from django.utils import timezone


def convert_decimal_to_float(obj):
    """
    Convierte recursivamente todos los Decimal y datetime en un objeto
    para que sean serializables a JSON.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    elif obj is None:
        return None
    return obj


class InterpretadorPrompt:
    """
    Interpreta prompts en lenguaje natural y los convierte en parámetros
    de consulta estructurados.
    """
    
    # Palabras clave para detectar entidades
    MESES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    FORMATOS = {
        'pdf': ['pdf'],
        'excel': ['excel', 'xls', 'xlsx'],
        'csv': ['csv'],
        'pantalla': ['pantalla', 'web', 'html']
    }
    
    AGRUPACIONES = {
        'producto': ['producto', 'productos', 'artículo', 'artículos', 'item', 'items'],
        'cliente': ['cliente', 'clientes', 'comprador', 'compradores'],
        'categoria': ['categoría', 'categorias', 'tipo', 'tipos'],
        'fecha': ['fecha', 'día', 'día', 'mes', 'año'],
        'vendedor': ['vendedor', 'vendedores', 'empleado', 'empleados'],
    }
    
    METRICAS = {
        'total': ['total', 'suma', 'monto', 'dinero', 'pagado'],
        'cantidad': ['cantidad', 'número', 'numero', 'count', 'cuantos'],
        'promedio': ['promedio', 'media', 'avg', 'average'],
        'maximo': ['máximo', 'maximo', 'max', 'mayor'],
        'minimo': ['mínimo', 'minimo', 'min', 'menor'],
    }
    
    TIPOS_REPORTE = {
        'ventas': ['venta', 'ventas', 'compra', 'compras', 'pedido', 'pedidos'],
        'clientes': ['cliente', 'clientes'],
        'productos': ['producto', 'productos'],
        'inventario': ['inventario', 'stock', 'existencia', 'existencias'],
    }
    
    def __init__(self, prompt):
        self.prompt = prompt.lower()
        self.resultado = {
            'tipo_reporte': None,
            'fecha_inicio': None,
            'fecha_fin': None,
            'agrupar_por': [],
            'metricas': [],
            'formato': 'pantalla',
            'filtros': {},
            'orden': None,
            'limite': None,
        }
    
    def interpretar(self):
        """Interpreta el prompt completo"""
        self._detectar_formato()
        self._detectar_fechas()
        self._detectar_tipo_reporte()
        self._detectar_consulta_personalizada()  # Nueva función para consultas específicas
        self._detectar_agrupacion()
        self._detectar_metricas()
        self._detectar_filtros()
        self._detectar_orden()
        self._detectar_limite()

        return self.resultado

    def _detectar_consulta_personalizada(self):
        """Detecta consultas con campos específicos mencionados"""
        prompt_lower = self.prompt.lower()

        # Detectar si pide campos específicos de clientes
        campos_cliente = ['nombre del cliente', 'cantidad de compras', 'monto total', 'rango de fechas']
        if all(campo in prompt_lower for campo in campos_cliente[:3]):  # Al menos nombre, cantidad, monto
            self.resultado['consulta_personalizada'] = 'ventas_clientes_detallado'
            self.resultado['tipo_reporte'] = 'ventas'
            self.resultado['agrupar_por'] = ['cliente']

            # Si menciona "rango de fechas", incluirlo
            if 'rango de fechas' in prompt_lower:
                self.resultado['incluir_rango_fechas'] = True

        # Detectar consultas de top productos
        if ('top' in prompt_lower and 'productos' in prompt_lower) or \
           ('productos más vendidos' in prompt_lower) or \
           ('productos más vendidos' in prompt_lower):
            self.resultado['consulta_personalizada'] = 'top_productos'
            self.resultado['tipo_reporte'] = 'productos'
            self.resultado['orden'] = '-ventas_totales'
    
    def _detectar_formato(self):
        """Detecta el formato de salida"""
        for formato, palabras in self.FORMATOS.items():
            for palabra in palabras:
                if palabra in self.prompt:
                    self.resultado['formato'] = formato
                    return
    
    def _detectar_fechas(self):
        """Detecta rangos de fechas en el prompt - MEJORADO"""
        # Patrón mejorado: dd/mm/yyyy, dd-mm-yyyy, yyyy/mm/dd, yyyy-mm-dd
        patrones_fecha = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # dd/mm/yyyy
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # yyyy/mm/dd
        ]

        fechas_encontradas = []

        for patron in patrones_fecha:
            matches = re.findall(patron, self.prompt)
            for match in matches:
                if len(match) == 3:
                    # Determinar formato basado en el orden de los números
                    nums = [int(x) for x in match]
                    if nums[2] > 31:  # Año en tercera posición (yyyy/mm/dd)
                        fecha = datetime(nums[2], nums[1], nums[0])
                    elif nums[0] > 31:  # Año en primera posición (yyyy-mm-dd)
                        fecha = datetime(nums[0], nums[1], nums[2])
                    else:  # Asumir dd/mm/yyyy
                        fecha = datetime(nums[2], nums[1], nums[0])
                    fechas_encontradas.append(fecha)

        # Detectar rango con palabras clave
        if 'del' in self.prompt and 'al' in self.prompt:
            # Buscar patrón "del DD/MM/YYYY al DD/MM/YYYY"
            patron_rango = r'del\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s+al\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
            match = re.search(patron_rango, self.prompt, re.IGNORECASE)
            if match:
                try:
                    fecha_inicio = self._parse_fecha_flexible(match.group(1))
                    fecha_fin = self._parse_fecha_flexible(match.group(2))
                    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)

                    self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
                    self.resultado['fecha_fin'] = timezone.make_aware(fecha_fin)
                    return  # Salir si encontramos un rango específico
                except ValueError:
                    pass

        # Si tenemos fechas individuales, usar las primeras dos
        if len(fechas_encontradas) >= 2:
            fecha_inicio = min(fechas_encontradas)
            fecha_fin = max(fechas_encontradas)
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)

            self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
            self.resultado['fecha_fin'] = timezone.make_aware(fecha_fin)
        elif len(fechas_encontradas) == 1:
            self.resultado['fecha_inicio'] = timezone.make_aware(fechas_encontradas[0])

        # Detectar meses específicos (código existente)
        for mes_nombre, mes_num in self.MESES.items():
            if mes_nombre in self.prompt:
                patron_anio = r'\b(20\d{2})\b'
                anio_match = re.search(patron_anio, self.prompt)
                anio = int(anio_match.group(1)) if anio_match else timezone.now().year

                fecha_inicio = datetime(anio, mes_num, 1)
                if mes_num == 12:
                    fecha_fin = datetime(anio + 1, 1, 1) - timedelta(days=1)
                else:
                    fecha_fin = datetime(anio, mes_num + 1, 1) - timedelta(days=1)

                self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
                self.resultado['fecha_fin'] = timezone.make_aware(fecha_fin.replace(hour=23, minute=59, second=59))
                break

        # Rangos relativos (código existente)
        if 'última semana' in self.prompt or 'ultima semana' in self.prompt:
            hoy = timezone.now()
            self.resultado['fecha_inicio'] = hoy - timedelta(days=7)
            self.resultado['fecha_fin'] = hoy
        elif 'último mes' in self.prompt or 'ultimo mes' in self.prompt:
            hoy = timezone.now()
            self.resultado['fecha_inicio'] = hoy - timedelta(days=30)
            self.resultado['fecha_fin'] = hoy
        elif 'este mes' in self.prompt:
            hoy = timezone.now()
            fecha_inicio = datetime(hoy.year, hoy.month, 1)
            self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
            self.resultado['fecha_fin'] = hoy

    def _parse_fecha_flexible(self, fecha_str):
        """Parse fecha en múltiples formatos"""
        # Intentar diferentes formatos
        formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']

        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato)
            except ValueError:
                continue
        raise ValueError(f"No se pudo parsear fecha: {fecha_str}")
    
    def _detectar_tipo_reporte(self):
        """Detecta el tipo de reporte solicitado"""
        # Detección directa para casos comunes
        if any(x in self.prompt for x in ['inventario', 'stock', 'existencia', 'existencias']):
            self.resultado['tipo_reporte'] = 'inventario'
            return
        for tipo, palabras in self.TIPOS_REPORTE.items():
            for palabra in palabras:
                if palabra in self.prompt:
                    self.resultado['tipo_reporte'] = tipo
                    return
        
        # Por defecto: ventas
        self.resultado['tipo_reporte'] = 'ventas'
    
    def _detectar_agrupacion(self):
        """Detecta por qué campos agrupar"""
        for grupo, palabras in self.AGRUPACIONES.items():
            for palabra in palabras:
                if f'por {palabra}' in self.prompt or f'agrupado por {palabra}' in self.prompt:
                    if grupo not in self.resultado['agrupar_por']:
                        self.resultado['agrupar_por'].append(grupo)
        # Soporte para expresiones tipo "top clientes/productos/categorías" sin 'por'
        if 'top' in self.prompt or 'mejores' in self.prompt or 'ranking' in self.prompt:
            if any(p in self.prompt for p in self.AGRUPACIONES['cliente']):
                if 'cliente' not in self.resultado['agrupar_por']:
                    self.resultado['agrupar_por'].append('cliente')
            if any(p in self.prompt for p in self.AGRUPACIONES['producto']):
                if 'producto' not in self.resultado['agrupar_por']:
                    self.resultado['agrupar_por'].append('producto')
            if any(p in self.prompt for p in self.AGRUPACIONES['categoria']):
                if 'categoria' not in self.resultado['agrupar_por']:
                    self.resultado['agrupar_por'].append('categoria')
    
    def _detectar_metricas(self):
        """Detecta qué métricas calcular"""
        for metrica, palabras in self.METRICAS.items():
            for palabra in palabras:
                if palabra in self.prompt:
                    if metrica not in self.resultado['metricas']:
                        self.resultado['metricas'].append(metrica)
        
        # Métricas por defecto según tipo de reporte
        if not self.resultado['metricas']:
            if self.resultado['tipo_reporte'] == 'ventas':
                self.resultado['metricas'] = ['total', 'cantidad']
            elif self.resultado['tipo_reporte'] == 'clientes':
                self.resultado['metricas'] = ['cantidad', 'total']
            elif self.resultado['tipo_reporte'] == 'productos':
                self.resultado['metricas'] = ['cantidad']
    
    def _detectar_filtros(self):
        """Detecta filtros específicos"""
        # Filtro por estado de pago
        if 'pagada' in self.prompt or 'pagado' in self.prompt:
            self.resultado['filtros']['pagado'] = True
        elif 'pendiente' in self.prompt or 'sin pagar' in self.prompt:
            self.resultado['filtros']['pagado'] = False
        
        # Filtro por categoría específica
        patron_categoria = r'categoría\s+["\']?([^"\']+)["\']?'
        match = re.search(patron_categoria, self.prompt)
        if match:
            self.resultado['filtros']['categoria'] = match.group(1)
    
    def _detectar_orden(self):
        """Detecta orden de resultados"""
        if 'mayor' in self.prompt or 'descendente' in self.prompt or 'desc' in self.prompt:
            self.resultado['orden'] = '-total'
        elif 'menor' in self.prompt or 'ascendente' in self.prompt or 'asc' in self.prompt:
            self.resultado['orden'] = 'total'
        # Si se pide "top" y no se definió orden, usar descendente por total
        if (('top' in self.prompt or 'mejores' in self.prompt or 'ranking' in self.prompt)
            and not self.resultado.get('orden')):
            self.resultado['orden'] = '-total'
    
    def _detectar_limite(self):
        """Detecta límite de resultados"""
        # Top N
        patron_top = r'top\s+(\d+)'
        match = re.search(patron_top, self.prompt)
        if match:
            limite = int(match.group(1))
            # Máximo 1000 registros para evitar problemas de rendimiento
            self.resultado['limite'] = min(limite, 1000)
            return
        # "mejores N"
        patron_mejores = r'mejores\s+(\d+)'
        match = re.search(patron_mejores, self.prompt)
        if match:
            limite = int(match.group(1))
            self.resultado['limite'] = min(limite, 1000)
            return
        
        # Primeros N
        patron_primeros = r'primeros?\s+(\d+)'
        match = re.search(patron_primeros, self.prompt)
        if match:
            limite = int(match.group(1))
            self.resultado['limite'] = min(limite, 1000)
            return
        
        # Límite por defecto según tipo de reporte
        # Para evitar consultas muy pesadas
        if not self.resultado['limite']:
            if self.resultado.get('agrupar_por'):
                # Con agrupación: si hay "top" sin número, usar 10 por defecto
                if 'top' in self.prompt or 'mejores' in self.prompt or 'ranking' in self.prompt:
                    self.resultado['limite'] = 10
                else:
                    self.resultado['limite'] = 100
            else:
                # Sin agrupación: 1000 por defecto
                self.resultado['limite'] = 1000


class GeneradorConsultas:
    """
    Genera consultas SQL dinámicas basadas en la interpretación del prompt
    """
    
    def __init__(self, interpretacion):
        self.params = interpretacion
    
    def generar_consulta(self):
        """Genera y ejecuta la consulta según el tipo de reporte"""
        # Verificar si es una consulta personalizada
        if 'consulta_personalizada' in self.params:
            consulta_tipo = self.params['consulta_personalizada']
            if consulta_tipo == 'ventas_clientes_detallado':
                return self._consulta_ventas_clientes_detallado()
            elif consulta_tipo == 'top_productos':
                return self._consulta_top_productos()

        # Consultas normales
        tipo = self.params['tipo_reporte']

        resultado = None
        if tipo == 'ventas':
            resultado = self._consulta_ventas()
        elif tipo == 'clientes':
            resultado = self._consulta_clientes()
        elif tipo == 'productos':
            resultado = self._consulta_productos()
        elif tipo == 'inventario':
            resultado = self._consulta_inventario()
        else:
            resultado = self._consulta_ventas()  # Default

        # Convertir todos los Decimals a float para JSON serialization
        if resultado:
            resultado = convert_decimal_to_float(resultado)

        return resultado
    
    def _aplicar_filtro_fechas(self, queryset, campo='fecha'):
        """Aplica filtros de fecha al queryset"""
        if self.params['fecha_inicio']:
            queryset = queryset.filter(**{f'{campo}__gte': self.params['fecha_inicio']})
        if self.params['fecha_fin']:
            queryset = queryset.filter(**{f'{campo}__lte': self.params['fecha_fin']})
        return queryset
    
    def _consulta_ventas(self):
        """Genera reporte de ventas"""
        from compra.models import Compra, CompraItem
        
        # Base queryset con optimización
        queryset = Compra.objects.select_related('cliente').all()
        
        # Filtros de fecha
        queryset = self._aplicar_filtro_fechas(queryset, 'fecha')
        
        # Filtro de pago
        if 'pagado' in self.params['filtros']:
            if self.params['filtros']['pagado']:
                queryset = queryset.filter(pagado_en__isnull=False)
            else:
                queryset = queryset.filter(pagado_en__isnull=True)
        
        # Agrupación
        agrupar_por = self.params['agrupar_por']
        
        if not agrupar_por:
            # Reporte general sin agrupación
            resultado = {
                'tipo': 'resumen_general',
                'columnas': ['total_ventas', 'cantidad_compras', 'promedio_venta', 'venta_maxima', 'venta_minima'],
                'datos': []
            }
            
            datos = queryset.aggregate(
                total_ventas=Sum('total'),
                cantidad_compras=Count('id'),
                promedio_venta=Avg('total'),
                venta_maxima=Max('total'),
                venta_minima=Min('total')
            )
            
            resultado['datos'].append(datos)
            return resultado
        
        elif 'producto' in agrupar_por:
            # Agrupar por producto - CORREGIDO para incluir filtros de fecha
            items = CompraItem.objects.filter(compra__in=queryset)

            resultado = {
                'tipo': 'por_producto',
                'columnas': ['producto', 'sku', 'categoria', 'cantidad_vendida', 'total_vendido', 'precio_unitario_promedio'],
                'datos': []
            }

            # Agrupar por producto con cálculos precisos
            datos = items.values(
                'producto__nombre',
                'producto__sku',
                'producto__categoria__nombre'
            ).annotate(
                cantidad_vendida=Sum('cantidad'),
                total_vendido=Sum('subtotal'),
                precio_unitario_promedio=Avg('precio_unitario'),
                numero_ventas=Count('compra', distinct=True)
            ).order_by('-total_vendido' if self.params['orden'] == '-total' else 'producto__nombre')

            if self.params['limite']:
                datos = datos[:self.params['limite']]

            for item in datos:
                resultado['datos'].append({
                    'producto': item['producto__nombre'],
                    'sku': item['producto__sku'],
                    'categoria': item['producto__categoria__nombre'] or 'Sin categoría',
                    'cantidad_vendida': item['cantidad_vendida'] or 0,
                    'total_vendido': float(item['total_vendido'] or 0),
                    'precio_unitario_promedio': float(item['precio_unitario_promedio'] or 0),
                    'numero_ventas': item['numero_ventas'] or 0
                })

            return resultado
        
        elif 'cliente' in agrupar_por:
            # Agrupar por cliente - MEJORADO con más métricas
            resultado = {
                'tipo': 'por_cliente',
                'columnas': ['cliente', 'email', 'telefono', 'cantidad_compras', 'total_pagado', 'promedio_compra', 'fecha_primera_compra', 'fecha_ultima_compra', 'dias_desde_ultima_compra'],
                'datos': []
            }

            # Obtener fecha actual para calcular días desde última compra
            from django.utils import timezone
            hoy = timezone.now().date()

            datos = queryset.values(
                'cliente__nombre',
                'cliente__email',
                'cliente__telefono'
            ).annotate(
                cantidad_compras=Count('id'),
                total_pagado=Sum('total'),
                promedio_compra=Avg('total'),
                fecha_primera_compra=Min('fecha'),
                fecha_ultima_compra=Max('fecha')
            ).order_by('-total_pagado' if self.params['orden'] == '-total' else 'cliente__nombre')

            if self.params['limite']:
                datos = datos[:self.params['limite']]

            for item in datos:
                # Calcular días desde última compra
                dias_desde_ultima = None
                if item['fecha_ultima_compra']:
                    fecha_ultima = item['fecha_ultima_compra'].date() if hasattr(item['fecha_ultima_compra'], 'date') else item['fecha_ultima_compra']
                    if isinstance(fecha_ultima, str):
                        from datetime import datetime
                        fecha_ultima = datetime.fromisoformat(fecha_ultima.replace('Z', '+00:00')).date()
                    dias_desde_ultima = (hoy - fecha_ultima).days

                resultado['datos'].append({
                    'cliente': item['cliente__nombre'],
                    'email': item['cliente__email'],
                    'telefono': item['cliente__telefono'] or 'Sin teléfono',
                    'cantidad_compras': item['cantidad_compras'],
                    'total_pagado': float(item['total_pagado'] or 0),
                    'promedio_compra': float(item['promedio_compra'] or 0),
                    'fecha_primera_compra': item['fecha_primera_compra'].strftime('%Y-%m-%d') if item['fecha_primera_compra'] else None,
                    'fecha_ultima_compra': item['fecha_ultima_compra'].strftime('%Y-%m-%d') if item['fecha_ultima_compra'] else None,
                    'dias_desde_ultima_compra': dias_desde_ultima,
                    'rango_fechas': f"{item['fecha_primera_compra'].strftime('%d/%m/%Y') if item['fecha_primera_compra'] else 'N/A'} - {item['fecha_ultima_compra'].strftime('%d/%m/%Y') if item['fecha_ultima_compra'] else 'N/A'}"
                })

            return resultado
        
        elif 'categoria' in agrupar_por:
            # Agrupar por categoría
            items = CompraItem.objects.filter(compra__in=queryset)
            
            resultado = {
                'tipo': 'por_categoria',
                'columnas': ['categoria', 'cantidad_productos', 'total_vendido'],
                'datos': []
            }
            
            datos = items.values(
                'producto__categoria__nombre'
            ).annotate(
                cantidad_productos=Count('producto', distinct=True),
                total_vendido=Sum('subtotal')
            ).order_by('-total_vendido' if self.params['orden'] == '-total' else 'producto__categoria__nombre')
            
            if self.params['limite']:
                datos = datos[:self.params['limite']]
            
            for item in datos:
                resultado['datos'].append({
                    'categoria': item['producto__categoria__nombre'] or 'Sin categoría',
                    'cantidad_productos': item['cantidad_productos'],
                    'total_vendido': float(item['total_vendido'])
                })
            
            return resultado
        
        elif 'fecha' in agrupar_por:
            # Agrupar por fecha (día)
            resultado = {
                'tipo': 'por_fecha',
                'columnas': ['fecha', 'cantidad_compras', 'total_vendido'],
                'datos': []
            }
            
            datos = queryset.extra(
                select={'fecha_dia': 'DATE(fecha)'}
            ).values('fecha_dia').annotate(
                cantidad_compras=Count('id'),
                total_vendido=Sum('total')
            ).order_by('fecha_dia')
            
            if self.params['limite']:
                datos = datos[:self.params['limite']]
            
            for item in datos:
                resultado['datos'].append({
                    'fecha': item['fecha_dia'].strftime('%Y-%m-%d') if item['fecha_dia'] else None,
                    'cantidad_compras': item['cantidad_compras'],
                    'total_vendido': float(item['total_vendido'] or 0)
                })
            
            return resultado
        
        return {'tipo': 'vacio', 'datos': []}
    
    def _consulta_clientes(self):
        """Genera reporte de clientes"""
        from clientes.models import Cliente
        
        queryset = Cliente.objects.all()
        
        resultado = {
            'tipo': 'clientes',
            'columnas': ['nombre', 'email', 'telefono', 'total_compras', 'monto_total'],
            'datos': []
        }
        
        datos = queryset.annotate(
            total_compras=Count('compras'),
            monto_total=Sum('compras__total')
        ).order_by('-monto_total' if self.params['orden'] == '-total' else 'nombre')
        
        if self.params['limite']:
            datos = datos[:self.params['limite']]
        
        for cliente in datos:
            resultado['datos'].append({
                'nombre': cliente.nombre,
                'email': cliente.email,
                'telefono': cliente.telefono,
                'total_compras': cliente.total_compras,
                'monto_total': float(cliente.monto_total or 0)
            })
        
        return resultado
    
    def _consulta_productos(self):
        """Genera reporte de productos"""
        from productos.models import Producto
        from compra.models import CompraItem

        # Base queryset con productos activos
        productos = Producto.objects.filter(activo=True)

        resultado = {
            'tipo': 'productos',
            'columnas': ['sku', 'nombre', 'categoria', 'precio', 'stock', 'ventas_totales', 'total_vendido'],
            'datos': []
        }

        # Obtener items de compra con filtros de fecha aplicados
        items_venta = CompraItem.objects.all()

        # Aplicar filtros de fecha a través de las compras
        if self.params['fecha_inicio'] or self.params['fecha_fin']:
            compras_filtradas = Compra.objects.all()
            compras_filtradas = self._aplicar_filtro_fechas(compras_filtradas, 'fecha')

            # Filtrar solo compras pagadas para ventas reales
            if 'pagado' not in self.params['filtros'] or self.params['filtros']['pagado'] is True:
                compras_filtradas = compras_filtradas.filter(pagado_en__isnull=False)

            items_venta = items_venta.filter(compra__in=compras_filtradas)

        # Calcular estadísticas por producto
        productos_con_ventas = productos.annotate(
            ventas_totales=Sum(
                'compraitem__cantidad',
                filter=Q(compraitem__in=items_venta) if items_venta.exists() else Q(pk__isnull=True)
            ),
            total_vendido=Sum(
                'compraitem__subtotal',
                filter=Q(compraitem__in=items_venta) if items_venta.exists() else Q(pk__isnull=True)
            )
        ).order_by('-ventas_totales' if self.params['orden'] == '-total' else 'nombre')

        if self.params['limite']:
            productos_con_ventas = productos_con_ventas[:self.params['limite']]

        for producto in productos_con_ventas:
            resultado['datos'].append({
                'sku': producto.sku,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                'precio': float(producto.precio),
                'stock': producto.stock,
                'ventas_totales': producto.ventas_totales or 0,
                'total_vendido': float(producto.total_vendido or 0)
            })

        return resultado
    
    def _consulta_inventario(self):
        """Genera reporte de inventario"""
        from productos.models import Producto
        
        queryset = Producto.objects.filter(activo=True)
        
        resultado = {
            'tipo': 'inventario',
            'columnas': ['sku', 'nombre', 'categoria', 'stock', 'precio', 'valor_inventario'],
            'datos': []
        }
        
        datos = queryset.annotate(
            valor_inventario=F('precio') * F('stock')
        ).order_by('stock' if self.params['orden'] != '-total' else '-stock')
        
        if self.params['limite']:
            datos = datos[:self.params['limite']]
        
        for producto in datos:
            resultado['datos'].append({
                'sku': producto.sku,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                'stock': producto.stock,
                'precio': float(producto.precio),
                'valor_inventario': float(producto.precio * producto.stock)
            })

        return resultado

    def _consulta_ventas_clientes_detallado(self):
        """Consulta específica: ventas del período con nombre cliente, cantidad compras, monto total, rango fechas"""
        from compra.models import Compra

        # Base queryset con filtros aplicados
        queryset = Compra.objects.select_related('cliente').all()
        queryset = self._aplicar_filtro_fechas(queryset, 'fecha')

        # Filtrar solo compras pagadas
        if 'pagado' not in self.params['filtros'] or self.params['filtros']['pagado'] is True:
            queryset = queryset.filter(pagado_en__isnull=False)

        resultado = {
            'tipo': 'ventas_clientes_detallado',
            'columnas': ['cliente', 'email', 'cantidad_compras', 'monto_total', 'rango_fechas'],
            'datos': []
        }

        datos = queryset.values(
            'cliente__nombre',
            'cliente__email'
        ).annotate(
            cantidad_compras=Count('id'),
            monto_total=Sum('total'),
            fecha_primera=Min('fecha'),
            fecha_ultima=Max('fecha')
        ).order_by('-monto_total')

        if self.params['limite']:
            datos = datos[:self.params['limite']]

        for item in datos:
            # Formatear rango de fechas
            rango_fechas = "N/A - N/A"
            if item['fecha_primera'] and item['fecha_ultima']:
                fecha_inicio = item['fecha_primera'].strftime('%d/%m/%Y')
                fecha_fin = item['fecha_ultima'].strftime('%d/%m/%Y')
                rango_fechas = f"{fecha_inicio} - {fecha_fin}"

            resultado['datos'].append({
                'cliente': item['cliente__nombre'],
                'email': item['cliente__email'],
                'cantidad_compras': item['cantidad_compras'],
                'monto_total': float(item['monto_total'] or 0),
                'rango_fechas': rango_fechas
            })

        return resultado

    def _consulta_top_productos(self):
        """Consulta específica: top productos más vendidos"""
        from productos.models import Producto
        from compra.models import CompraItem

        # Base con productos activos
        productos = Producto.objects.filter(activo=True)

        resultado = {
            'tipo': 'top_productos',
            'columnas': ['ranking', 'producto', 'sku', 'categoria', 'ventas_totales', 'total_vendido', 'precio_promedio'],
            'datos': []
        }

        # Obtener items de compra con filtros de fecha
        items_venta = CompraItem.objects.all()

        # Aplicar filtros de fecha a través de compras
        if self.params['fecha_inicio'] or self.params['fecha_fin']:
            compras_filtradas = Compra.objects.all()
            compras_filtradas = self._aplicar_filtro_fechas(compras_filtradas, 'fecha')

            # Solo compras pagadas
            if 'pagado' not in self.params['filtros'] or self.params['filtros']['pagado'] is True:
                compras_filtradas = compras_filtradas.filter(pagado_en__isnull=False)

            items_venta = items_venta.filter(compra__in=compras_filtradas)

        # Calcular estadísticas por producto
        productos_con_ventas = productos.annotate(
            ventas_totales=Sum(
                'compraitem__cantidad',
                filter=Q(compraitem__in=items_venta) if items_venta.exists() else Q(pk__isnull=True)
            ),
            total_vendido=Sum(
                'compraitem__subtotal',
                filter=Q(compraitem__in=items_venta) if items_venta.exists() else Q(pk__isnull=True)
            ),
            precio_promedio=Avg(
                'compraitem__precio_unitario',
                filter=Q(compraitem__in=items_venta) if items_venta.exists() else Q(pk__isnull=True)
            )
        ).filter(ventas_totales__gt=0).order_by('-ventas_totales')  # Solo productos con ventas > 0

        if self.params['limite']:
            productos_con_ventas = productos_con_ventas[:self.params['limite']]

        for ranking, producto in enumerate(productos_con_ventas, 1):
            resultado['datos'].append({
                'ranking': ranking,
                'producto': producto.nombre,
                'sku': producto.sku,
                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                'ventas_totales': producto.ventas_totales or 0,
                'total_vendido': float(producto.total_vendido or 0),
                'precio_promedio': float(producto.precio_promedio or producto.precio)
            })

        return resultado
