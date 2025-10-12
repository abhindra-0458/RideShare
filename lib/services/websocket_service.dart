//import 'dart:convert';
import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/app_config.dart';

class WebSocketService {
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  IO.Socket? _socket;
  final _storage = const FlutterSecureStorage();
  bool _isConnected = false;

  bool get isConnected => _isConnected;

  Future<void> connect() async {
    if (_isConnected) return;

    try {
      final token = await _storage.read(key: 'access_token');
      if (token == null) throw Exception('No auth token available');

      _socket = IO.io(
        AppConfig.wsBaseUrl,
        IO.OptionBuilder()
            .setTransports(['websocket'])
            .setAuth({'token': token})
            .build(),
      );

      _socket!.onConnect((_) {
        print('Connected to WebSocket server');
        _isConnected = true;
      });

      _socket!.onConnectError((error) {
        print('WebSocket connection error: $error');
        _isConnected = false;
      });

      _socket!.onDisconnect((_) {
        print('Disconnected from WebSocket server');
        _isConnected = false;
      });

      // Listen for location updates
      _socket!.on('participant_location_update', (data) {
        _handleParticipantLocationUpdate(data);
      });

      // Listen for drift alerts
      _socket!.on('drift_alerts', (data) {
        _handleDriftAlerts(data);
      });

      // Listen for ride events
      _socket!.on('participant_joined', (data) {
        _handleParticipantJoined(data);
      });

      _socket!.on('participant_left', (data) {
        _handleParticipantLeft(data);
      });

    } catch (e) {
      print('WebSocket connection failed: $e');
      _isConnected = false;
    }
  }

  void updateLocation({
    required double latitude,
    required double longitude,
    double? accuracy,
    String? rideId,
  }) {
    if (!_isConnected || _socket == null) return;

    _socket!.emit('location_update', {
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
      'timestamp': DateTime.now().toIso8601String(),
      if (rideId != null) 'rideId': rideId,
    });
  }

  void joinRide(String rideId) {
    if (!_isConnected || _socket == null) return;
    _socket!.emit('join_ride', {'rideId': rideId});
  }

  void leaveRide(String rideId) {
    if (!_isConnected || _socket == null) return;
    _socket!.emit('leave_ride', {'rideId': rideId});
  }

  void getRideLocations(String rideId) {
    if (!_isConnected || _socket == null) return;
    _socket!.emit('get_ride_locations', {'rideId': rideId});
  }

  // Event handlers (override in your UI)
  Function(Map<String, dynamic>)? onParticipantLocationUpdate;
  Function(List<dynamic>)? onDriftAlerts;
  Function(Map<String, dynamic>)? onParticipantJoined;
  Function(Map<String, dynamic>)? onParticipantLeft;

  void _handleParticipantLocationUpdate(dynamic data) {
    if (onParticipantLocationUpdate != null) {
      onParticipantLocationUpdate!(data as Map<String, dynamic>);
    }
  }

  void _handleDriftAlerts(dynamic data) {
    if (onDriftAlerts != null) {
      onDriftAlerts!(data as List<dynamic>);
    }
  }

  void _handleParticipantJoined(dynamic data) {
    if (onParticipantJoined != null) {
      onParticipantJoined!(data as Map<String, dynamic>);
    }
  }

  void _handleParticipantLeft(dynamic data) {
    if (onParticipantLeft != null) {
      onParticipantLeft!(data as Map<String, dynamic>);
    }
  }

  void disconnect() {
    if (_socket != null) {
      _socket!.disconnect();
      _socket = null;
    }
    _isConnected = false;
  }
}