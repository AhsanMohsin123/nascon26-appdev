import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();
  // 127.0.0.1 via ADB reverse tunnel (USB) or change to WiFi IP in settings
  static String _baseUrl = 'http://127.0.0.1:8080';

  static String get baseUrl => _baseUrl;
  static set baseUrl(String url) => _baseUrl = url.trim().isEmpty ? 'http://localhost:8080' : url.trim();

  static Future<String?> get token => _storage.read(key: 'jwt_token');

  static Future<Map<String, String>> get _headers async {
    final t = await token;
    return {
      'Content-Type': 'application/json',
      if (t != null) 'Authorization': 'Bearer $t',
    };
  }

  static Future<Map<String, dynamic>> post(String path, Map<String, dynamic> body) async {
    final h = await _headers;
    final r = await http
        .post(Uri.parse('$_baseUrl$path'), headers: h, body: jsonEncode(body))
        .timeout(const Duration(seconds: 8));
    return _parse(r);
  }

  static Future<Map<String, dynamic>> get(String path) async {
    final h = await _headers;
    final r = await http.get(Uri.parse('$_baseUrl$path'), headers: h).timeout(const Duration(seconds: 8));
    return _parse(r);
  }

  static Map<String, dynamic> _parse(http.Response r) {
    final body = jsonDecode(r.body);
    if (r.statusCode >= 400) {
      final err = body['error'] ?? {};
      throw ApiException(code: err['code'] ?? 'UNKNOWN_ERROR', message: err['message'] ?? 'Error', statusCode: r.statusCode);
    }
    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> login(String email, String password) =>
      post('/auth/login', {'email': email, 'password': password});

  static Future<Map<String, dynamic>> reset({int seed = 42}) =>
      post('/audit/v1/reset', {'seed': seed});

  static Future<Map<String, dynamic>> getScore(String matchId) =>
      get('/audit/v1/score/$matchId');

  static Future<Map<String, dynamic>> appendEvent(Map<String, dynamic> body) =>
      post('/audit/v1/events', body);

  static Future<Map<String, dynamic>> getStandings(String leagueId) =>
      get('/audit/v1/standings/$leagueId');

  static Future<Map<String, dynamic>> transferPlayer(Map<String, dynamic> body) =>
      post('/audit/v1/roster/transfer', body);

  static Future<Map<String, dynamic>> getRosterHistory(String playerId, {String? asOf}) =>
      get('/audit/v1/roster/history/$playerId${asOf != null ? '?as_of=$asOf' : ''}');

  static Future<Map<String, dynamic>> checkout(Map<String, dynamic> body) =>
      post('/audit/v1/checkout', body);

  static Future<Map<String, dynamic>> getInventory(String variantId) =>
      get('/audit/v1/inventory/$variantId');

  static Future<Map<String, dynamic>> offlineSync(String deviceId, List<Map<String, dynamic>> actions) =>
      post('/audit/v1/offline-sync', {'device_id': deviceId, 'actions': actions});

  static Future<bool> checkHealth() async {
    try {
      final r = await http.get(Uri.parse('$_baseUrl/health')).timeout(const Duration(seconds: 3));
      return r.statusCode == 200;
    } catch (_) { return false; }
  }
}

class ApiException implements Exception {
  final String code;
  final String message;
  final int statusCode;
  ApiException({required this.code, required this.message, required this.statusCode});

  String get userMessage {
    switch (code) {
      case 'OUT_OF_STOCK': return 'Out of stock';
      case 'PAYMENT_DECLINED': return 'Payment declined';
      case 'PAYMENT_CAPTURE_FAILED': return 'Capture failed';
      case 'TRANSFER_WINDOW_CLOSED': return 'Transfer window closed';
      case 'SQUAD_FULL': return 'Squad is full';
      case 'PLAYER_ON_LOAN': return 'Player is on loan';
      case 'UNAUTHENTICATED': return 'Please log in again';
      default: return message.length > 60 ? '${message.substring(0, 60)}...' : message;
    }
  }
}
