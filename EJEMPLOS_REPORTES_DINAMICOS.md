# 🚀 Ejemplos Prácticos - Reportes Dinámicos con IA y ML

## 📋 Comandos cURL para Probar el Sistema

### 🔧 Configuración Inicial

```bash
# Obtener token de autenticación primero
TOKEN="tu_token_aqui"  # Reemplaza con tu token real

# URL base
BASE_URL="https://smartsales365.duckdns.org/api/reportes-dinamicos/avanzados/"
```

### 📊 1. Predicciones Simples

#### Predicción de Ventas Básica
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Predice las ventas para el próximo mes" \
     --data-urlencode "formato=pdf" \
     -o "prediccion_ventas.pdf"
```

#### Predicción con Período Específico
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Pronóstico de ventas para los próximos 60 días" \
     --data-urlencode "formato=excel" \
     --data-urlencode "dias_prediccion=60" \
     -o "pronostico_60_dias.xlsx"
```

### 🔄 2. Comparaciones Históricas vs Predicciones

#### Comparación Mensual
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Compara ventas reales del último mes con predicciones" \
     --data-urlencode "formato=pdf" \
     -o "comparacion_mensual.pdf"
```

#### Análisis de Desviaciones
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Análisis de desviaciones: dónde las predicciones acertaron y fallaron" \
     --data-urlencode "formato=excel" \
     -o "analisis_desviaciones.xlsx"
```

### 🎯 3. Análisis de Rendimiento con ML

#### Productos con Mayor Potencial
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Top productos con mejor rendimiento predictivo según ML" \
     --data-urlencode "formato=pdf" \
     -o "productos_potencial.pdf"
```

#### Clientes con Crecimiento Esperado
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Clientes con mayor potencial de crecimiento basado en predicciones" \
     --data-urlencode "formato=csv" \
     -o "clientes_crecimiento.csv"
```

#### Análisis de Categorías
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Categorías con tendencias positivas según el modelo ML" \
     --data-urlencode "formato=excel" \
     -o "categorias_tendencias.xlsx"
```

### 📈 4. Reportes Ejecutivos

#### Dashboard Ejecutivo Completo
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Reporte ejecutivo mensual con métricas, predicciones e insights" \
     --data-urlencode "formato=pdf" \
     --data-urlencode "incluir_insights=true" \
     -o "reporte_ejecutivo.pdf"
```

#### Resumen Semanal con Recomendaciones
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Resumen semanal: rendimiento vs predicciones con recomendaciones" \
     --data-urlencode "formato=pdf" \
     -o "resumen_semanal.pdf"
```

### 📱 5. Consultas para Visualización Web

#### Datos para Dashboard
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Predicciones para dashboard de ventas" \
     --data-urlencode "formato=pantalla" \
     --data-urlencode "dias_prediccion=30"
```

#### Insights en Tiempo Real
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Insights automáticos: oportunidades y riesgos actuales" \
     --data-urlencode "formato=pantalla" \
     --data-urlencode "incluir_insights=true"
```

## 🎨 Ejemplos Avanzados de Prompts

### Consultas Complejas
```
"Genera un reporte comparativo entre ventas reales de septiembre y predicciones para octubre, identificando productos con mejor y peor rendimiento en PDF"

"Análisis predictivo: cuáles serán los 5 productos más vendidos el próximo mes según el modelo ML, con recomendaciones de inventario"

"Reporte ejecutivo trimestral: evolución de ventas, predicciones para el próximo trimestre, insights de ML y recomendaciones estratégicas en Excel"

"Dashboard de riesgos: productos que podrían quedar por debajo de las predicciones, con alertas de inventario crítico"
```

### Consultas Específicas por Negocio
```
"Predicción de temporada navideña: estima ventas para diciembre basado en patrones históricos y tendencias actuales"

"Análisis de clientes VIP: cuáles tendrán mayor crecimiento en compras según predicciones ML"

"Optimización de inventario: productos con alta predicción pero bajo stock actual"
```

## 🔧 Scripts de Automatización

### Bash Script para Reportes Diarios
```bash
#!/bin/bash
# reportes_diarios.sh

TOKEN="tu_token_aqui"
BASE_URL="https://smartsales365.duckdns.org/api/reportes-dinamicos/avanzados/"
FECHA=$(date +%Y-%m-%d)

# Reporte ejecutivo diario
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Reporte ejecutivo diario con predicciones" \
     --data-urlencode "formato=pdf" \
     -o "reporte_ejecutivo_$FECHA.pdf"

# Predicciones actualizadas
curl -H "Authorization: Bearer $TOKEN" \
     -G "$BASE_URL" \
     --data-urlencode "prompt=Predicciones actualizadas para hoy" \
     --data-urlencode "formato=excel" \
     -o "predicciones_$FECHA.xlsx"

echo "Reportes diarios generados: $FECHA"
```

### Python Script para Integración
```python
import requests
import json
from datetime import datetime

class ClienteReportesDinamicos:
    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}

    def generar_reporte(self, prompt, formato='pdf', **kwargs):
        params = {
            'prompt': prompt,
            'formato': formato,
            **kwargs
        }

        response = requests.get(self.base_url, headers=self.headers, params=params)
        return response.json()

    def reportes_diarios(self):
        """Genera suite completa de reportes diarios"""
        reportes = [
            ("Predicciones para hoy", "predicciones_hoy.pdf"),
            ("Análisis de rendimiento productos", "rendimiento_productos.xlsx"),
            ("Insights ejecutivos", "insights_ejecutivos.pdf")
        ]

        for prompt, filename in reportes:
            print(f"Generando: {filename}")
            resultado = self.generar_reporte(prompt, formato='pdf')
            if resultado.get('success'):
                # Guardar archivo
                with open(filename, 'wb') as f:
                    # Decodificar base64 y guardar
                    pass
            else:
                print(f"Error en {filename}: {resultado.get('error')}")

# Uso
cliente = ClienteReportesDinamicos("tu_token", "https://smartsales365.duckdns.org/api/reportes-dinamicos/avanzados/")
cliente.reportes_diarios()
```

## 📊 Casos de Uso Empresarial

### 1. Retail/E-commerce
- **Predicción de demanda** por producto y temporada
- **Optimización de inventario** basada en ML
- **Análisis de clientes** con mayor LTV potencial

### 2. Servicios Financieros
- **Predicción de ingresos** futuros
- **Análisis de riesgo** de impagos
- **Segmentación de clientes** por comportamiento predictivo

### 3. Manufactura
- **Pronóstico de demanda** de materias primas
- **Optimización de producción** basada en predicciones
- **Análisis de eficiencia** por línea de producción

### 4. SaaS/Software
- **Predicción de churn** de clientes
- **Estimación de crecimiento** de usuarios
- **Análisis de feature adoption** predictivo

## 🚀 Próximos Pasos

1. **Probar los ejemplos** con tu token real
2. **Crear automatizaciones** para reportes recurrentes
3. **Integrar con tu frontend** usando los hooks de React
4. **Personalizar prompts** según tus necesidades específicas
5. **Configurar alertas** basadas en insights de ML

## 🆘 Troubleshooting

### Error: "Consulta no interpretada"
```json
{"error": "No se pudo interpretar la consulta"}
```
**Solución:** Usa prompts más específicos y revisa los ejemplos.

### Error: "Modelo ML no disponible"
```json
{"error": "Modelo de predicción no entrenado"}
```
**Solución:** Ejecuta entrenamiento del modelo ML.

### Error: "Archivo muy grande"
```json
{"error": "El reporte excede el límite de tamaño"}
```
**Solución:** Reduce el período de análisis o usa formato CSV.

---

¡Experimenta con diferentes prompts y descubre el poder de los reportes dinámicos con IA! 🤖📊
