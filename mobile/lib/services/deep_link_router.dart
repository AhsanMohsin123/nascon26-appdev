import 'package:flutter/material.dart';
import '../screens/match_detail_screen.dart';
import '../screens/qr_entity_screen.dart';

/// Extracts the entity_id from either a `nascon://entity/{id}` deep link
/// or a scanned short URL (`http://host/q/{short_code}` — resolved on the
/// backend, so here we just detect it's a NaSCon link and let the metadata
/// call do the real resolution) and routes to the correct screen.
String? extractEntityId(String raw) {
  final trimmed = raw.trim();
  final nasconUri = Uri.tryParse(trimmed);
  if (nasconUri == null) return null;

  if (nasconUri.scheme == 'nascon' && nasconUri.host == 'entity' && nasconUri.pathSegments.isNotEmpty) {
    return nasconUri.pathSegments.first;
  }
  if (nasconUri.scheme == 'nascon' && nasconUri.pathSegments.length >= 2 && nasconUri.pathSegments.first == 'entity') {
    return nasconUri.pathSegments[1];
  }
  return null;
}

void navigateToEntity(BuildContext context, String entityId) {
  if (entityId.startsWith('match-')) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => MatchDetailScreen(matchId: entityId)));
  } else {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => QrEntityScreen(entityId: entityId)));
  }
}
