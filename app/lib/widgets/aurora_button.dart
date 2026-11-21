import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Primary action: a liquid-gold face, a glass rim, and a warm cast.
/// Pressing it compresses slightly instead of just flashing.
class AuroraButton extends StatefulWidget {
  const AuroraButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.trailingIcon,
    this.loading = false,
    this.onDark = false,
    this.compact = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  /// Optional icon in a foam disc on the right edge. When set, the label is
  /// left aligned instead of centered.
  final IconData? trailingIcon;
  final bool loading;

  /// True when the button sits on a deep-water surface (the scanner). Only the
  /// disabled treatment changes: a white ghost instead of a pale blue slab.
  final bool onDark;

  /// 48 px face for the scanner and result actions; 52 px stays the default
  /// page action size.
  final bool compact;

  @override
  State<AuroraButton> createState() => _AuroraButtonState();
}

class _AuroraButtonState extends State<AuroraButton> {
  var _pressed = false;

  static const _ocean = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFFFE45C), Color(0xFFFFD60A), Color(0xFFFFC300)],
    stops: [0.0, 0.55, 1.0],
  );

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null && !widget.loading;
    final tokens = context.tokens;
    final radius = AppRadius.button;
    final iconColor = enabled
        ? tokens.ink
        : widget.onDark
        ? Colors.white.withValues(alpha: 0.62)
        : tokens.ink.withValues(alpha: 0.45);
    final labelStyle = Theme.of(context).textTheme.labelLarge?.copyWith(
      color: iconColor,
      fontWeight: FontWeight.w700,
    );

    return AnimatedScale(
      scale: _pressed && enabled ? 0.975 : 1,
      duration: const Duration(milliseconds: 140),
      curve: Curves.easeOutCubic,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          minHeight: widget.compact ? 48 : 52,
          minWidth: AppTokens.tapMin,
        ),
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: enabled
                ? _ocean
                : LinearGradient(
                    colors: [
                      widget.onDark
                          ? Colors.white.withValues(alpha: 0.14)
                          : tokens.brand.withValues(alpha: 0.22),
                      widget.onDark
                          ? Colors.white.withValues(alpha: 0.14)
                          : tokens.brand.withValues(alpha: 0.22),
                    ],
                  ),
            borderRadius: radius,
            border: Border.all(
              color: enabled
                  ? const Color(0x6BFFFFFF)
                  : widget.onDark
                  ? Colors.white.withValues(alpha: 0.22)
                  : tokens.brand.withValues(alpha: 0.16),
            ),
            boxShadow: enabled
                ? const [
                    BoxShadow(
                      color: Color(0x4DFFC300),
                      blurRadius: 26,
                      offset: Offset(0, 11),
                    ),
                    BoxShadow(
                      color: Color(0x1F023E8A),
                      blurRadius: 6,
                      offset: Offset(0, 2),
                    ),
                  ]
                : null,
          ),
          child: ClipRRect(
            borderRadius: radius,
            child: Material(
              type: MaterialType.transparency,
              child: InkWell(
                onTap: enabled ? widget.onPressed : null,
                onHighlightChanged: (value) {
                  if (_pressed != value) {
                    setState(() => _pressed = value);
                  }
                },
                borderRadius: radius,
                splashColor: Colors.white.withValues(alpha: 0.18),
                highlightColor: Colors.white.withValues(alpha: 0.05),
                child: Stack(
                  children: [
                    // Light catching the top edge, like wet glass.
                    Positioned.fill(
                      child: IgnorePointer(
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Colors.white.withValues(alpha: 0.26),
                                Colors.white.withValues(alpha: 0.0),
                              ],
                              stops: const [0.0, 0.58],
                            ),
                          ),
                        ),
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.symmetric(
                        horizontal: widget.compact ? 16 : 18,
                        vertical: widget.compact ? 11 : 14,
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (widget.loading) ...[
                            SizedBox(
                              width: widget.compact ? 16 : 18,
                              height: widget.compact ? 16 : 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: tokens.ink,
                              ),
                            ),
                            SizedBox(width: widget.compact ? 8 : 10),
                          ] else if (widget.icon != null) ...[
                            Icon(
                              widget.icon,
                              size: widget.compact ? 18 : 20,
                              color: iconColor,
                            ),
                            SizedBox(width: widget.compact ? 7 : 8),
                          ],
                          if (widget.trailingIcon != null)
                            Expanded(
                              child: Text(
                                widget.label,
                                textAlign: TextAlign.start,
                                overflow: TextOverflow.ellipsis,
                                style: labelStyle,
                              ),
                            )
                          else
                            Flexible(
                              child: Text(
                                widget.label,
                                textAlign: TextAlign.center,
                                overflow: TextOverflow.ellipsis,
                                style: labelStyle,
                              ),
                            ),
                          if (widget.trailingIcon != null) ...[
                            SizedBox(width: widget.compact ? 10 : 12),
                            Container(
                              width: widget.compact ? 26 : 28,
                              height: widget.compact ? 26 : 28,
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(
                                  alpha: enabled ? 0.34 : 0.16,
                                ),
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.55),
                                ),
                              ),
                              child: Icon(
                                widget.trailingIcon,
                                size: widget.compact ? 16 : 18,
                                color: iconColor,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
