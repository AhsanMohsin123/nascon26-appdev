import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/local_db.dart';
import '../providers/auth_provider.dart';
import '../providers/sync_provider.dart';
import '../app_theme.dart';

class MatchDetailScreen extends StatefulWidget {
  final String matchId;
  const MatchDetailScreen({super.key, required this.matchId});
  @override
  State<MatchDetailScreen> createState() => _MatchDetailScreenState();
}

class _MatchDetailScreenState extends State<MatchDetailScreen> {
  Map<String, dynamic>? _score;
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getScore(widget.matchId);
      await LocalDb.cacheMatch(widget.matchId, data);
      setState(() { _score = data; _loading = false; });
    } catch (_) {
      final cached = await LocalDb.getMatch(widget.matchId);
      setState(() { _score = cached; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      appBar: AppBar(
        title: Text('Match: ${widget.matchId}'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _score == null
              ? const Center(child: Text('Match not found'))
              : Column(children: [
                  _scoreHeader(),
                  Expanded(
                    child: DefaultTabController(
                      length: auth.user?.isOrganizer == true ? 3 : 2,
                      child: Column(children: [
                        TabBar(tabs: [
                          const Tab(text: 'Timeline'),
                          const Tab(text: 'Stats'),
                          if (auth.user?.isOrganizer == true) const Tab(text: 'Score Event'),
                        ]),
                        Expanded(child: TabBarView(children: [
                          _timeline(),
                          _stats(),
                          if (auth.user?.isOrganizer == true) _scoreEntry(auth),
                        ])),
                      ]),
                    ),
                  ),
                ]),
    );
  }

  Widget _scoreHeader() {
    final home = _score!['home'] ?? {};
    final away = _score!['away'] ?? {};
    final status = _score!['status'] ?? 'upcoming';
    return Container(
      color: AppTheme.primary,
      padding: const EdgeInsets.all(20),
      child: Column(children: [
        _statusBadge(status),
        const SizedBox(height: 16),
        Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
          Expanded(child: Text(home['team_id'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18), textAlign: TextAlign.center)),
          Column(children: [
            Text('${home['score'] ?? 0}', style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.w900)),
            const Text('vs', style: TextStyle(color: Colors.white60, fontSize: 12)),
            Text('${away['score'] ?? 0}', style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.w900)),
          ]),
          Expanded(child: Text(away['team_id'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18), textAlign: TextAlign.center)),
        ]),
        if (_score!['outcome'] != 'pending') ...[
          const SizedBox(height: 8),
          Text(_outcomeText(), style: const TextStyle(color: Colors.white70, fontSize: 14)),
        ],
      ]),
    );
  }

  Widget _statusBadge(String status) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    decoration: BoxDecoration(color: AppColors.statusColor(status), borderRadius: BorderRadius.circular(20)),
    child: Text(status.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
  );

  String _outcomeText() {
    final outcome = _score!['outcome'] ?? '';
    final winner = _score!['winner_team_id'];
    switch (outcome) {
      case 'home_win': return '🏆 ${winner ?? "Home"} wins!';
      case 'away_win': return '🏆 ${winner ?? "Away"} wins!';
      case 'draw': return '🤝 Match drawn';
      default: return '';
    }
  }

  Widget _timeline() {
    final events = (_score?['events'] as List? ?? []).reversed.toList();
    if (events.isEmpty) return const Center(child: Text('No events yet', style: TextStyle(color: Colors.grey)));
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: events.length,
      itemBuilder: (_, i) {
        final ev = events[i] as Map<String, dynamic>;
        final type = ev['type'] ?? '';
        final compensated = ev['compensated'] == true;
        return Opacity(
          opacity: compensated ? 0.4 : 1.0,
          child: ListTile(
            leading: CircleAvatar(backgroundColor: _eventColor(type).withOpacity(0.15),
                child: Icon(_eventIcon(type), color: _eventColor(type), size: 18)),
            title: Text('${type.replaceAll('_', ' ')}${compensated ? ' [CANCELLED]' : ''}',
                style: TextStyle(fontWeight: FontWeight.w600, decoration: compensated ? TextDecoration.lineThrough : null)),
            subtitle: Text(_eventSubtitle(ev)),
            trailing: Text('#${ev['sequence']}', style: const TextStyle(color: Colors.grey, fontSize: 11)),
          ),
        );
      },
    );
  }

  Widget _stats() {
    final home = _score!['home'] ?? {};
    final away = _score!['away'] ?? {};
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(children: [
        _statRow('Score', '${home['score'] ?? 0}', '${away['score'] ?? 0}'),
        _statRow('Fair Play', '${home['fair_play'] ?? 0}', '${away['fair_play'] ?? 0}'),
        if (home['balls'] != null) ...[
          _statRow('Balls', '${home['balls']}', '${away['balls']}'),
          _statRow('Wickets', '${home['wickets']}', '${away['wickets']}'),
          _statRow('Overs', '${home['overs']}', '${away['overs']}'),
        ],
        const SizedBox(height: 16),
        _statRow('Sport', _score!['sport_id'] ?? '', ''),
        _statRow('League', _score!['league_id'] ?? '', ''),
      ]),
    );
  }

  Widget _statRow(String label, String home, String away) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Row(children: [
      Expanded(child: Text(home, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
      Expanded(child: Text(label, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey, fontSize: 13))),
      Expanded(child: Text(away, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
    ]),
  );

  Widget _scoreEntry(AuthProvider auth) {
    final eventTypes = <String>[];
    final sport = _score!['sport_id'] ?? '';
    if (sport == 'football') eventTypes.addAll(['goal']);
    else if (sport == 'basketball') eventTypes.addAll(['free_throw','two_pointer','three_pointer']);
    else if (sport == 'cricket') eventTypes.addAll(['dot_ball','single','two','four','six','wide','no_ball','wicket']);
    else if (sport == 'esports') eventTypes.addAll(['round_win']);

    final home = _score!['home']['team_id'] as String;
    final away = _score!['away']['team_id'] as String;
    String? selectedTeam = home;
    String? selectedEvent = eventTypes.isNotEmpty ? eventTypes.first : null;

    return StatefulBuilder(builder: (ctx, set2) => Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Append Score Event', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          value: selectedTeam,
          decoration: const InputDecoration(labelText: 'Team'),
          items: [home, away].map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
          onChanged: (v) => set2(() => selectedTeam = v),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          value: selectedEvent,
          decoration: const InputDecoration(labelText: 'Event Type'),
          items: eventTypes.map((e) => DropdownMenuItem(value: e, child: Text(e.replaceAll('_', ' ')))).toList(),
          onChanged: (v) => set2(() => selectedEvent = v),
        ),
        const SizedBox(height: 20),
        ElevatedButton.icon(
          onPressed: () => _appendScoreEvent(selectedTeam!, selectedEvent!, auth),
          icon: const Icon(Icons.add_circle_outline),
          label: const Text('Submit Event'),
        ),
      ]),
    ));
  }

  Future<void> _appendScoreEvent(String teamId, String eventType, AuthProvider auth) async {
    final sync = context.read<SyncProvider>();
    final currentVersion = (_score?['version'] as int?) ?? 0;
    final eventId = 'evt-${DateTime.now().millisecondsSinceEpoch}';
    final payload = {'event_id': eventId, 'match_id': widget.matchId, 'type': 'score',
        'payload': {'team_id': teamId, 'event_type': eventType}};
    if (sync.isOffline) {
      await sync.enqueue('score_event', payload, currentVersion);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Queued for sync when online'), backgroundColor: Colors.orange));
    } else {
      try {
        await ApiService.appendEvent(payload);
        _load();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Event recorded!'), backgroundColor: Colors.green));
      } on ApiException catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.userMessage), backgroundColor: Colors.red));
      }
    }
  }

  Color _eventColor(String type) {
    switch (type) {
      case 'score': return Colors.green;
      case 'match_start': return AppTheme.primary;
      case 'match_end': return Colors.grey;
      case 'compensation': return Colors.orange;
      case 'discipline': return Colors.red;
      default: return Colors.blueGrey;
    }
  }

  IconData _eventIcon(String type) {
    switch (type) {
      case 'score': return Icons.sports_score;
      case 'match_start': return Icons.play_arrow;
      case 'match_end': return Icons.stop;
      case 'compensation': return Icons.undo;
      case 'discipline': return Icons.warning_amber;
      default: return Icons.circle;
    }
  }

  String _eventSubtitle(Map<String, dynamic> ev) {
    final p = ev['payload'] as Map<String, dynamic>? ?? {};
    if (ev['type'] == 'score') return '${p['team_id']} — ${p['event_type']}'.replaceAll('_', ' ');
    if (ev['type'] == 'compensation') return 'Cancels event ${p['compensates']}';
    if (ev['type'] == 'discipline') return '${p['team_id']}: ${p['points']} pts';
    return '';
  }
}
