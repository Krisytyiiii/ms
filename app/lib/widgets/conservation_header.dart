import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Gradient header for the conservation tab.
///
/// Same blue band as Home and the Library, with a gold eco mark on the right
/// so the tab reads as part of the same system.
class ConservationHeader extends StatelessWidget {
  const ConservationHeader({super.key});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: context.tokens.headerGradient,
        border: Border(
          bottom: BorderSide(color: SkyPalette.foam.withValues(alpha: 0.10)),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Conservation',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.titleLarge?.copyWith(
                        color: SkyPalette.onHeader,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.2,
                      ),
                    ),
                    const SizedBox(height: 1),
                    Text(
                      'Why Mati City seagrasses matter',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.bodySmall?.copyWith(
                        color: SkyPalette.onHeader.withValues(alpha: 0.72),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: SkyPalette.foam.withValues(alpha: 0.14),
                  border: Border.all(
                    color: SkyPalette.foam.withValues(alpha: 0.26),
                  ),
                ),
                child: const Icon(
                  Icons.eco_rounded,
                  size: 22,
                  color: SkyPalette.goldBright,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
