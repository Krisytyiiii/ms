import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../data/scan_history.dart';
import '../data/species.dart';
import '../theme/tokens.dart';
import 'agent_answer_card.dart';

/// One scan as a chat turn: the photo the user sent, then the agent's answer.
class HistoryChatTurn extends StatelessWidget {
  const HistoryChatTurn({
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
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Align(
          alignment: Alignment.centerRight,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              _PhotoBubble(record: record),
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.only(right: 4),
                child: Text(
                  'You · ${scanRelativeTime(record.at)}',
                  style: text.labelSmall?.copyWith(
                    color: tokens.inkSubtle,
                    fontFamily: 'monospace',
                    fontSize: 10,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Padding(
          padding: const EdgeInsets.only(right: 12),
          child: AgentAnswerCard(
            record: record,
            species: species,
            onProfile: onProfile,
            onViewer: onViewer,
          ),
        ),
      ],
    );
  }
}

class _PhotoBubble extends StatefulWidget {
  const _PhotoBubble({required this.record});

  final ScanRecord record;

  @override
  State<_PhotoBubble> createState() => _PhotoBubbleState();
}

class _PhotoBubbleState extends State<_PhotoBubble> {
  late final Uint8List? _bytes = scanThumbBytes(widget.record);

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final bytes = _bytes;

    return Container(
      width: 158,
      height: 118,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(AppRadius.md),
          topRight: Radius.circular(AppRadius.md),
          bottomLeft: Radius.circular(AppRadius.md),
          bottomRight: Radius.circular(4),
        ),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [SkyPalette.primaryContainer, SkyPalette.mistDeep],
        ),
      ),
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (bytes == null)
            Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.photo_camera_back_outlined,
                    size: 24,
                    color: tokens.brandDeep.withValues(alpha: 0.55),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Earlier scan',
                    style: text.labelSmall?.copyWith(
                      color: tokens.inkMuted,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            )
          else
            Image.memory(
              bytes,
              fit: BoxFit.cover,
              gaplessPlayback: true,
              filterQuality: FilterQuality.medium,
            ),
          Positioned(
            left: 6,
            bottom: 6,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: SkyPalette.ink.withValues(alpha: 0.62),
                borderRadius: BorderRadius.circular(AppRadius.pill),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.center_focus_strong_rounded,
                    size: 10,
                    color: SkyPalette.foam,
                  ),
                  const SizedBox(width: 3),
                  Text(
                    'Scan',
                    style: text.labelSmall?.copyWith(
                      color: SkyPalette.foam,
                      fontSize: 9,
                      height: 1,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
