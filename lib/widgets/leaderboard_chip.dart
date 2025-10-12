import 'package:flutter/material.dart';

class LeaderboardChip extends StatelessWidget {
  final String leaderName;
  final String leaderDist;
  final String? aheadName;
  final String? aheadDist;
  final VoidCallback onTap;

  const LeaderboardChip({
    super.key,
    required this.leaderName,
    required this.leaderDist,
    required this.onTap,
    this.aheadName,
    this.aheadDist,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        margin: const EdgeInsets.all(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.emoji_events, size: 18),
              const SizedBox(width: 6),
              Text("$leaderName ($leaderDist)"),
              if (aheadName != null) ...[
                const SizedBox(width: 10),
                const Icon(Icons.arrow_upward, size: 16),
                Text("$aheadName ($aheadDist)"),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
