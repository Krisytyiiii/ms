import 'package:flutter/material.dart';

import '../data/scan_history.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../screens/history_screen.dart';
import '../screens/shell_scope.dart';
import '../theme/tokens.dart';

/// Slim scanner-history strip under the home hero.
///
/// Newest identification only, because home is a glance page. The whole card is
/// one target: it opens the last species, or the scanner when there is nothing
/// to show yet.
class HomeScanHistory extends StatelessWidget {
  const HomeScanHistory({super.key});

  @override
  Widget build(BuildContext context) {
    final history = ScanHistoryScope.of(context);
    final latest = history.latest;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => HistoryScreen(
                history: history,
                onScan: () {
                  Navigator.of(context).pop();
                  ShellScope.of(context).select(ShellTab.scan);
                },
              ),
            ),
          );
        },
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: Container(
          height: 76,
          padding: const EdgeInsets.fromLTRB(12, 9, 12, 9),
          decoration: BoxDecoration(
            color: context.tokens.surfaceHigh,
            borderRadius: BorderRadius.circular(AppRadius.md),
            border: Border.all(color: context.tokens.border),
            boxShadow: context.tokens.cardShadows,
          ),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: SkyPalette.goldContainer,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: SkyPalette.sandDeep.withValues(alpha: 0.38),
                  ),
                ),
                child: const Icon(
                  Icons.history_rounded,
                  size: 20,
                  color: SkyPalette.notice,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SCANNER HISTORY',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: context.tokens.inkSubtle,
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 3),
                    if (latest == null)
                      _EmptyCopy()
                    else
                      _LatestCopy(record: latest),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                latest == null
                    ? Icons.center_focus_weak_rounded
                    : Icons.chevron_right_rounded,
                size: 20,
                color: context.tokens.inkMuted,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyCopy extends StatelessWidget {
  const _EmptyCopy();

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'No scans yet',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            color: tokens.ink,
            fontWeight: FontWeight.w700,
          ),
        ),
        Text(
          'Your last identification will show here.',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(
            context,
          ).textTheme.bodySmall?.copyWith(color: tokens.inkMuted),
        ),
      ],
    );
  }
}

class _LatestCopy extends StatelessWidget {
  const _LatestCopy({required this.record});

  final ScanRecord record;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return FutureBuilder<Species?>(
      future: speciesCatalog.bySlug(record.slug),
      builder: (context, snapshot) {
        final species = snapshot.data;
        final name = species?.commonName ?? prettySlug(record.slug);
        return Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: tokens.ink,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              _meta(record),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: tokens.inkMuted),
            ),
          ],
        );
      },
    );
  }

  static String _meta(ScanRecord record) {
    final percent = scanPercent(record.confidence);
    final time = scanRelativeTime(record.at);
    return percent == null ? time : '$percent match · $time';
  }
}
