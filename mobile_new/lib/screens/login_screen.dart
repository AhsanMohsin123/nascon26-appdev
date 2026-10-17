import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _pass = TextEditingController();
  bool _obscure = true;

  static const _roles = [
    _R('Admin',     'admin@nascon.test',     Icons.admin_panel_settings, Colors.purple),
    _R('Organizer', 'organizer@nascon.test', Icons.event,                Colors.blue),
    _R('Manager',   'manager@nascon.test',   Icons.manage_accounts,      Colors.teal),
    _R('Player',    'player@nascon.test',     Icons.sports,               Colors.green),
    _R('Viewer',    'viewer@nascon.test',     Icons.visibility,           Colors.grey),
  ];

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: AppTheme.primary,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(children: [
            const SizedBox(height: 32),
            _logo(),
            const SizedBox(height: 20),
            _form(auth),
            const SizedBox(height: 14),
            _quickButtons(auth),
            const SizedBox(height: 20),
          ]),
        ),
      ),
    );
  }

  Widget _logo() => Column(children: [
    Container(width: 68, height: 68,
      decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
      child: const Icon(Icons.sports, color: AppTheme.primary, size: 38)),
    const SizedBox(height: 10),
    const Text("NaSCon '26", style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
    const Text('Sports Platform', style: TextStyle(color: Colors.white70, fontSize: 12)),
  ]);

  Widget _form(AuthProvider auth) => Card(
    elevation: 6,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Sign In', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.primaryDark)),
        const SizedBox(height: 14),
        TextField(
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined), isDense: true),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _pass,
          obscureText: _obscure,
          decoration: InputDecoration(
            labelText: 'Password',
            prefixIcon: const Icon(Icons.lock_outline),
            isDense: true,
            suffixIcon: IconButton(
              icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility, size: 20),
              onPressed: () => setState(() => _obscure = !_obscure),
            ),
          ),
        ),
        if (auth.error != null) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)),
            child: Row(children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 16),
              const SizedBox(width: 6),
              Expanded(child: Text(auth.error!, style: const TextStyle(color: Colors.red, fontSize: 12))),
            ]),
          ),
        ],
        const SizedBox(height: 14),
        SizedBox(
          width: double.infinity, height: 46,
          child: ElevatedButton(
            onPressed: auth.loading ? null : _submit,
            child: auth.loading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Sign In', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          ),
        ),
      ]),
    ),
  );

  Widget _quickButtons(AuthProvider auth) => Column(children: [
    const Text('— Tap to login instantly —', style: TextStyle(color: Colors.white70, fontSize: 11)),
    const SizedBox(height: 10),
    Wrap(
      spacing: 8, runSpacing: 8, alignment: WrapAlignment.center,
      children: _roles.map((r) => _roleBtn(r, auth)).toList(),
    ),
    const SizedBox(height: 6),
    const Text('All use password: Nascon@26', style: TextStyle(color: Colors.white54, fontSize: 10)),
  ]);

  Widget _roleBtn(_R r, AuthProvider auth) => Material(
    color: Colors.transparent,
    child: InkWell(
      onTap: auth.loading ? null : () => _loginAs(r.email),
      borderRadius: BorderRadius.circular(22),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.18),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: Colors.white38),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(r.icon, color: Colors.white, size: 15),
          const SizedBox(width: 5),
          Text(r.label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
        ]),
      ),
    ),
  );

  Future<void> _submit() async {
    if (_email.text.trim().isEmpty) return;
    await context.read<AuthProvider>().login(_email.text.trim(), _pass.text);
  }

  Future<void> _loginAs(String email) async {
    _email.text = email;
    _pass.text = 'Nascon@26';
    setState(() {});
    await context.read<AuthProvider>().login(email, 'Nascon@26');
  }
}

class _R {
  final String label, email;
  final IconData icon;
  final Color color;
  const _R(this.label, this.email, this.icon, this.color);
}
