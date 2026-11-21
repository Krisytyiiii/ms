import 'dart:math' as math;

import 'package:flutter/material.dart';

/// A full-bleed surface whose bottom edge rises and falls like water.
///
/// The curve is deliberately shallow: it should read as a water line, not as
/// decoration. It is a sampled sine so the crests never kink.
class WaveEdgeClipper extends CustomClipper<Path> {
  const WaveEdgeClipper({this.amplitude = 7});

  final double amplitude;

  @override
  Path getClip(Size size) => waveEdgePath(size, amplitude: amplitude);

  @override
  bool shouldReclip(covariant WaveEdgeClipper oldClipper) {
    return oldClipper.amplitude != amplitude;
  }
}

/// Height of the wavy edge at [x], in the same coordinate space as the box.
double waveEdgeY(double x, Size size, {double amplitude = 7}) {
  final w = size.width;
  final u = w == 0 ? 0.0 : x / w;
  // One full gentle rise and fall, settling on the baseline at both edges.
  return size.height -
      amplitude +
      math.sin(u * math.pi * 2 + 0.35) * amplitude * 0.55;
}

/// Shared geometry so the clip and the foam line follow the same curve.
Path waveEdgePath(Size size, {double amplitude = 7}) {
  final path = Path()
    ..moveTo(0, 0)
    ..lineTo(size.width, 0)
    ..lineTo(size.width, waveEdgeY(size.width, size, amplitude: amplitude));

  for (var x = size.width - 2; x >= 0; x -= 2) {
    path.lineTo(x, waveEdgeY(x, size, amplitude: amplitude));
  }
  path.close();
  return path;
}

/// Thin foam line on the wavy edge, so the photo sits in water rather than
/// stopping on a hard cut.
class WaveEdgeLine extends StatelessWidget {
  const WaveEdgeLine({
    super.key,
    this.amplitude = 7,
    this.color = const Color(0x8CFFFFFF),
  });

  final double amplitude;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(
        painter: _WaveLinePainter(amplitude: amplitude, color: color),
      ),
    );
  }
}

class _WaveLinePainter extends CustomPainter {
  const _WaveLinePainter({required this.amplitude, required this.color});

  final double amplitude;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final line = Path();
    for (var x = 0.0; x <= size.width + 2; x += 2) {
      final y = waveEdgeY(x, size, amplitude: amplitude);
      if (x == 0) {
        line.moveTo(x, y);
      } else {
        line.lineTo(x, y);
      }
    }

    canvas.drawPath(
      line,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4
        ..strokeCap = StrokeCap.round
        ..color = color,
    );
  }

  @override
  bool shouldRepaint(covariant _WaveLinePainter oldDelegate) {
    return oldDelegate.amplitude != amplitude || oldDelegate.color != color;
  }
}
