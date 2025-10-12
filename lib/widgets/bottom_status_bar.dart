import 'package:flutter/material.dart';

class BottomStatusBar extends StatelessWidget {
  final String distanceText;
  final String etaText;

  const BottomStatusBar({
    super.key,
    required this.distanceText,
    required this.etaText,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          boxShadow: const [BoxShadow(blurRadius: 6, color: Colors.black12)],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(children: [
              const Icon(Icons.place),
              const SizedBox(width: 8),
              Text(distanceText),
            ]),
            Row(children: [
              const Icon(Icons.access_time),
              const SizedBox(width: 8),
              Text(etaText),
            ]),
          ],
        ),
      ),
    );
  }
}
