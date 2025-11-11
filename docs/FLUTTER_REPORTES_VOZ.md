# 🎤 Flutter - Reportes por Voz con IA

## 📱 Integración para Administrador en Flutter

Este documento describe cómo integrar el sistema de reportes con IA usando voz en Flutter.

---

## 🎯 Características

- ✅ **Comandos de voz**: Convierte voz a texto y genera reportes
- ✅ **Lenguaje natural**: Interpreta frases como "Quiero un reporte de ventas de octubre en PDF"
- ✅ **Múltiples formatos**: PDF, Excel, CSV, o JSON (pantalla)
- ✅ **Historial**: Todas las consultas se guardan automáticamente
- ✅ **Autenticación**: Token-based authentication

---

## 🔐 Autenticación

### 1. Login

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> login(String username, String password) async {
  final response = await http.post(
    Uri.parse('https://tu-backend.com/api/usuarios/token/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return {
      'token': data['token'],
      'user': data,
    };
  }
  throw Exception('Error al iniciar sesión');
}
```

### 2. Guardar Token

```dart
import 'package:shared_preferences/shared_preferences.dart';

Future<void> saveToken(String token) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString('auth_token', token);
}

Future<String?> getToken() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getString('auth_token');
}
```

---

## 🎤 Reconocimiento de Voz

### Instalar Dependencias

```yaml
dependencies:
  speech_to_text: ^6.3.0
  http: ^1.1.0
  shared_preferences: ^2.2.0
  path_provider: ^2.1.0
  open_filex: ^3.3.0  # Para abrir PDF/Excel
```

### Servicio de Reconocimiento de Voz

```dart
import 'package:speech_to_text/speech_to_text.dart' as stt;

class VoiceRecognitionService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  
  Future<bool> initialize() async {
    return await _speech.initialize(
      onError: (error) => print('Error: $error'),
      onStatus: (status) => print('Status: $status'),
    );
  }
  
  Future<String?> listen() async {
    if (!await initialize()) {
      return null;
    }
    
    String? text;
    bool isAvailable = await _speech.initialize();
    
    if (isAvailable) {
      _isListening = true;
      await _speech.listen(
        onResult: (result) {
          text = result.recognizedWords;
          if (result.finalResult) {
            _isListening = false;
          }
        },
        listenFor: Duration(seconds: 10),
        pauseFor: Duration(seconds: 2),
      );
      
      // Esperar hasta que termine de escuchar
      while (_isListening) {
        await Future.delayed(Duration(milliseconds: 100));
      }
    }
    
    return text;
  }
  
  void stop() {
    _speech.stop();
    _isListening = false;
  }
}
```

---

## 📊 Servicio de Reportes

### Clase para Manejar Reportes

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ReportesService {
  final String baseUrl = 'https://tu-backend.com/api';
  
  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }
  
  /// Genera un reporte desde un prompt de texto (voz convertida)
  Future<ReporteResponse> generarReporte({
    required String prompt,
    String? formato, // Opcional: 'pdf', 'excel', 'csv', 'pantalla'
  }) async {
    final token = await _getToken();
    if (token == null) {
      throw Exception('No hay token de autenticación');
    }
    
    final url = Uri.parse('$baseUrl/ia/consulta/');
    final body = {
      'prompt': prompt,
      if (formato != null) 'formato': formato,
    };
    
    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
      body: jsonEncode(body),
    );
    
    if (response.statusCode == 200) {
      final contentType = response.headers['content-type'];
      
      // Si es JSON (pantalla)
      if (contentType?.contains('application/json') ?? false) {
        final data = jsonDecode(response.body);
        return ReporteResponse(
          tipo: TipoReporte.pantalla,
          datos: data,
        );
      }
      
      // Si es archivo (PDF, Excel, CSV)
      String extension = 'pdf';
      TipoReporte tipo = TipoReporte.pdf;
      
      if (contentType?.contains('excel') ?? false) {
        extension = 'xlsx';
        tipo = TipoReporte.excel;
      } else if (contentType?.contains('csv') ?? false) {
        extension = 'csv';
        tipo = TipoReporte.csv;
      }
      
      // Guardar archivo
      final file = await _saveFile(response.bodyBytes, extension);
      
      return ReporteResponse(
        tipo: tipo,
        archivo: file,
      );
    } else {
      final error = jsonDecode(response.body);
      throw Exception(error['detail'] ?? 'Error al generar reporte');
    }
  }
  
  /// Guarda un archivo temporalmente
  Future<File> _saveFile(List<int> bytes, String extension) async {
    final directory = await getTemporaryDirectory();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final file = File('${directory.path}/reporte_$timestamp.$extension');
    await file.writeAsBytes(bytes);
    return file;
  }
  
  /// Obtiene el historial de consultas
  Future<Map<String, dynamic>> obtenerHistorial({int limit = 20, String? formato}) async {
    final token = await _getToken();
    if (token == null) {
      throw Exception('No hay token de autenticación');
    }
    
    final url = Uri.parse('$baseUrl/ia/historial/').replace(
      queryParameters: {
        'limit': limit.toString(),
        if (formato != null) 'formato': formato,
      },
    );
    
    final response = await http.get(
      url,
      headers: {
        'Authorization': 'Token $token',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error al obtener historial');
    }
  }
}

/// Respuesta del reporte
class ReporteResponse {
  final TipoReporte tipo;
  final Map<String, dynamic>? datos;
  final File? archivo;
  
  ReporteResponse({
    required this.tipo,
    this.datos,
    this.archivo,
  });
}

enum TipoReporte {
  pantalla,
  pdf,
  excel,
  csv,
}
```

---

## 🎨 Widget de Flutter

### Widget Principal con Voz

```dart
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:open_filex/open_filex.dart';

class ReporteVozScreen extends StatefulWidget {
  @override
  _ReporteVozScreenState createState() => _ReporteVozScreenState();
}

class _ReporteVozScreenState extends State<ReporteVozScreen> {
  final ReportesService _reportesService = ReportesService();
  final VoiceRecognitionService _voiceService = VoiceRecognitionService();
  final TextEditingController _promptController = TextEditingController();
  
  bool _isListening = false;
  bool _isGenerating = false;
  String _statusMessage = '';
  ReporteResponse? _ultimoReporte;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Reportes por Voz'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Campo de texto (puede venir de voz o escribirse)
            TextField(
              controller: _promptController,
              decoration: InputDecoration(
                labelText: 'Tu consulta',
                hintText: 'Ej: Quiero un reporte de ventas de octubre en PDF',
                border: OutlineInputBorder(),
                suffixIcon: IconButton(
                  icon: Icon(_isListening ? Icons.mic : Icons.mic_none),
                  onPressed: _isGenerating ? null : _toggleListening,
                ),
              ),
              enabled: !_isGenerating,
            ),
            
            SizedBox(height: 16),
            
            // Botón de generar
            ElevatedButton.icon(
              onPressed: _isGenerating ? null : _generarReporte,
              icon: _isGenerating
                  ? SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(Icons.report),
              label: Text(_isGenerating ? 'Generando...' : 'Generar Reporte'),
            ),
            
            SizedBox(height: 16),
            
            // Mensaje de estado
            if (_statusMessage.isNotEmpty)
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _statusMessage.contains('Error')
                      ? Colors.red.shade100
                      : Colors.green.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(_statusMessage),
              ),
            
            SizedBox(height: 16),
            
            // Mostrar resultado si es pantalla
            if (_ultimoReporte?.tipo == TipoReporte.pantalla && _ultimoReporte?.datos != null)
              Expanded(
                child: _buildDataTable(_ultimoReporte!.datos!),
              ),
            
            // Botón para abrir archivo si es PDF/Excel/CSV
            if (_ultimoReporte?.archivo != null)
              ElevatedButton(
                onPressed: () => _abrirArchivo(_ultimoReporte!.archivo!),
                child: Text('Abrir ${_getTipoArchivo(_ultimoReporte!.tipo)}'),
              ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _toggleListening() async {
    if (_isListening) {
      _voiceService.stop();
      setState(() => _isListening = false);
    } else {
      setState(() => _isListening = true);
      final text = await _voiceService.listen();
      if (text != null && text.isNotEmpty) {
        _promptController.text = text;
      }
      setState(() => _isListening = false);
    }
  }
  
  Future<void> _generarReporte() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty) {
      setState(() {
        _statusMessage = 'Por favor, ingresa una consulta';
      });
      return;
    }
    
    setState(() {
      _isGenerating = true;
      _statusMessage = 'Generando reporte...';
      _ultimoReporte = null;
    });
    
    try {
      final resultado = await _reportesService.generarReporte(
        prompt: prompt,
      );
      
      setState(() {
        _ultimoReporte = resultado;
        _isGenerating = false;
        if (resultado.tipo == TipoReporte.pantalla) {
          _statusMessage = 'Reporte generado exitosamente';
        } else {
          _statusMessage = 'Archivo generado: ${resultado.archivo?.path}';
        }
      });
    } catch (e) {
      setState(() {
        _isGenerating = false;
        _statusMessage = 'Error: $e';
      });
    }
  }
  
  Future<void> _abrirArchivo(File file) async {
    final result = await OpenFilex.open(file.path);
    if (result.type != ResultType.done) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al abrir archivo')),
      );
    }
  }
  
  Widget _buildDataTable(Map<String, dynamic> datos) {
    final resultado = datos['resultado'] as Map<String, dynamic>?;
    if (resultado == null) return SizedBox();
    
    final columnas = resultado['columnas'] as List<dynamic>? ?? [];
    final datosTabla = resultado['datos'] as List<dynamic>? ?? [];
    
    if (datosTabla.isEmpty) {
      return Center(child: Text('No hay datos para mostrar'));
    }
    
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: columnas.map((col) => DataColumn(
          label: Text(col.toString().replaceAll('_', ' ').toUpperCase()),
        )).toList(),
        rows: datosTabla.map((fila) {
          return DataRow(
            cells: columnas.map((col) {
              final valor = fila[col] ?? '';
              return DataCell(Text(valor.toString()));
            }).toList(),
          );
        }).toList(),
      ),
    );
  }
  
  String _getTipoArchivo(TipoReporte tipo) {
    switch (tipo) {
      case TipoReporte.pdf:
        return 'PDF';
      case TipoReporte.excel:
        return 'Excel';
      case TipoReporte.csv:
        return 'CSV';
      default:
        return 'Archivo';
    }
  }
}
```

---

## 📝 Ejemplos de Prompts Válidos

### Ventas
- "Quiero un reporte de ventas del mes de octubre en PDF"
- "Ventas del último mes agrupadas por producto en Excel"
- "Top 10 productos más vendidos"
- "Ventas del 01/10/2024 al 15/11/2024 en CSV"
- "Ventas pagadas del último mes"

### Clientes
- "Clientes activos del último mes"
- "Top 5 clientes con más compras"

### Productos
- "Productos más vendidos"
- "Inventario actual en Excel"

### Inventario
- "Productos con bajo stock"
- "Valor del inventario por categoría"

---

## 🔧 Configuración Backend

### Endpoint Principal

```
POST /api/ia/consulta/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "prompt": "Quiero un reporte de ventas de octubre en PDF",
  "formato": "pdf"  // Opcional
}
```

### Respuestas

#### Formato Pantalla (JSON)
```json
{
  "consulta_id": 123,
  "interpretacion": {
    "tipo_reporte": "ventas",
    "fecha_inicio": "2024-10-01T00:00:00Z",
    "fecha_fin": "2024-10-31T23:59:59Z",
    "formato": "pantalla",
    "agrupar_por": ["producto"]
  },
  "resultado": {
    "tipo": "por_producto",
    "columnas": ["producto", "sku", "cantidad_vendida", "total_vendido"],
    "datos": [
      {
        "producto": "Refrigerador Samsung",
        "sku": "REF-001",
        "cantidad_vendida": 15,
        "total_vendido": 13499.85
      }
    ]
  },
  "tiempo_ejecucion": 0.45
}
```

#### Formato Archivo (PDF/Excel/CSV)
- **Content-Type**: `application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, o `text/csv`
- **Body**: Archivo binario
- **Headers**: `Content-Disposition: attachment; filename="reporte_20241104_201530.pdf"`

---

## ✅ Checklist de Implementación

- [x] Endpoint `/api/ia/consulta/` implementado
- [x] Soporte para reconocimiento de voz (lado Flutter)
- [x] Múltiples formatos (PDF, Excel, CSV, JSON)
- [x] Interpretación de lenguaje natural
- [x] Historial de consultas
- [x] Manejo de errores
- [x] Autenticación por token

---

## 🐛 Manejo de Errores

```dart
try {
  final resultado = await _reportesService.generarReporte(prompt: prompt);
  // Manejar éxito
} on http.ClientException catch (e) {
  // Error de conexión
  print('Error de conexión: $e');
} catch (e) {
  // Otro error
  print('Error: $e');
}
```

---

## 📚 Recursos Adicionales

- [Speech to Text Package](https://pub.dev/packages/speech_to_text)
- [HTTP Package](https://pub.dev/packages/http)
- [Open File Package](https://pub.dev/packages/open_filex)

---

**✅ Backend Listo para Flutter!** El sistema de reportes está completamente funcional y listo para ser consumido desde Flutter con reconocimiento de voz.

