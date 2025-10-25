from rest_framework import viewsets, permissions, filters
from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
	queryset = Cliente.objects.all()
	serializer_class = ClienteSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['nombre', 'email', 'telefono']
	ordering_fields = ['fecha_creacion', 'nombre']

	def perform_create(self, serializer):
		# Por defecto asigna el cliente al usuario autenticado (si aplica)
		serializer.save(asignado_a=self.request.user)

	def get_queryset(self):
		qs = super().get_queryset()
		user = self.request.user
		if user.is_staff:
			return qs
		return qs.filter(asignado_a=user)
