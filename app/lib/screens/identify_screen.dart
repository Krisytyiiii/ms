import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import '../classify/classifier.dart';
import '../data/scan_history.dart';
import '../data/scan_thumbnail.dart';
import '../theme/tokens.dart';
import '../widgets/aurora_button.dart';
import '../widgets/scanner_header.dart';
import 'result_screen.dart';

class IdentifyScreen extends StatefulWidget {
  const IdentifyScreen({super.key, required this.classifier, this.history});

  final Classifier classifier;

  /// Session scan log. When set, a finished identification is recorded and a
  /// "None of these" call removes it again.
  final ScanHistoryController? history;

  @override
  State<IdentifyScreen> createState() => _IdentifyScreenState();
}

class _IdentifyScreenState extends State<IdentifyScreen> {
  final _picker = ImagePicker();
  XFile? _image;
  Uint8List? _bytes;
  bool _busy = false;

  Future<void> _pick(ImageSource source) async {
    try {
      final picked = await _picker.pickImage(source: source);
      if (picked == null) {
        return;
      }
      final bytes = await picked.readAsBytes();
      setState(() {
        _image = picked;
        _bytes = bytes;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      final message = error is PlatformException
          ? (error.message ?? 'Could not open the camera or gallery.')
          : 'Could not open the camera or gallery.';
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _identify() async {
    if (_busy) {
      return;
    }
    final image = _image;
    if (image == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pick a camera or gallery photo first.')),
      );
      return;
    }
    setState(() => _busy = true);
    final thumbFuture = makeScanThumb(_bytes!);
    final result = await widget.classifier.identify(image);
    final thumb = await thumbFuture;
    if (!mounted) {
      return;
    }
    setState(() => _busy = false);
    final record = result.slug == null
        ? null
        : ScanRecord(
            slug: result.slug!,
            confidence: result.confidence,
            at: DateTime.now(),
            low: result.status == IdentifyStatus.lowConfidence,
            thumb: thumb,
          );
    if (record != null) {
      widget.history?.record(record);
    }
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ResultScreen(
          imageBytes: _bytes!,
          result: result,
          history: widget.history,
          record: record,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const ScannerHeader(),
        Expanded(
          child: Align(
            alignment: Alignment.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppSpace.maxContent),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: _Viewfinder(bytes: _bytes, busy: _busy),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                      decoration: BoxDecoration(
                        color: tokens.surfaceHigh,
                        borderRadius: BorderRadius.circular(AppRadius.md),
                        border: Border.all(color: tokens.border),
                        boxShadow: tokens.cardShadows,
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: SkyPalette.goldContainer,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: SkyPalette.sandDeep.withValues(
                                  alpha: 0.38,
                                ),
                              ),
                            ),
                            child: const Icon(
                              Icons.center_focus_weak_rounded,
                              size: 20,
                              color: SkyPalette.notice,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Frame a seagrass leaf, then tap Identify.',
                                  style: text.bodyMedium?.copyWith(
                                    color: tokens.ink,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Only the nine Mati species are supported.',
                                  style: text.bodySmall?.copyWith(
                                    color: tokens.inkMuted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _PickerButton(
                            icon: Icons.photo_camera_outlined,
                            label: 'Camera',
                            onPressed: () => _pick(ImageSource.camera),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: _PickerButton(
                            icon: Icons.photo_library_outlined,
                            label: 'Gallery',
                            onPressed: () => _pick(ImageSource.gallery),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    AuroraButton(
                      label: _busy ? 'Identifying…' : 'Identify',
                      icon: Icons.center_focus_strong_outlined,
                      loading: _busy,
                      compact: true,
                      onPressed: _busy ? null : _identify,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _Viewfinder extends StatelessWidget {
  const _Viewfinder({required this.bytes, required this.busy});

  final Uint8List? bytes;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        boxShadow: tokens.cardShadows,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: ColoredBox(
          color: SkyPalette.scanner,
          child: Stack(
            fit: StackFit.expand,
            children: [
              AnimatedSwitcher(
                duration: AppMotion.medium,
                switchInCurve: AppMotion.ease,
                switchOutCurve: AppMotion.ease,
                transitionBuilder: (child, animation) {
                  return FadeTransition(
                    opacity: animation,
                    child: ScaleTransition(
                      scale: Tween<double>(
                        begin: 1.03,
                        end: 1.0,
                      ).animate(animation),
                      child: child,
                    ),
                  );
                },
                child: bytes == null
                    ? Center(
                        key: const ValueKey('empty'),
                        child: Text(
                          'No photo yet',
                          style: text.titleMedium?.copyWith(
                            color: tokens.onBrand,
                          ),
                        ),
                      )
                    : Image.memory(
                        bytes!,
                        key: const ValueKey('photo'),
                        fit: BoxFit.cover,
                      ),
              ),
              IgnorePointer(
                child: CustomPaint(
                  painter: _FramePainter(color: SkyPalette.foam),
                  child: const SizedBox.expand(),
                ),
              ),
              IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: tokens.border),
                  ),
                ),
              ),
              if (busy)
                ColoredBox(
                  color: SkyPalette.scannerDeep.withValues(alpha: 0.55),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.4,
                            color: SkyPalette.foam,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          'Reading the photo…',
                          style: text.bodyMedium?.copyWith(
                            color: SkyPalette.foam,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FramePainter extends CustomPainter {
  const _FramePainter({required this.color});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
    const length = 28.0;
    const inset = 16.0;
    final right = size.width - inset;
    final bottom = size.height - inset;

    final corners = <Offset, List<Offset>>{
      const Offset(inset, inset): [
        const Offset(inset + length, inset),
        const Offset(inset, inset + length),
      ],
      Offset(right, inset): [
        Offset(right - length, inset),
        Offset(right, inset + length),
      ],
      Offset(inset, bottom): [
        Offset(inset + length, bottom),
        Offset(inset, bottom - length),
      ],
      Offset(right, bottom): [
        Offset(right - length, bottom),
        Offset(right, bottom - length),
      ],
    };

    for (final entry in corners.entries) {
      for (final end in entry.value) {
        canvas.drawLine(entry.key, end, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _FramePainter oldDelegate) =>
      oldDelegate.color != color;
}

class _PickerButton extends StatelessWidget {
  const _PickerButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return SizedBox(
      height: 48,
      child: FilledButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 18),
        label: Text(label),
        style: FilledButton.styleFrom(
          backgroundColor: tokens.surfaceHigh,
          foregroundColor: tokens.ink,
          minimumSize: const Size(0, 48),
          padding: const EdgeInsets.symmetric(horizontal: 14),
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          textStyle: Theme.of(context).textTheme.labelLarge,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.sm),
            side: BorderSide(color: tokens.border),
          ),
        ),
      ),
    );
  }
}
