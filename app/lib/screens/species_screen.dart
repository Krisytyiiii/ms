import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data/model_3d_library.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/app_states.dart';
import '../widgets/diamond_grid_background.dart';
import '../widgets/species_detail.dart';
import 'viewer_3d_screen.dart';

class SpeciesScreen extends StatefulWidget {
  const SpeciesScreen({super.key, required this.slug});

  final String slug;

  @override
  State<SpeciesScreen> createState() => _SpeciesScreenState();
}

class _SpeciesScreenState extends State<SpeciesScreen> {
  late Future<_SpeciesProfile> _future = _load();

  Future<_SpeciesProfile> _load() async {
    final species = await speciesCatalog.bySlug(widget.slug);
    final media = species == null
        ? const SpeciesMedia()
        : await Model3dLibrary.resolve(species.slug);
    return _SpeciesProfile(species: species, media: media);
  }

  void _reload() => setState(() => _future = _load());

  void _openViewer(Species species) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => Viewer3dScreen(slug: species.slug),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_SpeciesProfile>(
      future: _future,
      builder: (context, snapshot) {
        final ready = snapshot.hasData && snapshot.data?.species != null;
        return AnnotatedRegion<SystemUiOverlayStyle>(
          value: ready ? SkyPalette.lightStatusBar : SkyPalette.darkStatusBar,
          child: Scaffold(
            backgroundColor: context.tokens.abyss,
            body: _body(context, snapshot),
          ),
        );
      },
    );
  }

  Widget _body(BuildContext context, AsyncSnapshot<_SpeciesProfile> snapshot) {
    if (snapshot.hasError) {
      return _message(
        context,
        OceanError(message: 'Could not load this species.', onRetry: _reload),
      );
    }
    if (!snapshot.hasData && snapshot.connectionState != ConnectionState.done) {
      return _message(context, const OceanLoading(label: 'Loading profile…'));
    }
    final species = snapshot.data?.species;
    if (species == null) {
      return _message(
        context,
        const OceanEmpty(
          icon: Icons.search_off,
          title: 'Species not found',
          message: 'This slug is not in the bundled library.',
        ),
      );
    }

    return _profile(context, species: species, media: snapshot.data!.media);
  }

  Widget _profile(
    BuildContext context, {
    required Species species,
    required SpeciesMedia media,
  }) {
    final text = Theme.of(context).textTheme;
    final width = MediaQuery.sizeOf(context).width;
    final height = MediaQuery.sizeOf(context).height;
    final horizontal = width >= 768 ? 32.0 : 16.0;
    final heroHeight = (height * 0.46).clamp(290.0, 430.0);

    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: AppSpace.maxContent),
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              pinned: true,
              expandedHeight: heroHeight,
              backgroundColor: SkyPalette.primaryDark,
              foregroundColor: SkyPalette.onHeader,
              elevation: 0,
              scrolledUnderElevation: 0,
              leadingWidth: 64,
              leading: Center(
                child: _CircleBack(
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ),
              titleSpacing: 0,
              title: Text(
                species.commonName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: text.titleMedium?.copyWith(
                  color: SkyPalette.onHeader,
                  fontWeight: FontWeight.w600,
                ),
              ),
              actions: [
                Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: Center(child: SpeciesMediaChip(media: media)),
                ),
              ],
              flexibleSpace: FlexibleSpaceBar(
                collapseMode: CollapseMode.parallax,
                background: SpeciesHero(
                  species: species,
                  stillAsset: media.stillAsset,
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Container(
                color: context.tokens.abyss,
                padding: EdgeInsets.fromLTRB(horizontal, 18, horizontal, 40),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SpeciesMediaCard(
                      media: media,
                      onOpen: () => _openViewer(species),
                    ),
                    const SizedBox(height: 22),
                    const SpeciesSectionLabel(label: 'SPECIES NOTES'),
                    const SizedBox(height: 10),
                    SpeciesFactCard(
                      index: 1,
                      icon: Icons.spa_outlined,
                      title: 'Botanical characteristics',
                      value: species.botanicalCharacteristics,
                    ),
                    const SizedBox(height: 12),
                    SpeciesFactCard(
                      index: 2,
                      icon: Icons.water_outlined,
                      title: 'Ecological role',
                      value: species.ecologicalRole,
                    ),
                    const SizedBox(height: 12),
                    SpeciesFactCard(
                      index: 3,
                      icon: Icons.shield_outlined,
                      title: 'Conservation status',
                      value: species.conservationStatus,
                    ),
                    const SizedBox(height: 12),
                    SpeciesFactCard(
                      index: 4,
                      icon: Icons.place_outlined,
                      title: 'Habitat',
                      value: species.habitat,
                    ),
                    const SizedBox(height: 12),
                    SpeciesFactCard(
                      index: 5,
                      icon: Icons.timeline_outlined,
                      title: 'Growth process',
                      value: species.growthProcess,
                    ),
                    const SizedBox(height: 18),
                    if (species.transcript != null &&
                        species.transcript!.isNotEmpty) ...[
                      SpeciesTranscriptCard(text: species.transcript!),
                      const SizedBox(height: 12),
                    ],
                    SpeciesSourcesCard(sources: species.sources),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _message(BuildContext context, Widget child) {
    return Stack(
      children: [
        const Positioned.fill(child: DiamondGridBackground(seed: 77)),
        SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: _CircleBack(
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ),
              ),
              Expanded(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: child,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SpeciesProfile {
  const _SpeciesProfile({required this.species, required this.media});

  final Species? species;
  final SpeciesMedia media;
}

class _CircleBack extends StatelessWidget {
  const _CircleBack({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Material(
      color: SkyPalette.foam.withValues(alpha: 0.92),
      shape: CircleBorder(side: BorderSide(color: tokens.border)),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onPressed,
        child: const SizedBox(
          width: 44,
          height: 44,
          child: Icon(
            Icons.arrow_back_rounded,
            size: 20,
            color: SkyPalette.ink,
          ),
        ),
      ),
    );
  }
}
