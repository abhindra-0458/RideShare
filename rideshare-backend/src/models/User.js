const db = require('../config/database');
const Helpers = require('../utils/helpers');

class UserModel {
  static async create(userData) {
    const hashedPassword = await Helpers.hashPassword(userData.password);

    const [user] = await db('users')
      .insert({
        ...userData,
        password: hashedPassword,
        createdAt: new Date(),
        updatedAt: new Date(),
      })
      .returning('*');

    return Helpers.sanitizeUser(user);
  }

  static async findById(id) {
    const user = await db('users')
      .where({ id })
      .first();

    return user ? Helpers.sanitizeUser(user) : null;
  }

  static async findByEmail(email) {
    return await db('users')
      .where({ email })
      .first();
  }

  static async update(id, updateData) {
    const [user] = await db('users')
      .where({ id })
      .update({
        ...updateData,
        updatedAt: new Date(),
      })
      .returning('*');

    return user ? Helpers.sanitizeUser(user) : null;
  }

  static async updatePassword(id, newPassword) {
    const hashedPassword = await Helpers.hashPassword(newPassword);

    await db('users')
      .where({ id })
      .update({
        password: hashedPassword,
        updatedAt: new Date(),
      });

    return true;
  }

  static async setRefreshToken(id, refreshToken) {
    await db('users')
      .where({ id })
      .update({
        refreshToken,
        updatedAt: new Date(),
      });
  }

  static async clearRefreshToken(id) {
    await db('users')
      .where({ id })
      .update({
        refreshToken: null,
        updatedAt: new Date(),
      });
  }

  static async findByRefreshToken(refreshToken) {
    return await db('users')
      .where({ refreshToken })
      .first();
  }

  static async getUserStats(userId) {
    const stats = await db('rides')
      .select(
        db.raw('COUNT(CASE WHEN created_by = ? THEN 1 END) as rides_created', [userId]),
        db.raw('COUNT(CASE WHEN r.id IN (SELECT ride_id FROM ride_participants WHERE user_id = ?) THEN 1 END) as rides_joined', [userId]),
        db.raw('COUNT(CASE WHEN status = ? AND created_by = ? THEN 1 END) as completed_rides', ['completed', userId])
      )
      .from('rides as r')
      .first();

    return stats || { rides_created: 0, rides_joined: 0, completed_rides: 0 };
  }

  static async search(query, limit = 20, offset = 0) {
    const users = await db('users')
      .select(['id', 'firstName', 'lastName', 'email', 'profilePictureUrl', 'isProfileVisible'])
      .where('isActive', true)
      .where('isProfileVisible', true)
      .where(function() {
        this.where('firstName', 'ilike', `%${query}%`)
          .orWhere('lastName', 'ilike', `%${query}%`)
          .orWhere('email', 'ilike', `%${query}%`);
      })
      .limit(limit)
      .offset(offset);

    return users;
  }

  static async deactivate(id) {
    await db('users')
      .where({ id })
      .update({
        isActive: false,
        updatedAt: new Date(),
      });
  }
}

module.exports = UserModel;
