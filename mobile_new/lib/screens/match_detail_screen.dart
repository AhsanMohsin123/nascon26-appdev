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
    final sport = _score!['sport_id'] ?? '';
    final List<String> eventTypes;
    if (sport == 'football') {
      eventTypes = ['goal'];
    } else if (sport == 'basketball') {
      eventTypes = ['free_throw', 'two_pointer', 'three_pointer'];
    } else if (sport == 'cricket') {
      eventTypes = ['single', 'two', 'four', 'six', 'wicket', 'wide', 'no_ball', 'dot_ball'];
    } else if (sport == 'esports') {
      eventTypes = ['round_win'];
    } else {
      eventTypes = ['goal'];
    }

    final home = _score!['home']['team_id'] as String;
    final away = _score!['away']['team_id'] as String;
    final status = _score!['status'] ?? 'upcoming';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        // Match control
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Chip(
            avatar: Icon(
              status == 'in_progress' ? Icons.play_circle : status == 'completed' ? Icons.check_circle : Icons.schedule,
              color: AppColors.statusColor(status), size: 18,
            ),
            label: Text(status.replaceAll('_', ' ').toUpperCase(),
                style: TextStyle(color: AppColors.statusColor(status), fontWeight: FontWeight.w700, fontSize: 12)),
          ),
        ]),
        const SizedBox(height: 12),
        if (status == 'upcoming')
          ElevatedButton.icon(
            onPressed: () => _matchControl('match_start', auth),
            icon: const Icon(Icons.play_arrow),
            label: const Text('Start Match'),
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.success),
          ),
        if (status == 'completed')
          const Center(child: Text('Match completed. Scores are final.', style: TextStyle(color: Colors.grey))),

        if (status == 'in_progress') ...[
          const Text('Tap to add points', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16), textAlign: TextAlign.center),
          const SizedBox(height: 14),
          // Two team columns with score buttons
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(child: _teamScorePanel(home, '${_score!['home']['score']}', eventTypes, auth)),
            Container(width: 1, height: 220, color: Colors.grey.shade300),
            Expanded(child: _teamScorePanel(away, '${_score!['away']['score']}', eventTypes, auth)),
          ]),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _matchControl('match_end', auth),
              icon: const Icon(Icons.stop_circle, color: Colors.red),
              label: const Text('End Match', style: TextStyle(color: Colors.red)),
            ),
          ),
        ],
      ]),
    );
  }

  Widget _teamScorePanel(String team, String score, List<String> eventTypes, AuthProvider auth) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 8),
    child: Column(children: [
      Text(team, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15), textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis),
      const SizedBox(height: 4),
      Text(score, style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w900, color: AppTheme.primary)),
      const SizedBox(height: 10),
      ...eventTypes.map((ev) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => _appendScoreEvent(team, ev, auth),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 10),
              backgroundColor: _eventColor('score').withOpacity(0.85),
            ),
            child: Text('+ ${ev.replaceAll('_', ' ')}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
          ),
        ),
      )),
    ]),
  );

  Future<void> _matchControl(String type, AuthProvider auth) async {
    final eventId = 'evt-${DateTime.now().millisecondsSinceEpoch}';
    final payload = {'event_id': eventId, 'match_id': widget.matchId, 'type': type, 'payload': {}};
    try {
      await ApiService.appendEvent(payload);
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(type == 'match_start' ? 'Match started!' : 'Match ended!'),
          backgroundColor: AppTheme.success));
      }
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.userMessage), backgroundColor: Colors.red));
    }
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
