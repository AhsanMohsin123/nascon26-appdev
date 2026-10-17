import 'package:flutter/foundation.dart';
import 'dart:convert';

enum SyncStatus { online, offline, syncing }

class PendingAction {
  final String actionId;
  final String type;
  final String queuedAt;
  final int baseVersion;
  final Map<String, dynamic> payload;

  PendingAction({
    required this.actionId,
    required this.type,
    required this.queuedAt,
    required this.baseVersion,
    required this.payload,
  });

  Map<String, dynamic> toJson() => {
        'action_id': actionId,
        'type': type,
        'queued_at': queuedAt,
        'base_version': baseVersion,
        'payload': payload,
      };
}

class SyncService extends ChangeNotifier {
  SyncStatus _status = SyncStatus.online;
  final List<PendingAction> _queue = [];

  SyncStatus get status => _status;
  List<PendingAction> get queue => List.unmodifiable(_queue);
  int get pendingCount => _queue.length;

  void setOffline() {
    _status = SyncStatus.offline;
    notifyListeners();
  }

  void setOnline() {
    _status = SyncStatus.online;
    notifyListeners();
  }

  void enqueue(PendingAction action) {
    _queue.add(action);
    notifyListeners();
  }

  Future<void> sync(String baseUrl, String? token) async {
    if (_queue.isEmpty || token == null) return;
    _status = SyncStatus.syncing;
    notifyListeners();

    // POST /audit/v1/offline-sync
    _status = SyncStatus.online;
    notifyListeners();
  }
}
