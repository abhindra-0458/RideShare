const UserModel = require('../models/User');
const Helpers = require('../utils/helpers');
const redisClient = require('../config/redis');
const logger = require('../utils/logger');

class UserService {
  static async registerUser(userData) {
    try {
      // Check if user already exists
      const existingUser = await UserModel.findByEmail(userData.email);
      if (existingUser) {
        throw new Error('User with this email already exists');
      }

      // Create user
      const user = await UserModel.create(userData);

      // Generate tokens
      const tokens = Helpers.generateTokens({ 
        userId: user.id, 
        email: user.email,
        role: user.role 
      });

      // Store refresh token
      await UserModel.setRefreshToken(user.id, tokens.refreshToken);

      // Cache user data
      await redisClient.set(`user:${user.id}`, user, 3600); // 1 hour

      logger.info(`New user registered: ${user.email}`);

      return {
        user,
        tokens,
      };
    } catch (error) {
      logger.error('User registration error:', error);
      throw error;
    }
  }

  static async loginUser(email, password) {
    try {
      // Find user with password
      const user = await UserModel.findByEmail(email);
      if (!user) {
        throw new Error('Invalid email or password');
      }

      if (!user.isActive) {
        throw new Error('Account is deactivated');
      }

      // Verify password
      const isPasswordValid = await Helpers.comparePassword(password, user.password);
      if (!isPasswordValid) {
        throw new Error('Invalid email or password');
      }

      // Generate tokens
      const tokens = Helpers.generateTokens({ 
        userId: user.id, 
        email: user.email,
        role: user.role 
      });

      // Store refresh token
      await UserModel.setRefreshToken(user.id, tokens.refreshToken);

      // Cache user data
      const sanitizedUser = Helpers.sanitizeUser(user);
      await redisClient.set(`user:${user.id}`, sanitizedUser, 3600);

      // Update last login
      await UserModel.update(user.id, { lastLoginAt: new Date() });

      logger.info(`User logged in: ${user.email}`);

      return {
        user: sanitizedUser,
        tokens,
      };
    } catch (error) {
      logger.error('User login error:', error);
      throw error;
    }
  }

  static async refreshTokens(refreshToken) {
    try {
      // Verify refresh token
      const decoded = Helpers.verifyRefreshToken(refreshToken);

      // Find user with this refresh token
      const user = await UserModel.findByRefreshToken(refreshToken);
      if (!user || !user.isActive) {
        throw new Error('Invalid refresh token');
      }

      // Generate new tokens
      const tokens = Helpers.generateTokens({ 
        userId: user.id, 
        email: user.email,
        role: user.role 
      });

      // Update refresh token
      await UserModel.setRefreshToken(user.id, tokens.refreshToken);

      // Update cache
      const sanitizedUser = Helpers.sanitizeUser(user);
      await redisClient.set(`user:${user.id}`, sanitizedUser, 3600);

      return {
        user: sanitizedUser,
        tokens,
      };
    } catch (error) {
      logger.error('Token refresh error:', error);
      throw error;
    }
  }

  static async logoutUser(userId) {
    try {
      // Clear refresh token
      await UserModel.clearRefreshToken(userId);

      // Remove from cache
      await redisClient.del(`user:${userId}`);

      logger.info(`User logged out: ${userId}`);
    } catch (error) {
      logger.error('User logout error:', error);
      throw error;
    }
  }

  static async getUserProfile(userId) {
    try {
      // Try cache first
      let user = await redisClient.get(`user:${userId}`);

      if (!user) {
        user = await UserModel.findById(userId);
        if (user) {
          await redisClient.set(`user:${userId}`, user, 3600);
        }
      }

      if (!user) {
        throw new Error('User not found');
      }

      // Get user stats
      const stats = await UserModel.getUserStats(userId);

      return {
        ...user,
        stats,
      };
    } catch (error) {
      logger.error('Get user profile error:', error);
      throw error;
    }
  }

  static async updateUserProfile(userId, updateData) {
    try {
      const user = await UserModel.update(userId, updateData);
      if (!user) {
        throw new Error('User not found');
      }

      // Update cache
      await redisClient.set(`user:${userId}`, user, 3600);

      logger.info(`User profile updated: ${userId}`);

      return user;
    } catch (error) {
      logger.error('Update user profile error:', error);
      throw error;
    }
  }

  static async changePassword(userId, currentPassword, newPassword) {
    try {
      // Get user with password
      const user = await UserModel.findByEmail(
        (await UserModel.findById(userId)).email
      );

      // Verify current password
      const isCurrentPasswordValid = await Helpers.comparePassword(
        currentPassword, 
        user.password
      );

      if (!isCurrentPasswordValid) {
        throw new Error('Current password is incorrect');
      }

      // Update password
      await UserModel.updatePassword(userId, newPassword);

      // Clear all refresh tokens (force re-login on all devices)
      await UserModel.clearRefreshToken(userId);

      logger.info(`Password changed for user: ${userId}`);

      return true;
    } catch (error) {
      logger.error('Change password error:', error);
      throw error;
    }
  }

  static async searchUsers(query, limit = 20, offset = 0) {
    try {
      const users = await UserModel.search(query, limit, offset);
      return users;
    } catch (error) {
      logger.error('Search users error:', error);
      throw error;
    }
  }

  static async deactivateUser(userId) {
    try {
      await UserModel.deactivate(userId);

      // Clear cache
      await redisClient.del(`user:${userId}`);

      logger.info(`User deactivated: ${userId}`);

      return true;
    } catch (error) {
      logger.error('Deactivate user error:', error);
      throw error;
    }
  }
}

module.exports = UserService;
