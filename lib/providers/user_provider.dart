import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Simple username-based user provider (no backend authentication)
class UserProvider extends ChangeNotifier {
  String? _userId;
  String? _username;

  String? get userId => _userId;
  String? get username => _username;
  bool get hasUsername => _username != null && _username!.isNotEmpty;

  /// Load username from local storage on app start
  Future<void> loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    _userId = prefs.getString('userId');
    _username = prefs.getString('username');
    notifyListeners();
  }

  /// Set username and generate simple user ID
  Future<void> setUsername(String username) async {
    _username = username;
    // Generate simple user ID (in production, get from backend)
    _userId = 'user_${username}_${DateTime.now().millisecondsSinceEpoch}';
    
    // Save to local storage
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('userId', _userId!);
    await prefs.setString('username', username);
    
    notifyListeners();
  }

  /// Clear user data (logout)
  Future<void> clearUser() async {
    _userId = null;
    _username = null;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('userId');
    await prefs.remove('username');
    
    notifyListeners();
  }
}
