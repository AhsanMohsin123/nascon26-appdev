import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// FR-3.3 4-way co-stream split view, backed by POST /audit/v1/costream/session
/// and the moderation engine (POST /audit/v1/moderation/test) for chat.
class CostreamScreen extends StatefulWidget {
  const CostreamScreen({super.key});
  @override
  State<CostreamScreen> createState() => _CostreamScreenState();
}

class _CostreamScreenState extends State<CostreamScreen> {
  static const _all = ['player-alpha-1', 'player-alpha-2', 'player-beta-1', 'player-beta-2'];
  List<String> _participants = List.of(_all);
  String _layout = 'grid_4';
  Map<String, dynamic>? _session;
  final Set<String> _muted = {};
  String? _spotlight;
  final List<Map<String, dynamic>> _chat = [];
  final _chatCtrl = TextEditingController();
  String? _error;
  bool _busy = false;

  @override
  void initState() { super.initState(); _start(drop: false); }

  Future<void> _start({required bool drop}) async {
    setState(() { _busy = true; _error = null; });
    try {
      final r = await ApiService.post('/audit/v1/costream/session', {
        'session_id': 'cs-session-101',
        'host_player_id': _participants.first,
        'participants': _participants,
        'layout': _layout,
        'simulate_host_drop': drop,
      });
      setState(() {
        _session = r;
        _participants = List<String>.from(r['active_participants']);
      });
      if (drop && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(r['status'] == 'terminated' ? 'Host dropped, session terminated' : 'Host dropped → ${r['active_host']} is now host'),
        ));
      }
    } on ApiException catch (e) {
      setState(() => _error = '${e.code}: ${e.message}');
    } catch (_) {
      setState(() => _error = 'Server unreachable.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _send() async {
    final text = _chatCtrl.text.trim();
    if (text.isEmpty) return;
    _chatCtrl.clear();
    try {
      final r = await ApiService.post('/audit/v1/moderation/test', {
        'chat_room_id': _session?['chat_room_id'] ?? 'chat-cs-session-101',
        'incoming_messages': [
          {'message_id': 'm-${DateTime.now().millisecondsSinceEpoch}', 'sender': 'me', 'text': text},
        ],
        'check_dlq': false,
      });
      final filtered = List<Map<String, dynamic>>.from(r['filtered_messages']);
      setState(() {
        if (filtered.isEmpty) {
          _chat.add({'text': 'Message blocked: flood/spam', 'system': true});
        } else {
          _chat.addAll(filtered);
        }
      });
    } catch (_) {
      setState(() => _chat.add({'text': 'Could not send (server unreachable)', 'system': true}));
    }
  }

  @override
  Widget build(BuildContext context) {
    final host = _session?['active_host'];
    final tiles = _spotlight != null ? [_spotlight!] : _participants;
    final cols = _spotlight != null || _layout == 'solo' ? 1 : 2;
    return Scaffold(
      appBar: AppBar(title: const Text('Co-Stream · cs-session-101')),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'grid_2', label: Text('Grid 2')),
              ButtonSegment(value: 'grid_4', label: Text('Grid 4')),
              ButtonSegment(value: 'spotlight', label: Text('Spotlight')),
            ],
            selected: {_layout},
            onSelectionChanged: (s) {
              setState(() {
                _layout = s.first;
                _spotlight = null;
                _participants = _layout == 'grid_2' ? _participants.take(2).toList() : List.of(_all);
              });
              _start(drop: false);
            },
          ),
        ),
        if (_error != null) Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
        AspectRatio(
          aspectRatio: 16 / 10,
          child: GridView.count(
            crossAxisCount: cols,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            mainAxisSpacing: 6, crossAxisSpacing: 6,
            childAspectRatio: cols == 1 ? 16 / 9 : 16 / 11,
            physics: const NeverScrollableScrollPhysics(),
            children: tiles.map((p) => _tile(p, p == host)).toList(),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          child: OutlinedButton.icon(
            onPressed: _busy ? null : () => _start(drop: true),
            icon: const Icon(Icons.power_off_rounded),
            label: const Text('Simulate host disconnect'),
          ),
        ),
        const Divider(),
        Expanded(
          child: ListView(padding: const EdgeInsets.symmetric(horizontal: 12), children: _chat.map((m) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Text(
              m['system'] == true ? m['text'] : '${m['sender']}: ${m['text']}${m['flagged'] == true ? '  (filtered)' : ''}',
              style: TextStyle(color: m['system'] == true || m['flagged'] == true ? Colors.orange : null),
            ),
          )).toList()),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Row(children: [
              Expanded(child: TextField(controller: _chatCtrl, onSubmitted: (_) => _send(), decoration: const InputDecoration(hintText: 'Chat with the audience'))),
              IconButton.filled(onPressed: _send, icon: const Icon(Icons.send_rounded)),
            ]),
          ),
        ),
      ]),
    );
  }

  Widget _tile(String p, bool isHost) {
    final muted = _muted.contains(p);
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF12274A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isHost ? Colors.amber : Colors.transparent, width: 2),
      ),
      child: Stack(children: [
        const Center(child: Icon(Icons.person_rounded, color: Colors.white38, size: 40)),
        Positioned(left: 6, bottom: 6, child: Text('${isHost ? '★ ' : ''}$p', style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700))),
        Positioned(
          right: 0, top: 0,
          child: PopupMenuButton<String>(
            icon: Icon(muted ? Icons.mic_off_rounded : Icons.more_vert, color: Colors.white, size: 18),
            onSelected: (a) => setState(() {
              if (a == 'mute') { muted ? _muted.remove(p) : _muted.add(p); }
              if (a == 'spotlight') _spotlight = _spotlight == p ? null : p;
              if (a == 'kick' && _participants.length > 1) {
                _participants.remove(p);
                _start(drop: false);
              }
            }),
            itemBuilder: (_) => [
              PopupMenuItem(value: 'mute', child: Text(muted ? 'Unmute' : 'Mute')),
              PopupMenuItem(value: 'spotlight', child: Text(_spotlight == p ? 'Exit spotlight' : 'Spotlight')),
              const PopupMenuItem(value: 'kick', child: Text('Kick')),
            ],
          ),
        ),
      ]),
    );
  }
}
