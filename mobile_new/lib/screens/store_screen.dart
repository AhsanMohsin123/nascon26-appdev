import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../app_theme.dart';
import 'dart:convert';

class StoreScreen extends StatefulWidget {
  const StoreScreen({super.key});
  @override
  State<StoreScreen> createState() => _StoreScreenState();
}

class _StoreScreenState extends State<StoreScreen> {
  final List<Map<String, dynamic>> _cart = [];
  String? _selectedVariant;
  String _token = 'tok_success';
  String _discountCode = '';
  bool _loading = false;
  Map<String, dynamic>? _receipt;

  final List<Map<String, dynamic>> _variants = [
    {'id': 'var-jersey-001-M', 'label': 'Jersey - Medium', 'price': 450000},
    {'id': 'var-jersey-001-L', 'label': 'Jersey - Large', 'price': 450000},
  ];

  @override
  Widget build(BuildContext context) {
    if (_receipt != null) return _receiptView();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Club Store'),
        actions: [
          Stack(children: [
            IconButton(icon: const Icon(Icons.shopping_cart), onPressed: _cart.isEmpty ? null : _showCart),
            if (_cart.isNotEmpty) Positioned(right: 8, top: 8,
              child: Container(width: 16, height: 16,
                decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                child: Text('${_cart.length}', style: const TextStyle(color: Colors.white, fontSize: 10), textAlign: TextAlign.center))),
          ]),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _sectionHeader('Alpha Sports Collection', Icons.store),
          const SizedBox(height: 12),
          ..._variants.map(_productCard),
          const SizedBox(height: 8),
          if (_cart.isNotEmpty) _cartSection(),
        ],
      ),
    );
  }

  Widget _sectionHeader(String title, IconData icon) => Row(children: [
    Icon(icon, color: AppTheme.primary),
    const SizedBox(width: 8),
    Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
  ]);

  Widget _productCard(Map<String, dynamic> v) {
    final inCart = _cart.any((c) => c['variant_id'] == v['id']);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(children: [
          Container(width: 72, height: 72,
            decoration: BoxDecoration(color: AppTheme.primary.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.checkroom, color: AppTheme.primary, size: 40)),
          const SizedBox(width: 16),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(v['label'], style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
            const SizedBox(height: 4),
            Text('PKR ${(v['price'] as int) / 100}', style: const TextStyle(color: AppTheme.accent, fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 4),
            Text('Product: prod-jersey-001', style: TextStyle(color: Colors.grey.shade500, fontSize: 11)),
          ])),
          ElevatedButton(
            onPressed: inCart ? null : () { setState(() => _cart.add({'variant_id': v['id'], 'quantity': 1})); },
            style: ElevatedButton.styleFrom(backgroundColor: inCart ? Colors.grey : AppTheme.primary, minimumSize: const Size(80, 36)),
            child: Text(inCart ? 'Added' : 'Add'),
          ),
        ]),
      ),
    );
  }

  Widget _cartSection() => Card(
    color: AppTheme.primary.withOpacity(0.05),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Cart', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        const SizedBox(height: 12),
        ..._cart.map((c) {
          final v = _variants.firstWhere((x) => x['id'] == c['variant_id']);
          return ListTile(contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.checkroom, color: AppTheme.primary),
            title: Text(v['label']),
            subtitle: Text('PKR ${(v['price'] as int) / 100}'),
            trailing: IconButton(icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                onPressed: () => setState(() => _cart.remove(c))));
        }),
        const Divider(),
        TextField(
          decoration: const InputDecoration(labelText: 'Discount Code (e.g. WELCOME10)', prefixIcon: Icon(Icons.local_offer_outlined)),
          onChanged: (v) => setState(() => _discountCode = v.trim()),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          value: _token,
          decoration: const InputDecoration(labelText: 'Payment Method (Mock)'),
          items: const [
            DropdownMenuItem(value: 'tok_success', child: Text('✅ Credit Card (Success)')),
            DropdownMenuItem(value: 'tok_declined', child: Text('❌ Declined Card')),
            DropdownMenuItem(value: 'tok_capture_fail', child: Text('⚠️ Capture Fail')),
          ],
          onChanged: (v) => setState(() => _token = v!),
        ),
        const SizedBox(height: 16),
        SizedBox(width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _loading ? null : _checkout,
            icon: _loading ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.payment),
            label: Text(_loading ? 'Processing...' : 'Checkout  PKR ${_totalFormatted()}'),
          )),
      ]),
    ),
  );

  String _totalFormatted() {
    int total = _cart.fold(0, (s, c) {
      final v = _variants.firstWhere((x) => x['id'] == c['variant_id'], orElse: () => {'price': 0});
      return s + (v['price'] as int);
    });
    if (_discountCode == 'WELCOME10') total = (total * 0.9).floor();
    return (total / 100).toStringAsFixed(2);
  }

  Future<void> _checkout() async {
    setState(() => _loading = true);
    final orderId = 'ord-${DateTime.now().millisecondsSinceEpoch}';
    try {
      final body = {
        'order_id': orderId,
        'customer_id': 'mobile-user',
        'items': _cart,
        'discount_code': _discountCode.isEmpty ? null : _discountCode,
        'payment': {'token': _token},
      };
      final data = await ApiService.checkout(body);
      setState(() { _receipt = data; _loading = false; });
    } on ApiException catch (e) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.userMessage), backgroundColor: Colors.red));
    }
  }

  void _showCart() {
    showModalBottomSheet(context: context, builder: (_) => Padding(
      padding: const EdgeInsets.all(16),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Text('Your Cart', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        ..._cart.map((c) => ListTile(title: Text(c['variant_id']), trailing: Text('x${c['quantity']}'))),
        ElevatedButton(onPressed: () { Navigator.pop(context); _checkout(); }, child: const Text('Proceed to Checkout')),
      ]),
    ));
  }

  Widget _receiptView() {
    final receipt = _receipt!;
    final payload = receipt['receipt']?['payload'] ?? receipt;
    final total = (payload['total_minor'] ?? 0) / 100;
    final orderId = payload['order_id'] ?? receipt['order_id'] ?? '';
    return Scaffold(
      appBar: AppBar(title: const Text('Order Receipt'), backgroundColor: AppTheme.success),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(children: [
          const Icon(Icons.check_circle, color: AppTheme.success, size: 80),
          const SizedBox(height: 16),
          const Text('Payment Successful!', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppTheme.success)),
          const SizedBox(height: 24),
          Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(children: [
            _receiptRow('Order ID', orderId),
            _receiptRow('Total', 'PKR ${total.toStringAsFixed(2)}'),
            _receiptRow('Discount', 'PKR ${((payload['discount_minor'] ?? 0) / 100).toStringAsFixed(2)}'),
            _receiptRow('Status', receipt['status'] ?? 'paid'),
            _receiptRow('Paid at', payload['paid_at'] ?? ''),
          ]))),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => setState(() { _receipt = null; _cart.clear(); }),
            icon: const Icon(Icons.shopping_bag_outlined),
            label: const Text('Continue Shopping'),
          ),
        ]),
      ),
    );
  }

  Widget _receiptRow(String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
    ]),
  );
}
