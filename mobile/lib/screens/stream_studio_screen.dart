import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';

/// FR-3.2 broadcaster view, backed by POST /audit/v1/stream/key.
class StreamStudioScreen extends StatefulWidget {
  const StreamStudioScreen({super.key});
  @override
  State<StreamStudioScreen> createState() => _StreamStudioScreenState();
}

class _StreamStudioScreenState extends State<StreamStudioScreen> {
  String _playerId = 'player-alpha-1';
  Map<String, dynamic>? _key;
  bool _busy = false;
  String? _error;
  bool _scoreOverlay = true;
  bool _merchOverlay = true;

  Future<void> _call(String action) async {
    setState(() { _busy = true; _error = null; });
    try {
      final r = await ApiService.post('/audit/v1/stream/key', {'action': action, 'player_id': _playerId, 'label': 'Mobile Studio'});
      setState(() => _key = r);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Stream key ${action}d — status: ${r['status']}')));
      }
    } on ApiException catch (e) {
      setState(() => _error = '${e.code}: ${e.message}');
    } catch (_) {
      setState(() => _error = 'Server unreachable.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final active = _key?['status'] == 'active';
    return Scaffold(
      appBar: AppBar(title: const Text('Stream Studio')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        AspectRatio(
          aspectRatio: 16 / 9,
          child: Container(
            decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(16)),
            child: Stack(children: [
              Center(child: Icon(active ? Icons.videocam_rounded : Icons.videocam_off_rounded, color: Colors.white54, size: 56)),
              Positioned(top: 10, left: 10, child: _pill(active ? 'LIVE' : 'OFFLINE', active ? Colors.red : Colors.grey)),
              if (_scoreOverlay) Positioned(top: 10, right: 10, child: _pill('Alpha 1 - 0 Alpha 2', Colors.black54)),
              if (_merchOverlay) Positioned(bottom: 10, left: 10, child: _pill('Jersey 001 · PKR 4,500', const Color(0xFF2D5A9E))),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: _playerId,
          decoration: const InputDecoration(labelText: 'Broadcaster'),
          items: const ['player-alpha-1', 'player-alpha-2', 'player-beta-1', 'player-beta-2']
              .map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
          onChanged: (v) => setState(() { _playerId = v!; _key = null; }),
        ),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: ElevatedButton.icon(onPressed: _busy ? null : () => _call('generate'), icon: const Icon(Icons.key_rounded), label: const Text('Generate'))),
          const SizedBox(width: 8),
          Expanded(child: OutlinedButton.icon(onPressed: _busy ? null : () => _call('rotate'), icon: const Icon(Icons.autorenew_rounded), label: const Text('Rotate'))),
        ]),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: _busy ? null : () => _call('revoke'),
          style: OutlinedButton.styleFrom(foregroundColor: Colors.red, minimumSize: const Size.fromHeight(48)),
          icon: const Icon(Icons.block_rounded), label: const Text('Revoke (cuts ingest)'),
        ),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
        if (_key != null) Card(
          margin: const EdgeInsets.only(top: 16),
          child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _row('Status', '${_key!['status']}'),
            _row('Stream key', '${_key!['stream_key']}', copy: true),
            _row('RTMP', '${_key!['ingest_endpoints']?['rtmp'] ?? '—'}', copy: true),
            _row('WHIP', '${_key!['ingest_endpoints']?['webrtc'] ?? '—'}', copy: true),
            _row('HLS playback', '${_key!['playback_url'] ?? '—'}', copy: true),
            _row('Signature', '${(_key!['signature'] as String).substring(0, 16)}…'),
          ])),
        ),
        const SizedBox(height: 8),
        SwitchListTile(value: _scoreOverlay, onChanged: (v) => setState(() => _scoreOverlay = v), title: const Text('Live score overlay'), activeThumbColor: scheme.primary),
        SwitchListTile(value: _merchOverlay, onChanged: (v) => setState(() => _merchOverlay = v), title: const Text('Pinned merchandise overlay'), activeThumbColor: scheme.primary),
      ]),
    );
  }

  Widget _pill(String t, Color c) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(color: c, borderRadius: BorderRadius.circular(20)),
        child: Text(t, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
      );

  Widget _row(String k, String v, {bool copy = false}) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 100, child: Text(k, style: const TextStyle(fontWeight: FontWeight.w700))),
          Expanded(child: Text(v, style: const TextStyle(fontSize: 12))),
          if (copy && v != '—') InkWell(
            onTap: () { Clipboard.setData(ClipboardData(text: v)); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Copied'))); },
            child: const Icon(Icons.copy_rounded, size: 16),
          ),
        ]),
      );
}
