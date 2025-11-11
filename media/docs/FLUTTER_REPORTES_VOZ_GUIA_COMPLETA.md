# 📱 Flutter - Reportes por Voz - Guía Completa

## 🎯 Descripción General

Sistema completo para generar reportes mediante comandos de voz en Flutter. Integra Speech-to-Text, procesamiento de lenguaje natural en backend Django, y visualización de reportes en múltiples formatos.

## 🏗️ Arquitectura del Sistema

```
Flutter App
├── Speech Recognition Service
├── Voice Command Processor
├── Report API Client
├── Report Viewer (PDF/Excel/CSV)
└── Voice Feedback System

Backend Django
├── IA Interpreter (NLP)
├── Report Generator
├── File Exporter
└── API Endpoints
```

## 📋 Requisitos Previos

### **1. Dependencias Flutter**
```yaml
dependencies:
  flutter:
    sdk: flutter

  # Speech Recognition
  speech_to_text: ^6.1.1
  permission_handler: ^11.0.1

  # API y networking
  dio: ^5.3.2
  cached_network_image: ^3.2.3

  # Archivos y descarga
  path_provider: ^2.1.1
  open_filex: ^4.3.4
  share_plus: ^7.2.2

  # UI Components
  fluttertoast: ^8.2.4
  loading_animation_widget: ^1.2.0.4
  flutter_slidable: ^3.0.1

  # Audio feedback
  audioplayers: ^5.2.1
  vibration: ^1.8.4
```

### **2. Permisos iOS (ios/Runner/Info.plist)**
```xml
<key>NSMicrophoneUsageDescription</key>
<string>Se necesita acceso al micrófono para comandos de voz</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>Se necesita reconocimiento de voz para procesar comandos</string>
```

### **3. Permisos Android (android/app/src/main/AndroidManifest.xml)**
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

## 🔧 Implementación Paso a Paso

### **Paso 1: Servicio de Reconocimiento de Voz**

```dart
// lib/services/speech_service.dart
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';

class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  String _lastWords = '';

  Future<bool> initialize() async {
    // Solicitar permisos
    var status = await Permission.microphone.request();
    if (!status.isGranted) return false;

    // Inicializar speech recognition
    return await _speech.initialize(
      onStatus: (status) => print('Speech status: $status'),
      onError: (error) => print('Speech error: $error'),
    );
  }

  Future<String?> listenForCommand({
    Duration timeout = const Duration(seconds: 10),
    String prompt = 'Di tu comando de reporte...',
  }) async {
    if (!await initialize()) return null;

    _lastWords = '';
    _isListening = true;

    await _speech.listen(
      onResult: (result) {
        _lastWords = result.recognizedWords;
        if (result.finalResult) {
          _isListening = false;
        }
      },
      listenFor: timeout,
      pauseFor: const Duration(seconds: 3),
      listenOptions: stt.ListenOptions(
        enableHapticFeedback: true,
        autoPunctuation: true,
        listenMode: stt.ListenMode.confirmation,
      ),
    );

    // Esperar resultado
    await Future.delayed(timeout);

    if (_isListening) {
      await _speech.stop();
      _isListening = false;
    }

    return _lastWords.isNotEmpty ? _lastWords : null;
  }

  Future<void> stopListening() async {
    if (_isListening) {
      await _speech.stop();
      _isListening = false;
    }
  }

  bool get isListening => _isListening;
  String get lastWords => _lastWords;
}

// Singleton instance
final speechService = SpeechService();
```

### **Paso 2: Procesador de Comandos de Voz**

```dart
// lib/services/voice_command_processor.dart
import 'package:dio/dio.dart';

class VoiceCommandProcessor {
  final Dio _dio;

  VoiceCommandProcessor(this._dio);

  Future<VoiceCommandResult> processVoiceCommand(String voiceText, String token) async {
    try {
      // Enviar comando de voz al backend
      final response = await _dio.post(
        '/api/ia/procesar-voz/',
        data: {
          'comando_voz': voiceText,
          'formato_preferido': 'pdf', // o detectar del comando
        },
        options: Options(headers: {'Authorization': 'Token $token'}),
      );

      if (response.statusCode == 200) {
        return VoiceCommandResult.fromJson(response.data);
      } else {
        throw Exception('Error procesando comando de voz');
      }
    } catch (e) {
      return VoiceCommandResult.error(e.toString());
    }
  }

  Future<ReportResult> generateReport(String reportId, String format, String token) async {
    try {
      final response = await _dio.post(
        '/api/ia/generar-reporte/',
        data: {
          'reporte_id': reportId,
          'formato': format,
        },
        options: Options(
          headers: {'Authorization': 'Token $token'},
          responseType: ResponseType.bytes, // Para archivos
        ),
      );

      if (response.statusCode == 200) {
        return ReportResult.success(response.data, format);
      } else {
        throw Exception('Error generando reporte');
      }
    } catch (e) {
      return ReportResult.error(e.toString());
    }
  }
}

class VoiceCommandResult {
  final bool success;
  final String? reportId;
  final String? message;
  final Map<String, dynamic>? interpretation;
  final String? error;

  VoiceCommandResult._({
    required this.success,
    this.reportId,
    this.message,
    this.interpretation,
    this.error,
  });

  factory VoiceCommandResult.fromJson(Map<String, dynamic> json) {
    return VoiceCommandResult._(
      success: true,
      reportId: json['reporte_id'],
      message: json['mensaje'],
      interpretation: json['interpretacion'],
    );
  }

  factory VoiceCommandResult.error(String error) {
    return VoiceCommandResult._(
      success: false,
      error: error,
    );
  }
}

class ReportResult {
  final bool success;
  final List<int>? fileData;
  final String? format;
  final String? error;

  ReportResult._({
    required this.success,
    this.fileData,
    this.format,
    this.error,
  });

  factory ReportResult.success(List<int> data, String format) {
    return ReportResult._(
      success: true,
      fileData: data,
      format: format,
    );
  }

  factory ReportResult.error(String error) {
    return ReportResult._(
      success: false,
      error: error,
    );
  }
}
```

### **Paso 3: Widget Principal de Reportes por Voz**

```dart
// lib/widgets/voice_report_generator.dart
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:vibration/vibration.dart';
import '../services/speech_service.dart';
import '../services/voice_command_processor.dart';

class VoiceReportGenerator extends StatefulWidget {
  final String authToken;
  final Function(String, String)? onReportGenerated;

  const VoiceReportGenerator({
    Key? key,
    required this.authToken,
    this.onReportGenerated,
  }) : super(key: key);

  @override
  _VoiceReportGeneratorState createState() => _VoiceReportGeneratorState();
}

class _VoiceReportGeneratorState extends State<VoiceReportGenerator>
    with TickerProviderStateMixin {
  bool _isListening = false;
  String _recognizedText = '';
  bool _isProcessing = false;
  String? _errorMessage;

  late AnimationController _pulseController;
  late AudioPlayer _audioPlayer;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..repeat(reverse: true);

    _audioPlayer = AudioPlayer();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _startListening() async {
    setState(() {
      _isListening = true;
      _recognizedText = '';
      _errorMessage = null;
    });

    // Feedback háptico
    if (await Vibration.hasVibrator() ?? false) {
      Vibration.vibrate(duration: 100);
    }

    // Audio feedback
    await _playSound('listening_start.wav');

    try {
      final command = await speechService.listenForCommand(
        prompt: 'Di tu comando de reporte',
        timeout: const Duration(seconds: 8),
      );

      if (command != null && command.isNotEmpty) {
        setState(() {
          _recognizedText = command;
          _isProcessing = true;
        });

        await _processCommand(command);
      } else {
        setState(() {
          _errorMessage = 'No se detectó ningún comando';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error de reconocimiento: ${e.toString()}';
      });
    } finally {
      setState(() {
        _isListening = false;
      });

      await _playSound('listening_stop.wav');
    }
  }

  Future<void> _processCommand(String command) async {
    final processor = VoiceCommandProcessor(Dio());

    final result = await processor.processVoiceCommand(command, widget.authToken);

    if (result.success && result.reportId != null) {
      // Generar reporte automáticamente en PDF
      final reportResult = await processor.generateReport(
        result.reportId!,
        'pdf',
        widget.authToken,
      );

      if (reportResult.success) {
        await _playSound('success.wav');
        widget.onReportGenerated?.call(result.reportId!, 'pdf');

        // Mostrar diálogo de éxito
        _showSuccessDialog(result.reportId!, command);
      } else {
        setState(() {
          _errorMessage = 'Error generando reporte: ${reportResult.error}';
        });
        await _playSound('error.wav');
      }
    } else {
      setState(() {
        _errorMessage = result.error ?? 'Error procesando comando';
      });
      await _playSound('error.wav');
    }

    setState(() {
      _isProcessing = false;
    });
  }

  Future<void> _playSound(String soundFile) async {
    try {
      await _audioPlayer.play(AssetSource('sounds/$soundFile'));
    } catch (e) {
      // Silenciar errores de audio
      print('Error reproduciendo sonido: $e');
    }
  }

  void _showSuccessDialog(String reportId, String command) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('✅ Reporte Generado'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Comando reconocido:'),
            Text(
              '"$command"',
              style: const TextStyle(fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: 16),
            const Text('El reporte se ha generado y descargado automáticamente.'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Aceptar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Título
            Row(
              children: [
                Icon(
                  _isListening ? Icons.mic : Icons.mic_none,
                  size: 32,
                  color: _isListening ? Colors.red : Colors.blue,
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'Reportes por Voz',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 20),

            // Estado actual
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _isListening
                    ? Colors.red.withOpacity(0.1)
                    : _isProcessing
                        ? Colors.orange.withOpacity(0.1)
                        : Colors.grey.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: _isListening
                      ? Colors.red
                      : _isProcessing
                          ? Colors.orange
                          : Colors.grey,
                  width: 2,
                ),
              ),
              child: Column(
                children: [
                  // Indicador animado
                  AnimatedBuilder(
                    animation: _pulseController,
                    builder: (context, child) {
                      return Transform.scale(
                        scale: _isListening
                            ? 1.0 + _pulseController.value * 0.2
                            : 1.0,
                        child: Icon(
                          _isListening
                              ? Icons.mic
                              : _isProcessing
                                  ? Icons.hourglass_top
                                  : Icons.mic_none,
                          size: 48,
                          color: _isListening
                              ? Colors.red
                              : _isProcessing
                                  ? Colors.orange
                                  : Colors.grey,
                        ),
                      );
                    },
                  ),

                  const SizedBox(height: 12),

                  // Texto de estado
                  Text(
                    _isListening
                        ? 'Escuchando...'
                        : _isProcessing
                            ? 'Procesando comando...'
                            : 'Presiona el botón para hablar',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: _isListening
                          ? Colors.red
                          : _isProcessing
                              ? Colors.orange
                              : Colors.grey[700],
                    ),
                    textAlign: TextAlign.center,
                  ),

                  // Texto reconocido
                  if (_recognizedText.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.blue.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '"$_recognizedText"',
                        style: const TextStyle(
                          fontStyle: FontStyle.italic,
                          color: Colors.blue,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],

                  // Mensaje de error
                  if (_errorMessage != null) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(color: Colors.red),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Botón principal
            ElevatedButton.icon(
              onPressed: _isListening || _isProcessing ? null : _startListening,
              icon: Icon(_isListening ? Icons.stop : Icons.mic),
              label: Text(
                _isListening
                    ? 'Detener'
                    : _isProcessing
                        ? 'Procesando...'
                        : 'Hablar Comando',
              ),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                backgroundColor: _isListening ? Colors.red : Colors.blue,
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey,
              ),
            ),

            const SizedBox(height: 16),

            // Ejemplos de comandos
            const Text(
              'Ejemplos de comandos:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                _buildExampleChip('Ventas del mes de septiembre en PDF'),
                _buildExampleChip('Top 3 productos más vendidos'),
                _buildExampleChip('Inventario actual en Excel'),
                _buildExampleChip('Clientes de este mes'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExampleChip(String example) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.3)),
      ),
      child: Text(
        example,
        style: const TextStyle(fontSize: 12, color: Colors.grey),
      ),
    );
  }
}
```

### **Paso 4: Servicio de Gestión de Archivos**

```dart
// lib/services/file_manager.dart
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';

class FileManager {
  static Future<String> saveReportFile(
    List<int> fileData,
    String fileName,
    String format,
  ) async {
    final directory = await getApplicationDocumentsDirectory();
    final reportsDir = Directory('${directory.path}/reports');

    // Crear directorio si no existe
    if (!await reportsDir.exists()) {
      await reportsDir.create(recursive: true);
    }

    final filePath = '${reportsDir.path}/$fileName.$format';
    final file = File(filePath);
    await file.writeAsBytes(fileData);

    return filePath;
  }

  static Future<void> openReportFile(String filePath) async {
    final result = await OpenFilex.open(filePath);
    if (result.type != ResultType.done) {
      throw Exception('Error abriendo archivo: ${result.message}');
    }
  }

  static Future<void> shareReportFile(String filePath, String title) async {
    await Share.shareXFiles(
      [XFile(filePath)],
      text: title,
    );
  }

  static Future<void> deleteOldReports({int daysOld = 7}) async {
    final directory = await getApplicationDocumentsDirectory();
    final reportsDir = Directory('${directory.path}/reports');

    if (!await reportsDir.exists()) return;

    final files = reportsDir.listSync();
    final cutoffDate = DateTime.now().subtract(Duration(days: daysOld));

    for (final file in files) {
      if (file is File) {
        final stat = await file.stat();
        if (stat.modified.isBefore(cutoffDate)) {
          await file.delete();
        }
      }
    }
  }
}
```

### **Paso 5: Pantalla de Historial de Reportes**

```dart
// lib/screens/reports_history_screen.dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/file_manager.dart';
import '../widgets/voice_report_generator.dart';

class ReportsHistoryScreen extends StatefulWidget {
  final String authToken;

  const ReportsHistoryScreen({Key? key, required this.authToken}) : super(key: key);

  @override
  _ReportsHistoryScreenState createState() => _ReportsHistoryScreenState();
}

class _ReportsHistoryScreenState extends State<ReportsHistoryScreen> {
  List<Map<String, dynamic>> _reports = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadReportsHistory();
  }

  Future<void> _loadReportsHistory() async {
    setState(() {
      _isLoading = true;
    });

    // Simular carga de historial (implementar con API real)
    await Future.delayed(const Duration(seconds: 1));

    setState(() {
      _reports = [
        {
          'id': '1',
          'title': 'Ventas Septiembre 2025',
          'description': 'Reporte de ventas del mes de septiembre',
          'format': 'pdf',
          'createdAt': DateTime.now().subtract(const Duration(hours: 2)),
          'filePath': null, // null si no está descargado localmente
        },
        {
          'id': '2',
          'title': 'Top 3 Productos',
          'description': 'Productos más vendidos',
          'format': 'excel',
          'createdAt': DateTime.now().subtract(const Duration(days: 1)),
          'filePath': '/path/to/file.xlsx',
        },
      ];
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Historial de Reportes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadReportsHistory,
          ),
        ],
      ),
      body: Column(
        children: [
          // Generador por voz
          Expanded(
            flex: 1,
            child: VoiceReportGenerator(
              authToken: widget.authToken,
              onReportGenerated: (reportId, format) {
                _loadReportsHistory(); // Recargar lista
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Reporte generado en formato $format'),
                    action: SnackBarAction(
                      label: 'Ver',
                      onPressed: () {
                        // Navegar al reporte generado
                      },
                    ),
                  ),
                );
              },
            ),
          ),

          // Lista de reportes
          Expanded(
            flex: 2,
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _reports.isEmpty
                    ? const Center(
                        child: Text('No hay reportes generados aún'),
                      )
                    : ListView.builder(
                        itemCount: _reports.length,
                        itemBuilder: (context, index) {
                          final report = _reports[index];
                          return ReportListItem(
                            report: report,
                            onOpen: () => _openReport(report),
                            onShare: () => _shareReport(report),
                            onDownload: () => _downloadReport(report),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Future<void> _openReport(Map<String, dynamic> report) async {
    try {
      if (report['filePath'] != null) {
        await FileManager.openReportFile(report['filePath']);
      } else {
        // Descargar primero si no existe localmente
        await _downloadReport(report);
        await FileManager.openReportFile(report['filePath']);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error abriendo reporte: $e')),
      );
    }
  }

  Future<void> _shareReport(Map<String, dynamic> report) async {
    try {
      if (report['filePath'] != null) {
        await FileManager.shareReportFile(
          report['filePath'],
          'Reporte: ${report['title']}',
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Descarga el reporte primero para compartirlo')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error compartiendo reporte: $e')),
      );
    }
  }

  Future<void> _downloadReport(Map<String, dynamic> report) async {
    // Implementar descarga desde API
    // await api.downloadReport(report['id'], report['format']);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Funcionalidad de descarga próximamente')),
    );
  }
}

class ReportListItem extends StatelessWidget {
  final Map<String, dynamic> report;
  final VoidCallback onOpen;
  final VoidCallback onShare;
  final VoidCallback onDownload;

  const ReportListItem({
    Key? key,
    required this.report,
    required this.onOpen,
    required this.onShare,
    required this.onDownload,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat('dd/MM/yyyy HH:mm');

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: Icon(
          report['format'] == 'pdf' ? Icons.picture_as_pdf : Icons.table_chart,
          color: report['format'] == 'pdf' ? Colors.red : Colors.green,
          size: 32,
        ),
        title: Text(report['title']),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(report['description']),
            Text(
              'Generado: ${dateFormat.format(report['createdAt'])}',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            switch (value) {
              case 'open':
                onOpen();
                break;
              case 'share':
                onShare();
                break;
              case 'download':
                onDownload();
                break;
            }
          },
          itemBuilder: (context) => [
            const PopupMenuItem(value: 'open', child: Text('Abrir')),
            const PopupMenuItem(value: 'share', child: Text('Compartir')),
            const PopupMenuItem(value: 'download', child: Text('Descargar')),
          ],
        ),
        onTap: onOpen,
      ),
    );
  }
}
```

## 🎯 **Ejemplos de Comandos de Voz**

### **Reportes de Ventas:**
- "Quiero un reporte de ventas del mes de septiembre, agrupado por producto, en PDF"
- "Muéstrame las ventas del período del 01/10/2024 al 01/01/2025 en Excel"
- "Ventas de este mes agrupadas por cliente"

### **Reportes de Productos:**
- "Top 3 productos más vendidos en PDF"
- "Productos con menos stock en Excel"
- "Inventario actual"

### **Reportes de Clientes:**
- "Clientes que más han comprado este año"
- "Lista de clientes nuevos del mes pasado"

## 🔧 **Backend API Endpoints**

```dart
// Procesar comando de voz
POST /api/ia/procesar-voz/
{
  "comando_voz": "ventas del mes de septiembre en pdf",
  "formato_preferido": "pdf"
}

// Generar reporte
POST /api/ia/generar-reporte/
{
  "reporte_id": "abc123",
  "formato": "pdf"
}

// Historial de reportes
GET /api/ia/historial/
```

## 🛠️ **Manejo de Errores**

```dart
class VoiceErrorHandler {
  static String getErrorMessage(dynamic error) {
    if (error is DioError) {
      switch (error.type) {
        case DioErrorType.connectTimeout:
          return 'Error de conexión. Verifica tu conexión a internet.';
        case DioErrorType.response:
          return _getApiErrorMessage(error.response);
        default:
          return 'Error de red. Inténtalo de nuevo.';
      }
    }
    return error.toString();
  }

  static String _getApiErrorMessage(Response? response) {
    if (response?.data is Map) {
      final data = response!.data as Map;
      return data['message'] ?? data['error'] ?? 'Error del servidor';
    }
    return 'Error desconocido del servidor';
  }
}
```

## 📱 **Mejores Prácticas UX**

### **1. Feedback Visual Constante:**
- Indicadores de carga durante procesamiento
- Animaciones durante reconocimiento de voz
- Colores que indican estado (rojo=escuchando, naranja=procesando, verde=éxito)

### **2. Audio/Háptico Feedback:**
- Sonido al iniciar/detener escucha
- Vibración en eventos importantes
- Audio de confirmación en éxito/error

### **3. Manejo de Estados:**
```dart
enum VoiceCommandState {
  idle,
  listening,
  processing,
  success,
  error
}
```

### **4. Reintentos Inteligentes:**
```dart
class RetryHandler {
  static Future<T> withRetry<T>(
    Future<T> Function() operation,
    int maxRetries = 3,
  ) async {
    int attempts = 0;
    while (attempts < maxRetries) {
      try {
        return await operation();
      } catch (e) {
        attempts++;
        if (attempts >= maxRetries) rethrow;

        // Espera exponencial
        await Future.delayed(Duration(seconds: attempts * 2));
      }
    }
    throw Exception('Max retries exceeded');
  }
}
```

## 🚀 **Optimizaciones de Performance**

### **1. Cache de Resultados:**
```dart
class ReportCache {
  static final Map<String, CachedReport> _cache = {};

  static CachedReport? getReport(String reportId) {
    final cached = _cache[reportId];
    if (cached != null && !cached.isExpired) {
      return cached;
    }
    return null;
  }

  static void cacheReport(String reportId, List<int> data, String format) {
    _cache[reportId] = CachedReport(
      data: data,
      format: format,
      timestamp: DateTime.now(),
    );
  }
}
```

### **2. Lazy Loading de Historial:**
```dart
class ReportsHistoryProvider extends ChangeNotifier {
  List<ReportItem> _reports = [];
  bool _hasMore = true;
  bool _loading = false;

  Future<void> loadMoreReports() async {
    if (_loading || !_hasMore) return;

    _loading = true;
    notifyListeners();

    try {
      final newReports = await api.loadReportsPage(_reports.length ~/ 20 + 1);
      _reports.addAll(newReports);
      _hasMore = newReports.length == 20;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}
```

## 🔐 **Seguridad**

### **1. Validación de Tokens:**
```dart
class SecureApiClient {
  final Dio _dio;

  SecureApiClient(this._dio) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = await _getValidToken();
          options.headers['Authorization'] = 'Token $token';
          handler.next(options);
        },
        onError: (error, handler) {
          if (error.response?.statusCode == 401) {
            // Token expirado, renovar
            _refreshToken();
          }
          handler.next(error);
        },
      ),
    );
  }
}
```

### **2. Encriptación de Datos Sensibles:**
```dart
class SecureStorage {
  static const FlutterSecureStorage _storage = FlutterSecureStorage();

  static Future<void> saveVoiceData(String key, String data) async {
    final encrypted = await _encryptData(data);
    await _storage.write(key: key, value: encrypted);
  }

  static Future<String?> getVoiceData(String key) async {
    final encrypted = await _storage.read(key: key);
    return encrypted != null ? await _decryptData(encrypted) : null;
  }
}
```

¡Esta implementación completa te permitirá crear una experiencia de reportes por voz fluida y profesional en tu app Flutter! 🎉
