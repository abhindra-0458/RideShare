const rateLimit = require('express-rate-limit');
const config = require('../config');
const redisClient = require('../config/redis');
const ApiResponse = require('../utils/response');

// General API rate limiting
const generalLimiter = rateLimit({
  windowMs: config.rateLimit.windowMs,
  max: config.rateLimit.maxRequests,
  message: {
    success: false,
    message: 'Too many requests from this IP, please try again later.',
    timestamp: new Date().toISOString(),
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Strict rate limiting for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  message: {
    success: false,
    message: 'Too many authentication attempts, please try again later.',
    timestamp: new Date().toISOString(),
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Location update rate limiting
const locationLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30, // 30 location updates per minute
  message: {
    success: false,
    message: 'Too many location updates, please slow down.',
    timestamp: new Date().toISOString(),
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Custom rate limiter for WebSocket connections
const createWebSocketRateLimiter = (maxConnections = 5) => {
  return async (socket, next) => {
    try {
      const clientIp = socket.handshake.address;
      const key = `ws_connections:${clientIp}`;

      const currentConnections = await redisClient.incr(key, 3600); // 1 hour expiry

      if (currentConnections > maxConnections) {
        return next(new Error('Too many WebSocket connections from this IP'));
      }

      socket.on('disconnect', async () => {
        await redisClient.client.decr(key);
      });

      next();
    } catch (error) {
      next(error);
    }
  };
};

module.exports = {
  generalLimiter,
  authLimiter,
  locationLimiter,
  createWebSocketRateLimiter,
};
