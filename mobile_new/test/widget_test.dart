import 'package:flutter_test/flutter_test.dart';
import 'package:nascon26_app/main.dart';

void main() {
  testWidgets('App launches without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(const NaSConApp());
    expect(find.byType(NaSConApp), findsOneWidget);
  });
}
