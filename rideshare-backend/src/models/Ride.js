const db = require('../config/database');
const Helpers = require('../utils/helpers');

class RideModel {
  static async create(rideData, createdBy) {
    const trx = await db.transaction();

    try {
      const [ride] = await trx('rides')
        .insert({
          ...rideData,
          createdBy,
          status: 'scheduled',
          createdAt: new Date(),
          updatedAt: new Date(),
        })
        .returning('*');

      // Add creator as participant
      await trx('ride_participants')
        .insert({
          rideId: ride.id,
          userId: createdBy,
          status: 'accepted',
          joinedAt: new Date(),
        });

      await trx.commit();
      return ride;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  static async findById(id, userId = null) {
    const query = db('rides as r')
      .select([
        'r.*',
        'u.firstName as creatorFirstName',
        'u.lastName as creatorLastName',
        'u.profilePictureUrl as creatorProfilePicture',
      ])
      .leftJoin('users as u', 'r.createdBy', 'u.id')
      .where('r.id', id);

    if (userId) {
      query.select([
        db.raw('CASE WHEN rp.user_id IS NOT NULL THEN true ELSE false END as is_participant'),
        'rp.status as participant_status'
      ])
      .leftJoin('ride_participants as rp', function() {
        this.on('rp.ride_id', '=', 'r.id')
          .andOn('rp.user_id', '=', db.raw('?', [userId]));
      });
    }

    const ride = await query.first();

    if (ride) {
      ride.participants = await this.getRideParticipants(id);
    }

    return ride;
  }

  static async update(id, updateData, userId) {
    const [ride] = await db('rides')
      .where({ id, createdBy: userId })
      .update({
        ...updateData,
        updatedAt: new Date(),
      })
      .returning('*');

    return ride;
  }

  static async delete(id, userId) {
    const deletedCount = await db('rides')
      .where({ id, createdBy: userId })
      .del();

    return deletedCount > 0;
  }

  static async getUserRides(userId, options = {}) {
    const { 
      status, 
      type = 'all', // 'created', 'joined', 'all'
      limit = 20, 
      offset = 0,
      sortBy = 'scheduledDateTime',
      sortOrder = 'asc'
    } = options;

    let query = db('rides as r')
      .select([
        'r.*',
        'u.firstName as creatorFirstName',
        'u.lastName as creatorLastName',
        'u.profilePictureUrl as creatorProfilePicture',
      ])
      .leftJoin('users as u', 'r.createdBy', 'u.id');

    if (type === 'created') {
      query = query.where('r.createdBy', userId);
    } else if (type === 'joined') {
      query = query
        .join('ride_participants as rp', 'r.id', 'rp.rideId')
        .where('rp.userId', userId)
        .where('r.createdBy', '!=', userId);
    } else {
      query = query
        .leftJoin('ride_participants as rp', 'r.id', 'rp.rideId')
        .where(function() {
          this.where('r.createdBy', userId)
            .orWhere('rp.userId', userId);
        });
    }

    if (status) {
      query = query.where('r.status', status);
    }

    const rides = await query
      .orderBy(`r.${sortBy}`, sortOrder)
      .limit(limit)
      .offset(offset);

    // Get participant count for each ride
    for (let ride of rides) {
      const participantCount = await db('ride_participants')
        .where('rideId', ride.id)
        .where('status', 'accepted')
        .count('* as count')
        .first();

      ride.participantCount = parseInt(participantCount.count);
    }

    return rides;
  }

  static async searchRides(searchParams, userId = null) {
    const {
      latitude,
      longitude,
      radiusKm = 50,
      startDate,
      endDate,
      difficulty,
      isPublic = true,
      limit = 20,
      offset = 0,
    } = searchParams;

    let query = db('rides as r')
      .select([
        'r.*',
        'u.firstName as creatorFirstName',
        'u.lastName as creatorLastName',
        'u.profilePictureUrl as creatorProfilePicture',
      ])
      .leftJoin('users as u', 'r.createdBy', 'u.id')
      .where('r.status', 'scheduled')
      .where('r.isPublic', isPublic);

    // Location-based search
    if (latitude && longitude && radiusKm) {
      query = query.whereRaw(
        `ST_DWithin(ST_MakePoint(r.start_longitude, r.start_latitude)::geography, 
         ST_MakePoint(?, ?)::geography, ? * 1000)`,
        [longitude, latitude, radiusKm]
      );
    }

    // Date range filter
    if (startDate) {
      query = query.where('r.scheduledDateTime', '>=', startDate);
    }
    if (endDate) {
      query = query.where('r.scheduledDateTime', '<=', endDate);
    }

    // Difficulty filter
    if (difficulty) {
      query = query.where('r.difficulty', difficulty);
    }

    // Exclude user's own rides if userId provided
    if (userId) {
      query = query.where('r.createdBy', '!=', userId);
    }

    const rides = await query
      .orderBy('r.scheduledDateTime', 'asc')
      .limit(limit)
      .offset(offset);

    // Calculate distance and add participant count
    for (let ride of rides) {
      if (latitude && longitude) {
        ride.distanceKm = Helpers.calculateDistance(
          latitude, longitude, 
          ride.startLatitude, ride.startLongitude
        );
      }

      const participantCount = await db('ride_participants')
        .where('rideId', ride.id)
        .where('status', 'accepted')
        .count('* as count')
        .first();

      ride.participantCount = parseInt(participantCount.count);
    }

    return rides;
  }

  static async getRideParticipants(rideId) {
    return await db('ride_participants as rp')
      .select([
        'rp.*',
        'u.firstName',
        'u.lastName',
        'u.profilePictureUrl',
        'u.email',
      ])
      .join('users as u', 'rp.userId', 'u.id')
      .where('rp.rideId', rideId)
      .orderBy('rp.joinedAt', 'asc');
  }

  static async joinRide(rideId, userId) {
    // Check if ride exists and has space
    const ride = await db('rides')
      .where({ id: rideId, status: 'scheduled' })
      .first();

    if (!ride) {
      throw new Error('Ride not found or not available');
    }

    const currentParticipants = await db('ride_participants')
      .where({ rideId, status: 'accepted' })
      .count('* as count')
      .first();

    if (parseInt(currentParticipants.count) >= ride.maxParticipants) {
      throw new Error('Ride is full');
    }

    // Check if user is already a participant
    const existingParticipant = await db('ride_participants')
      .where({ rideId, userId })
      .first();

    if (existingParticipant) {
      throw new Error('User is already a participant');
    }

    const [participant] = await db('ride_participants')
      .insert({
        rideId,
        userId,
        status: ride.isPublic ? 'accepted' : 'pending',
        joinedAt: new Date(),
      })
      .returning('*');

    return participant;
  }

  static async leaveRide(rideId, userId) {
    const deletedCount = await db('ride_participants')
      .where({ rideId, userId })
      .del();

    return deletedCount > 0;
  }

  static async updateParticipantStatus(rideId, userId, status, updatedBy) {
    // Verify that updatedBy is the ride creator
    const ride = await db('rides')
      .where({ id: rideId, createdBy: updatedBy })
      .first();

    if (!ride) {
      throw new Error('Only ride creator can update participant status');
    }

    const [participant] = await db('ride_participants')
      .where({ rideId, userId })
      .update({ status })
      .returning('*');

    return participant;
  }
}

module.exports = RideModel;
