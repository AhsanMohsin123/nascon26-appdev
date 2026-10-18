import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../app_theme.dart';

/// Generic fallback for entity types whose dedicated screen (player profile,
/// club-by-id, co-stream view) isn't built yet — shows the resolved QR
/// metadata instead of crashing or silently dropping the scan/deep link.
class QrEntityScreen extends StatefulWidget {
  final String entityId;
  const QrEntityScreen({super.key, required this.entityId});
  @override
  State<QrEntityScreen> createState() => _QrEntityScreenState();
}

class _QrEntityScreenState extends State<QrEntityScreen> {
  Map<String, dynamic>? _meta;
  String? _error;
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await ApiService.getQrMetadata(widget.entityId);
      setState(() { _meta = data; _loading = false; });
    } on ApiException catch (e) {
      setState(() { _error = e.userMessage; _loading = false; });
    } catch (e) {
      setState(() { _error = 'Network error — could not resolve this QR code.'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.entityId)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(_error!, textAlign: TextAlign.center),
                ))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(_meta!['entity_type'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
                          const SizedBox(height: 8),
                          Text('Target route: ${_meta!['target_route']}'),
                          const SizedBox(height: 4),
                          Text('Deep link: ${_meta!['deep_link_uri']}'),
                          const SizedBox(height: 4),
                          Text('Scan count: ${_meta!['scan_count']}'),
                        ]),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Full profile/live view for this entity type ships in a later phase. '
                      'This confirms the QR code resolved correctly against the live backend.',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ],
                ),
    );
  }
}
