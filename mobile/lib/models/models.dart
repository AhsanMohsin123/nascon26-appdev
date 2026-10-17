class UserModel {
  final String email;
  final String role;
  final String? tenantId;
  final String? leagueId;
  final String? clubId;
  final String token;

  UserModel({required this.email, required this.role, this.tenantId, this.leagueId, this.clubId, required this.token});

  factory UserModel.fromJson(Map<String, dynamic> j, String token) => UserModel(
    email: j['sub'] ?? '',
    role: j['role'] ?? 'viewer',
    tenantId: j['tenant_id'],
    leagueId: j['league_id'],
    clubId: j['club_id'],
    token: token,
  );

  bool get isSuperAdmin => role == 'super_admin';
  bool get isOrganizer => role == 'league_organizer' || isSuperAdmin;
  bool get isManager => role == 'club_manager' || isSuperAdmin;
  bool get isPlayer => role == 'player';
}

class Match {
  final String matchId;
  final String? leagueId;
  final String sportId;
  final String homeTeamId;
  final String awayTeamId;
  final String status;
  final int homeScore;
  final int awayScore;
  final String outcome;

  Match({required this.matchId, this.leagueId, required this.sportId, required this.homeTeamId,
    required this.awayTeamId, required this.status, this.homeScore = 0, this.awayScore = 0, this.outcome = 'pending'});

  factory Match.fromScore(Map<String, dynamic> j) => Match(
    matchId: j['match_id'] ?? '',
    leagueId: j['league_id'],
    sportId: j['sport_id'] ?? '',
    homeTeamId: j['home']?['team_id'] ?? '',
    awayTeamId: j['away']?['team_id'] ?? '',
    status: j['status'] ?? 'upcoming',
    homeScore: j['home']?['score'] ?? 0,
    awayScore: j['away']?['score'] ?? 0,
    outcome: j['outcome'] ?? 'pending',
  );
}

class StandingEntry {
  final int rank;
  final String teamId;
  final int played, won, drawn, lost;
  final int scored, conceded, points;
  final dynamic diff;
  final String status;

  StandingEntry({required this.rank, required this.teamId, required this.played,
    required this.won, required this.drawn, required this.lost,
    required this.scored, required this.conceded, required this.points,
    required this.diff, required this.status});

  factory StandingEntry.fromJson(Map<String, dynamic> j) => StandingEntry(
    rank: j['rank'] ?? 0, teamId: j['team_id'] ?? '',
    played: j['played'] ?? 0, won: j['won'] ?? 0,
    drawn: j['drawn'] ?? 0, lost: j['lost'] ?? 0,
    scored: j['scored'] ?? 0, conceded: j['conceded'] ?? 0,
    points: j['points'] ?? 0, diff: j['diff'] ?? 0,
    status: j['status'] ?? 'still_possible',
  );
}

class Product {
  final String id;
  final String name;
  final List<ProductVariant> variants;

  Product({required this.id, required this.name, required this.variants});
}

class ProductVariant {
  final String id;
  final String size;
  final String? color;
  final int priceMinor;
  int stock;

  ProductVariant({required this.id, required this.size, this.color, required this.priceMinor, this.stock = 0});

  String get priceFormatted => 'PKR ${(priceMinor / 100).toStringAsFixed(2)}';

  factory ProductVariant.fromJson(Map<String, dynamic> j) => ProductVariant(
    id: j['variant_id'] ?? j['id'] ?? '',
    size: j['size'] ?? '',
    color: j['color'],
    priceMinor: j['unit_price_minor'] ?? j['price_minor'] ?? 0,
    stock: j['stock'] ?? 0,
  );
}

class Player {
  final String id;
  final String name;
  final String position;
  final String role;
  final String? squadId;

  Player({required this.id, required this.name, required this.position, required this.role, this.squadId});

  factory Player.fromJson(Map<String, dynamic> j) => Player(
    id: j['player_id'] ?? j['id'] ?? '',
    name: j['name'] ?? '',
    position: j['position'] ?? '',
    role: j['role'] ?? 'substitute',
    squadId: j['squad_id'],
  );
}

class PendingAction {
  final String actionId;
  final String type;
  final String queuedAt;
  final int baseVersion;
  final Map<String, dynamic> payload;
  String status;

  PendingAction({required this.actionId, required this.type, required this.queuedAt,
    required this.baseVersion, required this.payload, this.status = 'pending'});

  Map<String, dynamic> toJson() => {
    'action_id': actionId, 'type': type, 'queued_at': queuedAt,
    'base_version': baseVersion, 'payload': payload,
  };

  Map<String, dynamic> toStorageMap() => {
    'action_id': actionId, 'type': type, 'queued_at': queuedAt,
    'base_version': baseVersion, 'payload_json': payload.toString(), 'status': status,
  };
}
