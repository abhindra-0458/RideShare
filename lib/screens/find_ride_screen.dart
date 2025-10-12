import 'package:flutter/material.dart';

class FindRideScreen extends StatelessWidget {
  const FindRideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Find Ride")),
      body: ListView.builder(
        itemCount: 5, // mock data, later replace with API/DB
        itemBuilder: (context, index) {
          return Card(
            margin: const EdgeInsets.all(8),
            child: ListTile(
              leading: const Icon(Icons.directions_car),
              title: Text("Ride ${index + 1}"),
              subtitle: const Text("From Kochi to Thrissur"),
              trailing: ElevatedButton(
                onPressed: () {
                  Navigator.pushNamed(context, '/group_map');
                },
                child: const Text("Join"),
              ),
            ),
          );
        },
      ),
    );
  }
}
