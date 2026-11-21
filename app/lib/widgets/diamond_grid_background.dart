import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Ambient diamond grid behind the app: a faint 45-degree lattice with a few
/// seeded four-point sparks that breathe slowly. It sits behind every screen,
/// so cards and copy still carry the contrast.
class DiamondGridBackground extends StatefulWidget {
  const DiamondGridBackground({super.key, this.seed = 1337});

  final int seed;

  @override
  State<DiamondGridBackground> createState() => _DiamondGridBackgroundState();
}

class _DiamondGridBackgroundState extends State<DiamondGridBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _relay = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 14),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _relay.stop();
      _relay.value = 0.28;
    } else if (!_relay.isAnimating) {
      _relay.repeat();
    }
  }

  @override
  void dispose() {
    _relay.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(
        painter: _DiamondGridPainter(relay: _relay, seed: widget.seed),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _DiamondGridPainter extends CustomPainter {
  _DiamondGridPainter({required this.relay, required this.seed})
    : super(repaint: relay);

  final Animation<double> relay;
  final int seed;

  static const _spacing = 46.0;
  static const _root2 = 0.7071067811865476;

  /// Lattice cells (i, j). Rotating the grid puts these on real intersections.
  static const _cells = <(int, int)>[
    (0, 0),
    (3, -2),
    (-2, 3),
    (5, 4),
    (-4, -3),
    (7, -3),
    (-6, 5),
    (9, 2),
    (2, 9),
    (-8, 1),
    (4, -8),
    (-3, -8),
    (10, -4),
    (-9, -5),
    (11, 3),
    (-11, 6),
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final center = rect.center;

    final line = Paint()
      ..color = SkyPalette.primary.withValues(alpha: 0.07)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.7;

    final extent = size.width + size.height;
    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(math.pi / 4);
    for (var d = -extent; d <= extent; d += _spacing) {
      canvas.drawLine(Offset(d, -extent), Offset(d, extent), line);
      canvas.drawLine(Offset(-extent, d), Offset(extent, d), line);
    }
    canvas.restore();

    final random = math.Random(seed);
    var index = 0;
    for (final cell in _cells) {
      final position =
          center +
          Offset(
            (cell.$1 - cell.$2) * _spacing * _root2,
            (cell.$1 + cell.$2) * _spacing * _root2,
          );
      if (!rect.deflate(10).contains(position)) {
        index++;
        continue;
      }

      final phase = (index / _cells.length) + random.nextDouble() * 0.18;
      final pulse = 0.5 + 0.5 * math.sin(2 * math.pi * (relay.value + phase));
      final color = index % 5 == 0 ? SkyPalette.goldDeep : SkyPalette.primary;
      final alpha = 0.16 + 0.3 * pulse;
      final radius = 5 + (index % 3) * 1.7;

      canvas.drawCircle(
        position,
        radius * 2.4,
        Paint()
          ..color = color.withValues(alpha: alpha * 0.22)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6),
      );
      canvas.drawPath(
        _star(position, radius),
        Paint()..color = color.withValues(alpha: alpha),
      );
      canvas.drawCircle(
        position,
        1,
        Paint()..color = color.withValues(alpha: alpha + 0.16),
      );
      index++;
    }
  }

  Path _star(Offset center, double radius) {
    const waist = 0.9;
    return Path()
      ..moveTo(center.dx, center.dy - radius)
      ..quadraticBezierTo(
        center.dx + waist,
        center.dy - waist,
        center.dx + radius,
        center.dy,
      )
      ..quadraticBezierTo(
        center.dx + waist,
        center.dy + waist,
        center.dx,
        center.dy + radius,
      )
      ..quadraticBezierTo(
        center.dx - waist,
        center.dy + waist,
        center.dx - radius,
        center.dy,
      )
      ..quadraticBezierTo(
        center.dx - waist,
        center.dy - waist,
        center.dx,
        center.dy - radius,
      )
      ..close();
  }

  @override
  bool shouldRepaint(covariant _DiamondGridPainter oldDelegate) =>
      oldDelegate.seed != seed;
}
