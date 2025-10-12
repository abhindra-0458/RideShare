import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import 'dart:convert';

class AuthProvider extends ChangeNotifier {
  User? _user;
  bool _isLoading = false;
  bool _isAuthenticated = false;
  String? _error;

  final _storage = const FlutterSecureStorage();
  final _apiService = ApiService();

  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;
  String? get error => _error;

  // Login
  Future<bool> login(String email, String password) async {
    _setLoading(true);
    _error = null;

    try {
      final response = await _apiService.login(email, password);
      
      if (response.isSuccess) {
        final data = response.data!;
        _user = User.fromJson(data['user']);
        final tokens = AuthTokens.fromJson(data['tokens']);
        
        // Store tokens securely
        await _storage.write(key: 'access_token', value: tokens.accessToken);
        await _storage.write(key: 'refresh_token', value: tokens.refreshToken);
        
        _isAuthenticated = true;
        _setLoading(false);
        return true;
      } else {
        _error = response.error;
        _setLoading(false);
        return false;
      }
    } catch (e) {
      _error = 'Login failed: $e';
      _setLoading(false);
      return false;
    }
  }

  // Register
  // In auth_provider.dart - keep as is, just add better error logging
Future<bool> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    _setLoading(true);
    _error = null;

    try {
      print('Calling backend register with: email=$email, firstName=$firstName, lastName=$lastName');
      
      final response = await _apiService.register(
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        phone: phone,
      );

      print('Calling backend register with: email=$email, firstName=$firstName, lastName=$lastName');
      print('Backend response success: ${response.isSuccess}');  
      print('Backend response error: ${response.error}');

      if (!response.isSuccess) {
        final errorString = response.error ?? '';
        try {
          final errorJson = jsonDecode(errorString);
          if (errorJson['errors'] != null) {
            _error = (errorJson['errors'] as List)
                .map((e) => e['msg'])
                .join(', ');
          } else {
            _error = errorString;
          }
        } catch (_) {
          _error = errorString;
        }
      }


      
      if (response.isSuccess) {
        // Registration successful
        final data = response.data!;
        _user = User.fromJson(data['user']);
        final tokens = AuthTokens.fromJson(data['tokens']);
        
        await _storage.write(key: 'access_token', value: tokens.accessToken);
        await _storage.write(key: 'refresh_token', value: tokens.refreshToken);
        
        _isAuthenticated = true;
        _setLoading(false);
        return true;
      } else {
        _error = response.error;
        _setLoading(false);
        return false;
      }
    } catch (e) {
      print('Registration exception: $e');
      _error = 'Registration failed: $e';
      _setLoading(false);
      return false;
    }
  }


  // Logout
  Future<void> logout() async {
    _setLoading(true);
    
    try {
      await _apiService.logout();
      await _storage.deleteAll();
      
      _user = null;
      _isAuthenticated = false;
      _error = null;
    } catch (e) {
      print('Logout error: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Check if user is logged in (on app start)
  Future<void> checkAuthStatus() async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      // TODO: Validate token with backend
      _isAuthenticated = true;
    }
    notifyListeners();
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}