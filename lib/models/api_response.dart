import 'package:flutter/material.dart';

// Generic API Response wrapper
class ApiResponse<T> {
  final T? data;
  final String? error;
  final int? statusCode;
  final bool isSuccess;


  ApiResponse._({
    this.data,
    this.error,
    this.statusCode,
    required this.isSuccess,
  });

  factory ApiResponse.success(T data) {
    return ApiResponse._(
      data: data,
      isSuccess: true,
    );
  }

  factory ApiResponse.error(String error, {int? statusCode}) {
    return ApiResponse._(
      error: error,
      statusCode: statusCode,
      isSuccess: false,
    );
  }
}

// Loading states for UI
enum LoadingState { idle, loading, success, error }

// Network error types
enum NetworkError {
  noInternet,
  timeout,
  serverError,
  unauthorized,
  forbidden,
  notFound,
  unknown,
}

extension NetworkErrorExtension on NetworkError {
  String get message {
    switch (this) {
      case NetworkError.noInternet:
        return 'No internet connection available';
      case NetworkError.timeout:
        return 'Request timed out. Please try again';
      case NetworkError.serverError:
        return 'Server error occurred. Please try again later';
      case NetworkError.unauthorized:
        return 'You are not authorized to perform this action';
      case NetworkError.forbidden:
        return 'Access forbidden';
      case NetworkError.notFound:
        return 'Resource not found';
      case NetworkError.unknown:
        return 'An unexpected error occurred';
    }
  }

  IconData get icon {
    switch (this) {
      case NetworkError.noInternet:
        return Icons.wifi_off;
      case NetworkError.timeout:
        return Icons.access_time;
      case NetworkError.serverError:
        return Icons.error_outline;
      case NetworkError.unauthorized:
      case NetworkError.forbidden:
        return Icons.lock;
      case NetworkError.notFound:
        return Icons.search_off;
      case NetworkError.unknown:
        return Icons.help_outline;
    }
  }
}

// Form validation result
class ValidationResult {
  final bool isValid;
  final String? error;

  ValidationResult.valid() : isValid = true, error = null;
  ValidationResult.invalid(this.error) : isValid = false;
}

// Ride status enumeration
enum RideStatus { scheduled, active, completed, cancelled }

extension RideStatusExtension on RideStatus {
  String get displayName {
    switch (this) {
      case RideStatus.scheduled:
        return 'Scheduled';
      case RideStatus.active:
        return 'Active';
      case RideStatus.completed:
        return 'Completed';
      case RideStatus.cancelled:
        return 'Cancelled';
    }
  }

  Color get color {
    switch (this) {
      case RideStatus.scheduled:
        return Colors.blue;
      case RideStatus.active:
        return Colors.green;
      case RideStatus.completed:
        return Colors.grey;
      case RideStatus.cancelled:
        return Colors.red;
    }
  }
}

// Participant status
enum ParticipantStatus { pending, accepted, rejected }

extension ParticipantStatusExtension on ParticipantStatus {
  String get displayName {
    switch (this) {
      case ParticipantStatus.pending:
        return 'Pending';
      case ParticipantStatus.accepted:
        return 'Accepted';
      case ParticipantStatus.rejected:
        return 'Rejected';
    }
  }

  Color get color {
    switch (this) {
      case ParticipantStatus.pending:
        return Colors.orange;
      case ParticipantStatus.accepted:
        return Colors.green;
      case ParticipantStatus.rejected:
        return Colors.red;
    }
  }
}