import 'dart:async';
import 'package:socket_io_client/socket_io_client.dart' as IO;
import '../models/rider_location.dart';
import '../config/app_config.dart';

/// Socket.IO service for real-time group ride communication
class SocketService {
  static final SocketService _instance = SocketService._internal();
  factory SocketService() => _instance;
  SocketService._internal();

  IO.Socket? _socket;
  bool _isConnected = false;
  
  bool get isConnected => _isConnected;

  // Callbacks for location updates from other riders
  Function(RiderLocation)? onLocationUpdate;
  Function(String userId)? onUserJoined;
  Function(String userId)? onUserLeft;

  /// Connect to Socket.IO server with automatic reconnection
  Future<void> connect(String userId) async {
    if (_isConnected) return;

    try {
      _socket = IO.io(
        AppConfig.socketUrl,
        IO.OptionBuilder()
            .setTransports(['websocket'])  // Use WebSocket only for lower latency
            .enableAutoConnect()           // Auto-reconnect on disconnect
            .enableReconnection()          // Reconnection with backoff
            .setReconnectionAttempts(5)    // Try 5 times before giving up
            .setReconnectionDelay(1000)    // Start with 1 second delay
            .setAuth({'userId': userId})   // Send userId for authentication
            .build(),
      );

      // Connection successful
      _socket!.onConnect((_) {
        print('✅ Connected to Socket.IO server');
        _isConnected = true;
      });

      // Connection error
      _socket!.onConnectError((error) {
        print('❌ Connection error: $error');
        _isConnected = false;
      });

      // Disconnected from server
      _socket!.onDisconnect((_) {
        print('🔌 Disconnected from server');
        _isConnected = false;
      });

      // Listen for location updates from other riders
      _socket!.on('rider_location_update', (data) {
        try {
          final location = RiderLocation.fromJson(data as Map<String, dynamic>);
          onLocationUpdate?.call(location);
        } catch (e) {
          print('Error parsing location update: $e');
        }
      });

      // Listen for user joined event
      _socket!.on('participant_joined', (data) {
        final userId = data['userId'] as String;
        print('👋 User joined: $userId');
        onUserJoined?.call(userId);
      });

      // Listen for user left event
      _socket!.on('participant_left', (data) {
        final userId = data['userId'] as String;
        print('👋 User left: $userId');
        onUserLeft?.call(userId);
      });

      _socket!.connect();
    } catch (e) {
      print('Failed to connect to Socket.IO: $e');
      _isConnected = false;
    }
  }

  /// Get route polyline from current location to destination
  Future<Map<String, dynamic>?> getRoute(
    double startLat, 
    double startLon, 
    double endLat, 
    double endLon
  ) async {
    if (!_isConnected || _socket == null) return null;
    
    final completer = Completer<Map<String, dynamic>?>();

    _socket!.emitWithAck('get_route', {
      'startLat': startLat,
      'startLon': startLon,
      'endLat': endLat,
      'endLon': endLon,
    }, ack: (response) {
      if (response != null && response['success'] == true) {
        completer.complete(response);
      } else {
        completer.complete(null);
      }
    });

    return completer.future;
  }


  /// Join a specific ride room for location sharing
  void joinRide(String rideId, String userId, String displayName ,{double? latitude, double? longitude}) {
    if (!_isConnected || _socket == null) {
      print('⚠️ Cannot join ride: Not connected to server');
      return;
    }

    _socket!.emit('join_ride', {
      'rideId': rideId,
      'userId': userId,
      'username': displayName,
      'latitude' : latitude ?? 0.0,
      'longitude': longitude ?? 0.0,
    });

    print('🚴 Joined ride room: $rideId');
  }

  /// Leave the current ride room
  void leaveRide(String rideId, String userId) {
    if (!_isConnected || _socket == null) return;

    _socket!.emit('leave_ride', {
      'rideId': rideId,
      'userId': userId,
    });

    print('🚪 Left ride room: $rideId');
  }

  /// Send location update to all riders in the room
  /// Uses optimistic UI - update shown immediately, confirmed by server
  void sendLocationUpdate(String rideId, RiderLocation location) {
    if (!_isConnected || _socket == null) {
      print('⚠️ Cannot send location: Not connected');
      return;
    }

    final data = {
      'rideId': rideId,
      'userId': location.userId,
      'username': location.displayName,
      'latitude': location.position.latitude,
      'longitude': location.position.longitude,
    };

    // Send with acknowledgment for reliability
    _socket!.emitWithAck('location_update', data, ack: (response) {
      if (response != null && response['success'] == true) {
        print('✅ Location update confirmed by server');
      } else {
        print('⚠️ Location update failed');
      }
    });
  }

  /// Request current locations of all riders in the room
  void requestCurrentLocations(String rideId) {
    if (!_isConnected || _socket == null) return;

    _socket!.emit('requestLocations', {'rideId': rideId});
  }

  /// Disconnect from Socket.IO server
  void disconnect() {
    _socket?.disconnect();
    _socket?.dispose();
    _socket = null;
    _isConnected = false;
    print('🔌 Socket.IO disconnected');
  }

  

}
