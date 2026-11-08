import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:web/web.dart' as web;

import 'glb_orbit.dart';

/// Web viewer. A real `div` holds `<model-viewer>`, sized to this slot.
///
/// The package mounts that tag inside an `<html>` element, and that element
/// does not paint. This host does not use that slot.
class GlbModelHost extends StatefulWidget {
  const GlbModelHost({
    super.key,
    required this.src,
    required this.label,
    required this.onWebViewCreated,
  });

  final String src;
  final String label;

  /// The phone host runs scripts in its web view. The page script reaches this
  /// element by id, so the web host does not use the callback.
  final void Function(Future<void> Function(String source) run) onWebViewCreated;

  @override
  State<GlbModelHost> createState() => _GlbModelHostState();
}

class _GlbModelHostState extends State<GlbModelHost> {
  web.HTMLElement? _host;
  web.HTMLElement? _viewer;
  var _width = 0.0;
  var _height = 0.0;

  String get _src {
    final src = widget.src;
    if (src.startsWith('/') || src.startsWith('http://') || src.startsWith('https://')) {
      return src;
    }
    return '/$src';
  }

  void _paintBox(web.CSSStyleDeclaration style) {
    style.setProperty('display', 'block');
    style.setProperty('margin', '0');
    style.setProperty('padding', '0');
    style.setProperty('border', '0');
    style.setProperty('overflow', 'hidden');
    style.setProperty('background-color', '#1E8C98');
    style.setProperty('pointer-events', 'none');
    if (_width > 0 && _height > 0) {
      style.setProperty('width', '${_width}px');
      style.setProperty('height', '${_height}px');
    } else {
      style.setProperty('width', '100%');
      style.setProperty('height', '100%');
    }
  }

  void _applySize() {
    final host = _host;
    final viewer = _viewer;
    if (host == null || viewer == null) {
      return;
    }
    _paintBox(host.style);
    _paintBox(viewer.style);
  }

  void _mount(Object element) {
    final host = element as web.HTMLDivElement;
    final viewer = web.document.createElement('model-viewer') as web.HTMLElement;
    viewer.id = 'marinesee-model';
    viewer.setAttribute('src', _src);
    viewer.setAttribute('alt', widget.label);
    viewer.setAttribute('loading', 'eager');
    viewer.setAttribute('interaction-prompt', 'none');
    viewer.setAttribute('touch-action', 'none');
    viewer.setAttribute('camera-orbit', '0deg 75deg 105%');
    viewer.setAttribute('min-camera-orbit', 'auto auto ${GlbOrbit.minRadius}m');
    viewer.setAttribute('max-camera-orbit', 'auto auto ${GlbOrbit.maxRadius}m');
    viewer.setAttribute('shadow-intensity', '1');
    viewer.setAttribute('exposure', '1');
    host.appendChild(viewer);
    _host = host;
    _viewer = viewer;
    _applySize();
    // The phone host calls this. This page reaches the element by id.
    widget.onWebViewCreated;
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final dpr = MediaQuery.devicePixelRatioOf(context);
        final width = constraints.maxWidth;
        final height = constraints.maxHeight;
        if (width.isFinite && height.isFinite && width > 0 && height > 0) {
          _width = width * dpr;
          _height = height * dpr;
          _applySize();
        }
        return HtmlElementView.fromTagName(
          tagName: 'div',
          hitTestBehavior: PlatformViewHitTestBehavior.transparent,
          onElementCreated: _mount,
        );
      },
    );
  }
}
