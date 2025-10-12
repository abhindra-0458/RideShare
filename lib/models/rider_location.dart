import 'package:latlong2/latlong.dart';

class RiderLocation {
  final String userId;
  final String displayName;
  final LatLng position;     // current lat/lng
  final DateTime updatedAt;  // last update

  const RiderLocation({
    required this.userId,
    required this.displayName,
    required this.position,
    required this.updatedAt,
  });

  RiderLocation copyWith({
    LatLng? position,
    DateTime? updatedAt,
  }) {
    return RiderLocation(
      userId: userId,
      displayName: displayName,
      position: position ?? this.position,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}
