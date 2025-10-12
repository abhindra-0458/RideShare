const db = require('../config/database');
const Helpers = require('../utils/helpers');

class UserModel {
  static async create(userData) {
    const hashedPassword = await Helpers.hashPassword(userData.password);
    const [user] = await db('users').insert({
      email: userData.email,
      password: hashedPassword,
      firstName: userData.firstName,
      lastName: userData.lastName,
      phone: userData.phone,
      createdAt: new Date(),
      updatedAt: new Date()
    }).returning('*');
    return Helpers.sanitizeUser(user);
  }

  static async findById(id) {
    const user = await db('users').where({ id }).first();
    return user ? Helpers.sanitizeUser(user) : null;
  }

  static async findByEmail(email) {
    return db('users').where({ email }).first();
  }

  static async update(id, updateData) {
    const [user] = await db('users').where({ id }).update({ ...updateData, updatedAt: new Date() }).returning('*');
    return user ? Helpers.sanitizeUser(user) : null;
  }

  static async updatePassword(id, newPassword) {
    const hash = await Helpers.hashPassword(newPassword);
    await db('users').where({ id }).update({ password: hash, updatedAt: new Date() });
    return true;
  }

  static async setRefreshToken(id, refreshToken) {
    await db('users').where({ id }).update({ refreshToken, updatedAt: new Date() });
  }

  static async clearRefreshToken(id) {
    await db('users').where({ id }).update({ refreshToken: null, updatedAt: new Date() });
  }

  static async findByRefreshToken(refreshToken) {
    return db('users').where({ refreshToken }).first();
  }

  static async getUserStats(userId) {
    const stats = await db('rides as r')
      .select(
        db.raw('COUNT(*) FILTER (WHERE r.createdBy = ?) as rides_created', [userId]),
        db.raw('COUNT(*) FILTER (WHERE r.id IN (SELECT rp.rideId FROM ride_participants rp WHERE rp.userId = ?)) as rides_joined', [userId]),
        db.raw('COUNT(*) FILTER (WHERE r.status = ? AND r.createdBy = ?) as completed_rides', ['completed', userId])
      )
      .first();
    return stats || { rides_created: 0, rides_joined: 0, completed_rides: 0 };
  }

  static async search(query, limit = 20, offset = 0) {
    return db('users')
      .select(['id', 'firstName', 'lastName', 'email', 'profilePictureUrl', 'isProfileVisible'])
      .where('isActive', true).where('isProfileVisible', true)
      .where(builder => builder
        .where('firstName', 'ilike', `%${query}%`)
        .orWhere('lastName', 'ilike', `%${query}%`)
        .orWhere('email', 'ilike', `%${query}%`))
      .limit(limit)
      .offset(offset);
  }

  static async deactivate(id) {
    await db('users').where({ id }).update({ isActive: false, updatedAt: new Date() });
  }
}

module.exports = UserModel;
