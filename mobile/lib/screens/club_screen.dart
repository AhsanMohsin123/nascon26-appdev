import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/sync_provider.dart';
import '../services/api_service.dart';
import '../app_theme.dart';
import 'roster_screen.dart';

class ClubScreen extends StatefulWidget {
  const ClubScreen({super.key});
  @override
  State<ClubScreen> createState() => _ClubScreenState();
}

class _ClubScreenState extends State<ClubScreen> {
  bool _loading = false;
  List<Map<String, dynamic>> _players = [];
  String _clubId = 'club-alpha-1';

  @override
  void initState() { super.initState(); _loadPlayers(); }

  Future<void> _loadPlayers() async {
    setState(() => _loading = true);
    try {
      // Load roster history as proxy for players
      await Future.delayed(const Duration(milliseconds: 300));
      setState(() {
        _players = [
          {'player_id': 'player-alpha-1', 'name': 'Ali Hassan', 'position': 'gk', 'role': 'captain'},
          {'player_id': 'player-alpha-2', 'name': 'Bilal Ahmed', 'position': 'df', 'role': 'starter'},
        ];
        _loading = false;
      });
    } catch (_) { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Club Profile'),
        actions: [
          if (auth.user?.isManager == true)
            IconButton(icon: const Icon(Icons.group_add), tooltip: 'Manage Roster',
                onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RosterScreen()))),
        ],
      ),
      body: ListView(
        children: [
          _clubHeader(),
          _infoSection(),
          _rosterSection(auth),
        ],
      ),
    );
  }

  Widget _clubHeader() => Container(
    color: AppTheme.primary,
    padding: const EdgeInsets.all(24),
    child: Column(children: [
      Container(width: 80, height: 80,
        decoration: BoxDecoration(color: Colors.white, shape: BoxShape.circle),
        child: Center(child: Text(_clubId.split('-').last.toUpperCase(),
            style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w900, fontSize: 28)))),
      const SizedBox(height: 12),
      Text('Alpha FC', style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
      const Text('Alpha Sports Tenant', style: TextStyle(color: Colors.white70, fontSize: 13)),
      const SizedBox(height: 8),
      const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.location_on, color: Colors.white70, size: 14),
        SizedBox(width: 4),
        Text('Taxila Sports Complex', style: TextStyle(color: Colors.white70, fontSize: 12)),
      ]),
    ]),
  );

  Widget _infoSection() => Card(
    margin: const EdgeInsets.all(12),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Club Info', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
        const SizedBox(height: 12),
        _infoRow(Icons.badge_outlined, 'Club ID', _clubId),
        _infoRow(Icons.business, 'Tenant', 'tenant-alpha (Alpha Sports)'),
        _infoRow(Icons.sports_soccer, 'Home Sport', 'Football'),
        _infoRow(Icons.emoji_events, 'League', 'league-alpha-1'),
        const Divider(height: 24),
        const Text('Staff', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        const SizedBox(height: 8),
        _infoRow(Icons.person, 'Manager', 'Club Manager (manager@nascon.test)'),
        _infoRow(Icons.sports, 'Coach', 'Head Coach'),
        _infoRow(Icons.medical_services, 'Physio', 'Team Physio'),
      ]),
    ),
  );

  Widget _infoRow(IconData icon, String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(children: [
      Icon(icon, size: 18, color: AppTheme.primary),
      const SizedBox(width: 10),
      Text('$label: ', style: const TextStyle(color: Colors.grey, fontSize: 13)),
      Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
    ]),
  );

  Widget _rosterSection(AuthProvider auth) => Card(
    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const Text('Active Roster', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          Text('${_players.length} players', style: const TextStyle(color: Colors.grey, fontSize: 12)),
        ]),
        const SizedBox(height: 12),
        if (_loading) const Center(child: CircularProgressIndicator())
        else if (_players.isEmpty) const Center(child: Text('No players registered', style: TextStyle(color: Colors.grey)))
        else ..._players.map(_playerTile),
        if (auth.user?.isManager == true) ...[
          const SizedBox(height: 12),
          SizedBox(width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RosterScreen())),
              icon: const Icon(Icons.manage_accounts),
              label: const Text('Manage Roster'),
            )),
        ],
      ]),
    ),
  );

  Widget _playerTile(Map<String, dynamic> p) => ListTile(
    leading: CircleAvatar(
      backgroundColor: AppTheme.primary.withOpacity(0.1),
      child: Text(p['name'].toString().substring(0, 1).toUpperCase(),
          style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w700)),
    ),
    title: Text(p['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
    subtitle: Text('${p['position']?.toString().toUpperCase() ?? ''} • ${p['role'] ?? ''}'),
    trailing: _roleBadge(p['role'] ?? ''),
  );

  Widget _roleBadge(String role) {
    Color c;
    switch (role) {
      case 'captain': c = AppTheme.accent; break;
      case 'vice_captain': c = AppTheme.primary; break;
      case 'starter': c = AppTheme.success; break;
      default: c = Colors.grey;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: c.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
      child: Text(role.replaceAll('_', ' '), style: TextStyle(color: c, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
