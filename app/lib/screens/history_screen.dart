import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data/scan_history.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/agent_status_strip.dart';
import '../widgets/aurora_atmosphere.dart';
import '../widgets/diamond_grid_background.dart';
import '../widgets/history_chat_turn.dart';
import 'species_screen.dart';
import 'viewer_3d_screen.dart';

/// Saved scanner results as an agent thread: each scan shows the photo the
/// user sent, then the agent's cited answer, tool steps, and species source.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key, required this.history, this.onScan});

  /// The saved scan log owned by the app shell. Passed in because routes
  /// pushed over the shell cannot see its inherited scopes.
  final ScanHistoryController history;

  /// Leaves this page and opens the scanner tab.
  final VoidCallback? onScan;

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late final Future<Map<String, Species>> _speciesFuture = _loadSpecies();

  @override
  void initState() {
    super.initState();
    widget.history.addListener(_onHistory);
  }

  @override
  void didUpdateWidget(HistoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.history != widget.history) {
      oldWidget.history.removeListener(_onHistory);
      widget.history.addListener(_onHistory);
    }
  }

  @override
  void dispose() {
    widget.history.removeListener(_onHistory);
    super.dispose();
  }

  void _onHistory() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<Map<String, Species>> _loadSpecies() async {
    final all = await speciesCatalog.all();
    return {for (final species in all) species.slug: species};
  }

  void _open(Widget page) {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    final history = widget.history;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SkyPalette.lightStatusBar,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: Stack(
          fit: StackFit.expand,
          children: [
            const AuroraAtmosphere(),
            const DiamondGridBackground(seed: 45),
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _HistoryHeader(
                  count: history.count,
                  loaded: history.isLoaded,
                  onBack: () => Navigator.of(context).maybePop(),
                ),
                Expanded(
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(
                        maxWidth: AppSpace.maxContent,
                      ),
                      child: FutureBuilder<Map<String, Species>>(
                        future: _speciesFuture,
                        builder: (context, snapshot) {
                          final species = snapshot.data ?? const {};
                          if (!history.isLoaded) {
                            return const Center(
                              child: SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.4,
                                ),
                              ),
                            );
                          }
                          if (history.isEmpty) {
                            return _EmptyHistory(
                              onScan: widget.onScan,
                              onBack: () => Navigator.of(context).maybePop(),
                            );
                          }
                          return _answer(context, history, species);
                        },
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _answer(
    BuildContext context,
    ScanHistoryController history,
    Map<String, Species> species,
  ) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final records = history.records;

    return ListView(
      reverse: true,
      padding: AppSpace.pageInsets(context),
      children: [
        for (var index = 0; index < records.length; index++) ...[
          HistoryChatTurn(
            key: ObjectKey(records[index]),
            record: records[index],
            species: species[records[index].slug],
            onProfile: () => _open(SpeciesScreen(slug: records[index].slug)),
            onViewer: () => _open(Viewer3dScreen(slug: records[index].slug)),
          ),
          if (index < records.length - 1) const SizedBox(height: 22),
        ],
        const SizedBox(height: 18),
        AgentStatusStrip(count: records.length),
        const SizedBox(height: 8),
        Center(
          child: Text(
            'Oldest first · the latest answer is at the bottom',
            style: text.labelSmall?.copyWith(color: tokens.inkSubtle),
          ),
        ),
      ],
    );
  }
}

class _HistoryHeader extends StatelessWidget {
  const _HistoryHeader({
    required this.count,
    required this.loaded,
    required this.onBack,
  });

  final int count;
  final bool loaded;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final subtitle = !loaded
        ? 'Loading saved scans…'
        : count == 1
        ? 'Saved on this phone · 1 scan'
        : 'Saved on this phone · $count scans';

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
          padding: const EdgeInsets.fromLTRB(12, 10, 16, 12),
          child: Row(
            children: [
              Material(
                color: SkyPalette.foam.withValues(alpha: 0.14),
                shape: CircleBorder(
                  side: BorderSide(
                    color: SkyPalette.foam.withValues(alpha: 0.26),
                  ),
                ),
                child: InkWell(
                  onTap: onBack,
                  customBorder: const CircleBorder(),
                  child: const SizedBox(
                    width: 48,
                    height: 48,
                    child: Icon(
                      Icons.arrow_back_rounded,
                      color: SkyPalette.onHeader,
                      size: 22,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Scanner history',
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
                      subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.bodySmall?.copyWith(
                        color: SkyPalette.onHeader.withValues(alpha: 0.72),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
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
                  Icons.history_rounded,
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

class _EmptyHistory extends StatelessWidget {
  const _EmptyHistory({this.onScan, required this.onBack});

  final VoidCallback? onScan;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 60,
              height: 60,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: SkyPalette.goldContainer,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: SkyPalette.sandDeep.withValues(alpha: 0.38),
                ),
              ),
              child: const Icon(
                Icons.history_rounded,
                size: 28,
                color: SkyPalette.notice,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              'Nothing saved yet',
              style: text.titleMedium?.copyWith(
                color: tokens.ink,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Every finished identification is saved here with its species '
              'note and score.',
              textAlign: TextAlign.center,
              style: text.bodyMedium?.copyWith(color: tokens.inkMuted),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: onScan ?? onBack,
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(0, 48),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: Text(onScan == null ? 'Back' : 'Scan a seagrass'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
