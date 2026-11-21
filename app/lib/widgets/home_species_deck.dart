import 'package:flutter/material.dart';

import '../data/model_3d_library.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/app_photo.dart';
import '../widgets/section_header.dart';
import '../screens/shell_scope.dart';
import '../screens/species_screen.dart';

/// Home preview of the nine species as three stacked decks.
///
/// Each deck holds three species; tap the card (or a dot) to bring the next
/// species to the front, and tap a card's View to open its species page.
/// Photos and names come from the bundled catalog, not from invented copy.
class HomeSpeciesDeck extends StatefulWidget {
  const HomeSpeciesDeck({super.key});

  @override
  State<HomeSpeciesDeck> createState() => _HomeSpeciesDeckState();
}

class _HomeSpeciesDeckState extends State<HomeSpeciesDeck> {
  static const _stacks = 3;

  late final Future<_DeckPayload> _future = _load();
  final _positions = List<int>.filled(_stacks, 0);

  Future<_DeckPayload> _load() async {
    final species = await speciesCatalog.all();
    final media = await Model3dLibrary.resolveMany(
      species.map((item) => item.slug),
    );
    return _DeckPayload(species: species, media: media);
  }

  void _select(int stack, int index) {
    setState(() {
      _positions[stack] = index % _stacks;
    });
  }

  void _open(Species species) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => SpeciesScreen(slug: species.slug),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_DeckPayload>(
      future: _future,
      builder: (context, snapshot) {
        final payload = snapshot.data;
        if (payload == null) {
          return _frame(
            const Row(
              children: [
                Expanded(child: _Skeleton()),
                SizedBox(width: 10),
                Expanded(child: _Skeleton()),
                SizedBox(width: 10),
                Expanded(child: _Skeleton()),
              ],
            ),
          );
        }

        final columns = <List<Species>>[];
        for (var stack = 0; stack < _stacks; stack++) {
          final items = <Species>[];
          for (var row = 0; row < _stacks; row++) {
            final index = stack + row * _stacks;
            if (index < payload.species.length) {
              items.add(payload.species[index]);
            }
          }
          columns.add(items);
        }

        return _frame(
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var stack = 0; stack < _stacks; stack++) ...[
                if (stack > 0) const SizedBox(width: 10),
                Expanded(
                  child: _DeckColumn(
                    species: columns[stack],
                    media: payload.media,
                    position: _positions[stack] % columns[stack].length,
                    onSelect: (index) => _select(stack, index),
                    onOpen: _open,
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _frame(Widget decks) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Seagrass species',
          action: 'View all',
          onAction: () => ShellScope.of(context).select(ShellTab.library),
        ),
        const SizedBox(height: 10),
        decks,
      ],
    );
  }
}

class _DeckPayload {
  const _DeckPayload({required this.species, required this.media});

  final List<Species> species;
  final Map<String, SpeciesMedia> media;
}

/// One deck: two still layers behind, one interactive card in front.
class _DeckColumn extends StatelessWidget {
  const _DeckColumn({
    required this.species,
    required this.media,
    required this.position,
    required this.onSelect,
    required this.onOpen,
  });

  final List<Species> species;
  final Map<String, SpeciesMedia> media;
  final int position;
  final ValueChanged<int> onSelect;
  final void Function(Species) onOpen;

  static const _cardHeight = 156.0;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final current = species[position];

    return SizedBox(
      height: 170,
      child: Stack(
        alignment: Alignment.topCenter,
        children: [
          Positioned(
            left: 7,
            right: 7,
            top: 14,
            height: _cardHeight,
            child: _layer(tokens.surface, tokens.border),
          ),
          Positioned(
            left: 3.5,
            right: 3.5,
            top: 7,
            height: _cardHeight,
            child: _layer(tokens.surface, tokens.border),
          ),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 320),
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            transitionBuilder: (child, animation) {
              final slide =
                  Tween<Offset>(
                    begin: const Offset(0, 0.16),
                    end: Offset.zero,
                  ).animate(
                    CurvedAnimation(
                      parent: animation,
                      curve: Curves.easeOutBack,
                    ),
                  );
              return FadeTransition(
                opacity: animation,
                child: SlideTransition(position: slide, child: child),
              );
            },
            child: SizedBox(
              key: ValueKey(current.slug),
              height: _cardHeight,
              child: _SpeciesTile(
                species: current,
                imageAsset: media[current.slug]?.stillAsset,
                dots: species.length,
                activeDot: position,
                onSelect: onSelect,
                onCycle: () => onSelect((position + 1) % species.length),
                onOpen: () => onOpen(current),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _layer(Color color, Color border) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: border),
      ),
    );
  }
}

class _SpeciesTile extends StatelessWidget {
  const _SpeciesTile({
    required this.species,
    required this.imageAsset,
    required this.dots,
    required this.activeDot,
    required this.onSelect,
    required this.onCycle,
    required this.onOpen,
  });

  final Species species;
  final String? imageAsset;
  final int dots;
  final int activeDot;
  final ValueChanged<int> onSelect;
  final VoidCallback onCycle;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;
    final genus = species.scientificName.split(' ').first;

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        boxShadow: tokens.cardShadows,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Material(
          color: tokens.surfaceHigh,
          child: InkWell(
            onTap: onCycle,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  child: imageAsset == null
                      ? DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                SkyPalette.primaryContainer,
                                tokens.surfaceHigh,
                              ],
                            ),
                          ),
                          child: Center(
                            child: Icon(
                              Icons.spa_outlined,
                              size: 28,
                              color: tokens.brand,
                            ),
                          ),
                        )
                      : AppPhoto(
                          asset: imageAsset!,
                          semanticLabel: '${species.commonName} photo',
                        ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(8, 7, 8, 7),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        genus.toUpperCase(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: text.labelSmall?.copyWith(
                          color: tokens.inkSubtle,
                          fontSize: 7.5,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.7,
                        ),
                      ),
                      const SizedBox(height: 2),
                      SizedBox(
                        height: 26,
                        child: Text(
                          species.commonName,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: text.labelMedium?.copyWith(
                            color: tokens.ink,
                            fontSize: 11,
                            height: 1.18,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Expanded(
                            child: _DeckDots(
                              count: dots,
                              active: activeDot,
                              onSelect: onSelect,
                            ),
                          ),
                          const SizedBox(width: 2),
                          _ViewPill(onTap: onOpen),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DeckDots extends StatelessWidget {
  const _DeckDots({
    required this.count,
    required this.active,
    required this.onSelect,
  });

  final int count;
  final int active;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Row(
      children: [
        for (var dot = 0; dot < count; dot++)
          Expanded(
            child: Semantics(
              button: true,
              selected: dot == active,
              label: 'Species ${dot + 1} of $count',
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => onSelect(dot),
                child: SizedBox(
                  height: 20,
                  child: Center(
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      width: dot == active ? 6 : 4,
                      height: dot == active ? 6 : 4,
                      decoration: BoxDecoration(
                        color: dot == active
                            ? tokens.brand
                            : tokens.borderStrong,
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _ViewPill extends StatelessWidget {
  const _ViewPill({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 22,
        padding: const EdgeInsets.symmetric(horizontal: 9),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: SkyPalette.primary,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Text(
          'View',
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: SkyPalette.onPrimary,
            fontSize: 9,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class _Skeleton extends StatelessWidget {
  const _Skeleton();

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Container(
      height: 156,
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: tokens.border),
      ),
    );
  }
}
