const RideService = require('../services/rideService');
const ApiResponse = require('../utils/response');
const Helpers = require('../utils/helpers');
const logger = require('../utils/logger');

class RideController {
  /**
   * @desc    Create a new ride
   * @route   POST /api/v1/rides
   * @access  Private
   */
  static async createRide(req, res) {
    try {
      const rideData = req.body;
      const createdBy = req.user.userId;

      const ride = await RideService.createRide(rideData, createdBy);

      return ApiResponse.success(res, ride, 'Ride created successfully', 201);
    } catch (error) {
      logger.error('Create ride error:', error);
      return ApiResponse.error(res, 'Ride creation failed');
    }
  }

  /**
   * @desc    Get ride by ID
   * @route   GET /api/v1/rides/:id
   * @access  Private
   */
  static async getRideById(req, res) {
    try {
      const { id } = req.params;
      const userId = req.user.userId;

      const ride = await RideService.getRideDetails(id, userId);

      return ApiResponse.success(res, ride, 'Ride retrieved successfully');
    } catch (error) {
      logger.error('Get ride by ID error:', error);

      if (error.message.includes('not found')) {
        return ApiResponse.notFound(res, 'Ride not found');
      }

      return ApiResponse.error(res, 'Failed to get ride');
    }
  }

  /**
   * @desc    Update ride
   * @route   PUT /api/v1/rides/:id
   * @access  Private
   */
  static async updateRide(req, res) {
    try {
      const { id } = req.params;
      const updateData = req.body;
      const userId = req.user.userId;

      const ride = await RideService.updateRide(id, updateData, userId);

      return ApiResponse.success(res, ride, 'Ride updated successfully');
    } catch (error) {
      logger.error('Update ride error:', error);

      if (error.message.includes('not found') || error.message.includes('permission')) {
        return ApiResponse.notFound(res, error.message);
      }

      return ApiResponse.error(res, 'Ride update failed');
    }
  }

  /**
   * @desc    Delete ride
   * @route   DELETE /api/v1/rides/:id
   * @access  Private
   */
  static async deleteRide(req, res) {
    try {
      const { id } = req.params;
      const userId = req.user.userId;

      await RideService.deleteRide(id, userId);

      return ApiResponse.success(res, null, 'Ride deleted successfully');
    } catch (error) {
      logger.error('Delete ride error:', error);

      if (error.message.includes('not found') || error.message.includes('permission')) {
        return ApiResponse.notFound(res, error.message);
      }

      return ApiResponse.error(res, 'Ride deletion failed');
    }
  }

  /**
   * @desc    Get user's rides
   * @route   GET /api/v1/rides/user/:userId
   * @access  Private
   */
  static async getUserRides(req, res) {
    try {
      const { userId } = req.params;
      const { 
        status, 
        type, 
        limit = 20, 
        offset = 0,
        sortBy,
        sortOrder 
      } = req.query;

      // Users can only see their own rides unless they're admin
      if (userId !== req.user.userId && req.user.role !== 'admin') {
        return ApiResponse.forbidden(res, 'Cannot access other users rides');
      }

      const options = {
        status,
        type,
        limit: parseInt(limit),
        offset: parseInt(offset),
        sortBy,
        sortOrder,
      };

      const rides = await RideService.getUserRides(userId, options);

      const pagination = Helpers.getPaginationMeta(
        Math.floor(offset / limit) + 1,
        parseInt(limit),
        rides.length
      );

      return ApiResponse.success(res, {
        rides,
        pagination,
      }, 'User rides retrieved successfully');
    } catch (error) {
      logger.error('Get user rides error:', error);
      return ApiResponse.error(res, 'Failed to get user rides');
    }
  }

  /**
   * @desc    Search rides
   * @route   GET /api/v1/rides/search
   * @access  Private/Public
   */
  static async searchRides(req, res) {
    try {
      const searchParams = req.query;
      const userId = req.user?.userId;

      const rides = await RideService.searchRides(searchParams, userId);

      return ApiResponse.success(res, rides, 'Rides retrieved successfully');
    } catch (error) {
      logger.error('Search rides error:', error);
      return ApiResponse.error(res, 'Ride search failed');
    }
  }

  /**
   * @desc    Join a ride
   * @route   POST /api/v1/rides/:id/join
   * @access  Private
   */
  static async joinRide(req, res) {
    try {
      const { id } = req.params;
      const userId = req.user.userId;

      const participant = await RideService.joinRide(id, userId);

      return ApiResponse.success(res, participant, 'Successfully joined ride');
    } catch (error) {
      logger.error('Join ride error:', error);

      if (error.message.includes('not found') || 
          error.message.includes('full') || 
          error.message.includes('already')) {
        return ApiResponse.error(res, error.message, 400);
      }

      return ApiResponse.error(res, 'Failed to join ride');
    }
  }

  /**
   * @desc    Leave a ride
   * @route   POST /api/v1/rides/:id/leave
   * @access  Private
   */
  static async leaveRide(req, res) {
    try {
      const { id } = req.params;
      const userId = req.user.userId;

      await RideService.leaveRide(id, userId);

      return ApiResponse.success(res, null, 'Successfully left ride');
    } catch (error) {
      logger.error('Leave ride error:', error);
      return ApiResponse.error(res, error.message || 'Failed to leave ride');
    }
  }

  /**
   * @desc    Get ride participants
   * @route   GET /api/v1/rides/:id/participants
   * @access  Private
   */
  static async getRideParticipants(req, res) {
    try {
      const { id } = req.params;

      const participants = await RideService.getRideParticipants(id);

      return ApiResponse.success(res, participants, 'Participants retrieved successfully');
    } catch (error) {
      logger.error('Get ride participants error:', error);
      return ApiResponse.error(res, 'Failed to get participants');
    }
  }

  /**
   * @desc    Update participant status
   * @route   PUT /api/v1/rides/:id/participants/:userId
   * @access  Private
   */
  static async updateParticipantStatus(req, res) {
    try {
      const { id, userId } = req.params;
      const { status } = req.body;
      const updatedBy = req.user.userId;

      const participant = await RideService.updateParticipantStatus(
        id, 
        userId, 
        status, 
        updatedBy
      );

      return ApiResponse.success(res, participant, 'Participant status updated');
    } catch (error) {
      logger.error('Update participant status error:', error);
      return ApiResponse.error(res, error.message || 'Failed to update participant status');
    }
  }

  /**
   * @desc    Invite users to ride
   * @route   POST /api/v1/rides/:id/invite
   * @access  Private
   */
  static async inviteUsers(req, res) {
    try {
      const { id } = req.params;
      const { userIds, message } = req.body;
      const invitedBy = req.user.userId;

      const invitations = await RideService.inviteUsersToRide(
        id, 
        userIds, 
        invitedBy, 
        message
      );

      return ApiResponse.success(res, invitations, 'Invitations sent');
    } catch (error) {
      logger.error('Invite users error:', error);
      return ApiResponse.error(res, error.message || 'Failed to send invitations');
    }
  }
}

module.exports = RideController;
