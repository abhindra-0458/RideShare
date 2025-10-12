import 'package:flutter/material.dart';

class PostRideScreen extends StatelessWidget {
  const PostRideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final TextEditingController fromController = TextEditingController();
    final TextEditingController toController = TextEditingController();
    final TextEditingController dateController = TextEditingController();

    return Scaffold(
      appBar: AppBar(title: const Text("Post a Ride")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: fromController,
              decoration: const InputDecoration(labelText: "From"),
            ),
            TextField(
              controller: toController,
              decoration: const InputDecoration(labelText: "To"),
            ),
            TextField(
              controller: dateController,
              decoration: const InputDecoration(labelText: "Date"),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                // TODO: Save ride to DB
              },
              child: const Text("Post Ride"),
            ),
          ],
        ),
      ),
    );
  }
}
