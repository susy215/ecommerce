from django.db import models
from django.conf import settings


class Cliente(models.Model):
	usuario = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='perfil_cliente',
		help_text='Usuario asociado (si el cliente tiene cuenta)'
	)
	nombre = models.CharField(max_length=150)
	email = models.EmailField(blank=True, null=True)
	telefono = models.CharField(max_length=20, blank=True)
	direccion = models.CharField(max_length=255, blank=True)
	asignado_a = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='clientes_asignados',
	)
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	fecha_actualizacion = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'clientes'
		ordering = ['-fecha_creacion']
		verbose_name = 'Cliente'
		verbose_name_plural = 'Clientes'

	def __str__(self):
		return self.nombre
