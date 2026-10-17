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
  final _email  = TextEditingController();
  final _pass   = TextEditingController();
  final _server = TextEditingController();
  bool _obscure    = true;
  bool _showServer = false;
  bool _testing    = false;
  String? _serverStatus;

  static const _roles = [
    _R('Admin',     'admin@nascon.test',     Icons.admin_panel_settings, Color(0xFF7B1FA2)),
    _R('Organizer', 'organizer@nascon.test', Icons.event,                Color(0xFF1565C0)),
    _R('Manager',   'manager@nascon.test',   Icons.manage_accounts,      Color(0xFF00695C)),
    _R('Player',    'player@nascon.test',    Icons.sports,               Color(0xFF2E7D32)),
    _R('Viewer',    'viewer@nascon.test',    Icons.visibility,           Color(0xFF546E7A)),
  ];

  @override
  void initState() {
    super.initState();
    _server.text = ApiService.baseUrl;
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: AppTheme.primary,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 18),
          child: Column(children: [
            const SizedBox(height: 28),
            _logo(),
            const SizedBox(height: 18),
            _formCard(auth),
            const SizedBox(height: 12),
            _quickLogin(auth),
            const SizedBox(height: 16),
          ]),
        ),
      ),
    );
  }

  Widget _logo() => Column(children: [
    Container(
      width: 70, height: 70,
      decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
      child: const Icon(Icons.sports, color: AppTheme.primary, size: 40),
    ),
    const SizedBox(height: 10),
    const Text("NaSCon '26",
        style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
    const Text('Sports League Platform',
        style: TextStyle(color: Colors.white70, fontSize: 12)),
  ]);

  Widget _formCard(AuthProvider auth) => Card(
    elevation: 8,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Sign In',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppTheme.primaryDark)),
        const SizedBox(height: 14),
        TextField(
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            labelText: 'Email',
            hintText: 'admin@nascon.test',
            prefixIcon: Icon(Icons.email_outlined),
            isDense: true,
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _pass,
          obscureText: _obscure,
          decoration: InputDecoration(
            labelText: 'Password',
            hintText: 'Nascon@26',
            prefixIcon: const Icon(Icons.lock_outline),
            isDense: true,
            suffixIcon: IconButton(
              icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility, size: 20),
              onPressed: () => setState(() => _obscure = !_obscure),
            ),
          ),
        ),
        if (auth.error != null) ...[
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.red.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.shade200),
            ),
            child: Row(children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 16),
              const SizedBox(width: 8),
              Expanded(child: Text(
                auth.error!.toLowerCase().contains('connection') ||
                        auth.error!.toLowerCase().contains('socket') ||
                        auth.error!.toLowerCase().contains('timeout')
                    ? 'Cannot reach server. Tap "Server" below to check address.'
                    : auth.error!,
                style: const TextStyle(color: Colors.red, fontSize: 12),
              )),
            ]),
          ),
        ],
        const SizedBox(height: 14),
        SizedBox(
          width: double.infinity,
          height: 48,
          child: ElevatedButton(
            onPressed: auth.loading ? null : _login,
            child: auth.loading
                ? const SizedBox(
                    width: 22, height: 22,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Sign In',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          ),
        ),
        const SizedBox(height: 10),
        // Server info row
        GestureDetector(
          onTap: () => setState(() => _showServer = !_showServer),
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Icon(
              Icons.dns_outlined,
              size: 13,
              color: _serverStatus == 'ok'
                  ? Colors.green
                  : _serverStatus == 'fail'
                      ? Colors.red
                      : Colors.grey,
            ),
            const SizedBox(width: 4),
            Flexible(
              child: Text(
                'Server: ${_server.text}',
                style: TextStyle(
                  fontSize: 10,
                  color: _serverStatus == 'ok'
                      ? Colors.green
                      : _serverStatus == 'fail'
                          ? Colors.red
                          : Colors.grey,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 3),
            Icon(_showServer ? Icons.expand_less : Icons.expand_more,
                size: 13, color: Colors.grey),
          ]),
        ),
        if (_showServer) ...[
          const SizedBox(height: 10),
          TextField(
            controller: _server,
            decoration: const InputDecoration(
              labelText: 'Server URL',
              hintText: 'http://127.0.0.1:8080',
              prefixIcon: Icon(Icons.link, size: 18),
              isDense: true,
            ),
            onChanged: (v) {
              ApiService.baseUrl = v.trim();
              setState(() => _serverStatus = null);
            },
          ),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _testing ? null : _testServer,
                icon: _testing
                    ? const SizedBox(
                        width: 14, height: 14,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.wifi_tethering, size: 16),
                label: Text(_testing ? 'Testing...' : 'Test',
                    style: const TextStyle(fontSize: 12)),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () {
                  _server.text = 'http://127.0.0.1:8080';
                  ApiService.baseUrl = 'http://127.0.0.1:8080';
                  setState(() => _serverStatus = null);
                },
                icon: const Icon(Icons.usb, size: 16),
                label: const Text('USB', style: TextStyle(fontSize: 12)),
              ),
            ),
          ]),
          if (_serverStatus != null) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: _serverStatus == 'ok'
                    ? Colors.green.shade50
                    : Colors.red.shade50,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(children: [
                Icon(
                  _serverStatus == 'ok' ? Icons.check_circle : Icons.cancel,
                  color: _serverStatus == 'ok' ? Colors.green : Colors.red,
                  size: 16,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _serverStatus == 'ok'
                        ? 'Connected! Server is reachable.'
                        : 'Cannot connect. Check USB cable or WiFi.',
                    style: TextStyle(
                      color: _serverStatus == 'ok'
                          ? Colors.green.shade700
                          : Colors.red.shade700,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ]),
            ),
          ],
        ],
      ]),
    ),
  );

  Widget _quickLogin(AuthProvider auth) => Column(children: [
    const Text('— Tap any role to login instantly —',
        style: TextStyle(color: Colors.white70, fontSize: 11)),
    const SizedBox(height: 10),
    Wrap(
      spacing: 8, runSpacing: 8, alignment: WrapAlignment.center,
      children: _roles.map((r) => _chip(r, auth)).toList(),
    ),
    const SizedBox(height: 6),
    const Text('All use password: Nascon@26',
        style: TextStyle(color: Colors.white54, fontSize: 10)),
  ]);

  Widget _chip(_R r, AuthProvider auth) => GestureDetector(
    onTap: auth.loading ? null : () => _loginAs(r.email),
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white38),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(r.icon, color: Colors.white, size: 16),
        const SizedBox(width: 6),
        Text(r.label,
            style: const TextStyle(
                color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
      ]),
    ),
  );

  Future<void> _testServer() async {
    setState(() { _testing = true; _serverStatus = null; });
    ApiService.baseUrl = _server.text.trim();
    final ok = await ApiService.checkHealth();
    setState(() { _testing = false; _serverStatus = ok ? 'ok' : 'fail'; });
  }

  Future<void> _login() async {
    final email = _email.text.trim();
    if (email.isEmpty) return;
    ApiService.baseUrl = _server.text.trim();
    await context.read<AuthProvider>().login(email, _pass.text);
  }

  Future<void> _loginAs(String email) async {
    ApiService.baseUrl = _server.text.trim();
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
