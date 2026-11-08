import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'glb_control_tile.dart';
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
  var _sandClear = false;
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
            try { mv.currentTime = 0; } catch (e) {}
            mv.play({repetitions: Infinity});
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
        SizedBox(
          height: 320,
          child: Stack(
            children: [
              Positioned.fill(
                child: ColoredBox(
                  color: const Color(0xFF1E8C98),
                  child: GlbModelHost(
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
                ),
              ),
              if (kIsWeb)
                Positioned.fill(
                  child: GlbOrbitSurface(
                    onDrag: _web.dragBy,
                    onScroll: _web.scrollBy,
                    onPinch: _web.pinchBy,
                  ),
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
            ).textTheme.bodySmall?.copyWith(color: Colors.white70),
          ),
        ],
        const SizedBox(height: 12),
        DecoratedBox(
          decoration: BoxDecoration(
            color: SkyPalette.scanner.withValues(alpha: 0.55),
            borderRadius: AppRadius.card,
            border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
          ),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 14, 8, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  '3D Controls',
                  style: Theme.of(
                    context,
                  ).textTheme.titleMedium?.copyWith(color: Colors.white),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    GlbControlTile(
                      icon: _playing ? Icons.pause : Icons.play_arrow,
                      label: _playing ? 'Pause' : 'Play',
                      onPressed: ready ? () => _setPlaying(!_playing) : null,
                    ),
                    const SizedBox(width: 8),
                    GlbControlTile(
                      icon: Icons.rotate_right,
                      label: 'Rotate',
                      onPressed: ready ? () => _nudge(thetaDeg: 40) : null,
                    ),
                    const SizedBox(width: 8),
                    GlbControlTile(
                      icon: Icons.zoom_in,
                      label: 'Zoom in',
                      onPressed: ready ? () => _nudge(radiusScale: 0.82) : null,
                    ),
                    const SizedBox(width: 8),
                    GlbControlTile(
                      icon: Icons.zoom_out,
                      label: 'Zoom out',
                      onPressed: ready ? () => _nudge(radiusScale: 1.22) : null,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    GlbControlTile(
                      icon: _sandClear ? Icons.visibility_off : Icons.visibility,
                      label: _sandClear ? 'Hide roots' : 'See roots',
                      onPressed: ready ? () => _setSandClear(!_sandClear) : null,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
