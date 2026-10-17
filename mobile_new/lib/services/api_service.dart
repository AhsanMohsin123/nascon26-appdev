import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();
  static String _baseUrl = 'http://10.0.2.2:8080';

  static String get baseUrl => _baseUrl;
  static set baseUrl(String url) => _baseUrl = url;

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
    final r = await http.post(Uri.parse('$_baseUrl$path'), headers: h, body: jsonEncode(body));
    return _parse(r);
  }

  static Future<Map<String, dynamic>> get(String path) async {
    final h = await _headers;
    final r = await http.get(Uri.parse('$_baseUrl$path'), headers: h);
    return _parse(r);
  }

  static Map<String, dynamic> _parse(http.Response r) {
    final body = jsonDecode(r.body);
    if (r.statusCode >= 400) {
      final err = body['error'] ?? {};
      throw ApiException(
        code: err['code'] ?? 'UNKNOWN_ERROR',
        message: err['message'] ?? 'An error occurred',
        statusCode: r.statusCode,
      );
    }
    return body as Map<String, dynamic>;
  }

  // Auth
  static Future<Map<String, dynamic>> login(String email, String password) =>
      post('/auth/login', {'email': email, 'password': password});

  // Reset
  static Future<Map<String, dynamic>> reset({int seed = 42}) =>
      post('/audit/v1/reset', {'seed': seed});

  // Fixtures
  static Future<Map<String, dynamic>> getFixtures(String leagueId) =>
      get('/audit/v1/standings/$leagueId');

  // Score
  static Future<Map<String, dynamic>> getScore(String matchId) =>
      get('/audit/v1/score/$matchId');

  // Append event
  static Future<Map<String, dynamic>> appendEvent(Map<String, dynamic> body) =>
      post('/audit/v1/events', body);

  // Standings
  static Future<Map<String, dynamic>> getStandings(String leagueId) =>
      get('/audit/v1/standings/$leagueId');

  // Roster
  static Future<Map<String, dynamic>> setupRoster(Map<String, dynamic> body) =>
      post('/audit/v1/roster/setup', body);

  static Future<Map<String, dynamic>> transferPlayer(Map<String, dynamic> body) =>
      post('/audit/v1/roster/transfer', body);

  static Future<Map<String, dynamic>> getRosterHistory(String playerId, {String? asOf}) =>
      get('/audit/v1/roster/history/$playerId${asOf != null ? '?as_of=$asOf' : ''}');

  // Store
  static Future<Map<String, dynamic>> checkout(Map<String, dynamic> body) =>
      post('/audit/v1/checkout', body);

  static Future<Map<String, dynamic>> getInventory(String variantId) =>
      get('/audit/v1/inventory/$variantId');

  // Offline sync
  static Future<Map<String, dynamic>> offlineSync(String deviceId, List<Map<String, dynamic>> actions) =>
      post('/audit/v1/offline-sync', {'device_id': deviceId, 'actions': actions});

  // Health
  static Future<bool> checkHealth() async {
    try {
      final r = await http.get(Uri.parse('$_baseUrl/health')).timeout(const Duration(seconds: 3));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}

class ApiException implements Exception {
  final String code;
  final String message;
  final int statusCode;
  ApiException({required this.code, required this.message, required this.statusCode});

  String get userMessage {
    switch (code) {
      case 'OUT_OF_STOCK': return 'Sorry, this item is out of stock.';
      case 'PAYMENT_DECLINED': return 'Payment was declined. Please try again.';
      case 'PAYMENT_CAPTURE_FAILED': return 'Payment capture failed. Please try again.';
      case 'TRANSFER_WINDOW_CLOSED': return 'Transfer window is currently closed.';
      case 'SQUAD_FULL': return 'The destination squad is full.';
      case 'PLAYER_ON_LOAN': return 'This player is currently on loan.';
      case 'MIN_POSITION_VIOLATION': return 'Cannot remove player — minimum position requirement.';
      case 'INVALID_DISCOUNT_CODE': return 'Invalid discount code.';
      case 'UNAUTHENTICATED': return 'Please log in again.';
      default: return message;
    }
  }

  @override
  String toString() => 'ApiException[$statusCode/$code]: $message';
}
