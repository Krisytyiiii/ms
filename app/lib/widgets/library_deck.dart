import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data/model_3d_library.dart';
import '../data/species.dart';
import '../theme/tokens.dart';
import 'app_photo.dart';

/// Swipeable species deck.
///
/// The front card follows the finger downward; past a short threshold or with
/// a fast flick it flings off the bottom and the next species comes forward.
/// Tapping the card opens that species' full profile.
class LibraryDeck extends StatefulWidget {
  const LibraryDeck({
    super.key,
    required this.species,
    required this.media,
    required this.index,
    required this.onAdvance,
    required this.onOpen,
  });

  final List<Species> species;
  final Map<String, SpeciesMedia> media;
  final int index;
  final VoidCallback onAdvance;
  final ValueChanged<Species> onOpen;

  @override
  State<LibraryDeck> createState() => _LibraryDeckState();
}

enum _DeckMotion { idle, flying, returning }

class _LibraryDeckState extends State<LibraryDeck>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  _DeckMotion _motion = _DeckMotion.idle;
  final ValueNotifier<double> _drag = ValueNotifier<double>(0);
  double _from = 0;
  double _to = 0;
  Curve _curve = Curves.easeOutCubic;
  bool _advanceAfter = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: AppMotion.medium);
  }

  @override
  void didUpdateWidget(covariant LibraryDeck oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.index != widget.index) {
      _controller.stop();
      _motion = _DeckMotion.idle;
      _drag.value = 0;
    }
  }

  @override
  void dispose() {
    _drag.dispose();
    _controller.dispose();
    super.dispose();
  }

  double _offset(double cardHeight) {
    if (_motion == _DeckMotion.idle) {
      return _drag.value;
    }
    final t = _curve.transform(_controller.value);
    return _from + (_to - _from) * t;
  }

  void _settle(double from, double to, Curve curve, {required bool advance}) {
    setState(() {
      _motion = advance ? _DeckMotion.flying : _DeckMotion.returning;
      _from = from;
      _to = to;
      _curve = curve;
      _advanceAfter = advance;
    });
    _controller.duration = Duration(milliseconds: advance ? 280 : 220);
    _controller.forward(from: 0).then((_) {
      if (!mounted) {
        return;
      }
      final advanceNow = _advanceAfter;
      setState(() {
        _motion = _DeckMotion.idle;
        _advanceAfter = false;
      });
      _drag.value = 0;
      _controller.value = 0;
      if (advanceNow) {
        widget.onAdvance();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final count = widget.species.length;
    final index = count == 0 ? 0 : widget.index % count;

    return LayoutBuilder(
      builder: (context, constraints) {
        final peek = 16.0;
        final cardHeight = math.max(120.0, constraints.maxHeight - peek * 2);
        final current = widget.species[index];
        final backLayers = math.min(2, count - 1);

        return Stack(
          alignment: Alignment.topCenter,
          children: [
            for (var layer = backLayers; layer >= 1; layer--)
              Positioned(
                top: peek * layer,
                left: 10.0 * layer,
                right: 10.0 * layer,
                height: cardHeight,
                child: const _DeckLayer(),
              ),
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              height: cardHeight,
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => widget.onOpen(current),
                onVerticalDragUpdate: (details) {
                  if (_motion != _DeckMotion.idle) {
                    return;
                  }
                  _drag.value = math.max(0, _drag.value + details.delta.dy);
                },
                onVerticalDragEnd: (details) {
                  if (_motion != _DeckMotion.idle) {
                    return;
                  }
                  final velocity = details.primaryVelocity ?? 0;
                  if (_drag.value > cardHeight * 0.22 || velocity > 600) {
                    _settle(
                      _drag.value,
                      cardHeight * 1.4 + 40,
                      Curves.easeInCubic,
                      advance: true,
                    );
                  } else {
                    _settle(
                      _drag.value,
                      0,
                      Curves.easeOutCubic,
                      advance: false,
                    );
                  }
                },
                onVerticalDragCancel: () {
                  if (_motion == _DeckMotion.idle && _drag.value > 0) {
                    _settle(
                      _drag.value,
                      0,
                      Curves.easeOutCubic,
                      advance: false,
                    );
                  }
                },
                child: AnimatedBuilder(
                  animation: Listenable.merge([_controller, _drag]),
                  builder: (context, child) {
                    final offset = _offset(cardHeight);
                    final progress = (offset / cardHeight).clamp(0.0, 1.6);
                    return Opacity(
                      opacity: (1 - progress * 0.45).clamp(0.4, 1.0),
                      child: Transform.translate(
                        offset: Offset(0, offset),
                        child: Transform.rotate(
                          angle: progress * 0.14,
                          child: child,
                        ),
                      ),
                    );
                  },
                  child: RepaintBoundary(
                    child: AnimatedSwitcher(
                      duration: AppMotion.fast,
                      switchInCurve: AppMotion.ease,
                      switchOutCurve: AppMotion.ease,
                      child: _DeckCard(
                        key: ValueKey(current.slug),
                        species: current,
                        media: widget.media[current.slug],
                        position: index + 1,
                        total: count,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _DeckLayer extends StatelessWidget {
  const _DeckLayer();

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: tokens.border),
      ),
    );
  }
}

class _DeckCard extends StatelessWidget {
  const _DeckCard({
    super.key,
    required this.species,
    required this.media,
    required this.position,
    required this.total,
  });

  final Species species;
  final SpeciesMedia? media;
  final int position;
  final int total;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;
    final still = media?.stillAsset;
    final hasClip = media?.hasVideo == true || media?.hasLesson == true;
    final hasModel = media?.hasModel == true;

    return Semantics(
      button: true,
      label:
          '${species.scientificName}, ${species.commonName}. '
          'Tap for details. Swipe down for the next species.',
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          boxShadow: tokens.cardShadows,
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Stack(
            fit: StackFit.expand,
            children: [
              if (still == null)
                const _DeckFallback()
              else
                AppPhoto(
                  asset: still,
                  semanticLabel: '${species.commonName} photo',
                ),
              const Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Color(0x33023E8A),
                        Color(0x00023E8A),
                        Color(0xB3023E8A),
                        Color(0xF2023E8A),
                      ],
                      stops: [0.0, 0.34, 0.76, 1.0],
                    ),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        _DeckBadge(
                          label:
                              '${position.toString().padLeft(2, '0')}'
                              ' / ${total.toString().padLeft(2, '0')}',
                        ),
                        const Spacer(),
                        _DeckBadge(
                          label: hasClip
                              ? 'CLIP'
                              : hasModel
                              ? '3D'
                              : 'PHOTO',
                          icon: hasClip
                              ? Icons.play_arrow_rounded
                              : hasModel
                              ? Icons.view_in_ar_outlined
                              : Icons.photo_outlined,
                        ),
                      ],
                    ),
                    const Spacer(),
                    Text(
                      species.commonName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.titleLarge?.copyWith(
                        color: SkyPalette.onHeader,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      species.scientificName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.bodySmall?.copyWith(
                        color: SkyPalette.onHeader.withValues(alpha: 0.82),
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DeckBadge extends StatelessWidget {
  const _DeckBadge({required this.label, this.icon});

  final String label;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 26,
      padding: const EdgeInsets.symmetric(horizontal: 9),
      decoration: BoxDecoration(
        color: SkyPalette.primaryDark.withValues(alpha: 0.58),
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: SkyPalette.foam.withValues(alpha: 0.24)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 13, color: SkyPalette.goldBright),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: SkyPalette.onHeader,
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.7,
            ),
          ),
        ],
      ),
    );
  }
}

class _DeckFallback extends StatelessWidget {
  const _DeckFallback();

  @override
  Widget build(BuildContext context) {
    return const DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [SkyPalette.primary, SkyPalette.primaryDark],
        ),
      ),
      child: Center(
        child: Icon(Icons.spa_outlined, size: 52, color: SkyPalette.goldBright),
      ),
    );
  }
}
