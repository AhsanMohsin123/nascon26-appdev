import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/sync_provider.dart';
import '../widgets/sync_banner.dart';
import '../app_theme.dart';
import 'fixtures_screen.dart';
import 'standings_screen.dart';
import 'store_screen.dart';
import 'club_screen.dart';
import 'sync_screen.dart';
import 'dashboard_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  late final List<_Tab> _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = [
      _Tab(
        label: 'Home',
        icon: Icons.dashboard_rounded,
        screen: DashboardScreen(onNavigateTab: (idx) => setState(() => _currentIndex = idx)),
      ),
      _Tab(label: 'Fixtures', icon: Icons.sports, screen: const FixturesScreen()),
      _Tab(label: 'Standings', icon: Icons.leaderboard, screen: const StandingsScreen()),
      _Tab(label: 'Store', icon: Icons.store, screen: const StoreScreen()),
      _Tab(label: 'Club', icon: Icons.groups, screen: const ClubScreen()),
      _Tab(label: 'Sync', icon: Icons.sync, screen: const SyncScreen()),
    ];
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SyncProvider>().checkConnectivity();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final sync = context.watch<SyncProvider>();
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          const Icon(Icons.sports, color: Colors.white, size: 22),
          const SizedBox(width: 8),
          const Text("NaSCon '26"),
        ]),
        actions: [
          const SyncIndicatorChip(),
          _roleChip(auth.user?.role ?? 'viewer'),
          PopupMenuButton(
            icon: const Icon(Icons.more_vert),
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'logout', child: Row(children: [Icon(Icons.logout, size: 16), SizedBox(width: 8), Text('Logout')])),
            ],
            onSelected: (v) {
              if (v == 'logout') {
                showDialog(
                  context: context,
                  builder: (_) => AlertDialog(
                    title: const Text('Logout'),
                    content: const Text('Are you sure you want to logout?'),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                      ElevatedButton(onPressed: () { Navigator.pop(context); auth.logout(); }, child: const Text('Logout')),
                    ],
                  ),
                );
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          const SyncBanner(),
          Expanded(child: _tabs[_currentIndex].screen),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppTheme.primary,
        unselectedItemColor: Colors.grey,
        items: _tabs.map((t) => BottomNavigationBarItem(
          icon: Badge(
            isLabelVisible: t.label == 'Sync' && sync.pendingCount > 0,
            label: Text('${sync.pendingCount}'),
            child: Icon(t.icon),
          ),
          label: t.label,
        )).toList(),
      ),
    );
  }

  Widget _roleChip(String role) {
    final colors = {
      'super_admin': Colors.purple,
      'league_organizer': Colors.blue,
      'club_manager': Colors.teal,
      'player': Colors.green,
      'viewer': Colors.grey,
    };
    final labels = {
      'super_admin': 'Admin',
      'league_organizer': 'Organizer',
      'club_manager': 'Manager',
      'player': 'Player',
      'viewer': 'Viewer',
    };
    final color = colors[role] ?? Colors.grey;
    return Container(
      margin: const EdgeInsets.only(right: 4),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12)),
      child: Text(labels[role] ?? role, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
    );
  }
}

class _Tab {
  final String label;
  final IconData icon;
  final Widget screen;
  const _Tab({required this.label, required this.icon, required this.screen});
}
