import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class LocalDb {
  static Database? _db;

  static Future<Database> get db async {
    _db ??= await _open();
    return _db!;
  }

  static Future<Database> _open() async {
    final path = join(await getDatabasesPath(), 'nascon26.db');
    return openDatabase(path, version: 1, onCreate: (db, v) async {
      await db.execute('''CREATE TABLE cached_matches(
        id TEXT PRIMARY KEY, data TEXT, cached_at INTEGER)''');
      await db.execute('''CREATE TABLE cached_standings(
        league_id TEXT PRIMARY KEY, data TEXT, cached_at INTEGER)''');
      await db.execute('''CREATE TABLE cached_clubs(
        id TEXT PRIMARY KEY, data TEXT, cached_at INTEGER)''');
      await db.execute('''CREATE TABLE pending_actions(
        action_id TEXT PRIMARY KEY, type TEXT, queued_at TEXT,
        base_version INTEGER, payload TEXT, status TEXT)''');
    });
  }

  // Cache matches
  static Future<void> cacheMatch(String id, Map<String, dynamic> data) async {
    final d = await db;
    await d.insert('cached_matches', {'id': id, 'data': jsonEncode(data), 'cached_at': DateTime.now().millisecondsSinceEpoch},
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  static Future<Map<String, dynamic>?> getMatch(String id) async {
    final d = await db;
    final rows = await d.query('cached_matches', where: 'id=?', whereArgs: [id]);
    if (rows.isEmpty) return null;
    return jsonDecode(rows.first['data'] as String) as Map<String, dynamic>;
  }

  // Cache standings
  static Future<void> cacheStandings(String leagueId, Map<String, dynamic> data) async {
    final d = await db;
    await d.insert('cached_standings', {'league_id': leagueId, 'data': jsonEncode(data), 'cached_at': DateTime.now().millisecondsSinceEpoch},
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  static Future<Map<String, dynamic>?> getStandings(String leagueId) async {
    final d = await db;
    final rows = await d.query('cached_standings', where: 'league_id=?', whereArgs: [leagueId]);
    if (rows.isEmpty) return null;
    return jsonDecode(rows.first['data'] as String) as Map<String, dynamic>;
  }

  // Cache club
  static Future<void> cacheClub(String id, Map<String, dynamic> data) async {
    final d = await db;
    await d.insert('cached_clubs', {'id': id, 'data': jsonEncode(data), 'cached_at': DateTime.now().millisecondsSinceEpoch},
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  static Future<Map<String, dynamic>?> getClub(String id) async {
    final d = await db;
    final rows = await d.query('cached_clubs', where: 'id=?', whereArgs: [id]);
    if (rows.isEmpty) return null;
    return jsonDecode(rows.first['data'] as String) as Map<String, dynamic>;
  }

  // Pending actions queue
  static Future<void> enqueueAction(Map<String, dynamic> action) async {
    final d = await db;
    await d.insert('pending_actions', {
      'action_id': action['action_id'],
      'type': action['type'],
      'queued_at': action['queued_at'],
      'base_version': action['base_version'],
      'payload': jsonEncode(action['payload']),
      'status': 'pending',
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  static Future<List<Map<String, dynamic>>> getPendingActions() async {
    try {
      final d = await db;
      final rows = await d.query('pending_actions', where: "status='pending'", orderBy: 'queued_at ASC');
      return rows.map((r) => {
        'action_id': r['action_id'],
        'type': r['type'],
        'queued_at': r['queued_at'],
        'base_version': r['base_version'],
        'payload': jsonDecode(r['payload'] as String),
      }).toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> markActionSynced(String actionId) async {
    final d = await db;
    await d.update('pending_actions', {'status': 'synced'}, where: 'action_id=?', whereArgs: [actionId]);
  }

  static Future<void> clearSynced() async {
    final d = await db;
    await d.delete('pending_actions', where: "status='synced'");
  }

  static Future<int> pendingCount() async {
    final d = await db;
    final result = await d.rawQuery("SELECT COUNT(*) as c FROM pending_actions WHERE status='pending'");
    return (result.first['c'] as int?) ?? 0;
  }
}
