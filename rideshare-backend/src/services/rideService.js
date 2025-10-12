const RideModel = require('../models/Ride');
const redisClient = require('../config/redis');
const logger = require('../utils/logger');

class RideService {
  static async createRide(rideData, createdBy) {
    try {
      const ride = await RideModel.create(rideData, createdBy);

      // Cache ride data
      await redisClient.set(`ride:${ride.id}`, ride, 3600);

      logger.info(`New ride created: ${ride.id} by user ${createdBy}`);

      return ride;
    } catch (error) {
      logger.error('Create ride error:', error);
      throw error;
    }
  }

  static async getRideDetails(rideId, userId = null) {
    try {
      // Try cache first
      let ride = await redisClient.get(`ride:${rideId}`);

      if (!ride) {
        ride = await RideModel.findById(rideId, userId);
        if (ride) {
          await redisClient.set(`ride:${rideId}`, ride, 3600);
        }
      }

      if (!ride) {
        throw new Error('Ride not found');
      }

      return ride;
    } catch (error) {
      logger.error('Get ride details error:', error);
      throw error;
    }
  }

  static async updateRide(rideId, updateData, userId) {
    try {
      const ride = await RideModel.update(rideId, updateData, userId);
      if (!ride) {
        throw new Error('Ride not found or you do not have permission to update it');
      }

      // Update cache
      await redisClient.set(`ride:${rideId}`, ride, 3600);

      logger.info(`Ride updated: ${rideId} by user ${userId}`);

      return ride;
    } catch (error) {
      logger.error('Update ride error:', error);
      throw error;
    }
  }

  static async deleteRide(rideId, userId) {
    try {
      const success = await RideModel.delete(rideId, userId);
      if (!success) {
        throw new Error('Ride not found or you do not have permission to delete it');
      }

      // Remove from cache
      await redisClient.del(`ride:${rideId}`);

      logger.info(`Ride deleted: ${rideId} by user ${userId}`);

      return true;
    } catch (error) {
      logger.error('Delete ride error:', error);
      throw error;
    }
  }

  static async getUserRides(userId, options = {}) {
    try {
      const cacheKey = `user_rides:${userId}:${JSON.stringify(options)}`;

      // Try cache first
      let rides = await redisClient.get(cacheKey);

      if (!rides) {
        rides = await RideModel.getUserRides(userId, options);
        await redisClient.set(cacheKey, rides, 600); // 10 minutes
      }

      return rides;
    } catch (error) {
      logger.error('Get user rides error:', error);
      throw error;
    }
  }

  static async searchRides(searchParams, userId = null) {
    try {
      const cacheKey = `ride_search:${JSON.stringify(searchParams)}:${userId || 'anonymous'}`;

      // Try cache first
      let rides = await redisClient.get(cacheKey);

      if (!rides) {
        rides = await RideModel.searchRides(searchParams, userId);
        await redisClient.set(cacheKey, rides, 300); // 5 minutes
      }

      return rides;
    } catch (error) {
      logger.error('Search rides error:', error);
      throw error;
    }
  }

  static async joinRide(rideId, userId) {
    try {
      const participant = await RideModel.joinRide(rideId, userId);

      // Clear related caches
      await redisClient.del(`ride:${rideId}`);
      await redisClient.del(`ride_participants:${rideId}`);

      logger.info(`User ${userId} joined ride ${rideId}`);

      return participant;
    } catch (error) {
      logger.error('Join ride error:', error);
      throw error;
    }
  }

  static async leaveRide(rideId, userId) {
    try {
      const success = await RideModel.leaveRide(rideId, userId);
      if (!success) {
        throw new Error('You are not a participant in this ride');
      }

      // Clear related caches
      await redisClient.del(`ride:${rideId}`);
      await redisClient.del(`ride_participants:${rideId}`);

      logger.info(`User ${userId} left ride ${rideId}`);

      return true;
    } catch (error) {
      logger.error('Leave ride error:', error);
      throw error;
    }
  }

  static async getRideParticipants(rideId) {
    try {
      const cacheKey = `ride_participants:${rideId}`;

      // Try cache first
      let participants = await redisClient.get(cacheKey);

      if (!participants) {
        participants = await RideModel.getRideParticipants(rideId);
        await redisClient.set(cacheKey, participants, 600); // 10 minutes
      }

      return participants;
    } catch (error) {
      logger.error('Get ride participants error:', error);
      throw error;
    }
  }

  static async updateParticipantStatus(rideId, userId, status, updatedBy) {
    try {
      const participant = await RideModel.updateParticipantStatus(
        rideId, 
        userId, 
        status, 
        updatedBy
      );

      // Clear related caches
      await redisClient.del(`ride:${rideId}`);
      await redisClient.del(`ride_participants:${rideId}`);

      logger.info(`Participant ${userId} status updated to ${status} in ride ${rideId}`);

      return participant;
    } catch (error) {
      logger.error('Update participant status error:', error);
      throw error;
    }
  }

  static async inviteUsersToRide(rideId, userIds, invitedBy, message = '') {
    try {
      // Verify that the inviter is the ride creator
      const ride = await RideModel.findById(rideId);
      if (!ride || ride.createdBy !== invitedBy) {
        throw new Error('Only ride creator can invite users');
      }

      const invitations = [];

      for (const userId of userIds) {
        try {
          // Add user as pending participant
          const participant = await RideModel.joinRide(rideId, userId);

          // You could implement notification system here
          // await NotificationService.sendRideInvitation(userId, rideId, message);

          invitations.push({
            userId,
            status: 'invited',
            participant,
          });
        } catch (error) {
          invitations.push({
            userId,
            status: 'failed',
            error: error.message,
          });
        }
      }

      // Clear related caches
      await redisClient.del(`ride:${rideId}`);
      await redisClient.del(`ride_participants:${rideId}`);

      logger.info(`${userIds.length} users invited to ride ${rideId}`);

      return invitations;
    } catch (error) {
      logger.error('Invite users to ride error:', error);
      throw error;
    }
  }
}

module.exports = RideService;
