import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/app_config.dart';
import '../models/api_response.dart';
import '../models/ride_model.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final _storage = const FlutterSecureStorage();
  final _client = http.Client();

  // Legacy base URL for backward compatibility
  static const String baseUrl = "http://localhost:3000"; // Updated to match your backend

  // Get headers with authentication
  Future<Map<String, String>> _getHeaders() async {
    final token = await _storage.read(key: 'access_token');
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // Generic API request handler with token refresh
  Future<ApiResponse<T>> _makeRequest<T>(
    String method,
    String endpoint, {
    dynamic body,
    Map<String, String>? additionalHeaders,
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    try {
      final headers = await _getHeaders();
      if (additionalHeaders != null) {
        headers.addAll(additionalHeaders);
      }

      final uri = Uri.parse('${AppConfig.apiBaseUrl}$endpoint');
      http.Response response;

      switch (method.toUpperCase()) {
        case 'GET':
          response = await _client.get(uri, headers: headers)
              .timeout(Duration(milliseconds: AppConfig.receiveTimeout));
          break;
        case 'POST':
          response = await _client.post(
            uri,
            headers: headers,
            body: body != null ? jsonEncode(body) : null,
          ).timeout(Duration(milliseconds: AppConfig.receiveTimeout));
          break;
        case 'PUT':
          response = await _client.put(
            uri,
            headers: headers,
            body: body != null ? jsonEncode(body) : null,
          ).timeout(Duration(milliseconds: AppConfig.receiveTimeout));
          break;
        case 'DELETE':
          response = await _client.delete(uri, headers: headers)
              .timeout(Duration(milliseconds: AppConfig.receiveTimeout));
          break;
        default:
          throw Exception('Unsupported HTTP method: $method');
      }

      // Handle token expiration
      if (response.statusCode == 401) {
        final refreshed = await _refreshToken();
        if (refreshed) {
          // Retry request with new token
          final newHeaders = await _getHeaders();
          if (additionalHeaders != null) newHeaders.addAll(additionalHeaders);
          
          switch (method.toUpperCase()) {
            case 'GET':
              response = await _client.get(uri, headers: newHeaders);
              break;
            case 'POST':
              response = await _client.post(
                uri,
                headers: newHeaders,
                body: body != null ? jsonEncode(body) : null,
              );
              break;
            // Add other methods as needed
          }
        } else {
          return ApiResponse<T>.error('Authentication failed');
        }
      }

      final responseData = jsonDecode(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (fromJson != null && responseData['data'] != null) {
          return ApiResponse<T>.success(fromJson(responseData['data']));
        } else {
          return ApiResponse<T>.success(responseData['data']);
        }
      } else {
        return ApiResponse<T>.error(
          responseData['message'] ?? 'Request failed',
          statusCode: response.statusCode,
        );
      }
    } on SocketException {
      return ApiResponse<T>.error('No internet connection');
    } on HttpException {
      return ApiResponse<T>.error('Server error');
    } catch (e) {
      return ApiResponse<T>.error('Unexpected error: $e');
    }
  }

  // Token refresh logic
  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final response = await _client.post(
        Uri.parse('${AppConfig.apiBaseUrl}/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refreshToken': refreshToken}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body)['data'];
        await _storage.write(key: 'access_token', value: data['tokens']['accessToken']);
        await _storage.write(key: 'refresh_token', value: data['tokens']['refreshToken']);
        return true;
      }
    } catch (e) {
      print('Token refresh failed: $e');
    }
    return false;
  }

  // LEGACY METHOD - Firebase integration (keep for backward compatibility)
  Future<bool> saveUserData(String uid, String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/users"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"uid": uid, "email": email, "password": password}),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("API Error: $e");
      return false;
    }
  }

  // NEW METHOD - Sync Firebase user with backend
  Future<ApiResponse<Map<String, dynamic>>> syncFirebaseUser({
    required String uid,
    required String email,
    required String firstName,
    required String lastName,
    String? phone,
    String? profilePictureUrl,
  }) async {
    return _makeRequest<Map<String, dynamic>>(
      'POST',
      '/users/sync-firebase',
      body: {
        'firebaseUid': uid,
        'email': email,
        'firstName': firstName,
        'lastName': lastName,
        if (phone != null) 'phone': phone,
        if (profilePictureUrl != null) 'profilePictureUrl': profilePictureUrl,
      },
    );
  }

  // Auth endpoints
  Future<ApiResponse<Map<String, dynamic>>> login(String email, String password) {
    return _makeRequest<Map<String, dynamic>>(
      'POST',
      '/auth/login',
      body: {'email': email, 'password': password},
    );
  }

  Future<ApiResponse<Map<String, dynamic>>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) {
    return _makeRequest<Map<String, dynamic>>(
      'POST',
      '/auth/register',
      body: {
        'email': email,
        'password': password,
        'firstName': firstName,
        'lastName': lastName,
        if (phone != null) 'phone': phone,
      },
    );
  }

  Future<ApiResponse<void>> logout() {
    return _makeRequest<void>('POST', '/auth/logout');
  }

  // Ride endpoints
  Future<ApiResponse<List<dynamic>>> searchRides({
    double? latitude,
    double? longitude,
    double? radiusKm,
    String? difficulty,
    int limit = 20,
    int offset = 0,
  }) {
    final queryParams = <String, String>{
      if (latitude != null) 'latitude': latitude.toString(),
      if (longitude != null) 'longitude': longitude.toString(),
      if (radiusKm != null) 'radiusKm': radiusKm.toString(),
      if (difficulty != null) 'difficulty': difficulty,
      'limit': limit.toString(),
      'offset': offset.toString(),
    };

    final query = Uri(queryParameters: queryParams).query;
    return _makeRequest<List<dynamic>>('GET', '/rides/search?$query');
  }

  Future<ApiResponse<Map<String, dynamic>>> createRide({
    required String title,
    required String description,
    required LocationPoint startLocation,
    required LocationPoint endLocation,
    required DateTime scheduledDateTime,
    required bool isPublic,
    required int maxParticipants,
    String difficulty = 'medium',
  }) {
    return _makeRequest<Map<String, dynamic>>(
      'POST',
      '/rides',
      body: {
        'title': title,
        'description': description,
        'startLocation': startLocation.toJson(),
        'endLocation': endLocation.toJson(),
        'scheduledDateTime': scheduledDateTime.toIso8601String(),
        'isPublic': isPublic,
        'maxParticipants': maxParticipants,
        'difficulty': difficulty,
      },
    );
  }

  Future<ApiResponse<void>> joinRide(String rideId) {
    return _makeRequest<void>('POST', '/rides/$rideId/join');
  }

  // Location endpoints
  Future<ApiResponse<void>> updateLocation({
    required double latitude,
    required double longitude,
    double? accuracy,
  }) {
    return _makeRequest<void>(
      'POST',
      '/locations/update',
      body: {
        'latitude': latitude,
        'longitude': longitude,
        if (accuracy != null) 'accuracy': accuracy,
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }

  Future<ApiResponse<List<dynamic>>> getRideParticipantLocations(String rideId) {
    return _makeRequest<List<dynamic>>('GET', '/locations/ride/$rideId');
  }

  // Clean up
  void dispose() {
    _client.close();
  }
}