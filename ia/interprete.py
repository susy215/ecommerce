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
        'inventario': ['inventario', 'stock', 'existencia'],
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
        self._detectar_agrupacion()
        self._detectar_metricas()
        self._detectar_filtros()
        self._detectar_orden()
        self._detectar_limite()
        
        return self.resultado
    
    def _detectar_formato(self):
        """Detecta el formato de salida"""
        for formato, palabras in self.FORMATOS.items():
            for palabra in palabras:
                if palabra in self.prompt:
                    self.resultado['formato'] = formato
                    return
    
    def _detectar_fechas(self):
        """Detecta rangos de fechas en el prompt"""
        # Patrón: dd/mm/yyyy
        patron_fecha = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        fechas = re.findall(patron_fecha, self.prompt)
        
        if len(fechas) >= 2:
            # Rango de fechas
            try:
                fecha_inicio = datetime(
                    int(fechas[0][2]), int(fechas[0][1]), int(fechas[0][0])
                )
                fecha_fin = datetime(
                    int(fechas[1][2]), int(fechas[1][1]), int(fechas[1][0]), 23, 59, 59
                )
                self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
                self.resultado['fecha_fin'] = timezone.make_aware(fecha_fin)
            except ValueError:
                pass
        elif len(fechas) == 1:
            # Una sola fecha
            try:
                fecha_inicio = datetime(
                    int(fechas[0][2]), int(fechas[0][1]), int(fechas[0][0])
                )
                self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
            except ValueError:
                pass
        
        # Detectar meses específicos
        for mes_nombre, mes_num in self.MESES.items():
            if mes_nombre in self.prompt:
                # Detectar año
                patron_anio = r'\b(20\d{2})\b'
                anio_match = re.search(patron_anio, self.prompt)
                anio = int(anio_match.group(1)) if anio_match else timezone.now().year
                
                fecha_inicio = datetime(anio, mes_num, 1)
                # Último día del mes
                if mes_num == 12:
                    fecha_fin = datetime(anio + 1, 1, 1) - timedelta(days=1)
                else:
                    fecha_fin = datetime(anio, mes_num + 1, 1) - timedelta(days=1)
                
                # Hacer las fechas timezone-aware
                self.resultado['fecha_inicio'] = timezone.make_aware(fecha_inicio)
                self.resultado['fecha_fin'] = timezone.make_aware(fecha_fin.replace(hour=23, minute=59, second=59))
                break
        
        # Detectar rangos relativos
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
    
    def _detectar_tipo_reporte(self):
        """Detecta el tipo de reporte solicitado"""
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
                # Con agrupación: 100 por defecto
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
            # Agrupar por producto
            items = CompraItem.objects.filter(compra__in=queryset)
            
            resultado = {
                'tipo': 'por_producto',
                'columnas': ['producto', 'sku', 'cantidad_vendida', 'total_vendido'],
                'datos': []
            }
            
            datos = items.values(
                'producto__nombre',
                'producto__sku'
            ).annotate(
                cantidad_vendida=Sum('cantidad'),
                total_vendido=Sum('subtotal')
            ).order_by('-total_vendido' if self.params['orden'] == '-total' else 'producto__nombre')
            
            if self.params['limite']:
                datos = datos[:self.params['limite']]
            
            for item in datos:
                resultado['datos'].append({
                    'producto': item['producto__nombre'],
                    'sku': item['producto__sku'],
                    'cantidad_vendida': item['cantidad_vendida'],
                    'total_vendido': float(item['total_vendido'])
                })
            
            return resultado
        
        elif 'cliente' in agrupar_por:
            # Agrupar por cliente
            resultado = {
                'tipo': 'por_cliente',
                'columnas': ['cliente', 'email', 'cantidad_compras', 'total_pagado', 'fecha_primera', 'fecha_ultima'],
                'datos': []
            }
            
            datos = queryset.values(
                'cliente__nombre',
                'cliente__email'
            ).annotate(
                cantidad_compras=Count('id'),
                total_pagado=Sum('total'),
                fecha_primera=Min('fecha'),
                fecha_ultima=Max('fecha')
            ).order_by('-total_pagado' if self.params['orden'] == '-total' else 'cliente__nombre')
            
            if self.params['limite']:
                datos = datos[:self.params['limite']]
            
            for item in datos:
                resultado['datos'].append({
                    'cliente': item['cliente__nombre'],
                    'email': item['cliente__email'],
                    'cantidad_compras': item['cantidad_compras'],
                    'total_pagado': float(item['total_pagado'] or 0),
                    'fecha_primera': item['fecha_primera'].strftime('%Y-%m-%d %H:%M') if item['fecha_primera'] else None,
                    'fecha_ultima': item['fecha_ultima'].strftime('%Y-%m-%d %H:%M') if item['fecha_ultima'] else None,
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
        
        queryset = Producto.objects.filter(activo=True)
        
        resultado = {
            'tipo': 'productos',
            'columnas': ['sku', 'nombre', 'categoria', 'precio', 'stock', 'ventas_totales'],
            'datos': []
        }
        
        datos = queryset.annotate(
            ventas_totales=Sum('compraitem__cantidad')
        ).order_by('-ventas_totales' if self.params['orden'] == '-total' else 'nombre')
        
        if self.params['limite']:
            datos = datos[:self.params['limite']]
        
        for producto in datos:
            resultado['datos'].append({
                'sku': producto.sku,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                'precio': float(producto.precio),
                'stock': producto.stock,
                'ventas_totales': producto.ventas_totales or 0
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
