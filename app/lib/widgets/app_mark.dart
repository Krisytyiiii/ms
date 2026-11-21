import 'package:flutter/material.dart';

/// Vector MarineSee mark: two seagrass blades and a water line on an ocean
/// tile. Drawn, not a raster, so it stays crisp from 24 px to a splash size.
class MarineSeeMark extends StatelessWidget {
  const MarineSeeMark({super.key, required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: const _MarkPainter()),
    );
  }
}

class _MarkPainter extends CustomPainter {
  const _MarkPainter();

  static const _bladeTop = Color(0xFFFFFFFF);
  static const _bladeSide = Color(0xFFFFD60A);

  @override
  void paint(Canvas canvas, Size size) {
    final s = size.width;
    if (s <= 0) {
      return;
    }
    final rect = Offset.zero & size;
    final tile = RRect.fromRectAndRadius(rect, Radius.circular(s * 0.31));

    canvas.drawRRect(
      tile,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF0077B6), Color(0xFF0263A2), Color(0xFF023E8A)],
          stops: [0.0, 0.52, 1.0],
        ).createShader(rect),
    );

    canvas.save();
    canvas.clipRRect(tile);

    // Light enters the water at the top left.
    canvas.drawRect(
      rect,
      Paint()
        ..shader = RadialGradient(
          center: const Alignment(-0.65, -0.95),
          radius: 1.35,
          colors: [
            const Color(0xFFFFFFFF).withValues(alpha: 0.34),
            const Color(0x00FFFFFF),
          ],
        ).createShader(rect),
    );

    // Deeper water at the base.
    canvas.drawRect(
      rect,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0x00023E8A), Color(0x4D023E8A)],
          stops: [0.45, 1.0],
        ).createShader(rect),
    );

    // Water line behind the shoots.
    final wave = Path()
      ..moveTo(-0.06 * s, 0.80 * s)
      ..cubicTo(0.16 * s, 0.735 * s, 0.34 * s, 0.87 * s, 0.53 * s, 0.805 * s)
      ..cubicTo(0.72 * s, 0.74 * s, 0.86 * s, 0.865 * s, 1.06 * s, 0.79 * s);
    canvas.drawPath(
      wave,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.052
        ..strokeCap = StrokeCap.round
        ..color = const Color(0xFFFFFFFF).withValues(alpha: 0.34),
    );

    // Tall shoot, leaning right.
    final tall = Path()
      ..moveTo(0.500 * s, 0.870 * s)
      ..cubicTo(
        0.502 * s,
        0.645 * s,
        0.578 * s,
        0.382 * s,
        0.664 * s,
        0.218 * s,
      )
      ..cubicTo(
        0.690 * s,
        0.292 * s,
        0.626 * s,
        0.610 * s,
        0.572 * s,
        0.870 * s,
      )
      ..close();
    canvas.drawPath(
      tall,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Color(0xFFEAF3F8), _bladeTop],
        ).createShader(rect),
    );

    // Short shoot, leaning left.
    final short = Path()
      ..moveTo(0.372 * s, 0.870 * s)
      ..cubicTo(
        0.366 * s,
        0.716 * s,
        0.328 * s,
        0.588 * s,
        0.260 * s,
        0.468 * s,
      )
      ..cubicTo(
        0.300 * s,
        0.494 * s,
        0.398 * s,
        0.702 * s,
        0.452 * s,
        0.870 * s,
      )
      ..close();
    canvas.drawPath(
      short,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Color(0xFFFFE45C), _bladeSide],
        ).createShader(rect),
    );

    canvas.restore();

    canvas.drawRRect(
      tile.deflate(s * 0.012),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.024
        ..color = const Color(0xFFFFFFFF).withValues(alpha: 0.28),
    );
  }

  @override
  bool shouldRepaint(covariant _MarkPainter oldDelegate) => false;
}
