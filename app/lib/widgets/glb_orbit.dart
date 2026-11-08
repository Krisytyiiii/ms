import 'dart:math' as math;

/// Spherical camera kept in Dart so each gesture writes `cameraOrbit` once.
///
/// Theta is the turn in degrees. Phi is the tilt: 0 is above the plant and
/// 180 is below it. Radius is meters. Drag follows the same signs as
/// `<model-viewer>`: dragging right decreases theta, dragging down decreases
/// phi. One view-height of drag (320 px) is a full turn.
class GlbOrbit {
  GlbOrbit({
    required this.thetaDeg,
    required double phiDeg,
    required double radius,
  }) : phiDeg = clampPhi(phiDeg),
       radius = clampRadius(radius);

  static const double minRadius = 0.02;
  static const double maxRadius = 8;
  static const double minPhiDeg = 0;
  static const double maxPhiDeg = 180;

  /// Degrees of turn or tilt for one logical pixel of drag.
  static const double degreesPerPixel = 360 / 320;

  /// Scroll grows the radius by `exp(dy * scrollPerPixel)`.
  ///
  /// About 100 pixels downward, one mouse notch, matches the Zoom out button.
  static const double scrollPerPixel = 0.002;

  double thetaDeg;
  double phiDeg;
  double radius;

  /// [dx] and [dy] are logical pixels since the last drag update.
  void dragBy(double dx, double dy) {
    thetaDeg -= dx * degreesPerPixel;
    phiDeg = clampPhi(phiDeg - dy * degreesPerPixel);
  }

  /// Positive [dy] is a downward scroll and zooms out.
  void zoomByScroll(double dy) {
    if (dy == 0 || dy.isNaN) {
      return;
    }
    radius = clampRadius(radius * math.exp(dy * scrollPerPixel));
  }

  /// [scale] is this event's factor. Greater than 1 zooms in.
  void zoomByScale(double scale) {
    if (scale <= 0 || scale.isNaN) {
      return;
    }
    radius = clampRadius(radius / scale);
  }

  void turnBy(double degrees) {
    if (degrees == 0 || degrees.isNaN) {
      return;
    }
    thetaDeg += degrees;
  }

  void scaleRadius(double factor) {
    if (factor <= 0 || factor.isNaN) {
      return;
    }
    radius = clampRadius(radius * factor);
  }

  String get cameraOrbit {
    return '${thetaDeg.toStringAsFixed(2)}deg '
        '${phiDeg.toStringAsFixed(2)}deg '
        '${radius.toStringAsFixed(3)}m';
  }

  static double clampRadius(double value) {
    return value.clamp(minRadius, maxRadius).toDouble();
  }

  static double clampPhi(double value) {
    return value.clamp(minPhiDeg, maxPhiDeg).toDouble();
  }

  /// Parses `theta phi radius` from the live viewer, in degrees and meters.
  static GlbOrbit? tryParse(String raw) {
    final parts = raw.trim().split(RegExp(r'\s+'));
    if (parts.length != 3) {
      return null;
    }
    final theta = double.tryParse(parts[0]);
    final phi = double.tryParse(parts[1]);
    final radius = double.tryParse(parts[2]);
    if (theta == null ||
        phi == null ||
        radius == null ||
        theta.isNaN ||
        phi.isNaN ||
        radius.isNaN) {
      return null;
    }
    return GlbOrbit(thetaDeg: theta, phiDeg: phi, radius: radius);
  }
}
