const logger = require('../utils/logger');
const ApiResponse = require('../utils/response');

const errorHandler = (err, req, res, next) => {
  logger.error('Error:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
  });

  // Database errors
  if (err.code === '23505') {
    return ApiResponse.error(res, 'Duplicate entry - resource already exists', 409);
  }

  if (err.code === '23503') {
    return ApiResponse.error(res, 'Foreign key constraint violation', 400);
  }

  if (err.code === '23502') {
    return ApiResponse.error(res, 'Required field is missing', 400);
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    return ApiResponse.unauthorized(res, 'Invalid token');
  }

  if (err.name === 'TokenExpiredError') {
    return ApiResponse.unauthorized(res, 'Token expired');
  }

  // Validation errors
  if (err.name === 'ValidationError') {
    return ApiResponse.validationError(res, err.details);
  }

  // File upload errors
  if (err.code === 'LIMIT_FILE_SIZE') {
    return ApiResponse.error(res, 'File too large', 413);
  }

  if (err.code === 'LIMIT_UNEXPECTED_FILE') {
    return ApiResponse.error(res, 'Unexpected file field', 400);
  }

  // Default error
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';

  return ApiResponse.error(res, message, statusCode);
};

const notFoundHandler = (req, res) => {
  ApiResponse.notFound(res, `Route ${req.originalUrl} not found`);
};

module.exports = {
  errorHandler,
  notFoundHandler,
};
