# 📱 Reportes Dinámicos con IA y ML - Guía Flutter

## 🎯 Descripción General

La integración de **Reportes Dinámicos con IA y ML** en Flutter permite a tus usuarios generar reportes inteligentes directamente desde la app móvil. El sistema combina:

- **🧠 IA Avanzada**: Interpretación de consultas en lenguaje natural
- **🤖 Machine Learning**: Predicciones automáticas con RandomForest
- **📊 Reportes Inteligentes**: Insights y recomendaciones automáticas
- **📱 Integración Móvil**: Optimizada para dispositivos móviles

## 🛠️ Configuración del Proyecto Flutter

### Dependencias Necesarias

```yaml
# pubspec.yaml
dependencies:
  http: ^1.2.0
  shared_preferences: ^2.2.0
  path_provider: ^2.1.1
  open_file: ^3.3.2
  flutter_pdfview: ^1.3.2
  excel: ^2.1.0
  intl: ^0.19.0

# Para permisos de archivos
permission_handler: ^11.3.0

dev_dependencies:
  flutter_test:
    sdk: flutter
```

### Configuración de Permisos

```xml
<!-- Android: android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

```xml
<!-- iOS: ios/Runner/Info.plist -->
<key>NSPhotoLibraryUsageDescription</key>
<string>Para guardar reportes PDF y Excel</string>
<key>LSSupportsOpeningDocumentsInPlace</key>
<true/>
```

## 🔑 Servicio de Autenticación

### Clase de Autenticación JWT

```dart
// lib/services/auth_service.dart
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class AuthService {
  static const String _tokenKey = 'jwt_token';
  static const String _baseUrl = 'https://smartsales365.duckdns.org';

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  static Future<Map<String, String>> getAuthHeaders() async {
    final token = await getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }
}
```

## 📊 Servicio de Reportes Dinámicos

### Clase Principal del Servicio

```dart
// lib/services/reportes_dinamicos_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';
import 'auth_service.dart';

class ReportesDinamicosService {
  static const String _baseUrl = 'https://smartsales365.duckdns.org';
  static const String _endpoint = '/api/reportes-dinamicos/avanzados/';

  /// Genera un reporte dinámico (soporta GET y POST)
  static Future<ReporteResponse> generarReporte({
    required String prompt,
    String formato = 'pantalla',
    int diasPrediccion = 30,
    bool incluirInsights = true,
    bool usarPost = false, // Cambiar a true para usar POST en lugar de GET
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();

      if (usarPost) {
        // Usar POST para datos complejos o aplicaciones móviles
        final uri = Uri.parse('$_baseUrl$_endpoint');
        final body = json.encode({
          'prompt': prompt,
          'formato': formato,
          'dias_prediccion': diasPrediccion,
          'incluir_insights': incluirInsights,
        });

        final response = await http.post(uri, headers: headers, body: body);
      } else {
        // Usar GET (recomendado para navegación web)
        final uri = Uri.parse('$_baseUrl$_endpoint').replace(queryParameters: {
          'prompt': prompt,
          'formato': formato,
          'dias_prediccion': diasPrediccion.toString(),
          'incluir_insights': incluirInsights.toString(),
        });

        final response = await http.get(uri, headers: headers);
      }

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return ReporteResponse.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('Sesión expirada. Por favor, inicia sesión nuevamente.');
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Error desconocido');
      }
    } catch (e) {
      throw Exception('Error de conexión: $e');
    }
  }

  /// Descarga y guarda un archivo (PDF/Excel)
  static Future<String> descargarArchivo(String base64Data, String formato) async {
    try {
      // Decodificar base64
      final bytes = base64.decode(base64Data.split(',').last);

      // Obtener directorio de documentos
      final directory = await getApplicationDocumentsDirectory();
      final fileName = 'reporte_${DateTime.now().millisecondsSinceEpoch}.$formato';
      final filePath = '${directory.path}/$fileName';

      // Guardar archivo
      final file = File(filePath);
      await file.writeAsBytes(bytes);

      return filePath;
    } catch (e) {
      throw Exception('Error al guardar archivo: $e');
    }
  }

  /// Abre un archivo con la app correspondiente
  static Future<void> abrirArchivo(String filePath) async {
    try {
      final result = await OpenFile.open(filePath);
      if (result.type != ResultType.done) {
        throw Exception('No se pudo abrir el archivo: ${result.message}');
      }
    } catch (e) {
      throw Exception('Error al abrir archivo: $e');
    }
  }
}

/// Modelo de respuesta del API
class ReporteResponse {
  final bool success;
  final Reporte reporte;
  final String? archivoBase64;

  ReporteResponse({
    required this.success,
    required this.reporte,
    this.archivoBase64,
  });

  factory ReporteResponse.fromJson(Map<String, dynamic> json) {
    return ReporteResponse(
      success: json['success'] ?? false,
      reporte: Reporte.fromJson(json['reporte']),
      archivoBase64: json['archivo'],
    );
  }
}

class Reporte {
  final String titulo;
  final String tipo;
  final String formato;
  final String fechaGeneracion;
  final Map<String, dynamic> parametros;
  final List<String> insights;
  final List<String> recomendaciones;
  final Map<String, dynamic>? datos;

  Reporte({
    required this.titulo,
    required this.tipo,
    required this.formato,
    required this.fechaGeneracion,
    required this.parametros,
    required this.insights,
    required this.recomendaciones,
    this.datos,
  });

  factory Reporte.fromJson(Map<String, dynamic> json) {
    return Reporte(
      titulo: json['titulo'] ?? '',
      tipo: json['tipo'] ?? '',
      formato: json['formato'] ?? '',
      fechaGeneracion: json['fecha_generacion'] ?? '',
      parametros: Map<String, dynamic>.from(json['parametros'] ?? {}),
      insights: List<String>.from(json['insights'] ?? []),
      recomendaciones: List<String>.from(json['recomendaciones'] ?? []),
      datos: json['datos'],
    );
  }
}
```

## 🎨 Widgets de UI para Reportes

### Widget Principal de Reportes Dinámicos

```dart
// lib/widgets/reportes_dinamicos_widget.dart
import 'package:flutter/material.dart';
import '../services/reportes_dinamicos_service.dart';

class ReportesDinamicosWidget extends StatefulWidget {
  @override
  _ReportesDinamicosWidgetState createState() => _ReportesDinamicosWidgetState();
}

class _ReportesDinamicosWidgetState extends State<ReportesDinamicosWidget> {
  final TextEditingController _promptController = TextEditingController();
  String _formatoSeleccionado = 'pdf';
  bool _incluirInsights = true;
  int _diasPrediccion = 30;
  bool _isLoading = false;
  String? _errorMessage;
  ReporteResponse? _ultimoReporte;

  final List<String> _formatos = ['pdf', 'excel', 'csv', 'pantalla'];

  final List<String> _ejemplosPrompts = [
    'Predice las ventas para el próximo mes',
    'Compara ventas reales vs predicciones del último trimestre',
    'Análisis de productos con mayor potencial de crecimiento',
    'Reporte ejecutivo mensual con métricas y predicciones',
    'Top 10 productos más vendidos con predicciones',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('📊 Reportes Dinámicos IA'),
        backgroundColor: Colors.blue.shade700,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildEncabezado(),
            SizedBox(height: 20),
            _buildFormularioConsulta(),
            SizedBox(height: 20),
            _buildEjemplos(),
            SizedBox(height: 20),
            if (_errorMessage != null) _buildErrorWidget(),
            if (_ultimoReporte != null) _buildResultadoWidget(),
          ],
        ),
      ),
    );
  }

  Widget _buildEncabezado() {
    return Card(
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '🤖 Generador de Reportes Inteligente',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'Describe en lenguaje natural el reporte que necesitas. '
              'La IA interpretará tu consulta y generará insights automáticos.',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFormularioConsulta() {
    return Card(
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '📝 Consulta en Lenguaje Natural',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            TextField(
              controller: _promptController,
              maxLines: 3,
              decoration: InputDecoration(
                hintText: 'Ej: Predice las ventas para el próximo mes en PDF',
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.grey[50],
              ),
            ),
            SizedBox(height: 16),

            // Configuración avanzada
            ExpansionTile(
              title: Text('⚙️ Configuración Avanzada'),
              children: [
                SizedBox(height: 12),
                Row(
                  children: [
                    Text('Formato:'),
                    SizedBox(width: 12),
                    DropdownButton<String>(
                      value: _formatoSeleccionado,
                      items: _formatos.map((formato) {
                        return DropdownMenuItem(
                          value: formato,
                          child: Text(formato.toUpperCase()),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() => _formatoSeleccionado = value!);
                      },
                    ),
                  ],
                ),
                SizedBox(height: 12),
                Row(
                  children: [
                    Text('Días predicción:'),
                    SizedBox(width: 12),
                    Expanded(
                      child: Slider(
                        value: _diasPrediccion.toDouble(),
                        min: 7,
                        max: 90,
                        divisions: 11,
                        label: _diasPrediccion.toString(),
                        onChanged: (value) {
                          setState(() => _diasPrediccion = value.toInt());
                        },
                      ),
                    ),
                    Text('${_diasPrediccion} días'),
                  ],
                ),
                SwitchListTile(
                  title: Text('Incluir insights automáticos'),
                  value: _incluirInsights,
                  onChanged: (value) => setState(() => _incluirInsights = value),
                ),
              ],
            ),

            SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _generarReporte,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: _isLoading
                    ? CircularProgressIndicator(color: Colors.white)
                    : Text('🚀 Generar Reporte', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEjemplos() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '💡 Ejemplos de Consultas',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _ejemplosPrompts.map((ejemplo) {
                return ElevatedButton(
                  onPressed: () => _promptController.text = ejemplo,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green.shade50,
                    foregroundColor: Colors.green.shade800,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  child: Text(ejemplo, style: TextStyle(fontSize: 12)),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Card(
      color: Colors.red.shade50,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.error, color: Colors.red),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                _errorMessage!,
                style: TextStyle(color: Colors.red.shade800),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultadoWidget() {
    return Card(
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.check_circle, color: Colors.green),
                SizedBox(width: 8),
                Text(
                  'Reporte Generado',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            SizedBox(height: 16),

            // Información del reporte
            Text('📊 ${_ultimoReporte!.reporte.titulo}'),
            Text('🏷️ Tipo: ${_ultimoReporte!.reporte.tipo}'),
            Text('📅 Generado: ${_ultimoReporte!.reporte.fechaGeneracion}'),

            if (_ultimoReporte!.reporte.insights.isNotEmpty) ...[
              SizedBox(height: 16),
              Text(
                '🔍 Insights Automáticos',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              ..._ultimoReporte!.reporte.insights.map(
                (insight) => Padding(
                  padding: EdgeInsets.only(left: 16, top: 4),
                  child: Text('• $insight'),
                ),
              ),
            ],

            if (_ultimoReporte!.reporte.recomendaciones.isNotEmpty) ...[
              SizedBox(height: 16),
              Text(
                '💡 Recomendaciones',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              ..._ultimoReporte!.reporte.recomendaciones.map(
                (rec) => Padding(
                  padding: EdgeInsets.only(left: 16, top: 4),
                  child: Text('• $rec'),
                ),
              ),
            ],

            if (_ultimoReporte!.archivoBase64 != null) ...[
              SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _descargarAbrirArchivo,
                  icon: Icon(Icons.download),
                  label: Text('Descargar ${_formatoSeleccionado.toUpperCase()}'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green.shade600,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _generarReporte() async {
    if (_promptController.text.trim().isEmpty) {
      setState(() => _errorMessage = 'Por favor, escribe una consulta');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final reporte = await ReportesDinamicosService.generarReporte(
        prompt: _promptController.text.trim(),
        formato: _formatoSeleccionado,
        diasPrediccion: _diasPrediccion,
        incluirInsights: _incluirInsights,
      );

      setState(() => _ultimoReporte = reporte);

      if (reporte.archivoBase64 == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('✅ Reporte generado exitosamente')),
        );
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _descargarAbrirArchivo() async {
    if (_ultimoReporte?.archivoBase64 == null) return;

    try {
      final filePath = await ReportesDinamicosService.descargarArchivo(
        _ultimoReporte!.archivoBase64!,
        _formatoSeleccionado,
      );

      await ReportesDinamicosService.abrirArchivo(filePath);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('✅ Archivo abierto exitosamente')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Error: $e')),
      );
    }
  }
}
```

### Pantalla de Lista de Reportes Recientes

```dart
// lib/screens/reportes_recientes_screen.dart
import 'package:flutter/material.dart';
import '../services/reportes_dinamicos_service.dart';

class ReportesRecientesScreen extends StatefulWidget {
  @override
  _ReportesRecientesScreenState createState() => _ReportesRecientesScreenState();
}

class _ReportesRecientesScreenState extends State<ReportesRecientesScreen> {
  List<ReporteHistorial> _reportes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _cargarReportes();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('📋 Reportes Recientes'),
        backgroundColor: Colors.blue.shade700,
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _reportes.isEmpty
              ? _buildEmptyState()
              : _buildListaReportes(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.description, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'No hay reportes recientes',
            style: TextStyle(fontSize: 18, color: Colors.grey),
          ),
          SizedBox(height: 8),
          Text(
            'Genera tu primer reporte inteligente',
            style: TextStyle(color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildListaReportes() {
    return ListView.builder(
      itemCount: _reportes.length,
      itemBuilder: (context, index) {
        final reporte = _reportes[index];
        return Card(
          margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: ListTile(
            leading: _getFormatoIcon(reporte.formato),
            title: Text(reporte.titulo),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Tipo: ${reporte.tipo}'),
                Text('Fecha: ${reporte.fechaGeneracion}'),
                if (reporte.insights.isNotEmpty)
                  Text('Insights: ${reporte.insights.length}'),
              ],
            ),
            trailing: Icon(Icons.chevron_right),
            onTap: () => _mostrarDetalleReporte(reporte),
          ),
        );
      },
    );
  }

  Widget _getFormatoIcon(String formato) {
    switch (formato) {
      case 'pdf':
        return Icon(Icons.picture_as_pdf, color: Colors.red);
      case 'excel':
        return Icon(Icons.table_chart, color: Colors.green);
      case 'csv':
        return Icon(Icons.file_present, color: Colors.blue);
      default:
        return Icon(Icons.description, color: Colors.grey);
    }
  }

  void _mostrarDetalleReporte(ReporteHistorial reporte) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(reporte.titulo),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Tipo: ${reporte.tipo}'),
              Text('Formato: ${reporte.formato}'),
              SizedBox(height: 16),
              if (reporte.insights.isNotEmpty) ...[
                Text('🔍 Insights:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...reporte.insights.map((i) => Text('• $i')),
                SizedBox(height: 12),
              ],
              if (reporte.recomendaciones.isNotEmpty) ...[
                Text('💡 Recomendaciones:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...reporte.recomendaciones.map((r) => Text('• $r')),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Cerrar'),
          ),
          if (reporte.archivoPath != null)
            ElevatedButton(
              onPressed: () => ReportesDinamicosService.abrirArchivo(reporte.archivoPath!),
              child: Text('Abrir Archivo'),
            ),
        ],
      ),
    );
  }

  Future<void> _cargarReportes() async {
    // Aquí cargarías reportes desde SharedPreferences o una base de datos local
    // Por ahora, solo simulamos algunos reportes de ejemplo
    await Future.delayed(Duration(seconds: 1));
    setState(() {
      _reportes = [
        ReporteHistorial(
          titulo: 'Predicción de Ventas - Próximos 30 días',
          tipo: 'prediccion_simple',
          formato: 'pdf',
          fechaGeneracion: '2025-11-13T10:30:00Z',
          insights: ['Se espera crecimiento del 15%', 'Producto X con alto potencial'],
          recomendaciones: ['Aumentar inventario', 'Promociones estratégicas'],
          archivoPath: null, // Aquí iría la ruta real si se guardó
        ),
        // Más reportes...
      ];
      _isLoading = false;
    });
  }
}

class ReporteHistorial {
  final String titulo;
  final String tipo;
  final String formato;
  final String fechaGeneracion;
  final List<String> insights;
  final List<String> recomendaciones;
  final String? archivoPath;

  ReporteHistorial({
    required this.titulo,
    required this.tipo,
    required this.formato,
    required this.fechaGeneracion,
    required this.insights,
    required this.recomendaciones,
    this.archivoPath,
  });
}
```

## 🔧 Integración en la App Principal

### Actualizar main.dart

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'screens/reportes_dinamicos_screen.dart';
import 'screens/reportes_recientes_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartSales365 Mobile',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: HomeScreen(),
      routes: {
        '/reportes': (context) => ReportesDinamicosWidget(),
        '/reportes-recientes': (context) => ReportesRecientesScreen(),
      },
    );
  }
}

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('SmartSales365'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/reportes'),
              child: Text('📊 Generar Reportes IA'),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/reportes-recientes'),
              child: Text('📋 Reportes Recientes'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## 📱 Ejemplos de Uso Práctico

### 1. Predicción de Ventas Diaria

```dart
// En tu dashboard principal
class DashboardScreen extends StatelessWidget {
  Future<void> _generarPrediccionDiaria(BuildContext context) async {
    try {
      final reporte = await ReportesDinamicosService.generarReporte(
        prompt: 'Predicciones de ventas para hoy y recomendaciones',
        formato: 'pantalla',
        incluirInsights: true,
      );

      // Mostrar notificación con insights
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('📈 ${reporte.reporte.insights.first}'),
          duration: Duration(seconds: 5),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // ... tu UI existente ...
      floatingActionButton: FloatingActionButton(
        onPressed: () => _generarPrediccionDiaria(context),
        tooltip: 'Predicción IA',
        child: Icon(Icons.psychology),
      ),
    );
  }
}
```

### 2. Reportes Automáticos por Categoría

```dart
class ReportesPorCategoria extends StatelessWidget {
  final List<String> categorias = [
    'Electrónica', 'Ropa', 'Hogar', 'Deportes', 'Libros'
  ];

  Future<void> _generarReporteCategoria(String categoria, BuildContext context) async {
    final prompt = 'Análisis de rendimiento y predicciones para productos de $categoria';

    try {
      final reporte = await ReportesDinamicosService.generarReporte(
        prompt: prompt,
        formato: 'excel',
        diasPrediccion: 30,
        incluirInsights: true,
      );

      // Descargar automáticamente
      if (reporte.archivoBase64 != null) {
        final filePath = await ReportesDinamicosService.descargarArchivo(
          reporte.archivoBase64!,
          'excel',
        );

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('✅ Reporte de $categoria generado')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('📊 Reportes por Categoría')),
      body: ListView.builder(
        itemCount: categorias.length,
        itemBuilder: (context, index) {
          final categoria = categorias[index];
          return ListTile(
            title: Text(categoria),
            trailing: Icon(Icons.analytics),
            onTap: () => _generarReporteCategoria(categoria, context),
          );
        },
      ),
    );
  }
}
```

## 🔧 Manejo de Errores y Estados

### Widget de Loading Mejorado

```dart
class ReporteLoadingWidget extends StatelessWidget {
  final String mensaje;

  const ReporteLoadingWidget({required this.mensaje});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text(
            mensaje,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16),
          ),
          SizedBox(height: 8),
          Text(
            'La IA está procesando tu consulta...',
            style: TextStyle(color: Colors.grey[600], fontSize: 14),
          ),
        ],
      ),
    );
  }
}
```

### Manejo de Conectividad

```dart
// lib/services/connectivity_service.dart
import 'package:connectivity_plus/connectivity_plus.dart';

class ConnectivityService {
  static Future<bool> hasInternetConnection() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    return connectivityResult != ConnectivityResult.none;
  }

  static Stream<ConnectivityResult> get connectivityStream {
    return Connectivity().onConnectivityChanged;
  }
}
```

## 🎯 Mejores Prácticas

### 1. **Caché Inteligente**
```dart
// Guardar reportes recientes localmente
class ReportesCache {
  static const String _cacheKey = 'reportes_cache';

  static Future<void> guardarReporte(ReporteResponse reporte) async {
    final prefs = await SharedPreferences.getInstance();
    final reportes = await obtenerReportes() ?? [];
    reportes.insert(0, reporte); // Agregar al inicio

    // Mantener solo los últimos 10
    if (reportes.length > 10) {
      reportes.removeRange(10, reportes.length);
    }

    await prefs.setString(_cacheKey, json.encode(reportes));
  }

  static Future<List<ReporteResponse>?> obtenerReportes() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_cacheKey);
    if (data == null) return null;

    final reportesJson = json.decode(data) as List;
    return reportesJson.map((r) => ReporteResponse.fromJson(r)).toList();
  }
}
```

### 2. **Validación de Inputs**
```dart
class ValidacionReportes {
  static String? validarPrompt(String prompt) {
    if (prompt.trim().isEmpty) {
      return 'La consulta no puede estar vacía';
    }
    if (prompt.length < 5) {
      return 'La consulta debe tener al menos 5 caracteres';
    }
    if (prompt.length > 500) {
      return 'La consulta no puede exceder 500 caracteres';
    }
    return null; // Válido
  }

  static bool esPromptInteligente(String prompt) {
    final palabrasClave = [
      'predice', 'predicción', 'análisis', 'comparar', 'ventas',
      'productos', 'clientes', 'reporte', 'dashboard'
    ];

    return palabrasClave.any((palabra) =>
        prompt.toLowerCase().contains(palabra));
  }
}
```

### 3. **Gestión de Memoria**
```dart
class FileManager {
  static Future<void> limpiarArchivosAntiguos() async {
    final directory = await getApplicationDocumentsDirectory();
    final files = directory.listSync();

    // Eliminar archivos de más de 7 días
    final cutoffDate = DateTime.now().subtract(Duration(days: 7));

    for (final file in files) {
      if (file is File) {
        final stat = await file.stat();
        if (stat.modified.isBefore(cutoffDate)) {
          await file.delete();
        }
      }
    }
  }

  static Future<String> obtenerTamanoLibre() async {
    // Implementar verificación de espacio disponible
    return 'Espacio suficiente'; // Placeholder
  }
}
```

## 🚀 Próximas Funcionalidades

### 1. **Sincronización en la Nube**
- Guardar reportes en Firebase/S3
- Compartir reportes entre dispositivos
- Backup automático

### 2. **Notificaciones Push**
- Alertas cuando reportes estén listos
- Recordatorios de reportes programados
- Notificaciones de insights importantes

### 3. **Modo Offline**
- Generar reportes básicos sin conexión
- Sincronizar cuando haya internet
- Cache inteligente de datos

### 4. **Personalización Avanzada**
- Plantillas de reportes personalizadas
- Preferencias de usuario guardadas
- Temas personalizados

## 🆘 Solución de Problemas

### Error: "Sesión expirada"
```dart
// Redirigir a login
Navigator.of(context).pushReplacementNamed('/login');
```

### Error: "Sin conexión"
```dart
if (!await ConnectivityService.hasInternetConnection()) {
  // Mostrar mensaje offline
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Sin conexión'),
      content: Text('Se necesita internet para generar reportes IA'),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: Text('OK'))],
    ),
  );
}
```

### Error: "Archivo no se puede abrir"
```dart
// Verificar permisos
if (Platform.isAndroid) {
  await Permission.storage.request();
}
```

---

**¡La integración con Flutter está completa!** 📱✨

Los reportes dinámicos con IA y ML ahora están disponibles en tu app móvil Flutter. Los usuarios pueden generar reportes inteligentes simplemente escribiendo consultas en lenguaje natural.

¿Necesitas ayuda con alguna funcionalidad específica o tienes preguntas sobre la implementación?
