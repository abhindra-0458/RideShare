const express = require('express');
const UserController = require('../controllers/userController');
const { validate, validateQuery } = require('../middleware/validation');
const { authenticateToken } = require('../middleware/auth');
const schemas = require('../utils/validation');
const Joi = require('joi');

const router = express.Router();

// Query validation schemas
const searchUsersSchema = Joi.object({
  q: Joi.string().min(2).required(),
  limit: Joi.number().integer().min(1).max(100).default(20),
  offset: Joi.number().integer().min(0).default(0),
});

/**
 * @swagger
 * /api/v1/users/{id}:
 *   get:
 *     summary: Get user profile by ID
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     responses:
 *       200:
 *         description: User profile retrieved successfully
 *       404:
 *         description: User not found
 */
router.get('/:id', authenticateToken, UserController.getUserById);

/**
 * @swagger
 * /api/v1/users/profile:
 *   put:
 *     summary: Update user profile
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               firstName:
 *                 type: string
 *               lastName:
 *                 type: string
 *               phone:
 *                 type: string
 *               bio:
 *                 type: string
 *               profilePictureUrl:
 *                 type: string
 *                 format: uri
 *               socialLinks:
 *                 type: object
 *               isProfileVisible:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Profile updated successfully
 */
router.put(
  '/profile',
  authenticateToken,
  validate(schemas.userProfileUpdate),
  UserController.updateProfile
);

/**
 * @swagger
 * /api/v1/users/search:
 *   get:
 *     summary: Search users
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: q
 *         required: true
 *         schema:
 *           type: string
 *           minLength: 2
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           minimum: 1
 *           maximum: 100
 *           default: 20
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           minimum: 0
 *           default: 0
 *     responses:
 *       200:
 *         description: Users retrieved successfully
 */
router.get(
  '/search',
  authenticateToken,
  validateQuery(searchUsersSchema),
  UserController.searchUsers
);

/**
 * @swagger
 * /api/v1/users/deactivate:
 *   delete:
 *     summary: Deactivate user account
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Account deactivated successfully
 */
router.delete('/deactivate', authenticateToken, UserController.deactivateAccount);

module.exports = router;
