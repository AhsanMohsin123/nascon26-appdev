import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class AuthService extends ChangeNotifier {
  static const _storage = FlutterSecureStorage();
  String? _token;
  String? _role;
  bool _isLoggedIn = false;

  bool get isLoggedIn => _isLoggedIn;
  String? get token => _token;
  String? get role => _role;

  String _baseUrl = 'http://10.0.2.2:8080';
  String get baseUrl => _baseUrl;
  set baseUrl(String url) {
    _baseUrl = url;
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    try {
      final resp = await http.post(
        Uri.parse('$_baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        _token = data['access_token'];
        _role = data['role'];
        _isLoggedIn = true;
        await _storage.write(key: 'jwt', value: _token);
        notifyListeners();
        return true;
      }
    } catch (_) {}
    return false;
  }

  Future<void> logout() async {
    _token = null;
    _role = null;
    _isLoggedIn = false;
    await _storage.delete(key: 'jwt');
    notifyListeners();
  }
}
