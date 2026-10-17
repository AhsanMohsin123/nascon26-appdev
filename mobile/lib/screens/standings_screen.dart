import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/local_db.dart';
import '../app_theme.dart';

class StandingsScreen extends StatefulWidget {
  const StandingsScreen({super.key});
  @override
  State<StandingsScreen> createState() => _StandingsScreenState();
}

class _StandingsScreenState extends State<StandingsScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String _leagueId = 'league-alpha-1';
  String? _error;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await ApiService.getStandings(_leagueId);
      await LocalDb.cacheStandings(_leagueId, data);
      setState(() { _data = data; _loading = false; });
    } catch (e) {
      final cached = await LocalDb.getStandings(_leagueId);
      if (cached != null) {
        setState(() { _data = cached; _loading = false; });
      } else {
        setState(() { _loading = false; _error = e is ApiException ? e.userMessage : 'Failed to load standings'; });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Standings'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.filter_list),
            onSelected: (v) { setState(() => _leagueId = v); _load(); },
            itemBuilder: (_) => ['league-alpha-1','league-alpha-2','league-beta-1']
                .map((l) => PopupMenuItem(value: l, child: Text(l))).toList(),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  const Icon(Icons.leaderboard, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('No standings available', style: TextStyle(fontSize: 18, color: Colors.grey)),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(onPressed: _load, icon: const Icon(Icons.refresh), label: const Text('Retry')),
                ]))
              : _data == null
                  ? const Center(child: Text('No data'))
                  : RefreshIndicator(onRefresh: _load, child: _body()),
    );
  }

  Widget _body() {
    final table = (_data!['table'] as List? ?? []).cast<Map<String, dynamic>>();
    final spots = _data!['qualification_spots'] ?? 1;
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        _header(),
        const SizedBox(height: 8),
        ...table.asMap().entries.map((e) => _row(e.value, e.key < spots)),
        const SizedBox(height: 16),
        _legend(),
      ],
    );
  }

  Widget _header() => Card(
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('League: $_leagueId', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
        Text('Sport: ${_data!['sport_id'] ?? ''}  •  Qualification spots: ${_data!['qualification_spots']}',
            style: const TextStyle(color: Colors.grey, fontSize: 12)),
      ]),
    ),
  );

  Widget _row(Map<String, dynamic> entry, bool isQualifying) {
    final status = entry['status'] ?? 'still_possible';
    final qual = status == 'clinched';
    final elim = status == 'eliminated';
    return Card(
      color: qual ? Colors.green.shade50 : elim ? Colors.red.shade50 : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(children: [
          SizedBox(width: 28, child: Text('${entry['rank']}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16), textAlign: TextAlign.center)),
          const SizedBox(width: 4),
          _qualDot(status),
          const SizedBox(width: 8),
          Expanded(child: Text(entry['team_id'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700))),
          _stat('P', '${entry['played']}'),
          _stat('W', '${entry['won']}'),
          _stat('D', '${entry['drawn']}'),
          _stat('L', '${entry['lost']}'),
          _stat('GD', '${entry['diff']}'),
          Container(
            width: 36,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: AppTheme.primary, borderRadius: BorderRadius.circular(6)),
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Text('${entry['points']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14)),
          ),
        ]),
      ),
    );
  }

  Widget _qualDot(String status) {
    Color c;
    switch (status) {
      case 'clinched': c = AppTheme.success; break;
      case 'eliminated': c = AppTheme.error; break;
      default: c = Colors.transparent;
    }
    return Container(width: 8, height: 8, decoration: BoxDecoration(color: c, shape: BoxShape.circle));
  }

  Widget _stat(String label, String val) => Padding(
    padding: const EdgeInsets.only(right: 8),
    child: Column(children: [
      Text(label, style: const TextStyle(color: Colors.grey, fontSize: 9, fontWeight: FontWeight.w600)),
      Text(val, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
    ]),
  );

  Widget _legend() => Row(mainAxisAlignment: MainAxisAlignment.center, children: [
    _legendItem(AppTheme.success, 'Qualified'),
    const SizedBox(width: 16),
    _legendItem(AppTheme.error, 'Eliminated'),
    const SizedBox(width: 16),
    _legendItem(Colors.transparent, 'In contention', border: true),
  ]);

  Widget _legendItem(Color c, String label, {bool border = false}) => Row(mainAxisSize: MainAxisSize.min, children: [
    Container(width: 10, height: 10,
        decoration: BoxDecoration(color: c, shape: BoxShape.circle, border: border ? Border.all(color: Colors.grey) : null)),
    const SizedBox(width: 4),
    Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
  ]);
}
