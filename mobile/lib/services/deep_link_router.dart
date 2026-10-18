import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'api_service.dart';
import '../screens/match_detail_screen.dart';
import '../screens/qr_entity_screen.dart';

final _entityInWebRoute = RegExp(r'^/web/(?:matches|players|clubs|costream)/([^/?#]+)');

/// Synchronous parse for links that carry the entity id directly:
/// `nascon://entity/{id}`, `nascon://stream/{id}`, or a resolved `/web/...` route.
String? extractEntityId(String raw) {
  final uri = Uri.tryParse(raw.trim());
  if (uri == null) return null;
  if (uri.scheme == 'nascon') {
    if ((uri.host == 'entity' || uri.host == 'stream') && uri.pathSegments.isNotEmpty) {
      return uri.pathSegments.first;
    }
    if (uri.pathSegments.length >= 2 && (uri.pathSegments.first == 'entity' || uri.pathSegments.first == 'stream')) {
      return uri.pathSegments[1];
    }
    return null;
  }
  final m = _entityInWebRoute.firstMatch(uri.path);
  return m?.group(1);
}

/// Full resolution, including printed short links (`http://host/q/{code}`).
/// The host inside the QR is the server's own (`localhost`), which the phone
/// can't reach, so the short code is resolved against the app's configured server.
Future<String?> resolveEntityId(String raw) async {
  final direct = extractEntityId(raw);
  if (direct != null) return direct;

  final uri = Uri.tryParse(raw.trim());
  if (uri == null || uri.pathSegments.length < 2 || uri.pathSegments.first != 'q') return null;
  final code = uri.pathSegments[1];

  final req = http.Request('GET', Uri.parse('${ApiService.baseUrl}/q/$code'))..followRedirects = false;
  final client = http.Client();
  try {
    final res = await client.send(req).timeout(const Duration(seconds: 5));
    final location = res.headers['location'];
    if (res.statusCode == 302 && location != null) {
      return _entityInWebRoute.firstMatch(Uri.parse(location).path)?.group(1);
    }
    return null;
  } finally {
    client.close();
  }
}

void navigateToEntity(BuildContext context, String entityId) {
  final page = entityId.startsWith('match-')
      ? MatchDetailScreen(matchId: entityId)
      : QrEntityScreen(entityId: entityId);
  Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
}
