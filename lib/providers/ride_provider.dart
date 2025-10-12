import 'package:flutter/foundation.dart';
import '../models/ride_model.dart';
import '../services/api_service.dart';

class RideProvider extends ChangeNotifier {
  List<Ride> _rides = [];
  bool _isLoading = false;
  String? _error;

  final _apiService = ApiService();

  List<Ride> get rides => _rides;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Search rides
  Future<bool> searchRides({
    double? latitude,
    double? longitude,
    double? radiusKm,
    String? difficulty,
    int limit = 20,
    int offset = 0,
  }) async {
    _setLoading(true);
    _error = null;

    try {
      final response = await _apiService.searchRides(
        latitude: latitude,
        longitude: longitude,
        radiusKm: radiusKm,
        difficulty: difficulty,
        limit: limit,
        offset: offset,
      );

      if (response.isSuccess) {
        final ridesData = response.data as List<dynamic>;
        _rides = ridesData.map((rideJson) => Ride.fromJson(rideJson)).toList();
        _setLoading(false);
        return true;
      } else {
        _error = response.error;
        _setLoading(false);
        return false;
      }
    } catch (e) {
      _error = 'Failed to search rides: $e';
      _setLoading(false);
      return false;
    }
  }

  // Create ride
  Future<bool> createRide({
    required String title,
    required String description,
    required LocationPoint startLocation,
    required LocationPoint endLocation,
    required DateTime scheduledDateTime,
    required bool isPublic,
    required int maxParticipants,
    String difficulty = 'medium',
  }) async {
    _setLoading(true);
    _error = null;

    try {
      final response = await _apiService.createRide(
        title: title,
        description: description,
        startLocation: startLocation,
        endLocation: endLocation,
        scheduledDateTime: scheduledDateTime,
        isPublic: isPublic,
        maxParticipants: maxParticipants,
        difficulty: difficulty,
      );

      if (response.isSuccess) {
        // Add the new ride to the list
        final newRide = Ride.fromJson(response.data!);
        _rides.insert(0, newRide);
        _setLoading(false);
        return true;
      } else {
        _error = response.error;
        _setLoading(false);
        return false;
      }
    } catch (e) {
      _error = 'Failed to create ride: $e';
      _setLoading(false);
      return false;
    }
  }

  // Join ride
  Future<bool> joinRide(String rideId) async {
    _setLoading(true);
    _error = null;

    try {
      final response = await _apiService.joinRide(rideId);

      if (response.isSuccess) {
        // Update the ride in the list
        final rideIndex = _rides.indexWhere((ride) => ride.id == rideId);
        if (rideIndex != -1) {
          // You might need to refresh the ride details here
          // For now, just trigger a rebuild
          notifyListeners();
        }
        _setLoading(false);
        return true;
      } else {
        _error = response.error;
        _setLoading(false);
        return false;
      }
    } catch (e) {
      _error = 'Failed to join ride: $e';
      _setLoading(false);
      return false;
    }
  }

  // Refresh rides list
  Future<void> refreshRides() async {
    await searchRides();
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