# 🎤 Documentación de IA con Reconocimiento de Voz para Flutter

## 📋 Índice
1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Autenticación](#autenticación)
4. [API Endpoints](#api-endpoints)
5. [Capacidades del Backend](#capacidades-del-backend)
6. [Limitaciones](#limitaciones)
7. [Ejemplos de Prompts](#ejemplos-de-prompts)
8. [Integración con Flutter](#integración-con-flutter)
9. [Manejo de Errores](#manejo-de-errores)
10. [Código de Ejemplo Flutter](#código-de-ejemplo-flutter)

---

## 🎯 Introducción

El backend de SmartSales365 incluye un **motor de IA con procesamiento de lenguaje natural (NLP)** que puede interpretar consultas en español y generar reportes automáticamente en múltiples formatos.

### ¿Qué puede hacer?
- ✅ Interpretar prompts en lenguaje natural (español)
- ✅ Detectar automáticamente tipo de reporte, fechas, filtros, agrupaciones
- ✅ Generar reportes de: **ventas**, **clientes**, **productos**, **inventario**
- ✅ Exportar en: **PDF**, **Excel**, **CSV** o mostrar en **pantalla** (JSON)
- ✅ Guardar historial de consultas por usuario
- ✅ Optimizado para rendimiento (límites automáticos, índices DB)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐
│  Flutter App    │
│  (Voz → Texto)  │
└────────┬────────┘
         │ HTTP POST
         │ Token Auth
         ▼
┌─────────────────────────────────────┐
│  Backend Django REST API            │
│  Endpoint: /api/ia/consulta/        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  InterpretadorPrompt                │
│  • Detecta tipo de reporte          │
│  • Detecta fechas (meses, rangos)   │
│  • Detecta formato (PDF/Excel/CSV)  │
│  • Detecta agrupaciones             │
│  • Detecta filtros y límites        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  GeneradorConsultas                 │
│  • Construye query SQL dinámica     │
│  • Aplica filtros y agrupaciones    │
│  • Optimiza con select_related      │
│  • Limita resultados (max 1000)     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  GeneradorReportes                  │
│  • PDF: ReportLab con estilos       │
│  • Excel: openpyxl con formato      │
│  • CSV: Python csv module           │
│  • JSON: Datos estructurados        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Respuesta HTTP                     │
│  • JSON: Datos + metadata           │
│  • Archivo: PDF/Excel/CSV descarga  │
└─────────────────────────────────────┘
```

---

## 🔐 Autenticación

**Todas las peticiones requieren autenticación por Token.**

### 1. Obtener Token
```http
POST /api/usuarios/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Respuesta:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_staff": true
}
```

### 2. Usar Token en Peticiones
```http
POST /api/ia/consulta/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json
```

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/ia/
```

### 1. Health Check
```http
GET /api/ia/health/
Authorization: Token YOUR_TOKEN
```

**Respuesta:**
```json
{
  "status": "ok"
}
```

---

### 2. Consulta de IA (Principal)
```http
POST /api/ia/consulta/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "prompt": "Quiero un reporte de ventas del mes de septiembre en PDF",
  "formato": "pdf"  // OPCIONAL: se puede inferir del prompt
}
```

#### Parámetros del Body

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `prompt` | string | ✅ Sí | Consulta en lenguaje natural (min 10 caracteres) |
| `formato` | string | ❌ No | Sobrescribe formato detectado: `pantalla`, `pdf`, `excel`, `csv` |

---

### 3. Respuestas según Formato

#### A. Formato `pantalla` (JSON)
```json
{
  "consulta_id": 123,
  "interpretacion": {
    "tipo_reporte": "ventas",
    "fecha_inicio": "2024-09-01T00:00:00-05:00",
    "fecha_fin": "2024-09-30T23:59:59-05:00",
    "formato": "pantalla",
    "agrupar_por": ["producto"],
    "metricas": ["total", "cantidad"],
    "filtros": {},
    "orden": "-total",
    "limite": 100
  },
  "resultado": {
    "tipo": "por_producto",
    "columnas": ["producto", "sku", "cantidad_vendida", "total_vendido"],
    "datos": [
      {
        "producto": "Laptop HP",
        "sku": "LAP-001",
        "cantidad_vendida": 15,
        "total_vendido": 15000.00
      },
      {
        "producto": "Mouse Logitech",
        "sku": "MOU-002",
        "cantidad_vendida": 45,
        "total_vendido": 2250.00
      }
    ]
  },
  "tiempo_ejecucion": 0.23
}
```

#### B. Formato `pdf`, `excel`, `csv` (Archivo Binario)
```http
HTTP/1.1 200 OK
Content-Type: application/pdf  // o application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="reporte_20241028_143522.pdf"

[Contenido binario del archivo]
```

**Headers de Respuesta:**
- `Content-Type`: Tipo MIME del archivo
  - PDF: `application/pdf`
  - Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - CSV: `text/csv`
- `Content-Disposition`: Nombre del archivo generado

---

## ✅ Capacidades del Backend

### 📊 Tipos de Reporte Soportados

| Tipo | Palabras Clave | Datos que Retorna |
|------|----------------|-------------------|
| **Ventas** | venta, ventas, compra, compras, pedido, pedidos | Datos de transacciones (Compra model) |
| **Clientes** | cliente, clientes | Lista de clientes con total comprado |
| **Productos** | producto, productos | Catálogo con ventas totales |
| **Inventario** | inventario, stock, existencia | Stock actual y valor monetario |

### 📅 Detección de Fechas

#### 1. Formato Explícito (dd/mm/yyyy o dd-mm-yyyy)
```
"Ventas del 01/10/2024 al 31/10/2024"
"Ventas del 01-10-2024 al 31-10-2024"
```
**Resultado:** Rango específico de fechas

#### 2. Meses en Español
```
"Ventas de septiembre"           → Todo septiembre del año actual
"Ventas de septiembre 2024"      → Septiembre 2024
"Ventas de diciembre de 2023"    → Diciembre 2023
```
**Meses soportados:** enero, febrero, marzo, abril, mayo, junio, julio, agosto, septiembre, octubre, noviembre, diciembre

#### 3. Rangos Relativos
```
"Ventas de la última semana"  → Últimos 7 días
"Ventas del último mes"        → Últimos 30 días
"Ventas de este mes"           → Desde día 1 del mes actual hasta hoy
```

### 📊 Agrupaciones Soportadas

| Agrupación | Palabras Clave | Aplicable a |
|------------|----------------|-------------|
| **Por Producto** | "por producto", "agrupado por producto" | Ventas |
| **Por Cliente** | "por cliente", "agrupado por cliente" | Ventas |
| **Por Categoría** | "por categoría", "por tipo" | Ventas, Productos |
| **Por Fecha** | "por fecha", "por día" | Ventas |

**Ejemplo:**
```
"Ventas de octubre agrupado por producto en PDF"
```

### 📈 Métricas Detectadas

| Métrica | Palabras Clave | Descripción |
|---------|----------------|-------------|
| **Total** | total, suma, monto, dinero, pagado | Suma de valores monetarios |
| **Cantidad** | cantidad, número, count, cuantos | Conteo de registros |
| **Promedio** | promedio, media, avg | Promedio aritmético |
| **Máximo** | máximo, max, mayor | Valor más alto |
| **Mínimo** | mínimo, min, menor | Valor más bajo |

**Métricas por defecto:**
- Ventas: `total` + `cantidad`
- Clientes: `cantidad` + `total`
- Productos: `cantidad`

### 🎯 Filtros Soportados

#### 1. Estado de Pago
```
"Ventas pagadas de octubre"           → Solo ventas pagadas
"Ventas pendientes de este mes"        → Solo ventas no pagadas
```

#### 2. Categoría Específica
```
"Productos de categoría 'Electrónica'"
```

### 🔢 Límites y Ordenamiento

#### Top N / Primeros N
```
"Top 10 productos más vendidos"       → Límite: 10
"Los 5 clientes con más compras"      → Límite: 5
"Primeros 20 productos"                → Límite: 20
```
**Máximo permitido:** 1000 registros

#### Ordenamiento
```
"Ventas ordenadas de mayor a menor"   → Descendente
"Productos de menor a mayor precio"   → Ascendente
```

#### Límites Automáticos (si no se especifica)
- **Con agrupación:** 100 registros por defecto
- **Sin agrupación:** 1000 registros por defecto

### 📄 Formatos de Salida

| Formato | Palabras Clave | Content-Type | Características |
|---------|----------------|--------------|-----------------|
| **PDF** | pdf | application/pdf | Tablas estilizadas con ReportLab, encabezados, colores alternados |
| **Excel** | excel, xls, xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | Formato con colores, bordes, filtros |
| **CSV** | csv | text/csv | Texto plano separado por comas |
| **Pantalla** | pantalla, web, html | application/json | Datos estructurados en JSON |

---

## ⚠️ Limitaciones

### 1. **Límites de Rendimiento**
- ❌ No se permiten más de **1000 registros** por consulta
- ⚠️ Consultas sin límite tienen límite automático (100 con agrupación, 1000 sin agrupación)

### 2. **Idioma**
- ✅ Solo soporta **español** (México/Latinoamérica)
- ❌ No soporta inglés u otros idiomas

### 3. **Detección de Entidades**
- ⚠️ Usa **regex** y **palabras clave**, no IA avanzada (GPT)
- ⚠️ Requiere prompts claros y específicos
- ❌ No entiende contexto complejo o preguntas ambiguas

### 4. **Tipos de Reporte**
- ✅ Solo 4 tipos: ventas, clientes, productos, inventario
- ❌ No soporta otros tipos (empleados, proveedores, etc.)

### 5. **Agrupaciones Múltiples**
- ⚠️ Se pueden detectar múltiples agrupaciones, pero el backend solo usa la primera
- Ejemplo: "Por producto y por cliente" → Solo agrupa por producto

### 6. **Filtros Avanzados**
- ❌ No soporta rangos de precios (ej: "productos entre $100 y $500")
- ❌ No soporta comparaciones complejas
- ✅ Solo soporta: pagado/pendiente, categoría específica

### 7. **Formato de Fechas**
- ✅ Soporta: dd/mm/yyyy, dd-mm-yyyy
- ❌ No soporta: mm/dd/yyyy, yyyy-mm-dd en prompts (solo en parámetros)

### 8. **Validaciones**
```json
// Errores posibles:
{
  "detail": "Se requiere un prompt"                    // prompt vacío
}
{
  "detail": "⚠️ La consulta es muy corta..."          // menos de 10 caracteres
}
{
  "detail": "⚠️ No entendí qué tipo de reporte..."    // tipo no detectado
}
{
  "detail": "📭 No se encontraron datos..."           // sin resultados
}
```

---

## 💬 Ejemplos de Prompts

### ✅ Prompts Válidos y Bien Formados

#### 1. Ventas con Fecha y Formato
```json
{
  "prompt": "Quiero un reporte de ventas del mes de septiembre, agrupado por producto, en PDF"
}
```
**Interpretación:**
- Tipo: `ventas`
- Fechas: `01/09/2024 - 30/09/2024`
- Agrupación: `producto`
- Formato: `pdf`

---

#### 2. Ventas con Rango de Fechas y Cliente
```json
{
  "prompt": "Quiero un reporte en Excel que muestre las ventas del periodo del 01/10/2024 al 01/01/2025. Debe mostrar el nombre del cliente, la cantidad de compras que realizó, el monto total que pagó y el rango de fechas en las que hizo la compra"
}
```
**Interpretación:**
- Tipo: `ventas`
- Fechas: `01/10/2024 - 01/01/2025`
- Agrupación: `cliente`
- Formato: `excel`
- Métricas: `cantidad`, `total`

**Resultado esperado:**
```json
{
  "tipo": "por_cliente",
  "columnas": ["cliente", "email", "cantidad_compras", "total_pagado", "fecha_primera", "fecha_ultima"],
  "datos": [
    {
      "cliente": "Juan Pérez",
      "email": "juan@example.com",
      "cantidad_compras": 8,
      "total_pagado": 12500.00,
      "fecha_primera": "2024-10-05 10:30",
      "fecha_ultima": "2024-12-28 15:45"
    }
  ]
}
```

---

#### 3. Top Productos más Vendidos
```json
{
  "prompt": "Dame los top 10 productos más vendidos del último mes en pantalla"
}
```
**Interpretación:**
- Tipo: `ventas`
- Agrupación: `producto`
- Límite: `10`
- Orden: `-total` (descendente)
- Formato: `pantalla`
- Fechas: Últimos 30 días

---

#### 4. Clientes Activos
```json
{
  "prompt": "Lista de clientes activos que compraron en octubre de 2024 en CSV"
}
```
**Interpretación:**
- Tipo: `clientes`
- Fechas: `01/10/2024 - 31/10/2024` (aplica a las compras)
- Formato: `csv`

---

#### 5. Inventario Actual
```json
{
  "prompt": "Muéstrame el inventario actual con stock y valor en Excel"
}
```
**Interpretación:**
- Tipo: `inventario`
- Formato: `excel`
- Sin filtros de fecha

**Resultado esperado:**
```json
{
  "tipo": "inventario",
  "columnas": ["sku", "nombre", "categoria", "stock", "precio", "valor_inventario"],
  "datos": [
    {
      "sku": "LAP-001",
      "nombre": "Laptop HP",
      "categoria": "Electrónica",
      "stock": 25,
      "precio": 1200.00,
      "valor_inventario": 30000.00
    }
  ]
}
```

---

#### 6. Ventas por Categoría
```json
{
  "prompt": "Ventas de este mes agrupadas por categoría en PDF ordenadas de mayor a menor"
}
```

---

#### 7. Productos con Pocas Ventas
```json
{
  "prompt": "Los 20 productos con menos ventas del año 2024 en Excel"
}
```

---

### ❌ Prompts Inválidos (no funcionarán correctamente)

```json
// Muy corto
{ "prompt": "ventas" }  
// Error: "⚠️ La consulta es muy corta..."

// Ambiguo
{ "prompt": "Dame información" }
// Error: "⚠️ No entendí qué tipo de reporte..."

// Inglés (no soportado)
{ "prompt": "Show me sales report for September in PDF" }
// Error: No detectará correctamente

// Formato de fecha incorrecto
{ "prompt": "Ventas del 2024-10-01 al 2024-10-31" }
// Puede no detectar fechas correctamente

// Tipo no soportado
{ "prompt": "Reporte de empleados del mes" }
// Error: tipo_reporte será 'ventas' por defecto
```

---

## 📱 Integración con Flutter

### Paquetes Recomendados

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP para API
  http: ^1.1.0
  
  # Reconocimiento de voz
  speech_to_text: ^6.5.1
  
  # Permisos
  permission_handler: ^11.0.1
  
  # Manejo de archivos
  path_provider: ^2.1.1
  
  # Abrir archivos descargados
  open_file: ^3.3.2
  
  # Estado global (opcional)
  provider: ^6.1.1
```

### Configuración de Permisos

#### Android (`android/app/src/main/AndroidManifest.xml`)
```xml
<manifest>
  <uses-permission android:name="android.permission.INTERNET" />
  <uses-permission android:name="android.permission.RECORD_AUDIO" />
  <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
  <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
</manifest>
```

#### iOS (`ios/Runner/Info.plist`)
```xml
<dict>
  <key>NSMicrophoneUsageDescription</key>
  <string>Necesitamos acceso al micrófono para reconocimiento de voz</string>
  <key>NSSpeechRecognitionUsageDescription</key>
  <string>Necesitamos reconocimiento de voz para procesar consultas</string>
</dict>
```

---

## 🛠️ Código de Ejemplo Flutter

### 1. Servicio de API

```dart
// lib/services/ia_api_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

class IAApiService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator
  // static const String baseUrl = 'http://localhost:8000'; // iOS simulator
  // static const String baseUrl = 'https://tu-dominio.com'; // Producción
  
  final String token;
  
  IAApiService({required this.token});
  
  Map<String, String> get _headers => {
    'Authorization': 'Token $token',
    'Content-Type': 'application/json',
  };
  
  /// Health check
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/ia/health/'),
        headers: _headers,
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
  
  /// Consulta de IA - Formato pantalla (JSON)
  Future<Map<String, dynamic>> consultarIA({
    required String prompt,
    String? formato,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/ia/consulta/'),
        headers: _headers,
        body: jsonEncode({
          'prompt': prompt,
          if (formato != null) 'formato': formato,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(utf8.decode(response.bodyBytes));
      } else {
        final error = jsonDecode(utf8.decode(response.bodyBytes));
        throw Exception(error['detail'] ?? 'Error desconocido');
      }
    } catch (e) {
      throw Exception('Error de conexión: $e');
    }
  }
  
  /// Descargar reporte (PDF/Excel/CSV)
  Future<File> descargarReporte({
    required String prompt,
    required String formato, // 'pdf', 'excel', 'csv'
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/ia/consulta/'),
        headers: _headers,
        body: jsonEncode({
          'prompt': prompt,
          'formato': formato,
        }),
      );
      
      if (response.statusCode == 200) {
        // Extraer nombre del archivo del header
        final contentDisposition = response.headers['content-disposition'];
        String filename = 'reporte.$formato';
        
        if (contentDisposition != null) {
          final regex = RegExp(r'filename="(.+)"');
          final match = regex.firstMatch(contentDisposition);
          if (match != null) {
            filename = match.group(1)!;
          }
        }
        
        // Guardar archivo
        final directory = await getApplicationDocumentsDirectory();
        final file = File('${directory.path}/$filename');
        await file.writeAsBytes(response.bodyBytes);
        
        return file;
      } else {
        final error = jsonDecode(utf8.decode(response.bodyBytes));
        throw Exception(error['detail'] ?? 'Error al descargar reporte');
      }
    } catch (e) {
      throw Exception('Error de descarga: $e');
    }
  }
}
```

---

### 2. Servicio de Reconocimiento de Voz

```dart
// lib/services/voice_service.dart
import 'package:speech_to_text/speech_to_text.dart';
import 'package:permission_handler/permission_handler.dart';

class VoiceService {
  final SpeechToText _speech = SpeechToText();
  bool _isInitialized = false;
  
  /// Inicializar servicio de voz
  Future<bool> initialize() async {
    if (_isInitialized) return true;
    
    // Solicitar permiso de micrófono
    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      throw Exception('Permiso de micrófono denegado');
    }
    
    // Inicializar speech_to_text
    _isInitialized = await _speech.initialize(
      onError: (error) => print('Error de voz: $error'),
      onStatus: (status) => print('Estado de voz: $status'),
    );
    
    return _isInitialized;
  }
  
  /// Escuchar comando de voz
  Future<String?> listen({
    required Function(String) onResult,
    Function(String)? onPartialResult,
  }) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    if (!_isInitialized) {
      throw Exception('No se pudo inicializar el reconocimiento de voz');
    }
    
    String? finalResult;
    
    await _speech.listen(
      onResult: (result) {
        if (result.finalResult) {
          finalResult = result.recognizedWords;
          onResult(result.recognizedWords);
        } else if (onPartialResult != null) {
          onPartialResult(result.recognizedWords);
        }
      },
      localeId: 'es_ES', // Español
      listenMode: ListenMode.confirmation,
    );
    
    // Esperar hasta que termine
    await Future.delayed(Duration(seconds: 5));
    await stop();
    
    return finalResult;
  }
  
  /// Detener escucha
  Future<void> stop() async {
    if (_speech.isListening) {
      await _speech.stop();
    }
  }
  
  /// Verificar si está escuchando
  bool get isListening => _speech.isListening;
  
  /// Verificar disponibilidad
  bool get isAvailable => _isInitialized && _speech.isAvailable;
}
```

---

### 3. Pantalla de Consulta con Voz

```dart
// lib/screens/ia_voice_screen.dart
import 'package:flutter/material.dart';
import 'package:open_file/open_file.dart';
import '../services/ia_api_service.dart';
import '../services/voice_service.dart';

class IAVoiceScreen extends StatefulWidget {
  final String token;
  
  const IAVoiceScreen({required this.token, Key? key}) : super(key: key);
  
  @override
  State<IAVoiceScreen> createState() => _IAVoiceScreenState();
}

class _IAVoiceScreenState extends State<IAVoiceScreen> {
  late IAApiService _apiService;
  late VoiceService _voiceService;
  
  String _prompt = '';
  String _status = 'Listo';
  bool _isListening = false;
  bool _isProcessing = false;
  Map<String, dynamic>? _resultado;
  
  @override
  void initState() {
    super.initState();
    _apiService = IAApiService(token: widget.token);
    _voiceService = VoiceService();
    _initVoice();
  }
  
  Future<void> _initVoice() async {
    try {
      await _voiceService.initialize();
      setState(() => _status = 'Micrófono listo');
    } catch (e) {
      setState(() => _status = 'Error: $e');
    }
  }
  
  /// Iniciar escucha de voz
  Future<void> _startListening() async {
    if (_isListening) return;
    
    setState(() {
      _isListening = true;
      _status = 'Escuchando...';
      _prompt = '';
    });
    
    try {
      await _voiceService.listen(
        onPartialResult: (text) {
          setState(() => _prompt = text);
        },
        onResult: (text) {
          setState(() {
            _prompt = text;
            _isListening = false;
            _status = 'Texto capturado. Procesando...';
          });
          _procesarConsulta();
        },
      );
    } catch (e) {
      setState(() {
        _isListening = false;
        _status = 'Error: $e';
      });
    }
  }
  
  /// Procesar consulta con IA
  Future<void> _procesarConsulta() async {
    if (_prompt.trim().isEmpty) {
      setState(() => _status = 'Prompt vacío');
      return;
    }
    
    setState(() {
      _isProcessing = true;
      _status = 'Consultando IA...';
      _resultado = null;
    });
    
    try {
      // Detectar si pide archivo o pantalla
      final solicitaArchivo = _prompt.toLowerCase().contains('pdf') ||
          _prompt.toLowerCase().contains('excel') ||
          _prompt.toLowerCase().contains('csv');
      
      if (solicitaArchivo) {
        // Descargar archivo
        String formato = 'pdf';
        if (_prompt.toLowerCase().contains('excel')) formato = 'excel';
        if (_prompt.toLowerCase().contains('csv')) formato = 'csv';
        
        final file = await _apiService.descargarReporte(
          prompt: _prompt,
          formato: formato,
        );
        
        setState(() {
          _status = 'Reporte descargado: ${file.path}';
          _isProcessing = false;
        });
        
        // Abrir archivo
        await OpenFile.open(file.path);
        
      } else {
        // Mostrar en pantalla
        final resultado = await _apiService.consultarIA(
          prompt: _prompt,
          formato: 'pantalla',
        );
        
        setState(() {
          _resultado = resultado;
          _status = 'Consulta completada en ${resultado['tiempo_ejecucion']}s';
          _isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        _status = 'Error: $e';
        _isProcessing = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Consulta IA con Voz'),
        backgroundColor: Colors.deepPurple,
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Estado
            Card(
              color: _isListening
                  ? Colors.red.shade50
                  : _isProcessing
                      ? Colors.orange.shade50
                      : Colors.green.shade50,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(
                      _isListening
                          ? Icons.mic
                          : _isProcessing
                              ? Icons.hourglass_empty
                              : Icons.check_circle,
                      color: _isListening
                          ? Colors.red
                          : _isProcessing
                              ? Colors.orange
                              : Colors.green,
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _status,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            // Prompt capturado
            Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Prompt:',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      _prompt.isEmpty ? 'Presiona el micrófono y habla...' : _prompt,
                      style: TextStyle(
                        fontSize: 14,
                        color: _prompt.isEmpty ? Colors.grey : Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 24),
            
            // Botón de micrófono
            ElevatedButton.icon(
              onPressed: _isListening || _isProcessing ? null : _startListening,
              icon: Icon(Icons.mic, size: 32),
              label: Text(
                _isListening ? 'Escuchando...' : 'Presiona para hablar',
                style: TextStyle(fontSize: 18),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(vertical: 20),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            // Botón manual
            OutlinedButton.icon(
              onPressed: _isProcessing ? null : () {
                setState(() => _prompt = '');
                _showManualInputDialog();
              },
              icon: Icon(Icons.keyboard),
              label: Text('O escribe tu consulta'),
            ),
            
            SizedBox(height: 24),
            
            // Resultados
            if (_resultado != null) ...[
              Text(
                'Resultados:',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 8),
              Expanded(
                child: _buildResultado(_resultado!),
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  /// Mostrar diálogo de entrada manual
  void _showManualInputDialog() {
    final controller = TextEditingController(text: _prompt);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Escribe tu consulta'),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: InputDecoration(
            hintText: 'Ej: Ventas de octubre en PDF',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() => _prompt = controller.text);
              Navigator.pop(context);
              _procesarConsulta();
            },
            child: Text('Consultar'),
          ),
        ],
      ),
    );
  }
  
  /// Construir widget de resultados
  Widget _buildResultado(Map<String, dynamic> data) {
    final resultado = data['resultado'];
    final tipo = resultado['tipo'];
    final datos = resultado['datos'] as List;
    
    if (datos.isEmpty) {
      return Center(child: Text('Sin datos'));
    }
    
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SingleChildScrollView(
        child: DataTable(
          columns: (resultado['columnas'] as List)
              .map((col) => DataColumn(label: Text(col.toString().toUpperCase())))
              .toList(),
          rows: datos.map((row) {
            return DataRow(
              cells: (resultado['columnas'] as List).map((col) {
                final value = row[col];
                return DataCell(Text(value?.toString() ?? ''));
              }).toList(),
            );
          }).toList(),
        ),
      ),
    );
  }
}
```

---

### 4. Ejemplos de Uso

```dart
// Ejemplo 1: Consulta simple
final apiService = IAApiService(token: 'tu_token_aqui');

try {
  final resultado = await apiService.consultarIA(
    prompt: 'Ventas de octubre en pantalla',
  );
  
  print('Tipo: ${resultado['resultado']['tipo']}');
  print('Datos: ${resultado['resultado']['datos']}');
} catch (e) {
  print('Error: $e');
}

// Ejemplo 2: Descargar PDF
try {
  final file = await apiService.descargarReporte(
    prompt: 'Top 10 productos más vendidos',
    formato: 'pdf',
  );
  
  print('Archivo guardado en: ${file.path}');
  await OpenFile.open(file.path);
} catch (e) {
  print('Error: $e');
}

// Ejemplo 3: Con reconocimiento de voz
final voiceService = VoiceService();
await voiceService.initialize();

final prompt = await voiceService.listen(
  onResult: (text) => print('Capturado: $text'),
);

if (prompt != null) {
  final resultado = await apiService.consultarIA(prompt: prompt);
  print(resultado);
}
```

---

## 🚨 Manejo de Errores

### Errores HTTP Comunes

| Código | Significado | Acción Recomendada |
|--------|-------------|--------------------|
| 400 | Bad Request | Validar formato del prompt |
| 401 | Unauthorized | Renovar token de autenticación |
| 403 | Forbidden | Verificar permisos del usuario |
| 404 | Not Found | Verificar URL del endpoint |
| 500 | Internal Server Error | Mostrar mensaje amigable, reintentar |

### Ejemplo de Manejo de Errores

```dart
Future<void> consultarConManejo(String prompt) async {
  try {
    final resultado = await _apiService.consultarIA(prompt: prompt);
    // Procesar resultado
    
  } on SocketException {
    // Sin conexión a internet
    _mostrarError('Sin conexión a internet. Verifica tu red.');
    
  } on HttpException {
    // Error HTTP
    _mostrarError('Error de servidor. Intenta más tarde.');
    
  } on FormatException {
    // Error de formato JSON
    _mostrarError('Respuesta inválida del servidor.');
    
  } catch (e) {
    // Error genérico
    final mensaje = e.toString();
    
    if (mensaje.contains('⚠️') || mensaje.contains('❌')) {
      // Error amigable del backend
      _mostrarError(mensaje);
    } else {
      // Error técnico
      _mostrarError('Error: Contacta al administrador.');
    }
  }
}

void _mostrarError(String mensaje) {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Error'),
      content: Text(mensaje),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('OK'),
        ),
      ],
    ),
  );
}
```

---

## 📊 Estructura de Datos de Respuesta

### Respuesta para Ventas Agrupadas por Producto

```json
{
  "consulta_id": 45,
  "interpretacion": {
    "tipo_reporte": "ventas",
    "fecha_inicio": "2024-09-01T00:00:00-05:00",
    "fecha_fin": "2024-09-30T23:59:59-05:00",
    "agrupar_por": ["producto"],
    "metricas": ["total", "cantidad"],
    "formato": "pantalla",
    "filtros": {},
    "orden": "-total",
    "limite": 100
  },
  "resultado": {
    "tipo": "por_producto",
    "columnas": ["producto", "sku", "cantidad_vendida", "total_vendido"],
    "datos": [
      {
        "producto": "Laptop HP Pavilion",
        "sku": "LAP-001",
        "cantidad_vendida": 15,
        "total_vendido": 18750.0
      },
      {
        "producto": "Mouse Logitech MX",
        "sku": "MOU-002",
        "cantidad_vendida": 45,
        "total_vendido": 2250.0
      }
    ]
  },
  "tiempo_ejecucion": 0.23
}
```

### Respuesta para Ventas Agrupadas por Cliente

```json
{
  "resultado": {
    "tipo": "por_cliente",
    "columnas": ["cliente", "email", "cantidad_compras", "total_pagado", "fecha_primera", "fecha_ultima"],
    "datos": [
      {
        "cliente": "Juan Pérez",
        "email": "juan@example.com",
        "cantidad_compras": 8,
        "total_pagado": 12500.0,
        "fecha_primera": "2024-10-05 10:30",
        "fecha_ultima": "2024-12-28 15:45"
      }
    ]
  }
}
```

### Respuesta para Inventario

```json
{
  "resultado": {
    "tipo": "inventario",
    "columnas": ["sku", "nombre", "categoria", "stock", "precio", "valor_inventario"],
    "datos": [
      {
        "sku": "LAP-001",
        "nombre": "Laptop HP",
        "categoria": "Electrónica",
        "stock": 25,
        "precio": 1200.0,
        "valor_inventario": 30000.0
      }
    ]
  }
}
```

---

## ✅ Checklist de Implementación

### Backend (Ya implementado ✅)
- ✅ Endpoint `/api/ia/consulta/` funcional
- ✅ Autenticación por Token
- ✅ Interpretador de prompts en español
- ✅ Generador de consultas SQL dinámicas
- ✅ Exportación a PDF/Excel/CSV
- ✅ Validaciones y límites de rendimiento
- ✅ Mensajes de error amigables
- ✅ Historial de consultas

### Flutter (Por implementar en tu app)
- ⬜ Configurar paquetes: `http`, `speech_to_text`, `permission_handler`
- ⬜ Configurar permisos en AndroidManifest.xml e Info.plist
- ⬜ Implementar `IAApiService` para llamadas al backend
- ⬜ Implementar `VoiceService` para reconocimiento de voz
- ⬜ Crear pantalla de consulta con botón de micrófono
- ⬜ Manejar respuestas JSON (mostrar tablas)
- ⬜ Manejar descargas de archivos (abrir PDFs/Excel)
- ⬜ Implementar manejo de errores con mensajes amigables
- ⬜ Agregar indicadores de carga (CircularProgressIndicator)
- ⬜ Probar con diferentes prompts

---

## 🎓 Consejos de UX

### 1. **Guiar al Usuario**
```dart
// Mostrar ejemplos de prompts al usuario
final ejemplos = [
  "Ventas de octubre en PDF",
  "Top 10 productos más vendidos en Excel",
  "Clientes activos del último mes",
  "Inventario actual en CSV",
];
```

### 2. **Feedback Visual**
```dart
// Animación de micrófono
AnimatedContainer(
  duration: Duration(milliseconds: 300),
  decoration: BoxDecoration(
    color: _isListening ? Colors.red : Colors.grey,
    shape: BoxShape.circle,
  ),
  child: Icon(Icons.mic, color: Colors.white),
)
```

### 3. **Confirmación Antes de Procesar**
```dart
// Mostrar prompt antes de enviar
showDialog(
  context: context,
  builder: (context) => AlertDialog(
    title: Text('Confirmar consulta'),
    content: Text('¿Procesar: "$_prompt"?'),
    actions: [
      TextButton(child: Text('Editar'), onPressed: () {}),
      TextButton(child: Text('Enviar'), onPressed: _procesarConsulta),
    ],
  ),
);
```

### 4. **Caché de Resultados**
```dart
// Guardar historial local
SharedPreferences prefs = await SharedPreferences.getInstance();
List<String> historial = prefs.getStringList('historial_prompts') ?? [];
historial.insert(0, _prompt);
await prefs.setStringList('historial_prompts', historial.take(10).toList());
```

---

## 📞 Soporte

Si tienes dudas o problemas:
1. Revisa los logs del servidor Django: `python manage.py runserver`
2. Verifica la tabla `consultas_ia` en la base de datos para ver errores guardados
3. Usa el admin de Django: `/admin/ia/consultaia/` para ver el historial

---

## 📝 Changelog

**Versión 1.0** (Octubre 2024)
- ✅ Interpretación de prompts en español
- ✅ 4 tipos de reporte: ventas, clientes, productos, inventario
- ✅ Exportación a PDF, Excel, CSV
- ✅ Detección de fechas (meses, rangos, relativos)
- ✅ Agrupaciones por producto, cliente, categoría, fecha
- ✅ Límites automáticos y ordenamiento
- ✅ Optimizaciones de rendimiento
- ✅ Mensajes de error amigables

---

**¡Feliz codificación! 🚀**
