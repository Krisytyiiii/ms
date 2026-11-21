import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

import 'glb_orbit.dart';

/// Phone viewer. `<model-viewer>` lives in the plugin web view and owns the camera.
class GlbModelHost extends StatelessWidget {
  const GlbModelHost({
    super.key,
    required this.src,
    required this.label,
    required this.onWebViewCreated,
  });

  final String src;
  final String label;
  final void Function(Future<void> Function(String source) run)
  onWebViewCreated;

  @override
  Widget build(BuildContext context) {
    return ModelViewer(
      id: 'marinesee-model',
      src: src,
      loading: Loading.eager,
      alt: label,
      ar: false,
      autoRotate: false,
      autoPlay: false,
      cameraControls: true,
      disableZoom: false,
      interactionPrompt: InteractionPrompt.none,
      cameraOrbit: '0deg 75deg 105%',
      minCameraOrbit: 'auto auto ${GlbOrbit.minRadius}m',
      maxCameraOrbit: 'auto auto ${GlbOrbit.maxRadius}m',
      backgroundColor: const Color(0xFFEEF4FA),
      debugLogging: false,
      onWebViewCreated: (controller) {
        onWebViewCreated(controller.runJavaScript);
      },
    );
  }
}
