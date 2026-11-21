import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Slow water lines behind page content. Strokes, not filled bands: they read
/// as distance and depth without staining the copy. Stops when the system asks
/// for reduced motion.
class WaveField extends StatefulWidget {
  const WaveField({super.key, this.height = 264});

  final double height;

  @override
  State<WaveField> createState() => _WaveFieldState();
}

class _WaveFieldState extends State<WaveField>
    with SingleTickerProviderStateMixin {
  late final AnimationController _drift = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 26),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _drift.stop();
    } else if (!_drift.isAnimating) {
      _drift.repeat();
    }
  }

  @override
  void dispose() {
    _drift.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final still = MediaQuery.disableAnimationsOf(context);

    return Align(
      alignment: Alignment.bottomCenter,
      child: IgnorePointer(
        child: SizedBox(
          height: widget.height,
          width: double.infinity,
          child: AnimatedBuilder(
            animation: _drift,
            builder: (context, _) {
              return CustomPaint(
                painter: _WaveFieldPainter(phase: still ? 0.18 : _drift.value),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _WaveLine {
  const _WaveLine({
    required this.top,
    required this.amplitude,
    required this.turns,
    required this.shift,
    required this.color,
    this.width = 1,
  });

  /// 0..1 of the painted height.
  final double top;
  final double amplitude;
  final double turns;
  final double shift;
  final Color color;
  final double width;
}

const _lines = <_WaveLine>[
  _WaveLine(
    top: 0.42,
    amplitude: 9,
    turns: 1.2,
    shift: 0.0,
    color: Color(0x2E0077B6),
    width: 1.2,
  ),
  _WaveLine(
    top: 0.62,
    amplitude: 7,
    turns: 1.7,
    shift: 0.35,
    color: Color(0x3348CAE4),
  ),
  _WaveLine(
    top: 0.82,
    amplitude: 6,
    turns: 2.2,
    shift: 0.72,
    color: Color(0x33FFC300),
  ),
];

class _WaveFieldPainter extends CustomPainter {
  const _WaveFieldPainter({required this.phase});

  final double phase;

  @override
  void paint(Canvas canvas, Size size) {
    // Deep water gathering at the base.
    final washTop = size.height * 0.42;
    final wash = Rect.fromLTWH(0, washTop, size.width, size.height - washTop);
    canvas.drawRect(
      wash,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0x000077B6), Color(0x140077B6)],
        ).createShader(wash),
    );

    for (final line in _lines) {
      canvas.drawPath(
        _crest(line, size),
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = line.width
          ..strokeCap = StrokeCap.round
          ..color = line.color,
      );
    }
  }

  Path _crest(_WaveLine line, Size size) {
    final base = size.height * line.top;
    final path = Path();
    var x = 0.0;
    while (x <= size.width + 4) {
      final u = size.width == 0 ? 0.0 : x / size.width;
      final y =
          base +
          math.sin((u * line.turns + phase + line.shift) * math.pi * 2) *
              line.amplitude;
      if (x == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
      x += 6;
    }
    return path;
  }

  @override
  bool shouldRepaint(covariant _WaveFieldPainter oldDelegate) {
    return oldDelegate.phase != phase;
  }
}
