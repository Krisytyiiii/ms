import 'dart:math' as math;
import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Compact isometric loop of the app's own pipeline: photo, features, SVM,
/// match, and the retake line that closes the loop.
class HowMatchWorks extends StatefulWidget {
  const HowMatchWorks({super.key});

  @override
  State<HowMatchWorks> createState() => _HowMatchWorksState();
}

class _HowMatchWorksState extends State<HowMatchWorks>
    with SingleTickerProviderStateMixin {
  late final AnimationController _relay = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 7),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _relay.stop();
      _relay.value = 0.32;
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
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: SkyPalette.primaryDark.withValues(alpha: 0.18),
            blurRadius: 30,
            spreadRadius: -4,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
          child: Stack(
            children: [
              const Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xC21D79AC), Color(0xD90B4A6E)],
                    ),
                  ),
                ),
              ),
              // Glass sheen: one soft diagonal reflection across the surface.
              Positioned.fill(
                child: IgnorePointer(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.centerRight,
                        colors: [
                          Colors.white.withValues(alpha: 0.22),
                          Colors.white.withValues(alpha: 0),
                        ],
                        stops: const [0, 0.6],
                      ),
                    ),
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.22),
                  ),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'How the match is made',
                      style: text.labelSmall?.copyWith(
                        color: SkyPalette.onHeader.withValues(alpha: 0.8),
                        fontWeight: FontWeight.w600,
                        letterSpacing: 1,
                        fontSize: 9.5,
                      ),
                    ),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 108,
                      child: CustomPaint(painter: _LoopPainter(relay: _relay)),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LoopPainter extends CustomPainter {
  _LoopPainter({required this.relay}) : super(repaint: relay);

  final Animation<double> relay;

  static const _plates = [
    (Icons.photo_camera_outlined, 'Photo', SkyPalette.water),
    (Icons.grid_view_rounded, 'Features', Color(0xFF6FB6E8)),
    (Icons.memory_rounded, 'SVM', SkyPalette.goldDeep),
    (Icons.percent_rounded, 'Match', SkyPalette.goldBright),
  ];

  static const _plateWidth = 44.0;
  static const _plateHeight = 46.0;
  static const _plateCenterY = 34.0;
  static const _bottomLine = 86.0;

  @override
  void paint(Canvas canvas, Size size) {
    final centers = [
      Offset(size.width * 0.13, _plateCenterY),
      Offset(size.width * 0.375, _plateCenterY),
      Offset(size.width * 0.625, _plateCenterY),
      Offset(size.width * 0.87, _plateCenterY),
    ];

    final conduit = Paint()
      ..color = Colors.white.withValues(alpha: 0.22)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..strokeCap = StrokeCap.round;

    for (var i = 0; i < centers.length - 1; i++) {
      final from = Offset(centers[i].dx + _plateWidth / 2 - 2, _plateCenterY);
      final to = Offset(centers[i + 1].dx - _plateWidth / 2 + 2, _plateCenterY);
      final bend = (to.dx - from.dx) * 0.42;
      final path = Path()
        ..moveTo(from.dx, from.dy)
        ..cubicTo(
          from.dx + bend,
          from.dy - 5,
          to.dx - bend,
          to.dy - 5,
          to.dx,
          to.dy,
        );
      _dashed(canvas, path, conduit);
    }

    final last = centers.last;
    final first = centers.first;
    final returnPath = Path()..moveTo(last.dx + _plateWidth / 2, _plateCenterY);
    _addReturn(returnPath, first, last, size.width);
    _dashed(canvas, returnPath, conduit);

    // Small notch where the loop re-enters the first plate.
    final notch = Paint()
      ..color = Colors.white.withValues(alpha: 0.34)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..strokeCap = StrokeCap.round;
    final tip = Offset(first.dx - _plateWidth / 2 + 1, _plateCenterY);
    canvas.drawPath(
      Path()
        ..moveTo(tip.dx - 4, tip.dy - 3)
        ..lineTo(tip.dx, tip.dy)
        ..lineTo(tip.dx - 4, tip.dy + 3),
      notch,
    );

    _comet(canvas, centers, size.width);

    for (var i = 0; i < centers.length; i++) {
      _plate(canvas, centers[i], _plates[i].$1, _plates[i].$3);
      _text(
        canvas,
        _plates[i].$2,
        Offset(centers[i].dx, _plateCenterY + _plateHeight / 2 + 12),
        color: SkyPalette.onHeader.withValues(alpha: 0.76),
        size: 9.5,
        weight: FontWeight.w600,
        spacing: 0.2,
      );
    }

    _gem(canvas, Offset(size.width / 2, _bottomLine));
    _text(
      canvas,
      'retake',
      Offset(size.width / 2, _bottomLine + 14),
      color: SkyPalette.goldDeep.withValues(alpha: 0.82),
      size: 8,
      weight: FontWeight.w600,
      spacing: 0.8,
    );
  }

  /// Extends [path] from the last plate's right edge, around the outside,
  /// and back into the first plate's left edge.
  void _addReturn(Path path, Offset first, Offset last, double width) {
    const edge = 8.0;
    final exitX = width - edge;
    path
      ..lineTo(exitX - 10, _plateCenterY)
      ..quadraticBezierTo(exitX, _plateCenterY, exitX, _plateCenterY + 10)
      ..lineTo(exitX, _bottomLine - 10)
      ..quadraticBezierTo(exitX, _bottomLine, exitX - 10, _bottomLine)
      ..lineTo(edge + 10, _bottomLine)
      ..quadraticBezierTo(edge, _bottomLine, edge, _bottomLine - 10)
      ..lineTo(edge, _plateCenterY + 10)
      ..quadraticBezierTo(edge, _plateCenterY, edge + 10, _plateCenterY)
      ..lineTo(first.dx - _plateWidth / 2, _plateCenterY);
  }

  void _comet(Canvas canvas, List<Offset> centers, double width) {
    final path = Path()..moveTo(centers.first.dx, centers.first.dy);
    for (var i = 0; i < centers.length - 1; i++) {
      final from = centers[i];
      final to = centers[i + 1];
      final bend = (to.dx - from.dx) * 0.42;
      path.cubicTo(
        from.dx + bend,
        from.dy - 5,
        to.dx - bend,
        to.dy - 5,
        to.dx,
        to.dy,
      );
    }
    final last = centers.last;
    final fromEdge = Offset(last.dx + _plateWidth / 2, _plateCenterY);
    path.lineTo(fromEdge.dx, fromEdge.dy);
    _addReturn(path, centers.first, last, width);

    final metric = path.computeMetrics().first;
    final head = metric.getTangentForOffset(
      metric.length * (0.02 + relay.value * 0.96),
    );
    if (head == null) {
      return;
    }
    final trailOffset = (metric.length * (0.02 + relay.value * 0.96) - 9).clamp(
      0.0,
      metric.length,
    );
    final tail = metric.getTangentForOffset(trailOffset);
    if (tail != null) {
      canvas.drawLine(
        tail.position,
        head.position,
        Paint()
          ..shader = const LinearGradient(
            colors: [Color(0x00FFE45C), Color(0xFFFFE45C)],
          ).createShader(Rect.fromPoints(tail.position, head.position))
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.4
          ..strokeCap = StrokeCap.round,
      );
    }
    canvas.drawCircle(
      head.position,
      4.5,
      Paint()
        ..color = SkyPalette.goldBright.withValues(alpha: 0.22)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4),
    );
    canvas.drawCircle(
      head.position,
      1.8,
      Paint()..color = SkyPalette.goldBright,
    );
  }

  void _plate(Canvas canvas, Offset center, IconData icon, Color accent) {
    final rect = Rect.fromCenter(
      center: Offset.zero,
      width: _plateWidth,
      height: _plateHeight,
    );

    canvas.save();
    canvas.translate(center.dx, center.dy);

    // Warm accent glow on the floor, the way the reference badges light up.
    canvas.drawCircle(
      const Offset(1, 9),
      26,
      Paint()
        ..color = accent.withValues(alpha: 0.12)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: const Offset(1, 9),
          width: _plateWidth + 4,
          height: _plateHeight * 0.62,
        ),
        const Radius.circular(12),
      ),
      Paint()
        ..color = const Color(0x77000000)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 7),
    );

    // A gentle isometric lean: the row reads as objects on a table.
    canvas.transform(Matrix4.skewY(-0.05).storage);
    canvas.rotate(-0.09);

    // Extruded body: back-to-front slices build a real edge.
    const depth = 7;
    for (var i = depth; i >= 1; i--) {
      final slice = RRect.fromRectAndRadius(
        rect.shift(Offset(0.55 * i, 0.7 * i)),
        const Radius.circular(8),
      );
      canvas.drawRRect(
        slice,
        Paint()
          ..color = Color.lerp(
            const Color(0xFF071B29),
            const Color(0xFF16405A),
            1 - i / depth,
          )!,
      );
    }

    final face = RRect.fromRectAndRadius(rect, const Radius.circular(8));
    canvas.drawRRect(
      face,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF4782A6), Color(0xFF2A5874), Color(0xFF16405A)],
          stops: [0, 0.55, 1],
        ).createShader(rect),
    );

    // Top-left sheen and crisp rim.
    canvas.save();
    canvas.clipRRect(face);
    canvas.drawRect(
      rect,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withValues(alpha: 0.14),
            Colors.white.withValues(alpha: 0),
          ],
          stops: const [0, 0.55],
        ).createShader(rect),
    );
    canvas.restore();
    canvas.drawRRect(
      face,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..color = Colors.white.withValues(alpha: 0.14),
    );

    _chip(canvas, icon, accent);

    canvas.restore();
  }

  /// A raised mini badge: extruded plate plus a lit icon.
  void _chip(Canvas canvas, IconData icon, Color accent) {
    const size = 22.0;
    final rect = Rect.fromCenter(
      center: const Offset(0, -2),
      width: size,
      height: size,
    );

    canvas.drawCircle(
      const Offset(0.5, -1),
      13,
      Paint()
        ..color = accent.withValues(alpha: 0.2)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 7),
    );

    for (var i = 2; i >= 1; i--) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          rect.shift(Offset(0.35 * i, 0.5 * i)),
          const Radius.circular(6),
        ),
        Paint()..color = const Color(0xFF04111C),
      );
    }

    final face = RRect.fromRectAndRadius(rect, const Radius.circular(6));
    canvas.drawRRect(
      face,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color.lerp(accent, Colors.white, 0.24)!,
            accent,
            Color.lerp(accent, const Color(0xFF04121E), 0.14)!,
          ],
        ).createShader(rect),
    );
    canvas.drawRRect(
      face,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..color = Colors.white.withValues(alpha: 0.24),
    );

    _glyph(canvas, icon, const Offset(0, -2), const Color(0xFF04141F), 14);
  }

  void _gem(Canvas canvas, Offset center) {
    const s = 8.0;

    canvas.drawOval(
      Rect.fromCenter(
        center: center + const Offset(0, s * 0.95),
        width: s * 2.1,
        height: s * 0.7,
      ),
      Paint()
        ..color = const Color(0x99000000)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4),
    );
    canvas.drawCircle(
      center,
      17,
      Paint()
        ..color = SkyPalette.goldDeep.withValues(alpha: 0.2)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8),
    );

    final topLeft = Path()
      ..moveTo(center.dx, center.dy - s * 1.0)
      ..lineTo(center.dx - s * 0.64, center.dy - s * 0.34)
      ..lineTo(center.dx, center.dy + s * 0.2)
      ..close();
    canvas.drawPath(topLeft, Paint()..color = SkyPalette.goldBright);

    final topRight = Path()
      ..moveTo(center.dx, center.dy - s * 1.0)
      ..lineTo(center.dx + s * 0.64, center.dy - s * 0.34)
      ..lineTo(center.dx, center.dy + s * 0.2)
      ..close();
    canvas.drawPath(topRight, Paint()..color = const Color(0xFFFFD34D));

    final left = Path()
      ..moveTo(center.dx - s * 0.64, center.dy - s * 0.34)
      ..lineTo(center.dx, center.dy + s * 0.2)
      ..lineTo(center.dx, center.dy + s * 1.1)
      ..lineTo(center.dx - s * 0.64, center.dy + s * 0.5)
      ..close();
    canvas.drawPath(left, Paint()..color = SkyPalette.goldDeep);

    final right = Path()
      ..moveTo(center.dx + s * 0.64, center.dy - s * 0.34)
      ..lineTo(center.dx, center.dy + s * 0.2)
      ..lineTo(center.dx, center.dy + s * 1.1)
      ..lineTo(center.dx + s * 0.64, center.dy + s * 0.5)
      ..close();
    canvas.drawPath(right, Paint()..color = const Color(0xFFD9A400));

    canvas.drawPath(
      Path()
        ..moveTo(center.dx, center.dy - s * 1.0)
        ..lineTo(center.dx - s * 0.64, center.dy - s * 0.34)
        ..lineTo(center.dx, center.dy + s * 0.2)
        ..lineTo(center.dx + s * 0.64, center.dy - s * 0.34)
        ..close(),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 0.8
        ..color = Colors.white.withValues(alpha: 0.35),
    );
  }

  void _glyph(
    Canvas canvas,
    IconData icon,
    Offset center,
    Color color,
    double size,
  ) {
    final painter = TextPainter(
      text: TextSpan(
        text: String.fromCharCode(icon.codePoint),
        style: TextStyle(
          fontFamily: icon.fontFamily,
          package: icon.fontPackage,
          fontSize: size,
          color: color,
          height: 1,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(
      canvas,
      center - Offset(painter.width / 2, painter.height / 2),
    );
  }

  void _text(
    Canvas canvas,
    String value,
    Offset center, {
    required Color color,
    required double size,
    required FontWeight weight,
    required double spacing,
  }) {
    final painter = TextPainter(
      text: TextSpan(
        text: value,
        style: TextStyle(
          color: color,
          fontSize: size,
          fontWeight: weight,
          letterSpacing: spacing,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(
      canvas,
      Offset(center.dx - painter.width / 2, center.dy - painter.height / 2),
    );
  }

  void _dashed(Canvas canvas, Path path, Paint paint) {
    const dash = 3.2;
    const gap = 3.4;
    for (final metric in path.computeMetrics()) {
      var distance = 0.0;
      while (distance < metric.length) {
        final end = math.min(distance + dash, metric.length);
        canvas.drawPath(metric.extractPath(distance, end), paint);
        distance = end + gap;
      }
    }
  }

  @override
  bool shouldRepaint(covariant _LoopPainter oldDelegate) => false;
}
