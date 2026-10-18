import 'package:flutter/material.dart';

class AppTheme {
  // Palette taken from the reference portfolio's stylesheet.
  static const Color primary = Color(0xFF2D5A9E);
  static const Color primaryDark = Color(0xFF1B3A6B);
  static const Color navyDeep = Color(0xFF12274A);
  static const Color accent = Color(0xFF8B95A5);
  static const Color silver = Color(0xFFD8DEE9);
  static const Color ice = Color(0xFFE8EEFC);
  static const Color charcoal = Color(0xFF0D1116);
  static const Color charcoalCard = Color(0xFF161C24);
  static const Color success = Color(0xFF2E7D32);
  static const Color error = Color(0xFFC62828);
  static const Color surface = Color(0xFFF8F9FA);
  static const Color cardBg = Colors.white;

  static const _transitions = PageTransitionsTheme(builders: {
    TargetPlatform.android: CupertinoPageTransitionsBuilder(),
    TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
  });

  static ThemeData get light => _build(
        brightness: Brightness.light,
        scheme: ColorScheme.fromSeed(
          seedColor: primary,
          brightness: Brightness.light,
          primary: primary,
          secondary: primaryDark,
          surface: surface,
        ),
        scaffoldBg: surface,
        card: cardBg,
        appBarBg: primaryDark,
        inputFill: Colors.white,
      );

  static ThemeData get dark => _build(
        brightness: Brightness.dark,
        scheme: ColorScheme.fromSeed(
          seedColor: primary,
          brightness: Brightness.dark,
          primary: const Color(0xFF7FA6E0),
          secondary: silver,
          surface: charcoal,
        ),
        scaffoldBg: charcoal,
        card: charcoalCard,
        appBarBg: charcoal,
        inputFill: charcoalCard,
      );

  static ThemeData _build({
    required Brightness brightness,
    required ColorScheme scheme,
    required Color scaffoldBg,
    required Color card,
    required Color appBarBg,
    required Color inputFill,
  }) {
    final isDark = brightness == Brightness.dark;
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scaffoldBg,
      pageTransitionsTheme: _transitions,
      splashFactory: InkSparkle.splashFactory,
      appBarTheme: AppBarTheme(
        backgroundColor: appBarBg,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colors.white, letterSpacing: 0.5),
      ),
      cardTheme: CardThemeData(
        elevation: isDark ? 0 : 1.5,
        color: card,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: isDark ? BorderSide(color: Colors.white.withValues(alpha: 0.08)) : BorderSide.none,
        ),
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: isDark ? scheme.primary : primary,
          foregroundColor: isDark ? charcoal : Colors.white,
          minimumSize: const Size.fromHeight(50),
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          side: BorderSide(color: scheme.primary),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: inputFill,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: isDark ? Colors.white24 : silver),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: scheme.primary, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      chipTheme: ChipThemeData(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: isDark ? charcoalCard : Colors.white,
        selectedItemColor: scheme.primary,
        unselectedItemColor: isDark ? Colors.white54 : accent,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}

class AppColors {
  static Color statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'in_progress': return const Color(0xFF2E7D32);
      case 'upcoming': return AppTheme.primary;
      case 'completed': return Colors.grey.shade600;
      case 'postponed': return const Color(0xFFE65100);
      case 'cancelled': return const Color(0xFFB71C1C);
      default: return Colors.grey;
    }
  }

  static Color qualColor(String status) {
    switch (status) {
      case 'clinched': return AppTheme.success;
      case 'eliminated': return AppTheme.error;
      default: return Colors.orange;
    }
  }
}
