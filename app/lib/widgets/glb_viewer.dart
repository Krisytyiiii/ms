import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'glb_controls.dart';
import 'glb_model_host.dart';
import 'glb_orbit.dart';
import 'glb_orbit_surface.dart';
import 'glb_web_orbit.dart';
import 'page_script_stub.dart'
    if (dart.library.js_interop) 'page_script_web.dart';

/// Pinch, drag, and playback for one bundled `.glb`.
///
/// The plant animation loops. The camera stays put until the user turns it.
/// On the phone, `<model-viewer>` owns the camera. On the web build, a page
/// `div` holds `<model-viewer>` and Flutter writes `cameraOrbit`.
class GlbViewer extends StatefulWidget {
  const GlbViewer({super.key, required this.assetPath, required this.label});

  final String assetPath;
  final String label;

  static const webGestureHint = 'Drag to turn. Scroll or pinch to zoom.';

  @override
  State<GlbViewer> createState() => _GlbViewerState();
}

class _GlbViewerState extends State<GlbViewer> {
  Future<void> Function(String source)? _run;
  var _playing = true;
  var _spinning = false;
  var _sandClear = false;
  var _speed = 1.0;
  var _choseMotion = false;
  late final GlbWebOrbit _web = GlbWebOrbit(isActive: () => mounted);

  String get _src {
    if (kIsWeb && !widget.assetPath.startsWith('assets/assets/')) {
      return 'assets/${widget.assetPath}';
    }
    return widget.assetPath;
  }

  Future<void> _runJs(String source) async {
    if (kIsWeb) {
      await runPageScript(source);
      return;
    }
    final run = _run;
    if (run == null) {
      return;
    }
    await run(source);
  }

  Future<void> _nudge({double thetaDeg = 0, double radiusScale = 1}) async {
    if (kIsWeb) {
      await _web.nudge(thetaDeg: thetaDeg, radiusScale: radiusScale);
      return;
    }
    try {
      await _runJs('''
        (() => {
          const mv = document.getElementById('marinesee-model');
          if (!mv || !mv.getCameraOrbit) return;
          const orbit = mv.getCameraOrbit();
          const theta = orbit.theta * 180 / Math.PI + $thetaDeg;
          const phi = orbit.phi * 180 / Math.PI;
          const radius = Math.min(${GlbOrbit.maxRadius}, Math.max(${GlbOrbit.minRadius}, orbit.radius * $radiusScale));
          mv.cameraOrbit = theta.toFixed(2) + 'deg ' + phi.toFixed(2) + 'deg ' + radius.toFixed(3) + 'm';
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  /// Writes one of the three canned camera angles.
  Future<void> _setPreset(GlbCameraPreset preset) async {
    if (_spinning) {
      setState(() => _spinning = false);
    }
    if (kIsWeb) {
      _web.forgetOrbit();
    }
    try {
      await _runJs('''
        (() => {
          const mv = document.getElementById('marinesee-model');
          if (!mv) return;
          mv.autoRotate = false;
          mv.cameraOrbit = '${preset.orbit}';
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  Future<void> _resetView() async {
    setState(() {
      _spinning = false;
      _speed = 1.0;
    });
    if (kIsWeb) {
      _web.forgetOrbit();
    }
    try {
      await _runJs('''
        (() => {
          const mv = document.getElementById('marinesee-model');
          if (!mv) return;
          mv.autoRotate = false;
          mv.cameraOrbit = '0deg 75deg 105%';
          mv.timeScale = 1;
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  @override
  void initState() {
    super.initState();
    if (kIsWeb) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) {
          return;
        }
        _web.releasePointer();
        if (_playing) {
          _setPlaying(true);
        }
      });
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_choseMotion) {
      return;
    }
    _playing = !MediaQuery.disableAnimationsOf(context);
    _choseMotion = true;
  }

  Future<void> _setPlaying(bool playing) async {
    setState(() => _playing = playing);
    final call = playing
        ? '''
            if (!mv.loaded) {
              if (tries++ < 40) setTimeout(start, 200);
              return;
            }
            const clips = mv.availableAnimations || [];
            if (clips.length) mv.animationName = clips[0];
            mv.timeScale = $_speed;
            try { mv.currentTime = 0; } catch (e) {}
            mv.play({repetitions: 1});
          '''
        : 'mv.pause();';
    try {
      await _runJs('''
        (() => {
          let tries = 0;
          const start = () => {
            const mv = document.getElementById('marinesee-model');
            if (!mv || !mv.play) {
              if (tries++ < 40) setTimeout(start, 200);
              return;
            }
            $call
          };
          start();
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  Future<void> _setSpin(bool spinning) async {
    setState(() => _spinning = spinning);
    final value = spinning ? 'true' : 'false';
    try {
      await _runJs('''
        (() => {
          const mv = document.getElementById('marinesee-model');
          if (!mv) return;
          mv.autoRotate = $value;
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  Future<void> _setSpeed(double speed) async {
    setState(() => _speed = speed);
    try {
      await _runJs('''
        (() => {
          const mv = document.getElementById('marinesee-model');
          if (!mv) return;
          mv.timeScale = $speed;
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  Future<void> _setSandClear(bool clear) async {
    setState(() => _sandClear = clear);
    final show = clear ? 'true' : 'false';
    try {
      await _runJs('''
        (() => {
          const show = $show;
          let tries = 0;
          const apply = () => {
            const mv = document.getElementById('marinesee-model');
            if (!mv || !mv.loaded || !mv.model || !mv.model.materials) {
              if (tries++ < 40) setTimeout(apply, 200);
              return;
            }
            const stash = window.__marineseeSand || (window.__marineseeSand = {});
            for (const material of mv.model.materials) {
              const name = material.name || '';
              if (!/sand/i.test(name)) continue;
              const pbr = material.pbrMetallicRoughness;
              if (!pbr || !pbr.setBaseColorFactor) continue;
              if (!stash[name]) {
                const color = pbr.baseColorFactor;
                stash[name] = [color[0], color[1], color[2], color[3]];
              }
              const saved = stash[name];
              if (show) {
                pbr.setBaseColorFactor([saved[0], saved[1], saved[2], 0.16]);
                if (material.setAlphaMode) material.setAlphaMode('BLEND');
              } else {
                pbr.setBaseColorFactor(saved);
                if (material.setAlphaMode) material.setAlphaMode('OPAQUE');
              }
            }
          };
          apply();
        })();
      ''');
    } on Object {
      // The viewer may still be loading the model.
    }
  }

  @override
  Widget build(BuildContext context) {
    final ready = kIsWeb || _run != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Stage(
          ready: ready,
          child: Stack(
            fit: StackFit.expand,
            children: [
              GlbModelHost(
                src: _src,
                label: widget.label,
                onWebViewCreated: (run) {
                  if (!mounted) {
                    return;
                  }
                  _run = run;
                  setState(() {});
                  _setPlaying(_playing);
                },
              ),
              if (kIsWeb)
                GlbOrbitSurface(
                  onDrag: _web.dragBy,
                  onScroll: _web.scrollBy,
                  onPinch: _web.pinchBy,
                ),
            ],
          ),
        ),
        if (kIsWeb) ...[
          const SizedBox(height: 8),
          Text(
            GlbViewer.webGestureHint,
            textAlign: TextAlign.center,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: context.tokens.inkSubtle),
          ),
        ],
        const SizedBox(height: 14),
        GlbControlDock(
          enabled: ready,
          playing: _playing,
          spinning: _spinning,
          rootsClear: _sandClear,
          speed: _speed,
          onTogglePlay: () => _setPlaying(!_playing),
          onToggleSpin: () => _setSpin(!_spinning),
          onToggleRoots: () => _setSandClear(!_sandClear),
          onSpeed: _setSpeed,
          onZoomIn: () => _nudge(radiusScale: 0.82),
          onZoomOut: () => _nudge(radiusScale: 1.22),
          onPreset: _setPreset,
          onReset: _resetView,
        ),
      ],
    );
  }
}

/// Rounded stage that gives the platform view a soft frame and a loading scrim.
class _Stage extends StatelessWidget {
  const _Stage({required this.child, required this.ready});

  final Widget child;
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return LayoutBuilder(
      builder: (context, constraints) {
        final height = (constraints.maxWidth * 0.96).clamp(280.0, 420.0);

        return SizedBox(
          height: height,
          child: DecoratedBox(
            decoration: BoxDecoration(
              borderRadius: AppRadius.sheet,
              boxShadow: [
                BoxShadow(
                  color: tokens.shadow,
                  blurRadius: 24,
                  offset: const Offset(0, 12),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: AppRadius.sheet,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  const ColoredBox(color: Color(0xFFEEF4FA)),
                  child,
                  if (!ready)
                    ColoredBox(
                      color: const Color(0xCCEEF4FA),
                      child: Center(
                        child: SizedBox(
                          width: 26,
                          height: 26,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.2,
                            color: tokens.brand,
                          ),
                        ),
                      ),
                    ),
                  IgnorePointer(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        borderRadius: AppRadius.sheet,
                        border: Border.all(color: tokens.border),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
