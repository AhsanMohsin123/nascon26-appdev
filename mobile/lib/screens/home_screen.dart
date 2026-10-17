import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/sync_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  static const _tabs = ['Fixtures', 'Standings', 'Store', 'Club'];

  @override
  Widget build(BuildContext context) {
    final sync = context.watch<SyncService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('NaSCon \'26'),
        actions: [
          _SyncIndicator(status: sync.status, pendingCount: sync.pendingCount),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => context.read<AuthService>().logout(),
          ),
        ],
      ),
      body: _buildTab(_currentIndex),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.sports), label: 'Fixtures'),
          BottomNavigationBarItem(icon: Icon(Icons.leaderboard), label: 'Standings'),
          BottomNavigationBarItem(icon: Icon(Icons.store), label: 'Store'),
          BottomNavigationBarItem(icon: Icon(Icons.group), label: 'Club'),
        ],
      ),
    );
  }

  Widget _buildTab(int index) {
    switch (index) {
      case 0: return const Center(child: Text('Fixtures — coming soon'));
      case 1: return const Center(child: Text('Standings — coming soon'));
      case 2: return const Center(child: Text('Store — coming soon'));
      case 3: return const Center(child: Text('Club Profile — coming soon'));
      default: return const SizedBox();
    }
  }
}

class _SyncIndicator extends StatelessWidget {
  final SyncStatus status;
  final int pendingCount;

  const _SyncIndicator({required this.status, required this.pendingCount});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;
    String label;

    switch (status) {
      case SyncStatus.online:
        icon = Icons.cloud_done;
        color = Colors.green;
        label = 'Online';
        break;
      case SyncStatus.offline:
        icon = Icons.cloud_off;
        color = Colors.orange;
        label = 'Offline${pendingCount > 0 ? " ($pendingCount)" : ""}';
        break;
      case SyncStatus.syncing:
        icon = Icons.sync;
        color = Colors.blue;
        label = 'Syncing';
        break;
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 12)),
        ],
      ),
    );
  }
}
