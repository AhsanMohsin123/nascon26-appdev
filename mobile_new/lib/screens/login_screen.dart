import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
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
  final _server = TextEditingController(text: 'http://10.0.2.2:8080');
  bool _obscure = true;
  bool _showServer = false;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: AppTheme.primary,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 60),
              _logo(),
              const SizedBox(height: 40),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 24),
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 20, offset: const Offset(0, 8))],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Welcome Back', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppTheme.primaryDark)),
                    const SizedBox(height: 4),
                    const Text('Sign in to continue', style: TextStyle(color: Colors.grey, fontSize: 14)),
                    const SizedBox(height: 28),
                    _field('Email', _email, TextInputType.emailAddress, Icons.email_outlined),
                    const SizedBox(height: 16),
                    _passField(),
                    if (auth.error != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.red.shade200)),
                        child: Row(children: [
                          const Icon(Icons.error_outline, color: Colors.red, size: 18),
                          const SizedBox(width: 8),
                          Expanded(child: Text(auth.error!, style: const TextStyle(color: Colors.red, fontSize: 13))),
                        ]),
                      ),
                    ],
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        onPressed: auth.loading ? null : _login,
                        child: auth.loading
                            ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Text('Sign In', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    GestureDetector(
                      onTap: () => setState(() => _showServer = !_showServer),
                      child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Icon(Icons.settings, size: 14, color: Colors.grey.shade500),
                        const SizedBox(width: 4),
                        Text('Server Settings', style: TextStyle(color: Colors.grey.shade500, fontSize: 12)),
                      ]),
                    ),
                    if (_showServer) ...[
                      const SizedBox(height: 12),
                      TextField(
                        controller: _server,
                        decoration: const InputDecoration(labelText: 'Server URL', prefixIcon: Icon(Icons.dns_outlined)),
                        onChanged: (v) => ApiService.baseUrl = v.trim(),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 32),
              _demoAccounts(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _logo() => Column(children: [
    Container(
      width: 80, height: 80,
      decoration: BoxDecoration(color: Colors.white, shape: BoxShape.circle, boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 12)]),
      child: const Icon(Icons.sports, color: AppTheme.primary, size: 44),
    ),
    const SizedBox(height: 16),
    const Text("NaSCon '26", style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 1)),
    const Text('Sports League Platform', style: TextStyle(color: Colors.white70, fontSize: 14)),
  ]);

  Widget _field(String label, TextEditingController ctrl, TextInputType type, IconData icon) =>
    TextField(controller: ctrl, keyboardType: type, decoration: InputDecoration(labelText: label, prefixIcon: Icon(icon)));

  Widget _passField() => TextField(
    controller: _pass,
    obscureText: _obscure,
    decoration: InputDecoration(
      labelText: 'Password',
      prefixIcon: const Icon(Icons.lock_outline),
      suffixIcon: IconButton(icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility), onPressed: () => setState(() => _obscure = !_obscure)),
    ),
  );

  Widget _demoAccounts() => Container(
    margin: const EdgeInsets.symmetric(horizontal: 24),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(12)),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Demo Accounts', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
      const SizedBox(height: 10),
      ...[
        ('Admin', 'admin@nascon.test'),
        ('Organizer', 'organizer@nascon.test'),
        ('Manager', 'manager@nascon.test'),
        ('Player', 'player@nascon.test'),
        ('Viewer', 'viewer@nascon.test'),
      ].map((e) => GestureDetector(
        onTap: () { _email.text = e.$2; _pass.text = 'Nascon@26'; },
        child: Padding(padding: const EdgeInsets.symmetric(vertical: 3), child: Row(children: [
          const Icon(Icons.person_outline, color: Colors.white70, size: 14),
          const SizedBox(width: 6),
          Text('${e.$1}: ', style: const TextStyle(color: Colors.white70, fontSize: 12)),
          Text(e.$2, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
        ])),
      )),
      const SizedBox(height: 4),
      const Text('Password for all: Nascon@26', style: TextStyle(color: Colors.white54, fontSize: 11)),
    ]),
  );

  Future<void> _login() async {
    ApiService.baseUrl = _server.text.trim();
    await context.read<AuthProvider>().login(_email.text.trim(), _pass.text);
  }
}
