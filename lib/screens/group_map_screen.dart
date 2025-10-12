import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../controllers/group_map_controller.dart';
//import '../../models/rider_location.dart';
import '../../widgets/leaderboard_chip.dart';
import '../../widgets/expandable_leaderboard.dart';
import '../../widgets/bottom_status_bar.dart';

class GroupMapScreen extends StatefulWidget {
  // pass destination lat/lng (e.g., event venue)
  final LatLng destination;
  final String myUserId;

  const GroupMapScreen({
    super.key,
    required this.destination,
    required this.myUserId,
  });

  @override
  State<GroupMapScreen> createState() => _GroupMapScreenState();
}

class _GroupMapScreenState extends State<GroupMapScreen> {
  late GroupMapController _controller;
  StreamSubscription? _sub;

  @override
  void initState() {
    super.initState();
    _controller = GroupMapController(
      myUserId: widget.myUserId,
      destination: widget.destination,
    );
    _controller.init();
    _sub = _controller.stream.listen((_) => setState(() {}));
  }

  @override
  void dispose() {
    _sub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  String _fmtDistance(double meters) {
    if (meters >= 1000) return "${(meters / 1000).toStringAsFixed(1)} km";
    return "${meters.toStringAsFixed(0)} m";
    }

  String _fmtEta(double seconds) {
    final mins = (seconds / 60).round();
    if (mins >= 60) {
      final h = mins ~/ 60;
      final m = mins % 60;
      return "${h}h ${m}m";
    }
    return "${mins}m";
  }

  @override
  Widget build(BuildContext context) {
    final s = _controller.state;

    final markers = <Marker>[
      // destination marker
      Marker(
        point: s.destination,
        width: 36,
        height: 36,
        child: const Icon(Icons.flag, color: Colors.red, size: 30),
      ),
      // riders
      ...s.riders.map((r) => Marker(
            point: r.position,
            width: 36,
            height: 36,
            child: Tooltip(
              message: r.displayName,
              child: const Icon(Icons.location_history, size: 30),
            ),
          )),
    ];

    final polyLayers = <Polyline>[];
    if (s.routeToDest != null) {
      polyLayers.add(Polyline(
        points: s.routeToDest!.polyline,
        strokeJoin: StrokeJoin.round, //???
        strokeWidth: 4,
      ));
    }

    // Build leaderboard data
    final sorted = s.riderRemainingMeters.entries.toList()
      ..sort((a, b) => a.value.compareTo(b.value));
    String leaderName = "—";
    String leaderDist = "—";
    String? aheadName;
    String? aheadDist;

    final byId = {for (final r in s.riders) r.userId: r.displayName};

    if (sorted.isNotEmpty) {
      final leaderId = s.leaderUserId ?? sorted.first.key;
      leaderName = byId[leaderId] ?? leaderId;
      leaderDist = _fmtDistance(s.riderRemainingMeters[leaderId] ?? 0);
    }

    final ja = s.justAheadOfMeUserId;
    if (ja != null) {
      aheadName = byId[ja] ?? ja;
      aheadDist = _fmtDistance(s.riderRemainingMeters[ja] ?? 0);
    }

    final expandedRows = sorted
        .map((e) => (name: byId[e.key] ?? e.key, distance: _fmtDistance(e.value)))
        .toList();

    // Bottom status — distance & ETA for ME (if route available)
    String bottomDistance = "—";
    String bottomEta = "—";
    if (s.routeToDest != null) {
      bottomDistance = _fmtDistance(s.routeToDest!.distanceMeters);
      bottomEta = _fmtEta(s.routeToDest!.durationSeconds);
    }

    return Scaffold(
      body: Stack(
        children: [
          FlutterMap(
            options: MapOptions(
              initialCenter: s.riders.isNotEmpty ? s.riders.first.position : s.destination,
              initialZoom: 13,
            ),
            children: [
              TileLayer(
                urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                userAgentPackageName: "com.example.rideshare",
              ),
              PolylineLayer(polylines: polyLayers),
              MarkerLayer(markers: markers),
            ],
          ),

          // Leaderboard (top-left)
          Positioned(
            left: 8,
            top: 32 + MediaQuery.of(context).padding.top,
            child: s.leaderboardExpanded
                ? ExpandableLeaderboard(
                    rows: expandedRows,
                    onClose: _controller.toggleLeaderboard,
                  )
                : LeaderboardChip(
                    leaderName: leaderName,
                    leaderDist: leaderDist,
                    aheadName: aheadName,
                    aheadDist: aheadDist,
                    onTap: _controller.toggleLeaderboard,
                  ),
          ),

          // Alert FAB (tea stop) — right bottom above bottom bar
          Positioned(
            right: 16,
            bottom: 80 + MediaQuery.of(context).padding.bottom,
            child: FloatingActionButton.extended(
              onPressed: () {
                // TODO: call your backend to broadcast "Tea Stop" alert to ride group
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Alert sent: Tea Stop!")),
                );
              },
              icon: const Icon(Icons.local_cafe),
              label: const Text("Tea Stop"),
            ),
          ),

          // Bottom distance & ETA bar
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: BottomStatusBar(
              distanceText: bottomDistance,
              etaText: bottomEta,
            ),
          ),
        ],
      ),
    );
  }
}
