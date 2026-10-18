import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/score_bus.dart';

/// Organizer tool: create a match and record scoring events via POST /audit/v1/events.
class MatchControlScreen extends StatefulWidget {
  const MatchControlScreen({super.key});
  @override
  State<MatchControlScreen> createState() => _MatchControlScreenState();
}

class _MatchControlScreenState extends State<MatchControlScreen> {
  static const _clubs = ['club-alpha-1', 'club-alpha-2', 'club-beta-1'];
  String _home = 'club-alpha-1';
  String _away = 'club-alpha-2';
  String _matchId = 'match-m1';
  Map<String, dynamic>? _score;
  String? _error;
  bool _busy = false;

  @override
  void initState() { super.initState(); _refresh(); }

  String _eid() => 'evt-${DateTime.now().microsecondsSinceEpoch}';

  Future<void> _event(String type, Map<String, dynamic> payload, {String? matchId}) =>
      ApiService.appendEvent({'event_id': _eid(), 'match_id': matchId ?? _matchId, 'type': type, 'payload': payload});

  Future<void> _run(Future<void> Function() f) async {
    setState(() { _busy = true; _error = null; });
    try {
      await f();
      await _refresh();
    } on ApiException catch (e) {
      setState(() => _error = '${e.code}: ${e.message}');
    } catch (_) {
      setState(() => _error = 'Server unreachable.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _refresh() async {
    try {
      final s = await ApiService.getScore(_matchId);
      if (mounted) setState(() => _score = s);
    } catch (_) {}
  }

  Future<void> _createMatch() => _run(() async {
        if (_home == _away) throw ApiException(code: 'VALIDATION_ERROR', message: 'Pick two different clubs', statusCode: 400);
        final id = 'match-${DateTime.now().millisecondsSinceEpoch}';
        await _event('match_init', {'sport_id': 'football', 'home_team_id': _home, 'away_team_id': _away, 'league_id': 'league-alpha-1'}, matchId: id);
        await _event('match_start', {}, matchId: id);
        _matchId = id;
        ScoreBus.watch(id);
      });

  Future<void> _goal(String team) => _run(() => _event('score', {'team_id': team, 'event_type': 'goal'}));

  @override
  Widget build(BuildContext context) {
    final s = _score;
    final status = s?['status'] ?? '—';
    return Scaffold(
      appBar: AppBar(title: const Text('Match Control')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Card(
          margin: EdgeInsets.zero,
          child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('New football match', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: _clubPicker('Home', _home, (v) => setState(() => _home = v))),
              const SizedBox(width: 8),
              Expanded(child: _clubPicker('Away', _away, (v) => setState(() => _away = v))),
            ]),
            const SizedBox(height: 12),
            ElevatedButton.icon(onPressed: _busy ? null : _createMatch, icon: const Icon(Icons.add_rounded), label: const Text('Create & start match')),
          ])),
        ),
        const SizedBox(height: 16),
        Card(
          margin: EdgeInsets.zero,
          child: Padding(padding: const EdgeInsets.all(16), child: Column(children: [
            Text(_matchId, style: const TextStyle(fontWeight: FontWeight.w700)),
            Text('Status: $status'),
            const SizedBox(height: 12),
            Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
              _side(s?['home']?['team_id'] ?? '-', s?['home']?['score']),
              const Text('vs', style: TextStyle(fontSize: 18)),
              _side(s?['away']?['team_id'] ?? '-', s?['away']?['score']),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: ElevatedButton(onPressed: _busy || s == null ? null : () => _goal(s['home']['team_id']), child: const Text('+1 Home'))),
              const SizedBox(width: 8),
              Expanded(child: ElevatedButton(onPressed: _busy || s == null ? null : () => _goal(s['away']['team_id']), child: const Text('+1 Away'))),
            ]),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: _busy || status != 'in_progress' ? null : () => _run(() => _event('match_end', {})),
              style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(46)),
              child: const Text('End match'),
            ),
          ])),
        ),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
        const SizedBox(height: 12),
        const Text('Every change is saved on the server; all signed-in phones get a score banner within ~3 seconds.',
            style: TextStyle(color: Colors.grey)),
      ]),
    );
  }

  Widget _clubPicker(String label, String value, ValueChanged<String> onChanged) => DropdownButtonFormField<String>(
        initialValue: value,
        isExpanded: true,
        decoration: InputDecoration(labelText: label),
        items: _clubs.map((c) => DropdownMenuItem(value: c, child: Text(c, overflow: TextOverflow.ellipsis))).toList(),
        onChanged: (v) => onChanged(v!),
      );

  Widget _side(String team, dynamic score) => Column(children: [
        Text('${score ?? '-'}', style: const TextStyle(fontSize: 40, fontWeight: FontWeight.w900)),
        Text(team, style: const TextStyle(fontSize: 12)),
      ]);
}
