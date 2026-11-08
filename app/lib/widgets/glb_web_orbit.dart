import 'dart:async';

import 'glb_orbit.dart';
import 'page_script_stub.dart'
    if (dart.library.js_interop) 'page_script_web.dart';

/// Web camera. The first successful read keeps theta, phi, and radius.
/// Later drags, scrolls, and pinches each write `cameraOrbit` once.
class GlbWebOrbit {
  GlbWebOrbit({this.isActive = _alwaysActive});

  final bool Function() isActive;

  static bool _alwaysActive() => true;

  GlbOrbit? _orbit;
  Future<GlbOrbit?>? _loading;
  var _loadAttempts = 0;
  var _pendingDx = 0.0;
  var _pendingDy = 0.0;
  var _pendingScroll = 0.0;
  var _pendingScale = 1.0;
  var _scaleQueued = false;

  static const _readOrbitSource = '''
(() => {
  const mv = document.getElementById('marinesee-model');
  if (!mv || !mv.loaded || !mv.getCameraOrbit) return '';
  const orbit = mv.getCameraOrbit();
  return (orbit.theta * 180 / Math.PI) + ' ' +
    (orbit.phi * 180 / Math.PI) + ' ' + orbit.radius;
})()
''';

  void dragBy(double dx, double dy) {
    _pendingDx += dx;
    _pendingDy += dy;
    _flushPending();
  }

  void scrollBy(double dy) {
    if (dy == 0 || dy.isNaN) {
      return;
    }
    _pendingScroll += dy;
    _flushPending();
  }

  void pinchBy(double scale) {
    if (scale <= 0 || scale.isNaN) {
      return;
    }
    _pendingScale *= scale;
    _scaleQueued = true;
    _flushPending();
  }

  Future<void> nudge({double thetaDeg = 0, double radiusScale = 1}) async {
    final orbit = await _orbitReady();
    if (!isActive() || orbit == null) {
      return;
    }
    orbit.turnBy(thetaDeg);
    orbit.scaleRadius(radiusScale);
    _publish(orbit);
  }

  void releasePointer() {
    unawaited(
      _run('''
        (() => {
          let tries = 0;
          const pass = (el) => {
            if (el && el.style) el.style.pointerEvents = 'none';
          };
          const start = () => {
            const mv = document.getElementById('marinesee-model');
            if (!mv) {
              if (tries++ < 40) setTimeout(start, 200);
              return;
            }
            let node = mv;
            while (node && node !== document.body) {
              const tag = (node.tagName || '').toLowerCase();
              if (tag === 'flutter-view' || tag === 'flt-glass-pane') break;
              pass(node);
              const slot = node.assignedSlot;
              if (slot) {
                pass(slot);
                const host = slot.parentElement;
                if (host && (host.tagName || '').toLowerCase() === 'flt-platform-view-slot') {
                  pass(host);
                }
              }
              node = node.parentElement;
            }
          };
          start();
        })();
      '''),
    );
  }

  Future<void> _run(String source) async {
    try {
      await runPageScript(source);
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  void _publish(GlbOrbit orbit) {
    final value = orbit.cameraOrbit;
    unawaited(
      _run('''
        (() => {
          const mv = document.getElementById('marinesee-model');
          if (!mv) return;
          mv.cameraOrbit = '$value';
        })();
      '''),
    );
  }

  void _flushPending() {
    final orbit = _orbit;
    if (orbit == null) {
      _orbitReady();
      return;
    }
    var changed = false;
    if (_pendingDx != 0 || _pendingDy != 0) {
      orbit.dragBy(_pendingDx, _pendingDy);
      _pendingDx = 0;
      _pendingDy = 0;
      changed = true;
    }
    if (_pendingScroll != 0) {
      orbit.zoomByScroll(_pendingScroll);
      _pendingScroll = 0;
      changed = true;
    }
    if (_scaleQueued) {
      orbit.zoomByScale(_pendingScale);
      _pendingScale = 1;
      _scaleQueued = false;
      changed = true;
    }
    if (changed) {
      _publish(orbit);
    }
  }

  Future<GlbOrbit?> _orbitReady() {
    final orbit = _orbit;
    if (orbit != null) {
      return Future<GlbOrbit?>.value(orbit);
    }
    final loading = _loading;
    if (loading != null) {
      return loading;
    }
    if (_loadAttempts >= 40) {
      _loadAttempts = 0;
    }
    final next = _loadOrbit();
    _loading = next;
    return next;
  }

  Future<GlbOrbit?> _loadOrbit() async {
    try {
      while (isActive() && _orbit == null && _loadAttempts < 40) {
        _loadAttempts += 1;
        String? raw;
        try {
          raw = await readPageScript(_readOrbitSource);
        } on Object {
          raw = null;
        }
        final parsed = raw == null ? null : GlbOrbit.tryParse(raw);
        if (parsed != null) {
          _orbit = parsed;
          _flushPending();
          return parsed;
        }
        await Future<void>.delayed(const Duration(milliseconds: 200));
      }
      return _orbit;
    } finally {
      _loading = null;
    }
  }
}
