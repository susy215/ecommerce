from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from .serializers import UsuarioSerializer, RegisterSerializer, AdminUserCreateSerializer

Usuario = get_user_model()


class IsSelfOrAdmin(permissions.BasePermission):
	"""Permite al usuario acceder/modificar su propio perfil; admins pueden todo."""

	def has_object_permission(self, request, view, obj):
		return bool(request.user and (request.user.is_staff or obj == request.user))


class UsuarioViewSet(viewsets.ModelViewSet):
	queryset = Usuario.objects.all().order_by('id')
	serializer_class = UsuarioSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['username', 'email', 'first_name', 'last_name']
	ordering_fields = ['id', 'username']

	def get_permissions(self):
		if self.action in ['list', 'destroy', 'create']:
			return [permissions.IsAdminUser()]
		if self.action in ['retrieve', 'update', 'partial_update']:
			return [IsSelfOrAdmin()]
		return super().get_permissions()

	def create(self, request, *args, **kwargs):
		# Solo admin puede crear usuarios vía API
		serializer = AdminUserCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)

	def _sanitize_user_update(self, request):
		# Bloquea campos peligrosos si no es admin
		if not request.user.is_staff:
			mutable = request.data.copy()
			for field in ['rol', 'is_staff', 'is_superuser', 'groups', 'user_permissions']:
				if field in mutable:
					mutable.pop(field)
			request._full_data = None  # reset DRF cached data
			request.data._mutable = True if hasattr(request.data, '_mutable') else True
			request.data.clear()
			request.data.update(mutable)

	def update(self, request, *args, **kwargs):
		self._sanitize_user_update(request)
		return super().update(request, *args, **kwargs)

	def partial_update(self, request, *args, **kwargs):
		self._sanitize_user_update(request)
		return super().partial_update(request, *args, **kwargs)

	@action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
	def me(self, request):
		if request.method == 'GET':
			serializer = self.get_serializer(request.user)
			return Response(serializer.data)
		serializer = self.get_serializer(request.user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)


class RegisterView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = RegisterSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)


class EmailOrUsernameTokenView(APIView):
	"""Devuelve un token aceptando username o email + password.
	CSRF no requerido (sin autenticadores), apto para frontend React.
	"""
	permission_classes = [permissions.AllowAny]
	authentication_classes = []

	def post(self, request):
		data = request.data
		username = (data.get('username') or '').strip()
		email = (data.get('email') or '').strip()
		password = (data.get('password') or '')

		if not username and not email:
			return Response({'detail': 'username o email requerido'}, status=400)
		if not password:
			return Response({'detail': 'password requerido'}, status=400)

		user = None
		# Si en username viene un correo, úsalo como email
		if not email and '@' in username:
			email = username
			username = ''

		if email:
			user = Usuario.objects.filter(email__iexact=email).order_by('id').first()
		else:
			user = Usuario.objects.filter(username__iexact=username).order_by('id').first()

		if not user or not user.is_active or not user.check_password(password):
			return Response({'detail': 'Credenciales inválidas'}, status=400)

		token, _ = Token.objects.get_or_create(user=user)
		return Response({'token': token.key})
