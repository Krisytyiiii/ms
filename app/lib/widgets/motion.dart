import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Fades and lifts [child] into place once, on first build.
///
/// Used for cards and rows so a screen assembles instead of popping. Every
/// instance respects the system reduce-motion setting, and only animates
/// opacity and translation so it stays cheap on a mid-range phone.
class Reveal extends StatefulWidget {
  const Reveal({
    super.key,
    required this.child,
    this.delay = Duration.zero,
    this.offset = 14,
    this.duration = const Duration(milliseconds: 320),
    this.curve = Curves.easeOutCubic,
  });

  final Widget child;
  final Duration delay;

  /// Vertical travel in logical pixels.
  final double offset;
  final Duration duration;
  final Curve curve;

  @override
  State<Reveal> createState() => _RevealState();
}

class _RevealState extends State<Reveal> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: widget.duration,
  );
  var _started = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_started) {
      return;
    }
    _started = true;
    if (MediaQuery.disableAnimationsOf(context)) {
      _controller.value = 1;
      return;
    }
    Future<void>.delayed(widget.delay, () {
      if (mounted) {
        _controller.forward();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final value = widget.curve.transform(_controller.value);
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, (1 - value) * widget.offset),
            child: child,
          ),
        );
      },
      child: widget.child,
    );
  }
}

/// Soft fade for tab pages. The page keeps its state; only its presence
/// animates, so switching tabs never rebuilds the screen. A hidden page is
/// parked at zero instead of finishing a fade nobody sees.
class TabReveal extends StatefulWidget {
  const TabReveal({super.key, required this.active, required this.child});

  final bool active;
  final Widget child;

  @override
  State<TabReveal> createState() => _TabRevealState();
}

class _TabRevealState extends State<TabReveal>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: AppMotion.medium,
  );

  @override
  void initState() {
    super.initState();
    if (widget.active) {
      _controller.value = 1;
    }
  }

  @override
  void didUpdateWidget(covariant TabReveal oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active == oldWidget.active) {
      return;
    }
    if (widget.active) {
      _controller.forward(from: 0);
    } else {
      _controller.value = 0;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (MediaQuery.disableAnimationsOf(context)) {
      return widget.child;
    }

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final value = Curves.easeOutCubic.transform(_controller.value);
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, (1 - value) * 10),
            child: child,
          ),
        );
      },
      child: widget.child,
    );
  }
}

/// Staggered delay for list positions. Caps so a long grid never crawls.
Duration revealDelay(int index, {int step = 40, int max = 8}) {
  return Duration(milliseconds: step * (index < max ? index : max));
}
