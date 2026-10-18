import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';
import '../services/api_service.dart';
import '../app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _pass = TextEditingController();
  final _server = TextEditingController(text: ApiService.baseUrl);
  bool _obscure = true;
  bool _showServer = false;
  String? _pendingRole;

  static const _roles = [
    ('Admin', 'admin@nascon.test', Icons.admin_panel_settings_rounded, 'Full platform control'),
    ('Organizer', 'organizer@nascon.test', Icons.emoji_events_rounded, 'Leagues, fixtures, scores'),
    ('Manager', 'manager@nascon.test', Icons.groups_rounded, 'Club, roster, store'),
    ('Player', 'player@nascon.test', Icons.sports_soccer_rounded, 'Profile, matches, streams'),
    ('Viewer', 'viewer@nascon.test', Icons.visibility_rounded, 'Read-only access'),
  ];

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final theme = context.watch<ThemeProvider>();
    final scheme = Theme.of(context).colorScheme;
    final isDark = theme.isDark;

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: isDark
                ? const [AppTheme.charcoal, Color(0xFF111A28), AppTheme.navyDeep]
                : const [AppTheme.navyDeep, AppTheme.primaryDark, AppTheme.primary],
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
            children: [
              Align(
                alignment: Alignment.centerRight,
                child: IconButton(
                  tooltip: isDark ? 'Switch to light mode' : 'Switch to dark mode',
                  onPressed: () { HapticFeedback.selectionClick(); theme.toggle(); },
                  icon: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    transitionBuilder: (c, a) => RotationTransition(turns: a, child: c),
                    child: Icon(isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
                        key: ValueKey(isDark), color: Colors.white),
                  ),
                ),
              ),
              _logo(),
              const SizedBox(height: 28),
              const Text('Quick sign-in', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              const Text('Tap a role to sign in instantly with its demo account.',
                  style: TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 12),
              ..._roles.map((r) => _roleTile(r, auth)),
              const SizedBox(height: 20),
              _manualCard(auth, scheme),
            ],
          ),
        ),
      ),
    );
  }

  Widget _logo() => Column(children: [
        Container(
          width: 84, height: 84,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white.withValues(alpha: 0.12),
            border: Border.all(color: AppTheme.silver.withValues(alpha: 0.5)),
            boxShadow: [BoxShadow(color: AppTheme.primary.withValues(alpha: 0.5), blurRadius: 30)],
          ),
          child: const Icon(Icons.sports_rounded, color: Colors.white, size: 44),
        ),
        const SizedBox(height: 14),
        const Text("NaSCon '26", style: TextStyle(color: Colors.white, fontSize: 30, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const Text('Multi-Sport League Platform', style: TextStyle(color: AppTheme.silver, fontSize: 14)),
      ]);

  Widget _roleTile((String, String, IconData, String) r, AuthProvider auth) {
    final (label, email, icon, desc) = r;
    final busy = auth.loading && _pendingRole == label;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: Colors.white.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: auth.loading ? null : () => _quickLogin(label, email),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
            ),
            child: Row(children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: Colors.white.withValues(alpha: 0.15),
                child: Icon(icon, color: Colors.white),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                  Text(desc, style: const TextStyle(color: AppTheme.silver, fontSize: 12)),
                ]),
              ),
              busy
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white70, size: 16),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _manualCard(AuthProvider auth, ColorScheme scheme) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Sign in with email', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: scheme.onSurface)),
          const SizedBox(height: 16),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _pass,
            obscureText: _obscure,
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => _manualLogin(),
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outline),
              suffixIcon: IconButton(
                icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _obscure = !_obscure),
              ),
            ),
          ),
          AnimatedSize(
            duration: const Duration(milliseconds: 250),
            child: auth.error == null
                ? const SizedBox(width: double.infinity)
                : Container(
                    width: double.infinity,
                    margin: const EdgeInsets.only(top: 12),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.error.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(children: [
                      const Icon(Icons.error_outline, color: AppTheme.error, size: 18),
                      const SizedBox(width: 8),
                      Expanded(child: Text(auth.error!, style: const TextStyle(color: AppTheme.error, fontSize: 13))),
                    ]),
                  ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: auth.loading ? null : _manualLogin,
            child: auth.loading && _pendingRole == null
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Sign In'),
          ),
          const SizedBox(height: 8),
          Center(
            child: TextButton.icon(
              onPressed: () => setState(() => _showServer = !_showServer),
              icon: const Icon(Icons.dns_outlined, size: 16),
              label: Text(_showServer ? 'Hide server settings' : 'Server: ${ApiService.baseUrl}'),
            ),
          ),
          if (_showServer)
            TextField(
              controller: _server,
              decoration: const InputDecoration(labelText: 'Server URL', helperText: 'USB: http://127.0.0.1:8080  ·  Wi-Fi: http://<laptop-ip>:8080'),
              onChanged: (v) => setState(() => ApiService.baseUrl = v.trim()),
            ),
        ]),
      ),
    );
  }

  Future<void> _quickLogin(String role, String email) async {
    HapticFeedback.lightImpact();
    setState(() => _pendingRole = role);
    _email.text = email;
    _pass.text = 'Nascon@26';
    await _submit();
  }

  Future<void> _manualLogin() async {
    setState(() => _pendingRole = null);
    await _submit();
  }

  Future<void> _submit() async {
    FocusScope.of(context).unfocus();
    ApiService.baseUrl = _server.text.trim();
    final ok = await context.read<AuthProvider>().login(_email.text.trim(), _pass.text);
    if (!mounted) return;
    setState(() => _pendingRole = null);
    if (!ok) HapticFeedback.heavyImpact();
  }
}
