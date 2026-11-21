import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'app_logo.dart';

/// Flat home app bar: brand on the left, profile on the right.
///
/// Square bottom corners so the bar reads as a header, not a floating card.
class HomeAppBar extends StatelessWidget {
  const HomeAppBar({super.key, required this.name, required this.onProfile});

  final String name;
  final VoidCallback onProfile;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final initial = name.trim().isEmpty ? 'G' : name.trim()[0].toUpperCase();

    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: tokens.headerGradient,
        border: Border(
          bottom: BorderSide(color: SkyPalette.foam.withValues(alpha: 0.10)),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
          child: Row(
            children: [
              const AppLogo(size: 34, shadow: false),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'MarineSee',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: text.titleMedium?.copyWith(
                    color: SkyPalette.onHeader,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.2,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Semantics(
                button: true,
                label: 'Open profile',
                child: Material(
                  color: SkyPalette.foam.withValues(alpha: 0.14),
                  shape: CircleBorder(
                    side: BorderSide(
                      color: SkyPalette.foam.withValues(alpha: 0.28),
                    ),
                  ),
                  child: InkWell(
                    onTap: onProfile,
                    customBorder: const CircleBorder(),
                    child: SizedBox(
                      width: 40,
                      height: 40,
                      child: Center(
                        child: Text(
                          initial,
                          style: text.titleMedium?.copyWith(
                            color: SkyPalette.onHeader,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
