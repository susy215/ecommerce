from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.http import HttpResponse
from django.utils import timezone
import time

from .interprete import InterpretadorPrompt, GeneradorConsultas
from .generador_reportes import GeneradorReportes
from .models import ConsultaIA


class HealthView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		return Response({'status': 'ok'})


class ConsultaIAView(APIView):
	"""
	API para procesar consultas en lenguaje natural y generar reportes
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request):
		"""
		Procesa un prompt y devuelve los datos o genera un archivo
		
		Body:
		{
			"prompt": "Quiero un reporte de ventas del mes de septiembre en PDF",
			"formato": "pdf"  // opcional, se puede inferir del prompt
		}
		"""
		prompt = request.data.get('prompt', '').strip()
		
		if not prompt:
			return Response(
				{'detail': 'Se requiere un prompt'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Medir tiempo
		inicio = time.time()
		
		try:
			# 1. Interpretar prompt
			interprete = InterpretadorPrompt(prompt)
			interpretacion = interprete.interpretar()
			
			# Override formato si se especifica
			if 'formato' in request.data:
				interpretacion['formato'] = request.data['formato']
			
			# 2. Generar consulta
			generador = GeneradorConsultas(interpretacion)
			resultado = generador.generar_consulta()
			
			# 3. Convertir para JSON serialization
			from .interprete import convert_decimal_to_float
			interpretacion_serializable = convert_decimal_to_float(interpretacion)
			resultado_serializable = convert_decimal_to_float(resultado)
			
			# 4. Guardar en historial
			consulta = ConsultaIA.objects.create(
				usuario=request.user,
				prompt=prompt,
				prompt_interpretado=interpretacion_serializable,
				formato_salida=interpretacion['formato'],
				resultado=resultado_serializable,
				tiempo_ejecucion=time.time() - inicio
			)
			
			# 5. Responder según formato
			formato = interpretacion['formato']
			
			if formato == 'pantalla':
				# Devolver JSON con los datos
				return Response({
					'consulta_id': consulta.id,
					'interpretacion': interpretacion_serializable,
					'resultado': resultado_serializable,
					'tiempo_ejecucion': round(time.time() - inicio, 2)
				})
			else:
				# Generar archivo
				generador_reporte = GeneradorReportes(resultado, interpretacion)
				buffer = generador_reporte.generar(formato)
				
				# Preparar respuesta
				if formato == 'pdf':
					content_type = 'application/pdf'
					extension = 'pdf'
				elif formato == 'excel':
					content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
					extension = 'xlsx'
				elif formato == 'csv':
					content_type = 'text/csv'
					extension = 'csv'
				
				response = HttpResponse(buffer.read(), content_type=content_type)
				filename = f"reporte_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
				response['Content-Disposition'] = f'attachment; filename="{filename}"'
				
				return response
		
		except Exception as e:
			# Guardar error
			ConsultaIA.objects.create(
				usuario=request.user,
				prompt=prompt,
				error=str(e),
				tiempo_ejecucion=time.time() - inicio
			)
			
			return Response(
				{'detail': f'Error al procesar consulta: {str(e)}'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

