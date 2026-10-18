import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/score_bus.dart';
import '../app_theme.dart';
import 'match_detail_screen.dart';

/// Lists the matches this device tracks (seeded match-m1 plus any created in
/// Match Control), each read live from GET /audit/v1/score/{id}.
class FixturesScreen extends StatefulWidget {
  const FixturesScreen({super.key});
  @override
  State<FixturesScreen> createState() => _FixturesScreenState();
}

class _FixturesScreenState extends State<FixturesScreen> {
  List<Map<String, dynamic>> _matches = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    final out = <Map<String, dynamic>>[];
    for (final id in ScoreBus.watched.toList().reversed) {
      try {
        out.add(await ApiService.getScore(id));
      } catch (_) {}
    }
    if (!mounted) return;
    setState(() {
      _matches = out;
      _loading = false;
      if (out.isEmpty) _error = 'No matches reachable. Check the server connection.';
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          if (_error != null) Padding(padding: const EdgeInsets.all(24), child: Text(_error!, textAlign: TextAlign.center)),
          ..._matches.map((m) {
            final status = '${m['status']}';
            return Card(
              child: ListTile(
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MatchDetailScreen(matchId: m['match_id']))),
                leading: const Icon(Icons.sports_soccer_rounded),
                title: Text('${m['home']['team_id']}  ${m['home']['score']} - ${m['away']['score']}  ${m['away']['team_id']}',
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                subtitle: Text('${m['match_id']} · ${m['league_id']}'),
                trailing: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: AppColors.statusColor(status), borderRadius: BorderRadius.circular(12)),
                  child: Text(status.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                ),
              ),
            );
          }),
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text('Pull down to refresh.', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
          ),
        ],
      ),
    );
  }
}
