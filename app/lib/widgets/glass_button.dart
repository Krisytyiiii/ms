import 'dart:ui' as ui;

import 'package:flutter/material.dart';

/// Frosted action for use over photography. Blur, a thin rim, and a top
/// highlight; no drop shadow heavier than the content behind it.
class GlassButton extends StatelessWidget {
  const GlassButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.foreground = Colors.white,
    this.padding = const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final Color foreground;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(999);
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: radius,
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF023E8A).withValues(alpha: 0.18),
            blurRadius: 18,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 16, sigmaY: 16),
          child: Material(
            color: Colors.white.withValues(alpha: 0.20),
            shape: RoundedRectangleBorder(
              borderRadius: radius,
              side: BorderSide(
                color: Colors.white.withValues(alpha: 0.42),
                width: 1,
              ),
            ),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: onPressed,
              splashColor: Colors.white.withValues(alpha: 0.20),
              highlightColor: Colors.white.withValues(alpha: 0.08),
              child: Stack(
                children: [
                  Positioned.fill(
                    child: IgnorePointer(
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              Colors.white.withValues(alpha: 0.22),
                              Colors.white.withValues(alpha: 0.0),
                            ],
                            stops: const [0.0, 0.6],
                          ),
                        ),
                      ),
                    ),
                  ),
                  Padding(
                    padding: padding,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (icon != null) ...[
                          Icon(icon, size: 16, color: foreground),
                          const SizedBox(width: 6),
                        ],
                        Text(
                          label,
                          style: text.labelLarge?.copyWith(
                            color: foreground,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
