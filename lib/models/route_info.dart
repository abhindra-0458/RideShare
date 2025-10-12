import 'package:latlong2/latlong.dart';

class RouteInfo {
  final List<LatLng> polyline; // decoded polyline points
  final double distanceMeters; // route distance
  final double durationSeconds; // ETA (seconds)

  const RouteInfo({
    required this.polyline,
    required this.distanceMeters,
    required this.durationSeconds,
  });
}
