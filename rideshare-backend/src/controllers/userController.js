const UserService = require('../services/userService');
const ApiResponse = require('../utils/response');
const Helpers = require('../utils/helpers');
const logger = require('../utils/logger');

class UserController {
  /**
   * @desc    Get user profile by ID
   * @route   GET /api/v1/users/:id
   * @access  Private
   */
  static async getUserById(req, res) {
    try {
      const { id } = req.params;
      const user = await UserService.getUserProfile(id);

      return ApiResponse.success(res, user, 'User profile retrieved successfully');
    } catch (error) {
      logger.error('Get user by ID error:', error);

      if (error.message.includes('not found')) {
        return ApiResponse.notFound(res, 'User not found');
      }

      return ApiResponse.error(res, 'Failed to get user profile');
    }
  }

  /**
   * @desc    Update user profile
   * @route   PUT /api/v1/users/profile
   * @access  Private
   */
  static async updateProfile(req, res) {
    try {
      const updateData = req.body;
      const userId = req.user.userId;

      const user = await UserService.updateUserProfile(userId, updateData);

      return ApiResponse.success(res, user, 'Profile updated successfully');
    } catch (error) {
      logger.error('Update profile error:', error);
      return ApiResponse.error(res, 'Profile update failed');
    }
  }

  /**
   * @desc    Search users
   * @route   GET /api/v1/users/search
   * @access  Private
   */
  static async searchUsers(req, res) {
    try {
      const { q: query, limit = 20, offset = 0 } = req.query;

      if (!query || query.length < 2) {
        return ApiResponse.error(res, 'Search query must be at least 2 characters', 400);
      }

      const users = await UserService.searchUsers(
        query,
        parseInt(limit),
        parseInt(offset)
      );

      const pagination = Helpers.getPaginationMeta(
        Math.floor(offset / limit) + 1,
        parseInt(limit),
        users.length
      );

      return ApiResponse.success(res, {
        users,
        pagination,
      }, 'Users retrieved successfully');
    } catch (error) {
      logger.error('Search users error:', error);
      return ApiResponse.error(res, 'User search failed');
    }
  }

  /**
   * @desc    Deactivate user account
   * @route   DELETE /api/v1/users/deactivate
   * @access  Private
   */
  static async deactivateAccount(req, res) {
    try {
      const userId = req.user.userId;

      await UserService.deactivateUser(userId);

      return ApiResponse.success(res, null, 'Account deactivated successfully');
    } catch (error) {
      logger.error('Deactivate account error:', error);
      return ApiResponse.error(res, 'Account deactivation failed');
    }
  }
}

module.exports = UserController;
