import 'dart:async';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

/// Battery-efficient location tracking service
/// Uses distance-based filtering and adaptive accuracy
class LocationTrackingService {
  static final LocationTrackingService _instance = LocationTrackingService._internal();
  factory LocationTrackingService() => _instance;
  LocationTrackingService._internal();

  StreamSubscription<Position>? _positionSubscription;
  final _locationController = StreamController<Position>.broadcast();

  /// Stream of location updates (only when significant movement detected)
  Stream<Position> get locationStream => _locationController.stream;

  bool _isTracking = false;
  bool get isTracking => _isTracking;

  /// Start battery-efficient location tracking
  /// 
  /// Key optimizations:
  /// - Distance filter: Only updates every 50 meters of movement
  /// - Balanced accuracy: Uses WiFi/cell tower + occasional GPS
  /// - Time interval: Minimum 10 seconds between updates
  Future<void> startTracking() async {
    if (_isTracking) return;

    // Check location permissions
    final permission = await _checkPermissions();
    if (!permission) {
      throw Exception('Location permission denied');
    }

    // Battery-optimized location settings
    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.medium,  // Use balanced instead of high
      distanceFilter: 50,                   // Update only after 50m movement
      timeLimit: Duration(seconds: 50),     // Minimum time between updates
    );

    // Start listening to position updates
    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: locationSettings,
    ).listen(
      (Position position) {
        _locationController.add(position);
        print('Location updated: ${position.latitude}, ${position.longitude}');
      },
      onError: (error) {
        print('Location error: $error');
      },
    );

    _isTracking = true;
    print('Location tracking started with battery optimization');
  }

  /// Stop location tracking to save battery
  Future<void> stopTracking() async {
    await _positionSubscription?.cancel();
    _positionSubscription = null;
    _isTracking = false;
    print('Location tracking stopped');
  }

  /// Get current location once (for initialization)
  Future<Position> getCurrentPosition() async {
    final permission = await _checkPermissions();
    if (!permission) {
      throw Exception('Location permission denied');
    }

    return await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.medium,
    );
  }

  /// Check and request location permissions
  Future<bool> _checkPermissions() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return false;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return false;
    }

    return true;
  }

  /// Convert Geolocator Position to LatLng
  LatLng positionToLatLng(Position position) {
    return LatLng(position.latitude, position.longitude);
  }

  /// Cleanup resources
  void dispose() {
    _positionSubscription?.cancel();
    _locationController.close();
  }
}
