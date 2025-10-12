const UserService = require('../services/userService');
const ApiResponse = require('../utils/response');
const logger = require('../utils/logger');

class AuthController {
  /**
   * @desc    Register a new user
   * @route   POST /api/v1/auth/register
   * @access  Public
   */
  static async register(req, res) {
    try {
      const { email, password, firstName, lastName, phone } = req.body;

      const result = await UserService.registerUser({
        email,
        password,
        firstName,
        lastName,
        phone,
      });

      return ApiResponse.success(res, result, 'User registered successfully', 201);
    } catch (error) {
      logger.error('Registration error:', error);

      if (error.message.includes('already exists')) {
        return ApiResponse.error(res, error.message, 409);
      }

      return ApiResponse.error(res, 'Registration failed');
    }
  }

  /**
   * @desc    Authenticate user and get token
   * @route   POST /api/v1/auth/login
   * @access  Public
   */
  static async login(req, res) {
    try {
      const { email, password } = req.body;

      const result = await UserService.loginUser(email, password);

      return ApiResponse.success(res, result, 'Login successful');
    } catch (error) {
      logger.error('Login error:', error);

      if (error.message.includes('Invalid') || error.message.includes('deactivated')) {
        return ApiResponse.unauthorized(res, error.message);
      }

      return ApiResponse.error(res, 'Login failed');
    }
  }

  /**
   * @desc    Refresh access token
   * @route   POST /api/v1/auth/refresh
   * @access  Public
   */
  static async refreshToken(req, res) {
    try {
      const { refreshToken } = req.body;

      if (!refreshToken) {
        return ApiResponse.error(res, 'Refresh token is required', 400);
      }

      const result = await UserService.refreshTokens(refreshToken);

      return ApiResponse.success(res, result, 'Token refreshed successfully');
    } catch (error) {
      logger.error('Token refresh error:', error);
      return ApiResponse.unauthorized(res, 'Invalid refresh token');
    }
  }

  /**
   * @desc    Logout user
   * @route   POST /api/v1/auth/logout
   * @access  Private
   */
  static async logout(req, res) {
    try {
      await UserService.logoutUser(req.user.userId);

      return ApiResponse.success(res, null, 'Logout successful');
    } catch (error) {
      logger.error('Logout error:', error);
      return ApiResponse.error(res, 'Logout failed');
    }
  }

  /**
   * @desc    Change user password
   * @route   PUT /api/v1/auth/change-password
   * @access  Private
   */
  static async changePassword(req, res) {
    try {
      const { currentPassword, newPassword } = req.body;

      await UserService.changePassword(
        req.user.userId,
        currentPassword,
        newPassword
      );

      return ApiResponse.success(res, null, 'Password changed successfully');
    } catch (error) {
      logger.error('Change password error:', error);

      if (error.message.includes('incorrect')) {
        return ApiResponse.error(res, error.message, 400);
      }

      return ApiResponse.error(res, 'Password change failed');
    }
  }

  /**
   * @desc    Get current user profile
   * @route   GET /api/v1/auth/me
   * @access  Private
   */
  static async getCurrentUser(req, res) {
    try {
      const user = await UserService.getUserProfile(req.user.userId);

      return ApiResponse.success(res, user, 'User profile retrieved successfully');
    } catch (error) {
      logger.error('Get current user error:', error);
      return ApiResponse.error(res, 'Failed to get user profile');
    }
  }
}

module.exports = AuthController;
