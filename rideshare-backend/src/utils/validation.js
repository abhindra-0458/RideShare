const Joi = require('joi');

const schemas = {
  // User validation schemas
  userRegistration: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).pattern(new RegExp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)')).required()
      .messages({
        'string.pattern.base': 'Password must contain at least one lowercase letter, one uppercase letter, and one number'
      }),
    firstName: Joi.string().min(2).max(50).required(),
    lastName: Joi.string().min(2).max(50).required(),
    phone: Joi.string().pattern(/^\+?[1-9]\d{1,14}$/).required(),
  }),

  userLogin: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required(),
  }),

  userProfileUpdate: Joi.object({
    firstName: Joi.string().min(2).max(50),
    lastName: Joi.string().min(2).max(50),
    phone: Joi.string().pattern(/^\+?[1-9]\d{1,14}$/),
    bio: Joi.string().max(500),
    profilePictureUrl: Joi.string().uri(),
    socialLinks: Joi.object({
      facebook: Joi.string().uri(),
      instagram: Joi.string().uri(),
      twitter: Joi.string().uri(),
    }),
    isProfileVisible: Joi.boolean(),
  }),

  // Ride validation schemas
  createRide: Joi.object({
    title: Joi.string().min(3).max(100).required(),
    description: Joi.string().max(500),
    startLocation: Joi.object({
      latitude: Joi.number().min(-90).max(90).required(),
      longitude: Joi.number().min(-180).max(180).required(),
      address: Joi.string().max(200).required(),
    }).required(),
    endLocation: Joi.object({
      latitude: Joi.number().min(-90).max(90).required(),
      longitude: Joi.number().min(-180).max(180).required(),
      address: Joi.string().max(200).required(),
    }).required(),
    scheduledDateTime: Joi.date().iso().min('now').required(),
    isPublic: Joi.boolean().default(true),
    maxParticipants: Joi.number().integer().min(1).max(20).default(10),
    estimatedDurationMinutes: Joi.number().integer().min(1),
    difficulty: Joi.string().valid('easy', 'medium', 'hard').default('medium'),
  }),

  updateRide: Joi.object({
    title: Joi.string().min(3).max(100),
    description: Joi.string().max(500),
    startLocation: Joi.object({
      latitude: Joi.number().min(-90).max(90).required(),
      longitude: Joi.number().min(-180).max(180).required(),
      address: Joi.string().max(200).required(),
    }),
    endLocation: Joi.object({
      latitude: Joi.number().min(-90).max(90).required(),
      longitude: Joi.number().min(-180).max(180).required(),
      address: Joi.string().max(200).required(),
    }),
    scheduledDateTime: Joi.date().iso().min('now'),
    isPublic: Joi.boolean(),
    maxParticipants: Joi.number().integer().min(1).max(20),
    estimatedDurationMinutes: Joi.number().integer().min(1),
    difficulty: Joi.string().valid('easy', 'medium', 'hard'),
    status: Joi.string().valid('scheduled', 'active', 'completed', 'cancelled'),
  }),

  // Location validation schemas
  locationUpdate: Joi.object({
    latitude: Joi.number().min(-90).max(90).required(),
    longitude: Joi.number().min(-180).max(180).required(),
    accuracy: Joi.number().min(0),
    timestamp: Joi.date().iso().default(Date.now),
  }),

  // Invitation validation schemas
  inviteUsers: Joi.object({
    userIds: Joi.array().items(Joi.string().uuid()).min(1).required(),
    message: Joi.string().max(200),
  }),
};

module.exports = schemas;
