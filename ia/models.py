from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class PrediccionAdminEntry(models.Model):
	"""Modelo proxy sin tabla para exponer una entrada en el admin
	que renderiza una vista con predicción de ventas.
	"""

	class Meta:
		managed = False
		verbose_name = 'Predicción de Ventas'
		verbose_name_plural = 'Predicción de Ventas'


class ConsultaIA(models.Model):
	"""
	Historial de consultas realizadas por IA
	"""
	usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='consultas_ia', db_index=True)
	prompt = models.TextField(verbose_name='Consulta en lenguaje natural', db_index=True)
	prompt_interpretado = models.JSONField(null=True, blank=True, verbose_name='Interpretación del prompt')
	sql_generado = models.TextField(blank=True, verbose_name='SQL generado')
	formato_salida = models.CharField(
		max_length=20,
		choices=[
			('pantalla', 'Pantalla'),
			('pdf', 'PDF'),
			('excel', 'Excel'),
			('csv', 'CSV'),
		],
		default='pantalla',
		db_index=True
	)
	resultado = models.JSONField(null=True, blank=True, verbose_name='Resultado de la consulta')
	error = models.TextField(blank=True)
	fecha_consulta = models.DateTimeField(auto_now_add=True, db_index=True)
	tiempo_ejecucion = models.FloatField(null=True, blank=True, verbose_name='Tiempo de ejecución (segundos)')
	
	class Meta:
		db_table = 'consultas_ia'
		ordering = ['-fecha_consulta']
		verbose_name = 'Consulta IA'
		verbose_name_plural = 'Consultas IA'
		indexes = [
			models.Index(fields=['usuario', '-fecha_consulta'], name='idx_usuario_fecha'),
			models.Index(fields=['formato_salida', '-fecha_consulta'], name='idx_formato_fecha'),
		]
	
	def __str__(self):
		return f"{self.usuario.username} - {self.prompt[:50]}..."


class ReporteGenerado(models.Model):
	"""
	Modelo proxy para entrada en admin que genera reportes con IA
	"""
	class Meta:
		managed = False
		verbose_name = 'Generar Reporte con IA'
		verbose_name_plural = 'Generar Reportes con IA'
