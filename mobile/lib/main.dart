import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:app_links/app_links.dart';
import 'providers/auth_provider.dart';
import 'providers/sync_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'services/deep_link_router.dart';
import 'app_theme.dart';

final navigatorKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp, DeviceOrientation.portraitDown]);
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()..tryRestoreSession()),
        ChangeNotifierProvider(create: (_) => SyncProvider()),
      ],
      child: const NaSConApp(),
    ),
  );
}

class NaSConApp extends StatefulWidget {
  const NaSConApp({super.key});
  @override
  State<NaSConApp> createState() => _NaSConAppState();
}

class _NaSConAppState extends State<NaSConApp> {
  final _appLinks = AppLinks();
  StreamSubscription<Uri>? _linkSub;

  @override
  void initState() {
    super.initState();
    _initDeepLinks();
  }

  Future<void> _initDeepLinks() async {
    try {
      final initial = await _appLinks.getInitialLink();
      if (initial != null) _handleIncomingLink(initial);
    } catch (_) {}
    _linkSub = _appLinks.uriLinkStream.listen(_handleIncomingLink, onError: (_) {});
  }

  void _handleIncomingLink(Uri uri) {
    final entityId = extractEntityId(uri.toString());
    final ctx = navigatorKey.currentContext;
    if (entityId != null && ctx != null) {
      navigateToEntity(ctx, entityId);
    }
  }

  @override
  void dispose() { _linkSub?.cancel(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: navigatorKey,
      title: "NaSCon '26",
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: Consumer<AuthProvider>(
        builder: (ctx, auth, _) {
          if (auth.loading) {
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          return auth.isLoggedIn ? const HomeScreen() : const LoginScreen();
        },
      ),
    );
  }
}
