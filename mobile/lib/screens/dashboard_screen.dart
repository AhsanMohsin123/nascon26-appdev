import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/sync_provider.dart';
import '../app_theme.dart';

class DashboardScreen extends StatefulWidget {
  final void Function(int tabIndex)? onNavigateTab;
  const DashboardScreen({super.key, this.onNavigateTab});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  String _selectedSport = 'all';

  final List<Map<String, dynamic>> _quickMatches = [
    {
      'matchId': 'match-fb-01',
      'sport': 'Football',
      'sportIcon': Icons.sports_soccer,
      'status': 'LIVE',
      'homeTeam': 'Alpha Warriors',
      'awayTeam': 'Falcon FC',
      'homeScore': 2,
      'awayScore': 1,
      'minute': "68'",
      'league': 'Premier League A',
    },
    {
      'matchId': 'match-bb-02',
      'sport': 'Basketball',
      'sportIcon': Icons.sports_basketball,
      'status': 'LIVE',
      'homeTeam': 'Taxila Titans',
      'awayTeam': 'Islamabad Dunkers',
      'homeScore': 78,
      'awayScore': 74,
      'minute': 'Q4 03:12',
      'league': 'Super League B',
    },
    {
      'matchId': 'match-cr-03',
      'sport': 'Cricket',
      'sportIcon': Icons.sports_cricket,
      'status': 'UPCOMING',
      'homeTeam': 'Rawal Strikers',
      'awayTeam': 'Margalla Kings',
      'homeScore': 0,
      'awayScore': 0,
      'minute': '11:00 AM',
      'league': 'T20 Cup',
    },
  ];

  final List<Map<String, dynamic>> _topTeams = [
    {'rank': 1, 'name': 'Alpha Warriors', 'points': 15, 'diff': '+8', 'status': 'clinched'},
    {'rank': 2, 'name': 'Falcon FC', 'points': 12, 'diff': '+4', 'status': 'still_possible'},
    {'rank': 3, 'name': 'Taxila Titans', 'points': 9, 'diff': '+1', 'status': 'still_possible'},
  ];

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final sync = context.watch<SyncProvider>();
    final user = auth.user;
    final userName = user?.email.split('@').first ?? 'Competitor';

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: RefreshIndicator(
        onRefresh: () async {
          await Future.delayed(const Duration(milliseconds: 500));
          if (mounted) setState(() {});
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hero Welcome Banner
              _buildHeroHeader(userName, user?.role ?? 'viewer', !sync.isOffline),
              const SizedBox(height: 18),

              // KPI Summary Metrics
              _buildMetricGrid(sync.pendingCount),
              const SizedBox(height: 20),

              // Quick Action Bar
              _buildQuickActions(context),
              const SizedBox(height: 22),

              // Sport Filter Selector
              _buildSportFilter(),
              const SizedBox(height: 14),

              // Live & Featured Matches
              _buildSectionTitle(
                title: 'Featured & Live Fixtures',
                subtitle: 'Real-time event scores',
                actionLabel: 'View All',
                onAction: () => widget.onNavigateTab?.call(2),
              ),
              const SizedBox(height: 10),
              _buildMatchCarousel(),
              const SizedBox(height: 22),

              // Standings Preview
              _buildSectionTitle(
                title: 'Tournament Standings Preview',
                subtitle: 'Top qualifying teams',
                actionLabel: 'Full Table',
                onAction: () => widget.onNavigateTab?.call(3),
              ),
              const SizedBox(height: 10),
              _buildStandingsCard(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeroHeader(String userName, String role, bool isOnline) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0D47A1), Color(0xFF1976D2), Color(0xFF0288D1)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0D47A1).withValues(alpha: 0.28),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Row(
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.emoji_events, color: Colors.amber, size: 26),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "NaSCon '26 Championship",
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w600),
                          ),
                          Text(
                            'Welcome, $userName!',
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: isOnline
                      ? const Color(0xFF059669).withValues(alpha: 0.25)
                      : Colors.orange.withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: isOnline ? Colors.greenAccent : Colors.orangeAccent,
                    width: 1,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: isOnline ? Colors.greenAccent : Colors.orangeAccent,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      isOnline ? 'Online' : 'Offline',
                      style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                const Icon(Icons.shield_outlined, color: Colors.white70, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Active Role: ${role.toUpperCase()}',
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  'Phase II',
                  style: TextStyle(color: Colors.amberAccent, fontSize: 12, fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricGrid(int pendingSync) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final cardWidth = (constraints.maxWidth - 12) / 2;
        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _buildMetricCard(
              title: 'Live Matches',
              value: '2 Running',
              icon: Icons.live_tv,
              iconColor: Colors.redAccent,
              badge: 'LIVE',
              badgeColor: Colors.red,
              width: cardWidth,
            ),
            _buildMetricCard(
              title: 'Active Tournaments',
              value: '3 Leagues',
              icon: Icons.military_tech_outlined,
              iconColor: Colors.indigo,
              badge: 'PHASE II',
              badgeColor: Colors.indigo,
              width: cardWidth,
            ),
            _buildMetricCard(
              title: 'Registered Clubs',
              value: '8 Teams',
              icon: Icons.groups_outlined,
              iconColor: Colors.teal,
              badge: 'ACTIVE',
              badgeColor: Colors.teal,
              width: cardWidth,
            ),
            _buildMetricCard(
              title: 'Sync Queue',
              value: pendingSync == 0 ? 'Up to date' : '$pendingSync pending',
              icon: Icons.sync,
              iconColor: pendingSync == 0 ? Colors.green : Colors.orange,
              badge: pendingSync == 0 ? 'SYNCED' : 'PENDING',
              badgeColor: pendingSync == 0 ? Colors.green : Colors.orange,
              width: cardWidth,
            ),
          ],
        );
      },
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color iconColor,
    required String badge,
    required Color badgeColor,
    required double width,
  }) {
    return Container(
      width: width,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: iconColor, size: 20),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  badge,
                  style: TextStyle(color: badgeColor, fontSize: 10, fontWeight: FontWeight.w800),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(title, style: TextStyle(color: Colors.grey.shade600, fontSize: 12, fontWeight: FontWeight.w500)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(color: Color(0xFF1E293B), fontSize: 16, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildActionButton(Icons.sports, 'Fixtures', const Color(0xFF1976D2), () {
            widget.onNavigateTab?.call(2);
          }),
          _buildActionButton(Icons.leaderboard, 'Standings', const Color(0xFF7B1FA2), () {
            widget.onNavigateTab?.call(3);
          }),
          _buildActionButton(Icons.storefront, 'Merch Store', const Color(0xFFF57C00), () {
            widget.onNavigateTab?.call(4);
          }),
          _buildActionButton(Icons.sync, 'Offline Hub', const Color(0xFF388E3C), () {
            widget.onNavigateTab?.call(6);
          }),
        ],
      ),
    );
  }

  Widget _buildActionButton(IconData icon, String label, Color color, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 6),
            Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF334155))),
          ],
        ),
      ),
    );
  }

  Widget _buildSportFilter() {
    final sports = [
      {'id': 'all', 'label': 'All Sports', 'icon': Icons.tune},
      {'id': 'football', 'label': 'Football', 'icon': Icons.sports_soccer},
      {'id': 'basketball', 'label': 'Basketball', 'icon': Icons.sports_basketball},
      {'id': 'cricket', 'label': 'Cricket', 'icon': Icons.sports_cricket},
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: sports.map((s) {
          final isSelected = _selectedSport == s['id'];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              avatar: Icon(
                s['icon'] as IconData,
                size: 16,
                color: isSelected ? Colors.white : const Color(0xFF475569),
              ),
              label: Text(s['label'] as String),
              selected: isSelected,
              showCheckmark: false,
              selectedColor: AppTheme.primary,
              backgroundColor: Colors.white,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : const Color(0xFF334155),
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: BorderSide(
                  color: isSelected ? AppTheme.primary : Colors.grey.shade300,
                ),
              ),
              onSelected: (_) => setState(() => _selectedSport = s['id'] as String),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildSectionTitle({
    required String title,
    required String subtitle,
    required String actionLabel,
    required VoidCallback onAction,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Theme.of(context).colorScheme.onSurface),
              ),
              Text(
                subtitle,
                style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
              ),
            ],
          ),
        ),
        TextButton(
          onPressed: onAction,
          style: TextButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: Row(
            children: [
              Text(
                actionLabel,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: AppTheme.primary),
              ),
              const Icon(Icons.chevron_right, size: 18, color: AppTheme.primary),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMatchCarousel() {
    final filtered = _selectedSport == 'all'
        ? _quickMatches
        : _quickMatches.where((m) => (m['sport'] as String).toLowerCase() == _selectedSport).toList();

    if (filtered.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: const Center(
          child: Text('No matches scheduled in this category yet.', style: TextStyle(color: Colors.grey)),
        ),
      );
    }

    return Column(
      children: filtered.map((match) => _buildMatchCard(match)).toList(),
    );
  }

  Widget _buildMatchCard(Map<String, dynamic> match) {
    final isLive = match['status'] == 'LIVE';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isLive ? Colors.red.shade200 : Colors.grey.shade200,
          width: isLive ? 1.5 : 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(match['sportIcon'] as IconData, size: 16, color: Colors.grey.shade700),
                  const SizedBox(width: 6),
                  Text(
                    '${match['sport']} • ${match['league']}',
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isLive ? Colors.red : Colors.blueGrey.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  isLive ? '● LIVE ${match['minute']}' : match['minute'] as String,
                  style: TextStyle(
                    color: isLive ? Colors.white : Colors.blueGrey.shade800,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 18,
                      backgroundColor: Colors.indigo.shade50,
                      child: Text(
                        (match['homeTeam'] as String).substring(0, 2).toUpperCase(),
                        style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w700, fontSize: 12),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        match['homeTeam'] as String,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  isLive ? '${match['homeScore']} - ${match['awayScore']}' : 'VS',
                  style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: Color(0xFF0F172A)),
                ),
              ),
              Expanded(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Expanded(
                      child: Text(
                        match['awayTeam'] as String,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                        textAlign: TextAlign.end,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 10),
                    CircleAvatar(
                      radius: 18,
                      backgroundColor: Colors.amber.shade50,
                      child: Text(
                        (match['awayTeam'] as String).substring(0, 2).toUpperCase(),
                        style: const TextStyle(color: Colors.amber, fontWeight: FontWeight.w700, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStandingsCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        children: [
          Row(
            children: const [
              SizedBox(width: 28, child: Text('#', style: TextStyle(fontWeight: FontWeight.w700, color: Colors.grey))),
              Expanded(child: Text('Club', style: TextStyle(fontWeight: FontWeight.w700, color: Colors.grey))),
              SizedBox(width: 48, child: Text('Diff', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w700, color: Colors.grey))),
              SizedBox(width: 48, child: Text('Pts', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w700, color: Colors.grey))),
              SizedBox(width: 72, child: Text('Status', textAlign: TextAlign.end, style: TextStyle(fontWeight: FontWeight.w700, color: Colors.grey))),
            ],
          ),
          const Divider(height: 20),
          ..._topTeams.map((t) {
            final isClinched = t['status'] == 'clinched';
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                children: [
                  SizedBox(
                    width: 28,
                    child: Text(
                      '${t['rank']}',
                      style: const TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      t['name'] as String,
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                    ),
                  ),
                  SizedBox(
                    width: 48,
                    child: Text(
                      t['diff'] as String,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey.shade700, fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ),
                  SizedBox(
                    width: 48,
                    child: Text(
                      '${t['points']}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontWeight: FontWeight.w800, color: AppTheme.primary),
                    ),
                  ),
                  SizedBox(
                    width: 72,
                    child: Align(
                      alignment: Alignment.centerRight,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: isClinched ? Colors.green.shade50 : Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          isClinched ? 'Clinched' : 'In Hunt',
                          style: TextStyle(
                            color: isClinched ? Colors.green.shade800 : Colors.blue.shade800,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

