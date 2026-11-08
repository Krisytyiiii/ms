import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

/// Web-only layer over the plant. It wins the drag immediately so the page
/// list does not scroll, and it takes wheel and pinch through the pointer
/// signal resolver so the deepest target wins.
class GlbOrbitSurface extends StatelessWidget {
  const GlbOrbitSurface({
    super.key,
    required this.onDrag,
    required this.onScroll,
    required this.onPinch,
  });

  final void Function(double dx, double dy) onDrag;
  final void Function(double dy) onScroll;
  final void Function(double scale) onPinch;

  void _onSignal(PointerSignalEvent event) {
    if (event is! PointerScrollEvent && event is! PointerScaleEvent) {
      return;
    }
    GestureBinding.instance.pointerSignalResolver.register(event, (signal) {
      if (signal is PointerScrollEvent) {
        onScroll(signal.scrollDelta.dy);
      } else if (signal is PointerScaleEvent) {
        onPinch(signal.scale);
      }
      signal.respond(allowPlatformDefault: false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.grab,
      child: Listener(
        behavior: HitTestBehavior.opaque,
        onPointerSignal: _onSignal,
        child: RawGestureDetector(
          behavior: HitTestBehavior.opaque,
          gestures: <Type, GestureRecognizerFactory>{
            _EagerOrbitPan:
                GestureRecognizerFactoryWithHandlers<_EagerOrbitPan>(
                  _EagerOrbitPan.new,
                  (instance) {
                    instance.onUpdate = (details) {
                      onDrag(details.delta.dx, details.delta.dy);
                    };
                  },
                ),
          },
          child: const SizedBox.expand(),
        ),
      ),
    );
  }
}

class _EagerOrbitPan extends PanGestureRecognizer {
  _EagerOrbitPan() {
    dragStartBehavior = DragStartBehavior.down;
  }

  @override
  void addAllowedPointer(PointerDownEvent event) {
    super.addAllowedPointer(event);
    resolve(GestureDisposition.accepted);
  }
}
