const LocationService = require('../services/locationService');
const ApiResponse = require('../utils/response');
const Helpers = require('../utils/helpers');
const logger = require('../utils/logger');

class LocationController {
  /**
   * @desc    Update user's current location
   * @route   POST /api/v1/locations/update
   * @access  Private
   */
  static async updateLocation(req, res) {
    try {
      const { latitude, longitude, accuracy } = req.body;
      const userId = req.user.userId;

      const location = await LocationService.updateUserLocation(userId, {
        latitude,
        longitude,
        accuracy,
        timestamp: new Date(),
      });

      return ApiResponse.success(res, location, 'Location updated successfully');
    } catch (error) {
      logger.error('Update location error:', error);
      return ApiResponse.error(res, 'Location update failed');
    }
  }

  /**
   * @desc    Get ride participant locations
   * @route   GET /api/v1/locations/ride/:rideId
   * @access  Private
   */
  static async getRideLocations(req, res) {
    try {
      const { rideId } = req.params;
      const userId = req.user.userId;

      const locations = await LocationService.getRideParticipantLocations(rideId, userId);

      return ApiResponse.success(res, locations, 'Ride locations retrieved successfully');
    } catch (error) {
      logger.error('Get ride locations error:', error);

      if (error.message.includes('not a participant')) {
        return ApiResponse.forbidden(res, error.message);
      }

      return ApiResponse.error(res, 'Failed to get ride locations');
    }
  }

  /**
   * @desc    Get user's location history
   * @route   GET /api/v1/locations/history
   * @access  Private
   */
  static async getLocationHistory(req, res) {
    try {
      const {
        startDate,
        endDate,
        rideId,
        limit = 100,
        offset = 0,
      } = req.query;
      const userId = req.user.userId;

      const options = {
        startDate: startDate ? new Date(startDate) : null,
        endDate: endDate ? new Date(endDate) : null,
        rideId,
        limit: parseInt(limit),
        offset: parseInt(offset),
      };

      const history = await LocationService.getUserLocationHistory(userId, options);

      const pagination = Helpers.getPaginationMeta(
        Math.floor(offset / limit) + 1,
        parseInt(limit),
        history.length
      );

      return ApiResponse.success(res, {
        history,
        pagination,
      }, 'Location history retrieved successfully');
    } catch (error) {
      logger.error('Get location history error:', error);
      return ApiResponse.error(res, 'Failed to get location history');
    }
  }

  /**
   * @desc    Get nearby users
   * @route   GET /api/v1/locations/nearby
   * @access  Private
   */
  static async getNearbyUsers(req, res) {
    try {
      const { latitude, longitude, radius = 5 } = req.query;
      const userId = req.user.userId;

      if (!latitude || !longitude) {
        return ApiResponse.error(res, 'Latitude and longitude are required', 400);
      }

      const nearbyUsers = await LocationService.getNearbyUsers(
        parseFloat(latitude),
        parseFloat(longitude),
        parseFloat(radius),
        userId
      );

      return ApiResponse.success(res, nearbyUsers, 'Nearby users retrieved successfully');
    } catch (error) {
      logger.error('Get nearby users error:', error);
      return ApiResponse.error(res, 'Failed to get nearby users');
    }
  }

  /**
   * @desc    Check drift alerts for a ride
   * @route   GET /api/v1/locations/drift-alerts/:rideId
   * @access  Private
   */
  static async checkDriftAlerts(req, res) {
    try {
      const { rideId } = req.params;

      const alerts = await LocationService.checkDriftAlerts(rideId);

      return ApiResponse.success(res, alerts, 'Drift alerts retrieved successfully');
    } catch (error) {
      logger.error('Check drift alerts error:', error);
      return ApiResponse.error(res, 'Failed to check drift alerts');
    }
  }

  /**
   * @desc    Batch update locations (for bulk updates)
   * @route   POST /api/v1/locations/batch-update
   * @access  Private
   */
  static async batchUpdateLocations(req, res) {
    try {
      const { locations } = req.body;
      const userId = req.user.userId;

      if (!Array.isArray(locations) || locations.length === 0) {
        return ApiResponse.error(res, 'Locations array is required', 400);
      }

      // Add userId to each location update
      const locationUpdates = locations.map(loc => ({
        ...loc,
        userId,
      }));

      const results = await LocationService.batchUpdateLocations(locationUpdates);

      return ApiResponse.success(res, results, 'Batch location update completed');
    } catch (error) {
      logger.error('Batch update locations error:', error);
      return ApiResponse.error(res, 'Batch location update failed');
    }
  }
}

module.exports = LocationController;
