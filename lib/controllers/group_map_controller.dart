import 'dart:async';
import 'package:latlong2/latlong.dart';
import '../models/rider_location.dart';
import '../models/route_info.dart';
import '../services/location_service.dart';
import '../services/routing_service.dart';

class GroupMapState {
  final List<RiderLocation> riders;
  final RouteInfo? routeToDest;
  final Map<String, double> riderRemainingMeters; // userId -> remaining dist
  final String? leaderUserId;
  final String? justAheadOfMeUserId;
  final bool leaderboardExpanded;
  final LatLng destination;

  GroupMapState({
    required this.riders,
    required this.routeToDest,
    required this.riderRemainingMeters,
    required this.leaderUserId,
    required this.justAheadOfMeUserId,
    required this.leaderboardExpanded,
    required this.destination,
  });

  GroupMapState copyWith({
    List<RiderLocation>? riders,
    RouteInfo? routeToDest,
    Map<String, double>? riderRemainingMeters,
    String? leaderUserId,
    String? justAheadOfMeUserId,
    bool? leaderboardExpanded,
    LatLng? destination,
  }) {
    return GroupMapState(
      riders: riders ?? this.riders,
      routeToDest: routeToDest ?? this.routeToDest,
      riderRemainingMeters: riderRemainingMeters ?? this.riderRemainingMeters,
      leaderUserId: leaderUserId ?? this.leaderUserId,
      justAheadOfMeUserId: justAheadOfMeUserId ?? this.justAheadOfMeUserId,
      leaderboardExpanded: leaderboardExpanded ?? this.leaderboardExpanded,
      destination: destination ?? this.destination,
    );
  }
}

class GroupMapController {
  final String myUserId;
  final GroupLocationService locationService;
  final IRoutingService routingService;
  final _distance = const Distance();

  GroupMapState _state;
  final _stateController = StreamController<GroupMapState>.broadcast();
  StreamSubscription? _locSub;

  Stream<GroupMapState> get stream => _stateController.stream;
  GroupMapState get state => _state;

  GroupMapController({
    required this.myUserId,
    required LatLng destination,
    GroupLocationService? locationService,
    IRoutingService? routingService,
  })  : locationService = locationService ?? GroupLocationService(),
        routingService = routingService ?? const OsrmRoutingService(),
        _state = GroupMapState(
          riders: const [],
          routeToDest: null,
          riderRemainingMeters: const {},
          leaderUserId: null,
          justAheadOfMeUserId: null,
          leaderboardExpanded: false,
          destination: destination,
        );

  Future<void> init({LatLng? initialFrom}) async {
    // fetch route from my current position (or first rider) to destination
    final from = initialFrom ?? (state.riders.isNotEmpty
        ? state.riders.first.position
        : const LatLng(10.02, 76.36));

    final route = await routingService.route(from, state.destination);
    _state = _state.copyWith(routeToDest: route);
    _stateController.add(_state);

    // subscribe to group location updates
    _locSub = locationService.stream.listen((riders) {
      _recompute(riders);
    });

    // demo simulation
    locationService.startMockSimulation();
  }

  void toggleLeaderboard() {
    _state = _state.copyWith(leaderboardExpanded: !state.leaderboardExpanded);
    _stateController.add(_state);
  }

  void _recompute(List<RiderLocation> riders) {
    // remaining distance: straight-line to destination (fast & cheap).
    // If you want HIGH accuracy, query routingService.route(rider, destination) per rider (expensive).
    final remain = <String, double>{};
    for (final r in riders) {
      final d = _distance.as(LengthUnit.Meter, r.position, state.destination);
      remain[r.userId] = d;
    }

    // leader: min remaining distance
    String? leader;
    double best = double.infinity;
    remain.forEach((id, dist) {
      if (dist < best) {
        best = dist;
        leader = id;
      }
    });

    // just-ahead-of-me: the rider with remaining distance just less than mine
    String? ahead;
    final myRemain = remain[myUserId];
    if (myRemain != null) {
      final smaller = remain.entries
          .where((e) => e.key != myUserId && e.value < myRemain)
          .toList()
        ..sort((a, b) => b.value.compareTo(a.value)); // closest smaller
      if (smaller.isNotEmpty) ahead = smaller.first.key;
    }

    _state = _state.copyWith(
      riders: riders,
      riderRemainingMeters: remain,
      leaderUserId: leader,
      justAheadOfMeUserId: ahead,
    );
    _stateController.add(_state);
  }

  void dispose() {
    _locSub?.cancel();
    locationService.dispose();
    _stateController.close();
  }
}
