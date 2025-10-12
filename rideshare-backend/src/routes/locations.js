const express = require('express');
const LocationController = require('../controllers/locationController');
const { validate, validateQuery } = require('../middleware/validation');
const { authenticateToken } = require('../middleware/auth');
const { locationLimiter } = require('../middleware/rateLimiter');
const schemas = require('../utils/validation');
const Joi = require('joi');

const router = express.Router();

// Query validation schemas
const nearbyUsersSchema = Joi.object({
  latitude: Joi.number().min(-90).max(90).required(),
  longitude: Joi.number().min(-180).max(180).required(),
  radius: Joi.number().min(0.1).max(100).default(5),
});

const locationHistorySchema = Joi.object({
  startDate: Joi.date().iso(),
  endDate: Joi.date().iso(),
  rideId: Joi.string().uuid(),
  limit: Joi.number().integer().min(1).max(1000).default(100),
  offset: Joi.number().integer().min(0).default(0),
});

/**
 * @swagger
 * /api/v1/locations/update:
 *   post:
 *     summary: Update user's current location
 *     tags: [Locations]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - latitude
 *               - longitude
 *             properties:
 *               latitude:
 *                 type: number
 *                 minimum: -90
 *                 maximum: 90
 *               longitude:
 *                 type: number
 *                 minimum: -180
 *                 maximum: 180
 *               accuracy:
 *                 type: number
 *                 minimum: 0
 *     responses:
 *       200:
 *         description: Location updated successfully
 *       400:
 *         description: Invalid location data
 */
router.post(
  '/update',
  authenticateToken,
  locationLimiter,
  validate(schemas.locationUpdate),
  LocationController.updateLocation
);

/**
 * @swagger
 * /api/v1/locations/batch-update:
 *   post:
 *     summary: Batch update locations
 *     tags: [Locations]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - locations
 *             properties:
 *               locations:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     latitude:
 *                       type: number
 *                     longitude:
 *                       type: number
 *                     accuracy:
 *                       type: number
 *                     timestamp:
 *                       type: string
 *                       format: date-time
 *     responses:
 *       200:
 *         description: Batch update completed
 */
router.post(
  '/batch-update',
  authenticateToken,
  LocationController.batchUpdateLocations
);

/**
 * @swagger
 * /api/v1/locations/ride/{rideId}:
 *   get:
 *     summary: Get ride participant locations
 *     tags: [Locations]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: rideId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     responses:
 *       200:
 *         description: Ride locations retrieved successfully
 *       403:
 *         description: Not a participant in this ride
 */
router.get(
  '/ride/:rideId',
  authenticateToken,
  LocationController.getRideLocations
);

/**
 * @swagger
 * /api/v1/locations/history:
 *   get:
 *     summary: Get user's location history
 *     tags: [Locations]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: startDate
 *         schema:
 *           type: string
 *           format: date-time
 *       - in: query
 *         name: endDate
 *         schema:
 *           type: string
 *           format: date-time
 *       - in: query
 *         name: rideId
 *         schema:
 *           type: string
 *           format: uuid
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           minimum: 1
 *           maximum: 1000
 *           default: 100
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           minimum: 0
 *           default: 0
 *     responses:
 *       200:
 *         description: Location history retrieved successfully
 */
router.get(
  '/history',
  authenticateToken,
  validateQuery(locationHistorySchema),
  LocationController.getLocationHistory
);

/**
 * @swagger
 * /api/v1/locations/nearby:
 *   get:
 *     summary: Get nearby users
 *     tags: [Locations]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: latitude
 *         required: true
 *         schema:
 *           type: number
 *           minimum: -90
 *           maximum: 90
 *       - in: query
 *         name: longitude
 *         required: true
 *         schema:
 *           type: number
 *           minimum: -180
 *           maximum: 180
 *       - in: query
 *         name: radius
 *         schema:
 *           type: number
 *           minimum: 0.1
 *           maximum: 100
 *           default: 5
 *     responses:
 *       200:
 *         description: Nearby users retrieved successfully
 */
router.get(
  '/nearby',
  authenticateToken,
  validateQuery(nearbyUsersSchema),
  LocationController.getNearbyUsers
);

/**
 * @swagger
 * /api/v1/locations/drift-alerts/{rideId}:
 *   get:
 *     summary: Check drift alerts for a ride
 *     tags: [Locations]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: rideId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     responses:
 *       200:
 *         description: Drift alerts retrieved successfully
 */
router.get(
  '/drift-alerts/:rideId',
  authenticateToken,
  LocationController.checkDriftAlerts
);

module.exports = router;
