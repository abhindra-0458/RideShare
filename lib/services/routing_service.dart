import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';
import '../models/route_info.dart';

abstract class IRoutingService {
  Future<RouteInfo> route(LatLng from, LatLng to);
}

/// Default: OSRM demo (rate-limited). Replace with your hosted OSRM/OpenRouteService later.
class OsrmRoutingService implements IRoutingService {
  final String baseUrl;
  const OsrmRoutingService({
    this.baseUrl = "https://router.project-osrm.org",
  });

  @override
  Future<RouteInfo> route(LatLng from, LatLng to) async {
    final url =
        "$baseUrl/route/v1/driving/${from.longitude},${from.latitude};${to.longitude},${to.latitude}?overview=full&geometries=geojson";
    final resp = await http.get(Uri.parse(url));
    if (resp.statusCode != 200) {
      throw Exception("Routing error: ${resp.statusCode}");
    }
    final data = jsonDecode(resp.body);
    final routes = data["routes"] as List?;
    if (routes == null || routes.isEmpty) {
      throw Exception("No route found");
    }
    final route = routes.first;
    final geometry = route["geometry"]["coordinates"] as List;
    final poly = geometry
        .map<LatLng>((p) => LatLng(p[1] as double, p[0] as double))
        .toList();
    final distance = (route["distance"] as num).toDouble();
    final duration = (route["duration"] as num).toDouble();

    return RouteInfo(polyline: poly, distanceMeters: distance, durationSeconds: duration);
  }
}
