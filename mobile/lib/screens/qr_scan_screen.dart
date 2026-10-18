import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/deep_link_router.dart';

class QrScanScreen extends StatefulWidget {
  const QrScanScreen({super.key});
  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen> {
  final MobileScannerController _controller = MobileScannerController(autoStart: false);
  bool _busy = false;
  bool _cameraOn = false;
  String? _message;

  Future<void> _enableCamera() async {
    try {
      await _controller.start(); // triggers the OS permission dialog if not yet granted
      if (mounted) setState(() => _cameraOn = true);
    } catch (e) {
      if (mounted) setState(() => _message = 'Camera unavailable: $e');
    }
  }

  @override
  void dispose() { _controller.dispose(); super.dispose(); }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_busy) return;
    final raw = capture.barcodes.isEmpty ? null : capture.barcodes.first.rawValue;
    if (raw == null) return;

    setState(() { _busy = true; _message = 'Resolving QR code...'; });
    String? entityId;
    try {
      entityId = await resolveEntityId(raw);
    } catch (_) {
      entityId = null;
    }
    if (!mounted) return;

    if (entityId == null) {
      setState(() { _busy = false; _message = 'Not a NaSCon QR code, or the server is unreachable.'; });
      return;
    }
    setState(() => _message = null);
    await _controller.stop();
    if (!mounted) return;
    navigateToEntity(context, entityId);
    // Re-arm the scanner when the user comes back to this tab.
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;
    await _controller.start();
    setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    if (!_cameraOn) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.qr_code_scanner_rounded, size: 72, color: scheme.primary),
            const SizedBox(height: 16),
            const Text('Scan NaSCon QR codes', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            const Text('We need your camera to read match, club and player QR codes. Nothing is recorded or uploaded.',
                textAlign: TextAlign.center),
            const SizedBox(height: 20),
            ElevatedButton.icon(onPressed: _enableCamera, icon: const Icon(Icons.camera_alt_rounded), label: const Text('Allow camera')),
            if (_message != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_message!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red))),
          ]),
        ),
      );
    }
    return Stack(
      children: [
        MobileScanner(
          controller: _controller,
          onDetect: _onDetect,
          errorBuilder: (context, error, _) => Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.no_photography_rounded, size: 56),
              const SizedBox(height: 8),
              Text(error.errorCode == MobileScannerErrorCode.permissionDenied
                  ? 'Camera permission denied. Enable it in Settings > Apps > nascon26_app.'
                  : 'Camera error: ${error.errorCode.name}', textAlign: TextAlign.center),
              TextButton(onPressed: () => _controller.start(), child: const Text('Try again')),
            ]),
          ),
        ),
        Center(
          child: Container(
            width: 240, height: 240,
            decoration: BoxDecoration(
              border: Border.all(color: scheme.primary, width: 3),
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ),
        Positioned(
          top: 16, left: 0, right: 0,
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
              child: const Text('Point the camera at a NaSCon QR code', style: TextStyle(color: Colors.white)),
            ),
          ),
        ),
        if (_message != null)
          Positioned(
            bottom: 24, left: 16, right: 16,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(12)),
              child: Row(children: [
                if (_busy) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                if (_busy) const SizedBox(width: 12),
                Expanded(child: Text(_message!, style: const TextStyle(color: Colors.white))),
              ]),
            ),
          ),
      ],
    );
  }
}
