import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';

import '../models/ride_model.dart';
import '../models/rider_location.dart';
import '../providers/ride_provider.dart';
import '../providers/user_provider.dart';
import '../services/location_tracking_service.dart';
import '../services/socket_service.dart';

class GroupRideScreen extends StatefulWidget {
  final Ride ride;

  const GroupRideScreen({super.key, required this.ride});

  @override
  State<GroupRideScreen> createState() => _GroupRideScreenState();
}

class _GroupRideScreenState extends State<GroupRideScreen> {
  final MapController mapController = MapController();
  final LocationTrackingService _locationService = LocationTrackingService();
  final SocketService _socketService = SocketService();
  
  bool hasJoinedRide = false;
  List<LatLng> routePoints = [];
  int? etaMinutes;
  double? distanceKm;
  bool isLoadingRoute = false;

  @override
  void initState() {
    super.initState();
    joinRide();
    _startLocationTracking();
  }

  Future<void> joinRide() async {
    final rideProvider = Provider.of<RideProvider>(context, listen: false);
    final userProvider = Provider.of<UserProvider>(context, listen: false);
    await rideProvider.joinRide(
      widget.ride,
      userProvider.userId!,
      userProvider.username!,
    );
    setState(() {
      hasJoinedRide = true;
    });
    
    _updateRouteFromCurrentLocation();
  }

  void _startLocationTracking() {
    _locationService.locationStream.listen((position) {
      _updateRoute(position);
    });
  }

  Future<void> _updateRouteFromCurrentLocation() async {
    try {
      final position = await _locationService.getCurrentPosition();
      await _updateRoute(position);
    } catch (e) {
      print('Could not get current location for route: $e');
    }
  }

  Future<void> _updateRoute(Position currentPosition) async {
    if (!mounted) return;
    
    setState(() {
      isLoadingRoute = true;
    });

    try {
      final routeData = await _socketService.getRoute(
        currentPosition.latitude,
        currentPosition.longitude,
        widget.ride.destination.latitude,
        widget.ride.destination.longitude,
      );

      if (routeData != null && routeData['success'] == true && mounted) {
        setState(() {
          routePoints = (routeData['coordinates'] as List)
              .map((coord) => LatLng(
                    coord['latitude'] as double,
                    coord['longitude'] as double,
                  ))
              .toList();

          final durationSeconds = routeData['duration'] as num;
          etaMinutes = (durationSeconds / 60).round();
          distanceKm = (routeData['distance'] as num) / 1000;
          isLoadingRoute = false;
        });
      } else {
        setState(() {
          isLoadingRoute = false;
        });
      }
    } catch (e) {
      print('Error updating route: $e');
      if (mounted) {
        setState(() {
          isLoadingRoute = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.ride.title),
        actions: [
          Consumer<RideProvider>(
            builder: (context, rideProvider, _) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Center(
                  child: Row(
                    children: [
                      const Icon(Icons.group, size: 20),
                      const SizedBox(width: 4),
                      Text('${rideProvider.riderLocations.length}'),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: hasJoinedRide
          ? Consumer<RideProvider>(
              builder: (context, rideProvider, _) {
                return Stack(
                  children: [
                    _buildMap(rideProvider.riderLocations),

                    if (isLoadingRoute)
                      Positioned(
                        top: 16,
                        right: 16,
                        child: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.black54,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          ),
                        ),
                      ),

                    Positioned(
                      bottom: 0,
                      left: 0,
                      right: 0,
                      child: _buildStatusBar(rideProvider),
                    ),
                  ],
                );
              },
            )
          : const Center(child: CircularProgressIndicator()),
    );
  }

  Widget _buildMap(List<RiderLocation> locations) {
    final userProvider = Provider.of<UserProvider>(context, listen: false);

    return FlutterMap(
      mapController: mapController,
      options: MapOptions(
        initialCenter: widget.ride.destination,
        initialZoom: 14.0,
        minZoom: 10.0,
        maxZoom: 18.0,
      ),
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.example.group_ride',
        ),
        
        if (routePoints.isNotEmpty)
          PolylineLayer(
            polylines: [
              Polyline(
                points: routePoints,
                color: Colors.blue,
                strokeWidth: 4.0,
                borderColor: Colors.white,
                borderStrokeWidth: 1.0,
              ),
            ],
          ),
        
        MarkerLayer(
          markers: locations.map((location) {
            final isMe = location.userId == userProvider.userId;

            return Marker(
              point: location.position,
              width: 80,
              height: 80,
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: isMe ? Colors.blue : Colors.green,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black26,
                          blurRadius: 4,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Icon(
                      isMe ? Icons.navigation : Icons.person_outline,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.black87,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      location.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
        
        MarkerLayer(
          markers: [
            Marker(
              point: widget.ride.destination,
              width: 50,
              height: 50,
              child: Column(
                children: [
                  const Icon(
                    Icons.location_on,
                    color: Colors.red,
                    size: 40,
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'Destination',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 8,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStatusBar(RideProvider rideProvider) {
    return SafeArea(
      top: false,  // Only apply SafeArea to bottom
      child: Container(
        constraints: const BoxConstraints(maxHeight: 80),  // ← Limit maximum height
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),  // ← Minimal padding
        decoration: BoxDecoration(
          color: Colors.black87,
          boxShadow: [
            BoxShadow(
              color: Colors.black26,
              blurRadius: 8,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SingleChildScrollView(  // ← Allows scrolling if content too large
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (etaMinutes != null) ...[
                Row(
                  children: [
                    const Icon(Icons.directions, color: Colors.blue, size: 16),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        '$etaMinutes min • ${distanceKm?.toStringAsFixed(1)} km',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.refresh, color: Colors.white, size: 14),
                      padding: const EdgeInsets.all(4),
                      constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                      onPressed: _updateRouteFromCurrentLocation,
                    ),
                  ],
                ),
                const SizedBox(height: 4),  // ← Small spacing instead of Divider
              ],
              
              Row(
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      color: rideProvider.isInRide ? Colors.green : Colors.red,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      rideProvider.isInRide ? 'Active • 50m' : 'Stopped',
                      style: const TextStyle(color: Colors.white70, fontSize: 9),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  TextButton(
                    onPressed: _leaveRide,
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      minimumSize: const Size(40, 24),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: const Text(
                      'Leave',
                      style: TextStyle(color: Colors.red, fontSize: 10),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }


  Future<void> _leaveRide() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Leave Ride?'),
        content: const Text('Are you sure you want to leave this ride?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Leave', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      final rideProvider = Provider.of<RideProvider>(context, listen: false);
      final userProvider = Provider.of<UserProvider>(context, listen: false);
      await rideProvider.leaveRide(userProvider.userId!);
      if (mounted) Navigator.of(context).pop();
    }
  }

  @override
  void dispose() {
    mapController.dispose();
    super.dispose();
  }
}
