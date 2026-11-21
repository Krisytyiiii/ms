import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Bundled photo with a guaranteed visible state.
///
/// Three things it does that a bare [Image.asset] does not:
/// - paints a tinted base while the first frame decodes, so a card is never a
///   transparent hole;
/// - fades the frame in (skipped when the OS asks for reduced motion);
/// - replaces a missing or corrupt asset with a labeled placeholder, so a
///   screen never shows an unexplained empty box.
class AppPhoto extends StatelessWidget {
  const AppPhoto({
    super.key,
    required this.asset,
    this.fit = BoxFit.cover,
    this.errorIcon = Icons.spa_outlined,
    this.semanticLabel,
    this.fade = true,
  });

  final String asset;
  final BoxFit fit;
  final IconData errorIcon;
  final String? semanticLabel;

  /// Set false where the photo sits under a moving clip and should be on the
  /// first painted frame, not faded.
  final bool fade;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;
    final reduce = MediaQuery.disableAnimationsOf(context);
    final animate = fade && !reduce;

    return ColoredBox(
      color: tokens.surfaceHigh,
      child: Image.asset(
        asset,
        fit: fit,
        width: double.infinity,
        height: double.infinity,
        gaplessPlayback: true,
        semanticLabel: semanticLabel,
        frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
          if (!animate || wasSynchronouslyLoaded) {
            return child;
          }
          return AnimatedOpacity(
            opacity: frame == null ? 0 : 1,
            duration: AppMotion.medium,
            curve: AppMotion.ease,
            child: child,
          );
        },
        errorBuilder: (context, error, stackTrace) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(errorIcon, size: 32, color: tokens.brand),
                const SizedBox(height: 6),
                Text(
                  'Image unavailable',
                  style: text.bodySmall?.copyWith(color: tokens.inkMuted),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
