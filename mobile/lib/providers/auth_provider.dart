import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  static const _storage = FlutterSecureStorage();
  UserModel? _user;
  bool _loading = false;
  String? _error;

  UserModel? get user => _user;
  bool get isLoggedIn => _user != null;
  bool get loading => _loading;
  String? get error => _error;

  Future<void> tryRestoreSession() async {
    final token = await _storage.read(key: 'jwt_token');
    if (token == null) return;
    try {
      final parts = token.split('.');
      if (parts.length == 3) {
        final payload = jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))));
        final exp = payload['exp'] as int?;
        if (exp != null && DateTime.fromMillisecondsSinceEpoch(exp * 1000).isAfter(DateTime.now())) {
          _user = UserModel.fromJson(payload, token);
          notifyListeners();
        }
      }
    } catch (_) {}
  }

  Future<bool> login(String email, String password) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final data = await ApiService.login(email, password);
      final token = data['access_token'] as String;
      await _storage.write(key: 'jwt_token', value: token);
      final parts = token.split('.');
      final payload = jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))));
      _user = UserModel.fromJson(payload, token);
      _loading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.userMessage;
      _loading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Connection failed. Check server address.';
      _loading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'jwt_token');
    _user = null;
    notifyListeners();
  }
}
