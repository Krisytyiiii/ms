import 'dart:math' as math;

import 'package:flutter_test/flutter_test.dart';
import 'package:marine_see/widgets/glb_orbit.dart';

void main() {
  test('drag turns and tilts', () {
    final orbit = GlbOrbit(thetaDeg: 10, phiDeg: 75, radius: 2);

    orbit.dragBy(8, -4);

    expect(orbit.thetaDeg, 10 - 8 * GlbOrbit.degreesPerPixel);
    expect(orbit.phiDeg, 75 + 4 * GlbOrbit.degreesPerPixel);
    expect(orbit.radius, 2);

    orbit.dragBy(0, 10000);
    expect(orbit.phiDeg, GlbOrbit.minPhiDeg);
    orbit.dragBy(0, -10000);
    expect(orbit.phiDeg, GlbOrbit.maxPhiDeg);
  });

  test('scroll down zooms out and scroll up zooms in', () {
    final orbit = GlbOrbit(thetaDeg: 0, phiDeg: 75, radius: 2);

    orbit.zoomByScroll(100);

    expect(
      orbit.radius,
      closeTo(2 * math.exp(100 * GlbOrbit.scrollPerPixel), 1e-9),
    );
    expect(orbit.radius, greaterThan(2));

    orbit.zoomByScroll(-100);

    expect(orbit.radius, closeTo(2, 1e-9));
  });

  test('pinch uses the same radius', () {
    final orbit = GlbOrbit(thetaDeg: 0, phiDeg: 75, radius: 2);

    orbit.zoomByScale(2);
    expect(orbit.radius, 1);

    orbit.zoomByScale(0.5);
    expect(orbit.radius, 2);

    orbit.zoomByScale(0);
    expect(orbit.radius, 2);
  });

  test('radius stays inside the closest and farthest zoom', () {
    final orbit = GlbOrbit(thetaDeg: 0, phiDeg: 75, radius: 1);

    orbit.zoomByScroll(100000);
    expect(orbit.radius, GlbOrbit.maxRadius);

    orbit.zoomByScroll(-100000);
    expect(orbit.radius, GlbOrbit.minRadius);

    orbit.zoomByScale(0.00001);
    expect(orbit.radius, GlbOrbit.maxRadius);

    orbit.zoomByScale(1000);
    expect(orbit.radius, GlbOrbit.minRadius);

    expect(
      GlbOrbit.tryParse('1 200 0.01'),
      isA<GlbOrbit>()
          .having((orbit) => orbit.radius, 'radius', GlbOrbit.minRadius)
          .having((orbit) => orbit.phiDeg, 'phi', GlbOrbit.maxPhiDeg),
    );
    expect(GlbOrbit.tryParse('nope'), isNull);
  });
}
