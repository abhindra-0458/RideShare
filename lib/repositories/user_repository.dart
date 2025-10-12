import 'package:firebase_auth/firebase_auth.dart';
import '../services/firebase_auth_service.dart';
import '../services/api_service.dart';
import '../models/user_model.dart' as app_models;

class UserRepository {
  final FirebaseAuthService _firebaseAuthService = FirebaseAuthService();
  final ApiService _apiService = ApiService();

  // Option 1: Firebase-first authentication (your current approach)
  Future<User?> loginWithFirebase(String email, String password) async {
    try {
      final user = await _firebaseAuthService.signInWithEmail(email, password);
      
      // Sync with backend if user exists
      if (user != null) {
        await _syncUserWithBackend(user);
      }
      
      return user;
    } catch (e) {
      print("Firebase login error: $e");
      return null;
    }
  }

  Future<User?> registerWithFirebase(String email, String password, {
    String? firstName,
    String? lastName,
    String? phone,
  }) async {
    try {
      final user = await _firebaseAuthService.signUpWithEmail(email, password);
      
      if (user != null) {
        // Legacy method for backward compatibility
        await _apiService.saveUserData(user.uid, email, password);
        
        // New method - sync with proper user data
        if (firstName != null && lastName != null) {
          await _apiService.syncFirebaseUser(
            uid: user.uid,
            email: email,
            firstName: firstName,
            lastName: lastName,
            phone: phone,
            profilePictureUrl: user.photoURL,
          );
        }
      }
      
      return user;
    } catch (e) {
      print("Firebase registration error: $e");
      return null;
    }
  }

  // Option 2: Backend-first authentication (recommended for full integration)
  Future<app_models.User?> loginWithBackend(String email, String password) async {
    try {
      final response = await _apiService.login(email, password);
      
      if (response.isSuccess) {
        final userData = response.data!['user'];
        return app_models.User.fromJson(userData);
      } else {
        print("Backend login error: ${response.error}");
        return null;
      }
    } catch (e) {
      print("Backend login error: $e");
      return null;
    }
  }

  Future<app_models.User?> registerWithBackend({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    try {
      final response = await _apiService.register(
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        phone: phone,
      );

      if (response.isSuccess) {
        final userData = response.data!['user'];
        return app_models.User.fromJson(userData);
      } else {
        print("Backend registration error: ${response.error}");
        return null;
      }
    } catch (e) {
      print("Backend registration error: $e");
      return null;
    }
  }

  // Hybrid approach - use both Firebase and backend
  Future<Map<String, dynamic>?> registerHybrid({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    try {
      // 1. Create Firebase user first
      final firebaseUser = await _firebaseAuthService.signUpWithEmail(email, password);
      
      if (firebaseUser != null) {
        // 2. Sync with backend
        final backendResponse = await _apiService.syncFirebaseUser(
          uid: firebaseUser.uid,
          email: email,
          firstName: firstName,
          lastName: lastName,
          phone: phone,
          profilePictureUrl: firebaseUser.photoURL,
        );

        if (backendResponse.isSuccess) {
          return {
            'firebaseUser': firebaseUser,
            'backendUser': app_models.User.fromJson(backendResponse.data!['user']),
          };
        } else {
          // If backend sync fails, you might want to delete the Firebase user
          await firebaseUser.delete();
          return null;
        }
      }
      
      return null;
    } catch (e) {
      print("Hybrid registration error: $e");
      return null;
    }
  }

  // Helper method to sync existing Firebase user with backend
  Future<bool> _syncUserWithBackend(User firebaseUser) async {
    try {
      // Check if user exists in backend first
      // This is a simplified approach - you might want to implement a proper check
      final response = await _apiService.syncFirebaseUser(
        uid: firebaseUser.uid,
        email: firebaseUser.email!,
        firstName: firebaseUser.displayName?.split(' ').first ?? 'User',
        lastName: firebaseUser.displayName?.split(' ').skip(1).join(' ') ?? '',
        profilePictureUrl: firebaseUser.photoURL,
      );

      return response.isSuccess;
    } catch (e) {
      print("Sync error: $e");
      return false;
    }
  }

  // Legacy methods (keep for backward compatibility)
  Future<User?> login(String email, String password) async {
    return await loginWithFirebase(email, password);
  }

  Future<User?> register(String email, String password) async {
    return await registerWithFirebase(email, password);
  }

  // Logout from both Firebase and backend
  Future<void> logout() async {
    try {
      // Logout from backend first
      await _apiService.logout();
      
      // Then logout from Firebase
      await _firebaseAuthService.signOut();
    } catch (e) {
      print("Logout error: $e");
    }
  }
}