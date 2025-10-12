const LocationModel = require('../models/Location');
const redisClient = require('../config/redis');
const logger = require('../utils/logger');

class LocationService {
  static async updateUserLocation(userId, locationData) {
    try {
      const location = await LocationModel.updateUserLocation(userId, locationData);

      // Store in Redis for real-time access
      await redisClient.set(
        `user_location:${userId}`, 
        {
          latitude: locationData.latitude,
          longitude: locationData.longitude,
          accuracy: locationData.accuracy,
          timestamp: locationData.timestamp || new Date(),
        }, 
        300 // 5 minutes expiry
      );

      logger.info(`Location updated for user ${userId}`);

      return location;
    } catch (error) {
      logger.error('Update user location error:', error);
      throw error;
    }
  }

  static async getRideParticipantLocations(rideId, userId) {
    try {
      const cacheKey = `ride_locations:${rideId}`;

      // Try cache first
      let locations = await redisClient.get(cacheKey);

      if (!locations) {
        locations = await LocationModel.getRideParticipantLocations(rideId, userId);
        await redisClient.set(cacheKey, locations, 30); // 30 seconds for real-time data
      }

      return locations;
    } catch (error) {
      logger.error('Get ride participant locations error:', error);
      throw error;
    }
  }

  static async checkDriftAlerts(rideId) {
    try {
      const alerts = await LocationModel.checkDriftAlerts(rideId);

      if (alerts.length > 0) {
        // Store alerts in cache for real-time notifications
        await redisClient.set(`drift_alerts:${rideId}`, alerts, 300);

        logger.warn(`${alerts.length} drift alerts detected for ride ${rideId}`);
      }

      return alerts;
    } catch (error) {
      logger.error('Check drift alerts error:', error);
      throw error;
    }
  }

  static async getUserLocationHistory(userId, options = {}) {
    try {
      const cacheKey = `location_history:${userId}:${JSON.stringify(options)}`;

      // Try cache first
      let history = await redisClient.get(cacheKey);

      if (!history) {
        history = await LocationModel.getUserLocationHistory(userId, options);
        await redisClient.set(cacheKey, history, 600); // 10 minutes
      }

      return history;
    } catch (error) {
      logger.error('Get user location history error:', error);
      throw error;
    }
  }

  static async getNearbyUsers(latitude, longitude, radiusKm = 5, excludeUserId = null) {
    try {
      const cacheKey = `nearby_users:${latitude}:${longitude}:${radiusKm}:${excludeUserId || 'none'}`;

      // Try cache first
      let nearbyUsers = await redisClient.get(cacheKey);

      if (!nearbyUsers) {
        nearbyUsers = await LocationModel.getNearbyUsers(
          latitude, 
          longitude, 
          radiusKm, 
          excludeUserId
        );
        await redisClient.set(cacheKey, nearbyUsers, 60); // 1 minute
      }

      return nearbyUsers;
    } catch (error) {
      logger.error('Get nearby users error:', error);
      throw error;
    }
  }

  static async getRealTimeUserLocation(userId) {
    try {
      // Try Redis first for real-time data
      let location = await redisClient.get(`user_location:${userId}`);

      if (!location) {
        // Fall back to database
        const user = await db('users')
          .select([
            'currentLatitude as latitude',
            'currentLongitude as longitude', 
            'lastLocationUpdate as timestamp'
          ])
          .where({ id: userId })
          .first();

        if (user && user.latitude && user.longitude) {
          location = {
            latitude: user.latitude,
            longitude: user.longitude,
            timestamp: user.timestamp,
            accuracy: null,
          };
        }
      }

      return location;
    } catch (error) {
      logger.error('Get real-time user location error:', error);
      throw error;
    }
  }

  static async batchUpdateLocations(locationUpdates) {
    try {
      const results = [];

      for (const update of locationUpdates) {
        try {
          const location = await this.updateUserLocation(update.userId, {
            latitude: update.latitude,
            longitude: update.longitude,
            accuracy: update.accuracy,
            timestamp: update.timestamp,
          });

          results.push({
            userId: update.userId,
            success: true,
            location,
          });
        } catch (error) {
          results.push({
            userId: update.userId,
            success: false,
            error: error.message,
          });
        }
      }

      logger.info(`Batch location update completed: ${results.length} updates processed`);

      return results;
    } catch (error) {
      logger.error('Batch update locations error:', error);
      throw error;
    }
  }

  static async clearOldLocationData(olderThanDays = 30) {
    try {
      const deletedCount = await LocationModel.cleanOldLocationData(olderThanDays);

      logger.info(`Cleaned ${deletedCount} old location records`);

      return deletedCount;
    } catch (error) {
      logger.error('Clear old location data error:', error);
      throw error;
    }
  }
}

module.exports = LocationService;
