import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/sync_provider.dart';
import '../providers/theme_provider.dart';
import '../widgets/sync_banner.dart';
import '../app_theme.dart';
import 'fixtures_screen.dart';
import 'standings_screen.dart';
import 'store_screen.dart';
import 'club_screen.dart';
import 'sync_screen.dart';
import 'dashboard_screen.dart';
import 'qr_scan_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final _pageController = PageController();

  late final List<_Tab> _tabs;

  void _goTo(int i) {
    setState(() => _currentIndex = i);
    _pageController.animateToPage(i, duration: const Duration(milliseconds: 320), curve: Curves.easeOutCubic);
  }

  @override
  void dispose() { _pageController.dispose(); super.dispose(); }

  @override
  void initState() {
    super.initState();
    _tabs = [
      _Tab(
        label: 'Home',
        icon: Icons.dashboard_rounded,
        screen: DashboardScreen(onNavigateTab: _goTo),
      ),
      _Tab(label: 'Scan', icon: Icons.qr_code_scanner, screen: const QrScanScreen()),
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
        titleSpacing: 12,
        title: const Text("NaSCon '26", overflow: TextOverflow.ellipsis),
        actions: [
          const SyncIndicatorChip(),
          _roleChip(auth.user?.role ?? 'viewer'),
          IconButton(
            tooltip: 'Toggle light/dark mode',
            onPressed: () => context.read<ThemeProvider>().toggle(),
            icon: AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              transitionBuilder: (c, a) => RotationTransition(turns: a, child: c),
              child: Icon(
                context.watch<ThemeProvider>().isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
                key: ValueKey(context.watch<ThemeProvider>().isDark),
              ),
            ),
          ),
          PopupMenuButton(
            icon: const Icon(Icons.more_vert),
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'feedback', child: Row(children: [Icon(Icons.feedback_outlined, size: 16), SizedBox(width: 8), Text('Send feedback')])),
              const PopupMenuItem(value: 'logout', child: Row(children: [Icon(Icons.logout, size: 16), SizedBox(width: 8), Text('Logout')])),
            ],
            onSelected: (v) {
              if (v == 'feedback') {
                _showFeedback(context, _tabs[_currentIndex].label, auth.user?.role ?? 'viewer');
              }
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
          Expanded(
            child: PageView(
              controller: _pageController,
              onPageChanged: (i) => setState(() => _currentIndex = i),
              children: _tabs.map((t) => t.screen).toList(),
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: _goTo,
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

  void _showFeedback(BuildContext context, String page, String role) {
    final ctrl = TextEditingController();
    int rating = 0;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (sheetCtx) => StatefulBuilder(
        builder: (sheetCtx, setSheet) => Padding(
          padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(sheetCtx).viewInsets.bottom + 20),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Feedback on "$page"', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            Text('Signed in as $role', style: TextStyle(color: Theme.of(sheetCtx).colorScheme.outline)),
            const SizedBox(height: 12),
            Row(children: List.generate(5, (i) => IconButton(
              onPressed: () => setSheet(() => rating = i + 1),
              icon: Icon(i < rating ? Icons.star_rounded : Icons.star_outline_rounded, color: Colors.amber, size: 32),
            ))),
            TextField(controller: ctrl, maxLines: 3, decoration: const InputDecoration(hintText: 'What works, what doesn\'t?')),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(sheetCtx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Thanks! Feedback for $page saved (${rating > 0 ? '$rating★' : 'no rating'}).')),
                );
              },
              child: const Text('Submit'),
            ),
          ]),
        ),
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
