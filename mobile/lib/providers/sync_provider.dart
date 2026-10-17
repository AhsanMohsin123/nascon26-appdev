import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:uuid/uuid.dart';
import '../services/api_service.dart';
import '../services/local_db.dart';

enum SyncStatus { online, offline, syncing }

class SyncProvider extends ChangeNotifier {
  SyncStatus _status = SyncStatus.online;
  int _pendingCount = 0;
  List<Map<String, dynamic>> _pendingActions = [];
  static const _deviceId = 'nascon26-mobile-device';
  static const _uuid = Uuid();

  SyncStatus get status => _status;
  int get pendingCount => _pendingCount;
  List<Map<String, dynamic>> get pendingActions => _pendingActions;
  bool get isOffline => _status == SyncStatus.offline;

  SyncProvider() {
    Connectivity().onConnectivityChanged.listen((result) async {
      final online = result.any((r) => r != ConnectivityResult.none);
      if (online && _status == SyncStatus.offline) {
        _status = SyncStatus.online;
        notifyListeners();
        await sync();
      } else if (!online) {
        _status = SyncStatus.offline;
        notifyListeners();
      }
    });
    _refreshPending();
  }

  Future<void> checkConnectivity() async {
    final online = await ApiService.checkHealth();
    if (!online && _status != SyncStatus.offline) {
      _status = SyncStatus.offline;
      notifyListeners();
    } else if (online && _status == SyncStatus.offline) {
      _status = SyncStatus.online;
      notifyListeners();
    }
  }

  Future<void> enqueue(String type, Map<String, dynamic> payload, int baseVersion) async {
    final action = {
      'action_id': _uuid.v4(),
      'type': type,
      'queued_at': DateTime.now().toUtc().toIso8601String().replaceFirst(RegExp(r'\.\d+'), '').endsWith('Z')
          ? DateTime.now().toUtc().toIso8601String().replaceFirst(RegExp(r'\.\d+'), '')
          : '${DateTime.now().toUtc().toIso8601String().replaceFirst(RegExp(r'\.\d+'), '')}Z',
      'base_version': baseVersion,
      'payload': payload,
    };
    await LocalDb.enqueueAction(action);
    await _refreshPending();
  }

  Future<List<Map<String, dynamic>>> sync() async {
    final pending = await LocalDb.getPendingActions();
    if (pending.isEmpty) return [];
    _status = SyncStatus.syncing;
    notifyListeners();

    try {
      final result = await ApiService.offlineSync(_deviceId, pending);
      final results = result['results'] as List? ?? [];
      for (final r in results) {
        if (r['status'] == 'applied' || r['status'] == 'duplicate') {
          await LocalDb.markActionSynced(r['action_id'] as String);
        }
      }
      await LocalDb.clearSynced();
      await _refreshPending();
      _status = SyncStatus.online;
      notifyListeners();
      return results.cast<Map<String, dynamic>>();
    } catch (_) {
      _status = SyncStatus.online;
      notifyListeners();
      return [];
    }
  }

  Future<void> _refreshPending() async {
    _pendingActions = await LocalDb.getPendingActions();
    _pendingCount = _pendingActions.length;
    notifyListeners();
  }
}
