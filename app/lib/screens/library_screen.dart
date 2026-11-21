import 'package:flutter/material.dart';

import '../data/model_3d_library.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/library_deck.dart';
import '../widgets/library_filter_bar.dart';
import '../widgets/library_header.dart';
import 'species_screen.dart';

/// The nine documented Mati City seagrasses as a swipeable deck.
///
/// Search and genus filters narrow the deck; the facing card carries the photo
/// and names, and the bottom panel carries the readable details.
class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  late Future<_LibraryPayload> _future = _load();
  final _search = TextEditingController();
  String _query = '';
  String _genus = 'All';
  int _deckIndex = 0;

  Future<_LibraryPayload> _load() async {
    final items = await speciesCatalog.all();
    final media = await Model3dLibrary.resolveMany(
      items.map((species) => species.slug),
    );
    return _LibraryPayload(items: items, media: media);
  }

  void _reload() {
    setState(() {
      Model3dLibrary.resetCache();
      _future = _load();
    });
  }

  void _setQuery(String value) {
    setState(() {
      _query = value.trim().toLowerCase();
      _deckIndex = 0;
    });
  }

  void _setGenus(String value) {
    setState(() {
      _genus = value;
      _deckIndex = 0;
    });
  }

  void _clear() {
    _search.clear();
    setState(() {
      _query = '';
      _genus = 'All';
      _deckIndex = 0;
    });
  }

  void _open(Species species) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => SpeciesScreen(slug: species.slug),
      ),
    );
  }

  List<Species> _filter(List<Species> items) {
    return items.where((species) {
      final genus = species.scientificName.split(' ').first;
      final matchesGenus = _genus == 'All' || genus == _genus;
      final haystack = '${species.scientificName} ${species.commonName}'
          .toLowerCase();
      final matchesQuery = _query.isEmpty || haystack.contains(_query);
      return matchesGenus && matchesQuery;
    }).toList();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_LibraryPayload>(
      future: _future,
      builder: (context, snapshot) {
        final payload = snapshot.data;
        final items = payload?.items ?? const <Species>[];
        final genera = [
          'All',
          ...{
            for (final species in items)
              species.scientificName.split(' ').first,
          },
        ];

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LibraryHeader(
              controller: _search,
              onChanged: _setQuery,
              onClear: () {
                _search.clear();
                _setQuery('');
              },
            ),
            Expanded(
              child: switch (snapshot) {
                AsyncSnapshot(hasError: true) => _scrollPage([
                  _LibraryError(onRetry: _reload),
                ]),
                AsyncSnapshot(hasData: false) => const _DeckSkeleton(),
                _ => _library(
                  items: items,
                  visible: _filter(items),
                  media: payload?.media ?? const <String, SpeciesMedia>{},
                  genera: genera,
                ),
              },
            ),
          ],
        );
      },
    );
  }

  Widget _library({
    required List<Species> items,
    required List<Species> visible,
    required Map<String, SpeciesMedia> media,
    required List<String> genera,
  }) {
    final filtered = _query.isNotEmpty || _genus != 'All';
    final keyboard = MediaQuery.viewInsetsOf(context).bottom > 0;
    final label = visible.length == items.length
        ? 'Showing ${items.length} species'
        : 'Showing ${visible.length} of ${items.length} species';

    return Column(
      children: [
        if (!keyboard) ...[
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
            child: LibraryFilterBar(
              labels: genera,
              selected: _genus,
              onSelected: _setGenus,
            ),
          ),
          _showingRow(label, filtered),
        ],
        if (visible.isEmpty)
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              child: _LibraryEmpty(
                message: _query.isNotEmpty
                    ? 'No species name matches “$_query”.'
                    : 'No species in the $_genus filter.',
                onReset: _clear,
              ),
            ),
          )
        else
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              child: Column(
                children: [
                  Expanded(child: _deck(visible, media)),
                  if (!keyboard) ...[
                    const SizedBox(height: 10),
                    const _SwipeHint(),
                  ],
                ],
              ),
            ),
          ),
      ],
    );
  }

  Widget _deck(List<Species> visible, Map<String, SpeciesMedia> media) {
    final index = _deckIndex % visible.length;
    void advance() => setState(() => _deckIndex = (index + 1) % visible.length);

    return LibraryDeck(
      species: visible,
      media: media,
      index: index,
      onAdvance: advance,
      onOpen: _open,
    );
  }

  Widget _showingRow(String label, bool filtered) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 2, 8, 0),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(color: context.tokens.ink),
            ),
          ),
          if (filtered)
            TextButton(
              onPressed: _clear,
              style: TextButton.styleFrom(
                minimumSize: const Size(0, 32),
                padding: const EdgeInsets.symmetric(horizontal: 8),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text('Reset'),
            ),
        ],
      ),
    );
  }

  Widget _scrollPage(List<Widget> children) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: AppSpace.maxContent),
        child: ListView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: children,
        ),
      ),
    );
  }
}

class _LibraryPayload {
  const _LibraryPayload({required this.items, required this.media});

  final List<Species> items;
  final Map<String, SpeciesMedia> media;
}

/// One-line instruction above the deck. Gold reads as a hint, not an error,
/// and it disappears while the keyboard is open.
class _SwipeHint extends StatelessWidget {
  const _SwipeHint();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(
        color: SkyPalette.goldContainer,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: SkyPalette.sandDeep.withValues(alpha: 0.38)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.swipe_down_alt_rounded,
            size: 18,
            color: SkyPalette.notice,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Swipe the card down to see other species. '
              'Tap the image to see the info.',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: SkyPalette.notice,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// The empty state is part of the design: it names what failed to match and
/// offers one clear way back to the full deck.
class _LibraryEmpty extends StatelessWidget {
  const _LibraryEmpty({required this.message, required this.onReset});

  final String message;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(22, 26, 22, 22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: SkyPalette.goldContainer,
                border: Border.all(
                  color: SkyPalette.sandDeep.withValues(alpha: 0.4),
                ),
              ),
              child: const Icon(
                Icons.search_off_rounded,
                size: 28,
                color: SkyPalette.notice,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              'No matching species',
              textAlign: TextAlign.center,
              style: text.titleMedium?.copyWith(
                color: tokens.ink,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(message, textAlign: TextAlign.center, style: text.bodySmall),
            const SizedBox(height: 18),
            FilledButton(
              onPressed: onReset,
              style: FilledButton.styleFrom(
                minimumSize: const Size(0, 32),
                padding: const EdgeInsets.symmetric(horizontal: 14),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text('Show all species'),
            ),
          ],
        ),
      ),
    );
  }
}

class _LibraryError extends StatelessWidget {
  const _LibraryError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: tokens.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_rounded, size: 30, color: tokens.danger),
            const SizedBox(height: 12),
            Text(
              'The library could not open',
              textAlign: TextAlign.center,
              style: text.titleMedium?.copyWith(
                color: tokens.ink,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'The bundled species list did not load.',
              textAlign: TextAlign.center,
              style: text.bodySmall,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: onRetry,
              style: FilledButton.styleFrom(
                minimumSize: const Size(0, 32),
                padding: const EdgeInsets.symmetric(horizontal: 14),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text('Try again'),
            ),
          ],
        ),
      ),
    );
  }
}

class _DeckSkeleton extends StatelessWidget {
  const _DeckSkeleton();

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      child: Column(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: tokens.surfaceHigh,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: tokens.border),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Container(
            height: 168,
            decoration: BoxDecoration(
              color: tokens.surfaceHigh,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: tokens.border),
            ),
          ),
        ],
      ),
    );
  }
}
