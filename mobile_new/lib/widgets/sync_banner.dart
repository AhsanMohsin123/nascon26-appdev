import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/sync_provider.dart';
import '../app_theme.dart';

class SyncBanner extends StatelessWidget {
  const SyncBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final sync = context.watch<SyncProvider>();
    Color bg; IconData icon; String text;
    switch (sync.status) {
      case SyncStatus.online:
        if (sync.pendingCount == 0) return const SizedBox.shrink();
        bg = Colors.orange; icon = Icons.sync; text = '${sync.pendingCount} action(s) pending sync';
        break;
      case SyncStatus.offline:
        bg = Colors.red.shade700; icon = Icons.cloud_off;
        text = sync.pendingCount > 0 ? 'Offline — ${sync.pendingCount} pending' : 'Offline';
        break;
      case SyncStatus.syncing:
        bg = AppTheme.primary; icon = Icons.sync; text = 'Syncing...';
        break;
    }
    return Container(
      color: bg,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Row(children: [
        Icon(icon, color: Colors.white, size: 16),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600))),
        if (sync.status == SyncStatus.online && sync.pendingCount > 0)
          GestureDetector(
            onTap: () => context.read<SyncProvider>().sync(),
            child: const Text('Sync Now', style: TextStyle(color: Colors.white, fontSize: 12, decoration: TextDecoration.underline)),
          ),
      ]),
    );
  }
}

class SyncIndicatorChip extends StatelessWidget {
  const SyncIndicatorChip({super.key});
  @override
  Widget build(BuildContext context) {
    final sync = context.watch<SyncProvider>();
    Color color; IconData icon; String label;
    switch (sync.status) {
      case SyncStatus.online: color = Colors.green; icon = Icons.cloud_done; label = 'Online'; break;
      case SyncStatus.offline: color = Colors.orange; icon = Icons.cloud_off; label = 'Offline${sync.pendingCount > 0 ? " (${sync.pendingCount})" : ""}'; break;
      case SyncStatus.syncing: color = Colors.blue; icon = Icons.sync; label = 'Syncing'; break;
    }
    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, color: color, size: 16),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
      ]),
    );
  }
}
