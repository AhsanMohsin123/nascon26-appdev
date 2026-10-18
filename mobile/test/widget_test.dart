import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:nascon26_app/providers/auth_provider.dart';
import 'package:nascon26_app/providers/sync_provider.dart';
import 'package:nascon26_app/screens/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard renders tournament metrics, actions, and match cards', (WidgetTester tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => AuthProvider()),
          ChangeNotifierProvider(create: (_) => SyncProvider()),
        ],
        child: const MaterialApp(
          home: DashboardScreen(),
        ),
      ),
    );

    // Verify tournament header, metrics, and sections
    expect(find.text("NaSCon '26 Championship"), findsOneWidget);
    expect(find.text('Live Matches'), findsOneWidget);
    expect(find.text('Active Tournaments'), findsOneWidget);
    expect(find.text('Featured & Live Fixtures'), findsOneWidget);
    expect(find.text('Tournament Standings Preview'), findsOneWidget);
    expect(find.text('Fixtures'), findsWidgets);
    expect(find.text('Standings'), findsWidgets);
  });
}
