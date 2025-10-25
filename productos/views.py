from rest_framework import viewsets, permissions, filters
from .models import Producto, Categoria
from .serializers import ProductoSerializer, CategoriaSerializer


class ProductoViewSet(viewsets.ModelViewSet):
	queryset = Producto.objects.all()
	serializer_class = ProductoSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['sku', 'nombre', 'descripcion']
	ordering_fields = ['nombre', 'precio', 'stock', 'fecha_creacion']

	def get_permissions(self):
		# Solo admin puede crear/editar/eliminar; todos los autenticados pueden leer
		if self.action in ['create', 'update', 'partial_update', 'destroy']:
			return [permissions.IsAdminUser()]
		return super().get_permissions()

	def get_queryset(self):
		qs = super().get_queryset()
		categoria = self.request.query_params.get('categoria')
		if categoria:
			try:
				qs = qs.filter(categoria_id=int(categoria))
			except ValueError:
				pass
		# Usuarios no admin solo ven productos activos
		if not self.request.user.is_staff:
			qs = qs.filter(activo=True)
		return qs


class CategoriaViewSet(viewsets.ModelViewSet):
	queryset = Categoria.objects.all()
	serializer_class = CategoriaSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_permissions(self):
		# Solo admin puede crear/editar/eliminar; todos los autenticados pueden leer
		if self.action in ['create', 'update', 'partial_update', 'destroy']:
			return [permissions.IsAdminUser()]
		return super().get_permissions()
