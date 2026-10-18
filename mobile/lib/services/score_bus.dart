import 'dart:async';
import 'package:flutter/material.dart';
import 'api_service.dart';

final scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

/// Polls watched matches every 3s and pops a banner on any screen when a score changes.
/// Polling stands in for push until the server has a WebSocket/SSE channel.
class ScoreBus {
  static final Set<String> watched = {'match-m1'};
  static final Map<String, String> _last = {};
  static Timer? _timer;

  static void start() {
    _timer ??= Timer.periodic(const Duration(seconds: 3), (_) => _tick());
  }

  static void watch(String matchId) => watched.add(matchId);

  static Future<void> _tick() async {
    for (final id in watched.toList()) {
      try {
        final s = await ApiService.getScore(id);
        final line = '${s['home']['team_id']} ${s['home']['score']} - ${s['away']['score']} ${s['away']['team_id']}';
        final prev = _last[id];
        _last[id] = line;
        if (prev != null && prev != line) {
          scaffoldMessengerKey.currentState?.showSnackBar(SnackBar(
            content: Row(children: [
              const Icon(Icons.sports_score_rounded, color: Colors.white),
              const SizedBox(width: 10),
              Expanded(child: Text('Score update · $line (${s['status']})')),
            ]),
            duration: const Duration(seconds: 4),
          ));
        }
      } catch (_) {}
    }
  }
}
