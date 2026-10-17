import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/sync_provider.dart';
import '../services/api_service.dart';
import '../app_theme.dart';

class RosterScreen extends StatefulWidget {
  const RosterScreen({super.key});
  @override
  State<RosterScreen> createState() => _RosterScreenState();
}

class _RosterScreenState extends State<RosterScreen> {
  final _formKey = GlobalKey<FormState>();
  String _type = 'transfer';
  String _playerId = 'player-alpha-1';
  String _fromSquad = 'sq-a';
  String _toSquad = 'sq-b';
  String _leagueId = 'lg-r1';
  String _effectiveDate = DateTime.now().toIso8601String().substring(0, 10);
  String? _loanEnd;
  String _reason = '';
  bool _loading = false;
  String? _result;
  String? _error;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Roster Management')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _sectionTitle('Transfer / Loan / Release Player'),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(labelText: 'Action Type', prefixIcon: Icon(Icons.swap_horiz)),
              items: ['transfer', 'loan', 'release'].map((t) => DropdownMenuItem(value: t, child: Text(t.capitalize()))).toList(),
              onChanged: (v) => setState(() => _type = v!),
            ),
            const SizedBox(height: 12),
            TextFormField(
              initialValue: _playerId,
              decoration: const InputDecoration(labelText: 'Player ID', prefixIcon: Icon(Icons.person)),
              onChanged: (v) => _playerId = v,
              validator: (v) => v?.isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              initialValue: _leagueId,
              decoration: const InputDecoration(labelText: 'League ID', prefixIcon: Icon(Icons.emoji_events)),
              onChanged: (v) => _leagueId = v,
            ),
            const SizedBox(height: 12),
            TextFormField(
              initialValue: _fromSquad,
              decoration: const InputDecoration(labelText: 'From Squad ID', prefixIcon: Icon(Icons.group_remove)),
              onChanged: (v) => _fromSquad = v,
            ),
            if (_type != 'release') ...[
              const SizedBox(height: 12),
              TextFormField(
                initialValue: _toSquad,
                decoration: const InputDecoration(labelText: 'To Squad ID', prefixIcon: Icon(Icons.group_add)),
                onChanged: (v) => _toSquad = v,
              ),
            ],
            const SizedBox(height: 12),
            TextFormField(
              initialValue: _effectiveDate,
              decoration: const InputDecoration(labelText: 'Effective Date (YYYY-MM-DD)', prefixIcon: Icon(Icons.calendar_today)),
              onChanged: (v) => _effectiveDate = v,
            ),
            if (_type == 'loan') ...[
              const SizedBox(height: 12),
              TextFormField(
                decoration: const InputDecoration(labelText: 'Loan End Date (YYYY-MM-DD)', prefixIcon: Icon(Icons.event_available)),
                onChanged: (v) => _loanEnd = v,
                validator: (v) => _type == 'loan' && (v?.isEmpty == true) ? 'Required for loan' : null,
              ),
            ],
            const SizedBox(height: 12),
            TextFormField(
              decoration: const InputDecoration(labelText: 'Reason', prefixIcon: Icon(Icons.note_alt_outlined)),
              onChanged: (v) => _reason = v,
            ),
            const SizedBox(height: 24),
            if (_error != null) _errorBox(_error!),
            if (_result != null) _successBox(_result!),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _loading ? null : _submit,
                icon: _loading ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.check_circle_outline),
                label: Text(_loading ? 'Processing...' : 'Submit ${_type.capitalize()}'),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _sectionTitle(String t) => Text(t, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17, color: AppTheme.primaryDark));

  Widget _errorBox(String msg) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.red.shade200)),
    child: Row(children: [const Icon(Icons.error_outline, color: Colors.red, size: 18), const SizedBox(width: 8), Expanded(child: Text(msg, style: const TextStyle(color: Colors.red, fontSize: 13)))]),
  );

  Widget _successBox(String msg) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.green.shade200)),
    child: Row(children: [const Icon(Icons.check_circle, color: Colors.green, size: 18), const SizedBox(width: 8), Expanded(child: Text(msg, style: const TextStyle(color: Colors.green, fontSize: 13)))]),
  );

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; _result = null; });

    final sync = context.read<SyncProvider>();
    final reqId = 'tr-${DateTime.now().millisecondsSinceEpoch}';
    final body = {
      'request_id': reqId, 'league_id': _leagueId, 'player_id': _playerId,
      'type': _type, 'from_squad_id': _fromSquad,
      'to_squad_id': _type != 'release' ? _toSquad : null,
      'effective_date': _effectiveDate,
      'loan_end_date': _type == 'loan' ? _loanEnd : null,
      'reason': _reason, 'requested_by': 'club-manager',
    };

    if (sync.isOffline) {
      await sync.enqueue('roster_transfer', body, 0);
      setState(() { _loading = false; _result = 'Action queued for sync when back online.'; });
    } else {
      try {
        final data = await ApiService.transferPlayer(body);
        setState(() { _loading = false; _result = 'Success: ${data['state'] ?? 'accepted'} — ${data['audit_entry']?['action'] ?? _type}'; });
      } on ApiException catch (e) {
        setState(() { _loading = false; _error = e.userMessage; });
      }
    }
  }
}

extension StringExt on String {
  String capitalize() => isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';
}
