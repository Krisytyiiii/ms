import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'app_mark.dart';

/// App mark. Vector, so it never needs a raster swap.
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 40, this.shadow = true});

  final double size;
  final bool shadow;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Semantics(
      label: 'MarineSee',
      image: true,
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(size * 0.31),
          boxShadow: shadow
              ? [
                  BoxShadow(
                    color: SkyPalette.primaryDark.withValues(alpha: 0.28),
                    blurRadius: size * 0.34,
                    offset: Offset(0, size * 0.12),
                  ),
                  BoxShadow(
                    color: tokens.shadow,
                    blurRadius: size * 0.10,
                    offset: Offset(0, size * 0.03),
                  ),
                ]
              : null,
        ),
        child: MarineSeeMark(size: size),
      ),
    );
  }
}
