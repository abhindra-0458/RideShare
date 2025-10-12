import 'package:flutter/material.dart';

class ExpandableLeaderboard extends StatelessWidget {
  final List<({String name, String distance})> rows;
  final VoidCallback onClose;

  const ExpandableLeaderboard({
    super.key,
    required this.rows,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(8),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 280),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              dense: true,
              leading: const Icon(Icons.leaderboard),
              title: const Text("Leaderboard"),
              trailing: IconButton(
                icon: const Icon(Icons.close),
                onPressed: onClose,
              ),
            ),
            const Divider(height: 1),
            ...rows.map((r) => ListTile(
                  dense: true,
                  title: Text(r.name),
                  trailing: Text(r.distance),
                )),
          ],
        ),
      ),
    );
  }
}
