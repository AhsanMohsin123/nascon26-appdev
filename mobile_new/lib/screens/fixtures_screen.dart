import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/local_db.dart';
import '../providers/sync_provider.dart';
import '../app_theme.dart';
import 'match_detail_screen.dart';
import 'package:provider/provider.dart';

class FixturesScreen extends StatefulWidget {
  const FixturesScreen({super.key});
  @override
  State<FixturesScreen> createState() => _FixturesScreenState();
}

class _FixturesScreenState extends State<FixturesScreen> {
  List<Map<String, dynamic>> _matches = [];
  bool _loading = true;
  String? _error;
  String _leagueId = 'league-alpha-1';

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await ApiService.get('/audit/v1/matches/$_leagueId');
      final list = (data['matches'] as List? ?? []).map((m) => {
        'match_id': m['match_id'],
        'sport_id': m['sport_id'],
        'home_team_id': m['home']?['team_id'] ?? '',
        'away_team_id': m['away']?['team_id'] ?? '',
        'home_score': m['home']?['score'] ?? 0,
        'away_score': m['away']?['score'] ?? 0,
        'status': m['status'] ?? 'upcoming',
      }).toList().cast<Map<String, dynamic>>();
      setState(() { _matches = list; _loading = false; });
    } catch (e) {
      setState(() { _loading = false; _error = e is ApiException ? e.userMessage : 'Could not load fixtures'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fixtures'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.filter_list),
            onSelected: (v) { setState(() => _leagueId = v); _load(); },
            itemBuilder: (_) => const {
              'league-alpha-1': '⚽ Football League',
              'basketball-league': '🏀 Basketball League',
              'cricket-league': '🏏 Cricket League',
            }.entries.map((e) => PopupMenuItem(value: e.key, child: Text(e.value))).toList(),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _errorView()
              : _matchList(),
    );
  }

  Widget _errorView() => Center(
    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      const Icon(Icons.sports_soccer, size: 64, color: Colors.grey),
      const SizedBox(height: 16),
      const Text('No fixtures available', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Colors.grey)),
      const SizedBox(height: 8),
      Text(_error ?? '', style: const TextStyle(color: Colors.grey, fontSize: 13), textAlign: TextAlign.center),
      const SizedBox(height: 24),
      ElevatedButton.icon(onPressed: _load, icon: const Icon(Icons.refresh), label: const Text('Retry')),
    ]),
  );

  Widget _matchList() => _matches.isEmpty
      ? Center(
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            const Icon(Icons.sports_soccer, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('No matches yet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Colors.grey)),
            Text('League: $_leagueId', style: const TextStyle(color: Colors.grey)),
          ]),
        )
      : RefreshIndicator(
          onRefresh: _load,
          child: ListView.builder(
            itemCount: _matches.length,
            itemBuilder: (_, i) => _matchCard(_matches[i]),
          ),
        );

  Widget _matchCard(Map<String, dynamic> m) {
    final status = m['status'] ?? 'upcoming';
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MatchDetailScreen(matchId: m['match_id'] ?? ''))),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(children: [
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              _statusChip(status),
              Text(m['sport_id'] ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: Text(m['home_team_id'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16), textAlign: TextAlign.center)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                child: Text('${m['home_score'] ?? 0}  –  ${m['away_score'] ?? 0}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: AppTheme.primary)),
              ),
              Expanded(child: Text(m['away_team_id'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16), textAlign: TextAlign.center)),
            ]),
          ]),
        ),
      ),
    );
  }

  Widget _statusChip(String status) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    decoration: BoxDecoration(color: AppColors.statusColor(status).withOpacity(0.15), borderRadius: BorderRadius.circular(20)),
    child: Text(status.replaceAll('_', ' ').toUpperCase(),
        style: TextStyle(color: AppColors.statusColor(status), fontSize: 10, fontWeight: FontWeight.w700)),
  );
}
