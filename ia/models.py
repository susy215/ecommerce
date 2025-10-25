from django.db import models


class PrediccionAdminEntry(models.Model):
	"""Modelo proxy sin tabla para exponer una entrada en el admin
	que renderiza una vista con predicción de ventas.
	"""

	class Meta:
		managed = False
		verbose_name = 'Predicción de Ventas'
		verbose_name_plural = 'Predicción de Ventas'
