import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/sync_provider.dart';
import '../app_theme.dart';

class SyncScreen extends StatelessWidget {
  const SyncScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final sync = context.watch<SyncProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Sync Status')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _statusCard(sync),
          const SizedBox(height: 16),
          _queueCard(sync, context),
        ],
      ),
    );
  }

  Widget _statusCard(SyncProvider sync) {
    Color color; IconData icon; String title; String subtitle;
    switch (sync.status) {
      case SyncStatus.online:
        color = AppTheme.success; icon = Icons.cloud_done; title = 'Online'; subtitle = 'All data synced with server';
        break;
      case SyncStatus.offline:
        color = Colors.orange; icon = Icons.cloud_off; title = 'Offline'; subtitle = 'Changes will sync when back online';
        break;
      case SyncStatus.syncing:
        color = AppTheme.primary; icon = Icons.sync; title = 'Syncing'; subtitle = 'Uploading queued actions...';
        break;
    }
    return Card(
      child: ListTile(
        leading: Container(width: 48, height: 48, decoration: BoxDecoration(color: color.withOpacity(0.15), shape: BoxShape.circle),
            child: Icon(icon, color: color, size: 26)),
        title: Text(title, style: TextStyle(fontWeight: FontWeight.w800, color: color, fontSize: 18)),
        subtitle: Text(subtitle),
        trailing: sync.status == SyncStatus.syncing ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2)) : null,
      ),
    );
  }

  Widget _queueCard(SyncProvider sync, BuildContext context) {
    final actions = sync.pendingActions;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text('Pending Queue (${actions.length})', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
            if (actions.isNotEmpty && sync.status == SyncStatus.online)
              TextButton.icon(
                onPressed: () => sync.sync(),
                icon: const Icon(Icons.sync, size: 16),
                label: const Text('Sync Now'),
              ),
          ]),
          const SizedBox(height: 8),
          if (actions.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: Column(children: [
                Icon(Icons.check_circle_outline, size: 48, color: Colors.green),
                SizedBox(height: 8),
                Text('No pending actions', style: TextStyle(color: Colors.grey)),
              ])),
            )
          else
            ...actions.map((a) => ListTile(
              leading: CircleAvatar(
                backgroundColor: AppTheme.primary.withOpacity(0.1),
                child: Icon(a['type'] == 'score_event' ? Icons.sports_score : Icons.swap_horiz, color: AppTheme.primary, size: 18),
              ),
              title: Text(a['type'].toString().replaceAll('_', ' '), style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text('Queued: ${a['queued_at'].toString().substring(0, 16)}', style: const TextStyle(fontSize: 11)),
              trailing: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: Colors.orange.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                child: const Text('Pending', style: TextStyle(color: Colors.orange, fontSize: 11, fontWeight: FontWeight.w600)),
              ),
            )),
        ]),
      ),
    );
  }
}
