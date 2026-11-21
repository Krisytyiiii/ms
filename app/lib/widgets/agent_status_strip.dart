import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Agent-status strip above the thread: who answered, and where.
class AgentStatusStrip extends StatelessWidget {
  const AgentStatusStrip({super.key, required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [SkyPalette.primary, SkyPalette.primaryDark],
              ),
            ),
            child: const Icon(
              Icons.auto_awesome_rounded,
              size: 17,
              color: SkyPalette.onPrimary,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'MarineSee agent',
                  style: text.labelMedium?.copyWith(
                    color: tokens.ink,
                    fontWeight: FontWeight.w700,
                    height: 1.25,
                  ),
                ),
                Text(
                  count == 1
                      ? 'Reviewed 1 scan on this phone'
                      : 'Reviewed $count scans on this phone',
                  style: text.labelSmall?.copyWith(
                    color: tokens.inkMuted,
                    fontSize: 10.5,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Container(
            height: 22,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFE7F6EE),
              borderRadius: BorderRadius.circular(AppRadius.pill),
              border: Border.all(
                color: const Color(0xFF1B9A66).withValues(alpha: 0.26),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(
                    color: Color(0xFF1B9A66),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  'Ready',
                  style: text.labelSmall?.copyWith(
                    color: const Color(0xFF14684A),
                    fontSize: 9.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.1,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
