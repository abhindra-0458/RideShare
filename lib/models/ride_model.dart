class Ride {
  final String id;
  final String title;
  final String description;
  final LocationPoint startLocation;
  final LocationPoint endLocation;
  final DateTime scheduledDateTime;
  final bool isPublic;
  final int maxParticipants;
  final String status; // scheduled, active, completed, cancelled
  final String difficulty; // easy, medium, hard
  final String createdBy;
  final DateTime createdAt;
  final List<RideParticipant>? participants;
  
  Ride({
    required this.id,
    required this.title,
    required this.description,
    required this.startLocation,
    required this.endLocation,
    required this.scheduledDateTime,
    required this.isPublic,
    required this.maxParticipants,
    required this.status,
    required this.difficulty,
    required this.createdBy,
    required this.createdAt,
    this.participants,
  });
  
  factory Ride.fromJson(Map<String, dynamic> json) {
    return Ride(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      startLocation: LocationPoint.fromJson(json['startLocation']),
      endLocation: LocationPoint.fromJson(json['endLocation']),
      scheduledDateTime: DateTime.parse(json['scheduledDateTime']),
      isPublic: json['isPublic'],
      maxParticipants: json['maxParticipants'],
      status: json['status'],
      difficulty: json['difficulty'],
      createdBy: json['createdBy'],
      createdAt: DateTime.parse(json['createdAt']),
      participants: json['participants'] != null
          ? (json['participants'] as List)
              .map((p) => RideParticipant.fromJson(p))
              .toList()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'startLocation': startLocation.toJson(),
      'endLocation': endLocation.toJson(),
      'scheduledDateTime': scheduledDateTime.toIso8601String(),
      'isPublic': isPublic,
      'maxParticipants': maxParticipants,
      'status': status,
      'difficulty': difficulty,
      'createdBy': createdBy,
      'createdAt': createdAt.toIso8601String(),
      'participants': participants?.map((p) => p.toJson()).toList(),
    };
  }
}

class LocationPoint {
  final double latitude;
  final double longitude;
  final String address;
  
  LocationPoint({
    required this.latitude,
    required this.longitude,
    required this.address,
  });
  
  factory LocationPoint.fromJson(Map<String, dynamic> json) {
    return LocationPoint(
      latitude: json['latitude'].toDouble(),
      longitude: json['longitude'].toDouble(),
      address: json['address'],
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'latitude': latitude,
      'longitude': longitude,
      'address': address,
    };
  }
}

class RideParticipant {
  final String id;
  final String userId;
  final String rideId;
  final String status; // pending, accepted, rejected
  final DateTime joinedAt;
  final String? userName;
  final String? userEmail;
  
  RideParticipant({
    required this.id,
    required this.userId,
    required this.rideId,
    required this.status,
    required this.joinedAt,
    this.userName,
    this.userEmail,
  });
  
  factory RideParticipant.fromJson(Map<String, dynamic> json) {
    return RideParticipant(
      id: json['id'],
      userId: json['userId'],
      rideId: json['rideId'],
      status: json['status'],
      joinedAt: DateTime.parse(json['joinedAt']),
      userName: json['userName'],
      userEmail: json['userEmail'],
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'userId': userId,
      'rideId': rideId,
      'status': status,
      'joinedAt': joinedAt.toIso8601String(),
      'userName': userName,
      'userEmail': userEmail,
    };
  }
}