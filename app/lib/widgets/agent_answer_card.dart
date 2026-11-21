import 'package:flutter/material.dart';

import '../data/scan_history.dart';
import '../data/species.dart';
import '../theme/tokens.dart';
import 'tool_ledger.dart';

/// One agent reply in the scan thread.
///
/// The pattern is borrowed from cited-answer / tool-ledger / agent-status: a
/// short answer with a numbered marker, the tool steps behind it, and the
/// species note as the source behind the marker.
class AgentAnswerCard extends StatefulWidget {
  const AgentAnswerCard({
    super.key,
    required this.record,
    required this.species,
    required this.onProfile,
    required this.onViewer,
  });

  final ScanRecord record;
  final Species? species;
  final VoidCallback onProfile;
  final VoidCallback onViewer;

  @override
  State<AgentAnswerCard> createState() => _AgentAnswerCardState();
}

class _AgentAnswerCardState extends State<AgentAnswerCard> {
  bool _showNote = false;

  ScanRecord get _record => widget.record;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final name = widget.species?.commonName ?? prettySlug(_record.slug);
    final percent = scanPercent(_record.confidence);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 26,
              height: 26,
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
                size: 14,
                color: SkyPalette.onPrimary,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'MarineSee agent',
                    style: text.labelMedium?.copyWith(
                      color: tokens.ink,
                      fontWeight: FontWeight.w700,
                      height: 1.2,
                    ),
                  ),
                  Text(
                    'on-device · svm_mobile',
                    style: text.labelSmall?.copyWith(
                      color: tokens.inkSubtle,
                      fontFamily: 'monospace',
                      fontSize: 10,
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: tokens.navy,
                borderRadius: BorderRadius.circular(AppRadius.pill),
                border: Border.all(
                  color: SkyPalette.primary.withValues(alpha: 0.20),
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
                    'Answered',
                    style: text.labelSmall?.copyWith(
                      color: tokens.brandDeep,
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
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 6),
          decoration: BoxDecoration(
            color: tokens.surfaceHigh,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(4),
              topRight: Radius.circular(AppRadius.md),
              bottomLeft: Radius.circular(AppRadius.md),
              bottomRight: Radius.circular(AppRadius.md),
            ),
            border: Border.all(color: tokens.border),
            boxShadow: tokens.cardShadows,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const ToolLedger(),
              const SizedBox(height: 10),
              Text.rich(
                TextSpan(
                  style: text.bodyMedium?.copyWith(
                    color: tokens.inkMuted,
                    height: 1.62,
                  ),
                  children: _answerSpans(context, name, percent),
                ),
              ),
              const SizedBox(height: 9),
              Row(
                children: [
                  _VerdictChip(record: _record),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Scanned ${scanRelativeTime(_record.at)}'
                      '${percent == null ? '' : ' · $percent match'}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.labelSmall?.copyWith(
                        color: tokens.inkSubtle,
                        fontFamily: 'monospace',
                        fontSize: 10.5,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              _sourceRow(context, name),
              if (_showNote) ...[const SizedBox(height: 8), _note(context)],
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(
                    Icons.lock_outline_rounded,
                    size: 13,
                    color: tokens.inkSubtle,
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      'Photo and answer stay on this phone',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.labelSmall?.copyWith(
                        color: tokens.inkSubtle,
                        fontSize: 10,
                      ),
                    ),
                  ),
                  _LinkButton(label: 'Profile', onPressed: widget.onProfile),
                  _LinkButton(label: '3D', onPressed: widget.onViewer),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  List<InlineSpan> _answerSpans(
    BuildContext context,
    String name,
    String? percent,
  ) {
    final tokens = context.tokens;
    final spans = <InlineSpan>[
      const TextSpan(text: 'This looks like '),
      TextSpan(
        text: name,
        style: TextStyle(color: tokens.ink, fontWeight: FontWeight.w700),
      ),
      TextSpan(
        text: percent == null
            ? ' — the SVM returned no score'
            : ' with a $percent match',
      ),
      _marker(context),
      const TextSpan(text: '.'),
    ];

    if (_record.low) {
      spans.add(
        const TextSpan(
          text:
              ' That is below the retake threshold, so treat it as a hint and '
              'check the leaf in person.',
        ),
      );
    } else {
      spans.add(
        const TextSpan(
          text: ' The species note is quoted in the source below.',
        ),
      );
    }
    return spans;
  }

  InlineSpan _marker(BuildContext context) {
    final tokens = context.tokens;
    return WidgetSpan(
      alignment: PlaceholderAlignment.middle,
      child: Padding(
        padding: const EdgeInsets.only(left: 4),
        child: Semantics(
          button: true,
          label: 'Open the species source',
          child: InkWell(
            onTap: () => setState(() => _showNote = !_showNote),
            customBorder: const CircleBorder(),
            child: Container(
              width: 17,
              height: 17,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: _showNote ? tokens.brandDeep : tokens.navy,
                shape: BoxShape.circle,
                border: Border.all(
                  color: SkyPalette.primary.withValues(alpha: 0.25),
                ),
              ),
              child: Text(
                '1',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: _showNote ? tokens.onBrand : tokens.inkMuted,
                  fontSize: 10,
                  height: 1,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _sourceRow(BuildContext context, String name) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final scientific = widget.species?.scientificName;

    return Material(
      color: _showNote
          ? tokens.navy.withValues(alpha: 0.7)
          : Colors.transparent,
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: InkWell(
        onTap: () => setState(() => _showNote = !_showNote),
        borderRadius: BorderRadius.circular(AppRadius.sm),
        child: Container(
          padding: const EdgeInsets.fromLTRB(8, 7, 8, 7),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppRadius.sm),
            border: Border.all(
              color: _showNote
                  ? SkyPalette.primary.withValues(alpha: 0.28)
                  : tokens.border,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 18,
                height: 18,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: tokens.surfaceHigh,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: SkyPalette.primary.withValues(alpha: 0.30),
                  ),
                ),
                child: Text(
                  '1',
                  style: text.labelSmall?.copyWith(
                    color: tokens.brandDeep,
                    fontSize: 10,
                    height: 1,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Species profile',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.labelMedium?.copyWith(
                        color: tokens.ink,
                        fontWeight: FontWeight.w700,
                        height: 1.3,
                      ),
                    ),
                    Text(
                      scientific == null
                          ? '$name · seagrass library'
                          : '$scientific · seagrass library',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.labelSmall?.copyWith(
                        color: tokens.inkSubtle,
                        fontFamily: 'monospace',
                        fontSize: 10,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              Icon(
                _showNote
                    ? Icons.keyboard_arrow_up_rounded
                    : Icons.keyboard_arrow_down_rounded,
                size: 18,
                color: tokens.inkSubtle,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _note(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final name = widget.species?.commonName ?? prettySlug(_record.slug);
    final note =
        widget.species?.botanicalCharacteristics ??
        'The species note is still loading.';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
      decoration: BoxDecoration(
        color: tokens.abyss,
        borderRadius: BorderRadius.circular(AppRadius.sm),
        border: Border.all(color: tokens.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.format_quote_rounded,
                size: 13,
                color: tokens.inkSubtle,
              ),
              const SizedBox(width: 4),
              Text(
                'FROM THE SPECIES PROFILE',
                style: text.labelSmall?.copyWith(
                  color: tokens.inkSubtle,
                  fontSize: 9,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.6,
                ),
              ),
            ],
          ),
          const SizedBox(height: 5),
          Container(
            margin: const EdgeInsets.only(left: 3),
            padding: const EdgeInsets.only(left: 10),
            decoration: BoxDecoration(
              border: Border(
                left: BorderSide(color: tokens.borderStrong, width: 2),
              ),
            ),
            child: _quote(text, tokens, name, note),
          ),
        ],
      ),
    );
  }

  Widget _quote(TextTheme text, AppTokens tokens, String name, String note) {
    final style = text.bodySmall?.copyWith(
      color: tokens.inkMuted,
      height: 1.55,
      fontSize: 12.5,
    );
    final match = RegExp(
      RegExp.escape(name),
      caseSensitive: false,
    ).firstMatch(note);
    if (match == null) {
      return Text(
        '“$note”',
        style: style,
        maxLines: 6,
        overflow: TextOverflow.ellipsis,
      );
    }
    return Text.rich(
      TextSpan(
        style: style,
        children: [
          TextSpan(text: '“${note.substring(0, match.start)}'),
          TextSpan(
            text: note.substring(match.start, match.end),
            style: TextStyle(color: tokens.ink, fontWeight: FontWeight.w700),
          ),
          TextSpan(text: '${note.substring(match.end)}”'),
        ],
      ),
      maxLines: 6,
      overflow: TextOverflow.ellipsis,
    );
  }
}

class _LinkButton extends StatelessWidget {
  const _LinkButton({required this.label, required this.onPressed});

  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    return TextButton(
      onPressed: onPressed,
      style: TextButton.styleFrom(
        minimumSize: const Size(0, 40),
        padding: const EdgeInsets.symmetric(horizontal: 7),
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        foregroundColor: tokens.brandDeep,
        textStyle: Theme.of(
          context,
        ).textTheme.labelSmall?.copyWith(fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label),
          const SizedBox(width: 2),
          const Icon(Icons.arrow_outward_rounded, size: 12),
        ],
      ),
    );
  }
}

class _VerdictChip extends StatelessWidget {
  const _VerdictChip({required this.record});

  final ScanRecord record;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final confidence = record.confidence;
    final String label;
    final Color color;

    if (record.low) {
      label = 'Retake';
      color = tokens.notice;
    } else if (confidence == null) {
      label = 'No score';
      color = tokens.inkMuted;
    } else if (confidence >= 0.7) {
      label = 'Strong';
      color = SkyPalette.primaryDark;
    } else {
      label = 'Fair';
      color = tokens.notice;
    }

    return Container(
      height: 18,
      padding: const EdgeInsets.symmetric(horizontal: 6),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 5,
            height: 5,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color,
              fontSize: 9.5,
              height: 1,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.1,
            ),
          ),
        ],
      ),
    );
  }
}
