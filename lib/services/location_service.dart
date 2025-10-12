import 'dart:async';
import 'package:latlong2/latlong.dart';
import '../models/rider_location.dart';

class GroupLocationService {
  final _controller = StreamController<List<RiderLocation>>.broadcast();
  Timer? _timer;

  // Simulated members (replace with live data)
  List<RiderLocation> _members = [
    RiderLocation(
      userId: "u1",
      displayName: "Akhil",
      position: const LatLng(10.015, 76.36),
      updatedAt: DateTime.now(),
    ),
    RiderLocation(
      userId: "u2",
      displayName: "Neha",
      position: const LatLng(10.02, 76.37),
      updatedAt: DateTime.now(),
    ),
    RiderLocation(
      userId: "me",
      displayName: "You",
      position: const LatLng(10.03, 76.35),
      updatedAt: DateTime.now(),
    ),
  ];

  Stream<List<RiderLocation>> get stream => _controller.stream;

  void startMockSimulation() {
    // Simulate movement every 2s
    _timer = Timer.periodic(const Duration(seconds: 2), (_) {
      _members = _members.map((m) {
        final jitterLat = (m.userId.hashCode % 3 - 1) * 0.0003; // -0.0003..0.0003
        final jitterLng = (m.userId.hashCode % 5 - 2) * 0.0002; // -0.0004..0.0002
        return m.copyWith(
          position: LatLng(m.position.latitude + jitterLat * 0.2,
              m.position.longitude + jitterLng * 0.2),
          updatedAt: DateTime.now(),
        );
      }).toList();
      _controller.add(_members);
    });
  }

  void push(List<RiderLocation> members) {
    _members = members;
    _controller.add(_members);
  }

  void dispose() {
    _timer?.cancel();
    _controller.close();
  }
}
