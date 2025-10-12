const db = require('../config/database');
const Helpers = require('../utils/helpers');
const config = require('../config');

class LocationModel {
  static async updateUserLocation(userId, locationData) {
    const { latitude, longitude, accuracy, timestamp = new Date() } = locationData;

    // Store in location_updates table
    const [location] = await db('location_updates')
      .insert({
        userId,
        latitude,
        longitude,
        accuracy,
        timestamp,
        createdAt: new Date(),
      })
      .returning('*');

    // Update user's current location
    await db('users')
      .where({ id: userId })
      .update({
        currentLatitude: latitude,
        currentLongitude: longitude,
        lastLocationUpdate: timestamp,
        updatedAt: new Date(),
      });

    return location;
  }

  static async getRideParticipantLocations(rideId, userId) {
    // Verify user is a participant in the ride
    const participant = await db('ride_participants')
      .where({ rideId, userId })
      .first();

    if (!participant) {
      throw new Error('User is not a participant in this ride');
    }

    // Get current locations of all ride participants
    const locations = await db('users as u')
      .select([
        'u.id',
        'u.firstName',
        'u.lastName',
        'u.profilePictureUrl',
        'u.currentLatitude as latitude',
        'u.currentLongitude as longitude',
        'u.lastLocationUpdate',
        'rp.status as participantStatus'
      ])
      .join('ride_participants as rp', 'u.id', 'rp.userId')
      .where('rp.rideId', rideId)
      .where('rp.status', 'accepted')
      .where('u.currentLatitude', 'is not', null)
      .where('u.currentLongitude', 'is not', null);

    return locations;
  }

  static async checkDriftAlerts(rideId) {
    const participants = await this.getRideParticipantLocations(rideId);

    if (participants.length < 2) {
      return []; // Need at least 2 participants to check drift
    }

    const alerts = [];
    const maxDistance = config.location.driftAlertDistanceKm;

    // Calculate center point of the group
    const centerLat = participants.reduce((sum, p) => sum + p.latitude, 0) / participants.length;
    const centerLon = participants.reduce((sum, p) => sum + p.longitude, 0) / participants.length;

    for (let participant of participants) {
      const distance = Helpers.calculateDistance(
        centerLat, centerLon,
        participant.latitude, participant.longitude
      );

      if (distance > maxDistance) {
        alerts.push({
          userId: participant.id,
          userName: `${participant.firstName} ${participant.lastName}`,
          distanceFromGroup: Math.round(distance * 100) / 100, // Round to 2 decimal places
          maxAllowedDistance: maxDistance,
          latitude: participant.latitude,
          longitude: participant.longitude,
          timestamp: new Date(),
        });

        // Store drift alert in database
        await db('drift_alerts').insert({
          rideId,
          userId: participant.id,
          distance: distance,
          latitude: participant.latitude,
          longitude: participant.longitude,
          createdAt: new Date(),
        });
      }
    }

    return alerts;
  }

  static async getUserLocationHistory(userId, options = {}) {
    const {
      startDate,
      endDate,
      rideId,
      limit = 100,
      offset = 0,
    } = options;

    let query = db('location_updates')
      .select('*')
      .where('userId', userId);

    if (startDate) {
      query = query.where('timestamp', '>=', startDate);
    }
    if (endDate) {
      query = query.where('timestamp', '<=', endDate);
    }
    if (rideId) {
      // Get location updates during the ride timeframe
      const ride = await db('rides')
        .select('scheduledDateTime', 'estimatedDurationMinutes')
        .where('id', rideId)
        .first();

      if (ride) {
        const rideStart = new Date(ride.scheduledDateTime);
        const rideEnd = new Date(rideStart.getTime() + (ride.estimatedDurationMinutes || 120) * 60 * 1000);

        query = query
          .where('timestamp', '>=', rideStart)
          .where('timestamp', '<=', rideEnd);
      }
    }

    return await query
      .orderBy('timestamp', 'desc')
      .limit(limit)
      .offset(offset);
  }

  static async getNearbyUsers(latitude, longitude, radiusKm = 5, excludeUserId = null) {
    let query = db('users')
      .select([
        'id',
        'firstName',
        'lastName',
        'profilePictureUrl',
        'currentLatitude as latitude',
        'currentLongitude as longitude',
        'lastLocationUpdate'
      ])
      .where('isActive', true)
      .where('isProfileVisible', true)
      .where('currentLatitude', 'is not', null)
      .where('currentLongitude', 'is not', null)
      .whereRaw(
        `ST_DWithin(ST_MakePoint(current_longitude, current_latitude)::geography, 
         ST_MakePoint(?, ?)::geography, ? * 1000)`,
        [longitude, latitude, radiusKm]
      );

    if (excludeUserId) {
      query = query.where('id', '!=', excludeUserId);
    }

    const users = await query.limit(50);

    // Add distance calculation
    return users.map(user => ({
      ...user,
      distanceKm: Helpers.calculateDistance(
        latitude, longitude,
        user.latitude, user.longitude
      ),
    })).sort((a, b) => a.distanceKm - b.distanceKm);
  }

  static async cleanOldLocationData(olderThanDays = 30) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

    const deletedCount = await db('location_updates')
      .where('createdAt', '<', cutoffDate)
      .del();

    return deletedCount;
  }
}

module.exports = LocationModel;
