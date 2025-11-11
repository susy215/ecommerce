# 📊 Dashboard de Administrador - Flutter

## 🎯 Pantalla Principal del Admin

Este documento complementa `FLUTTER_REPORTES_VOZ.md` y `FLUTTER_IA_VOZ.md` con el flujo específico para el administrador.

---

## 🏠 Layout del Dashboard

```
┌────────────────────────────────────┐
│  🏪 SmartSales Admin      👤 Admin │
├────────────────────────────────────┤
│                                    │
│  📊 REPORTES RÁPIDOS               │
│  ┌──────────┐  ┌──────────┐       │
│  │ 📈 Ventas│  │ 👥 Clientes│      │
│  │  Hoy     │  │  Activos  │      │
│  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐       │
│  │ 📦 Stock │  │ 🔝 Top   │       │
│  │  Bajo    │  │  Productos│      │
│  └──────────┘  └──────────┘       │
│                                    │
│  📝 HISTORIAL RECIENTE             │
│  • Ventas de octubre en PDF        │
│  • Top 10 clientes...              │
│                                    │
└────────────────────────────────────┘
                  🎤 ← FloatingActionButton
```

---

## 💻 Código del Dashboard

### 1. Pantalla Principal con Atajos y FAB

```dart
// lib/screens/admin_dashboard_screen.dart
import 'package:flutter/material.dart';
import '../services/ia_api_service.dart';
import '../services/voice_service.dart';
import 'ia_voice_screen.dart';
import 'package:open_filex/open_filex.dart';

class AdminDashboardScreen extends StatefulWidget {
  final String token;
  final String username;

  const AdminDashboardScreen({
    required this.token,
    required this.username,
    Key? key,
  }) : super(key: key);

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  late IAApiService _apiService;
  late VoiceService _voiceService;
  
  bool _isGenerating = false;
  String _statusMessage = '';
  List<Map<String, dynamic>> _historialReciente = [];

  @override
  void initState() {
    super.initState();
    _apiService = IAApiService(token: widget.token);
    _voiceService = VoiceService();
    _cargarHistorial();
  }

  Future<void> _cargarHistorial() async {
    // TODO: Cargar historial del backend
    // GET /api/ia/historial/?limit=5
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('🏪 SmartSales Admin'),
        backgroundColor: Colors.deepPurple,
        actions: [
          Padding(
            padding: EdgeInsets.only(right: 16),
            child: Center(
              child: Text(
                '👤 ${widget.username}',
                style: TextStyle(fontSize: 16),
              ),
            ),
          ),
        ],
      ),
      
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mensaje de estado
            if (_statusMessage.isNotEmpty)
              Card(
                color: _statusMessage.contains('Error')
                    ? Colors.red.shade100
                    : Colors.green.shade100,
                child: Padding(
                  padding: EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Icon(
                        _statusMessage.contains('Error')
                            ? Icons.error_outline
                            : Icons.check_circle_outline,
                      ),
                      SizedBox(width: 8),
                      Expanded(child: Text(_statusMessage)),
                    ],
                  ),
                ),
              ),
            
            SizedBox(height: 16),
            
            // Sección de Reportes Rápidos
            _buildSeccionReportesRapidos(),
            
            SizedBox(height: 24),
            
            // Historial Reciente
            _buildSeccionHistorial(),
          ],
        ),
      ),
      
      // 🎤 Botón flotante para voz
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isGenerating ? null : _abrirReporteVoz,
        icon: Icon(Icons.mic),
        label: Text('Reporte por Voz'),
        backgroundColor: Colors.deepPurple,
      ),
    );
  }

  /// Sección con botones de reportes rápidos
  Widget _buildSeccionReportesRapidos() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📊 REPORTES RÁPIDOS',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 12),
        GridView.count(
          shrinkWrap: true,
          physics: NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 1.5,
          children: [
            _buildReporteRapidoCard(
              titulo: '📈 Ventas',
              subtitulo: 'Este mes',
              icono: Icons.trending_up,
              color: Colors.blue,
              onTap: () => _generarReporteRapido(
                'Ventas de este mes agrupado por producto en PDF',
              ),
            ),
            _buildReporteRapidoCard(
              titulo: '👥 Clientes',
              subtitulo: 'Activos',
              icono: Icons.people,
              color: Colors.green,
              onTap: () => _generarReporteRapido(
                'Clientes activos del último mes en Excel',
              ),
            ),
            _buildReporteRapidoCard(
              titulo: '📦 Stock',
              subtitulo: 'Inventario',
              icono: Icons.inventory,
              color: Colors.orange,
              onTap: () => _generarReporteRapido(
                'Inventario actual con stock y valor en Excel',
              ),
            ),
            _buildReporteRapidoCard(
              titulo: '🔝 Top',
              subtitulo: 'Productos',
              icono: Icons.star,
              color: Colors.purple,
              onTap: () => _generarReporteRapido(
                'Top 10 productos más vendidos del último mes en PDF',
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Card para reporte rápido
  Widget _buildReporteRapidoCard({
    required String titulo,
    required String subtitulo,
    required IconData icono,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 4,
      child: InkWell(
        onTap: _isGenerating ? null : onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            gradient: LinearGradient(
              colors: [color.withOpacity(0.7), color],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icono, size: 40, color: Colors.white),
              SizedBox(height: 8),
              Text(
                titulo,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              Text(
                subtitulo,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Sección de historial
  Widget _buildSeccionHistorial() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📝 HISTORIAL RECIENTE',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 12),
        if (_historialReciente.isEmpty)
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'No hay reportes recientes',
                style: TextStyle(color: Colors.grey),
              ),
            ),
          )
        else
          ..._historialReciente.map((item) => Card(
                child: ListTile(
                  leading: Icon(Icons.description, color: Colors.deepPurple),
                  title: Text(item['prompt']),
                  subtitle: Text(item['fecha']),
                  trailing: Icon(Icons.arrow_forward_ios, size: 16),
                  onTap: () {
                    // TODO: Ver detalles o regenerar
                  },
                ),
              )),
      ],
    );
  }

  /// Generar reporte rápido (predefinido)
  Future<void> _generarReporteRapido(String prompt) async {
    setState(() {
      _isGenerating = true;
      _statusMessage = 'Generando reporte...';
    });

    try {
      final file = await _apiService.descargarReporte(
        prompt: prompt,
        formato: prompt.contains('Excel') ? 'excel' : 'pdf',
      );

      setState(() {
        _isGenerating = false;
        _statusMessage = 'Reporte generado exitosamente';
      });

      // Abrir archivo
      await OpenFilex.open(file.path);

      // Limpiar mensaje después de 3 segundos
      Future.delayed(Duration(seconds: 3), () {
        if (mounted) {
          setState(() => _statusMessage = '');
        }
      });
    } catch (e) {
      setState(() {
        _isGenerating = false;
        _statusMessage = 'Error: ${e.toString()}';
      });
    }
  }

  /// Abrir pantalla de reporte por voz
  void _abrirReporteVoz() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => IAVoiceScreen(token: widget.token),
      ),
    );
  }
}
```

---

## 🎤 FAB (FloatingActionButton) Avanzado

### Opción 1: FAB Simple (como arriba)

```dart
FloatingActionButton.extended(
  onPressed: _abrirReporteVoz,
  icon: Icon(Icons.mic),
  label: Text('Reporte por Voz'),
  backgroundColor: Colors.deepPurple,
)
```

### Opción 2: FAB con Speed Dial (Opciones múltiples)

```dart
// Agregar dependencia:
// dependencies:
//   flutter_speed_dial: ^7.0.0

import 'package:flutter_speed_dial/flutter_speed_dial.dart';

SpeedDial(
  animatedIcon: AnimatedIcons.menu_close,
  backgroundColor: Colors.deepPurple,
  overlayColor: Colors.black,
  overlayOpacity: 0.5,
  children: [
    SpeedDialChild(
      child: Icon(Icons.mic),
      label: 'Reporte por Voz',
      backgroundColor: Colors.red,
      onTap: _abrirReporteVoz,
    ),
    SpeedDialChild(
      child: Icon(Icons.keyboard),
      label: 'Reporte por Texto',
      backgroundColor: Colors.blue,
      onTap: _abrirReporteTexto,
    ),
    SpeedDialChild(
      child: Icon(Icons.history),
      label: 'Ver Historial',
      backgroundColor: Colors.green,
      onTap: _verHistorial,
    ),
  ],
)
```

---

## 🚀 Flujo de Navegación

```
Login Screen
     │
     ├──> Admin Dashboard (este archivo)
     │        │
     │        ├──> FAB → Reporte por Voz (FLUTTER_REPORTES_VOZ.md)
     │        │
     │        ├──> Botón Rápido → Generar PDF/Excel directo
     │        │
     │        └──> Historial → Ver consultas anteriores
     │
     └──> Logout
```

---

## 📱 Estructura de Archivos Recomendada

```
lib/
├── main.dart
├── screens/
│   ├── login_screen.dart              # Login de admin
│   ├── admin_dashboard_screen.dart    # Dashboard principal (este)
│   ├── ia_voice_screen.dart           # Pantalla voz (FLUTTER_REPORTES_VOZ.md)
│   └── historial_screen.dart          # Ver historial completo
├── services/
│   ├── ia_api_service.dart            # Llamadas API (FLUTTER_IA_VOZ.md)
│   ├── voice_service.dart             # Reconocimiento de voz
│   └── auth_service.dart              # Autenticación
├── widgets/
│   ├── reporte_rapido_card.dart       # Card de reporte rápido
│   └── historial_item.dart            # Item de historial
└── models/
    ├── usuario.dart
    └── reporte.dart
```

---

## 🔐 Login Screen

```dart
// lib/screens/login_screen.dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'admin_dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController(text: 'admin');
  final _passwordController = TextEditingController();
  
  bool _isLoading = false;
  String _errorMessage = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.deepPurple, Colors.purpleAccent],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: EdgeInsets.all(24),
            child: Card(
              elevation: 8,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Logo
                      Icon(
                        Icons.admin_panel_settings,
                        size: 80,
                        color: Colors.deepPurple,
                      ),
                      SizedBox(height: 16),
                      Text(
                        '🏪 SmartSales Admin',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 32),
                      
                      // Usuario
                      TextFormField(
                        controller: _usernameController,
                        decoration: InputDecoration(
                          labelText: 'Usuario',
                          prefixIcon: Icon(Icons.person),
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Ingresa tu usuario';
                          }
                          return null;
                        },
                      ),
                      
                      SizedBox(height: 16),
                      
                      // Contraseña
                      TextFormField(
                        controller: _passwordController,
                        obscureText: true,
                        decoration: InputDecoration(
                          labelText: 'Contraseña',
                          prefixIcon: Icon(Icons.lock),
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Ingresa tu contraseña';
                          }
                          return null;
                        },
                      ),
                      
                      SizedBox(height: 8),
                      
                      // Error
                      if (_errorMessage.isNotEmpty)
                        Text(
                          _errorMessage,
                          style: TextStyle(color: Colors.red),
                        ),
                      
                      SizedBox(height: 24),
                      
                      // Botón
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _login,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.deepPurple,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: _isLoading
                              ? CircularProgressIndicator(color: Colors.white)
                              : Text(
                                  'Ingresar',
                                  style: TextStyle(
                                    fontSize: 18,
                                    color: Colors.white,
                                  ),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final authService = AuthService();
      final result = await authService.login(
        _usernameController.text,
        _passwordController.text,
      );

      // Verificar que sea admin
      if (result['is_staff'] != true) {
        throw Exception('Acceso solo para administradores');
      }

      // Navegar al dashboard
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => AdminDashboardScreen(
            token: result['token'],
            username: result['username'],
          ),
        ),
      );
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}
```

---

## 🎯 AuthService

```dart
// lib/services/auth_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  static const String baseUrl = 'https://smartsales365.duckdns.org';

  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/usuarios/token/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Guardar token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', data['token']);
        await prefs.setString('username', data['username']);
        
        return data;
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Error al iniciar sesión');
      }
    } catch (e) {
      throw Exception('Error de conexión: $e');
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('username');
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }
}
```

---

## ✅ Checklist de Implementación

### Pantallas
- [ ] Login Screen (con validación de admin)
- [ ] Admin Dashboard (con reportes rápidos)
- [ ] Reporte por Voz Screen (FLUTTER_REPORTES_VOZ.md)
- [ ] Historial Screen

### Servicios
- [ ] AuthService (login/logout/token)
- [ ] IAApiService (consultas IA)
- [ ] VoiceService (speech-to-text)

### Widgets
- [ ] ReporteRapidoCard (botones del dashboard)
- [ ] HistorialItem (items de historial)

### Features
- [ ] Login solo para admin (is_staff=true)
- [ ] Dashboard con 4 reportes rápidos predefinidos
- [ ] FAB para reporte por voz
- [ ] Historial de reportes recientes
- [ ] Descarga y apertura automática de PDF/Excel
- [ ] Manejo de errores con mensajes amigables

---

## 🎨 Personalización

### Cambiar Colores del Tema
```dart
// main.dart
MaterialApp(
  theme: ThemeData(
    primarySwatch: Colors.deepPurple,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.deepPurple,
      brightness: Brightness.light,
    ),
    useMaterial3: true,
  ),
  // ...
)
```

### Cambiar Reportes Rápidos
```dart
// En _buildSeccionReportesRapidos(), modifica los cards:
_buildReporteRapidoCard(
  titulo: '💰 Caja',
  subtitulo: 'Hoy',
  icono: Icons.payments,
  color: Colors.teal,
  onTap: () => _generarReporteRapido(
    'Ventas de hoy en PDF',
  ),
),
```

---

**🚀 Con esto tienes todo listo para implementar el Dashboard de Admin con reportes rápidos y voz!**

