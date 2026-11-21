import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Gradient header for the species library.
///
/// Carries the title, the number of bundled species, and a live search field
/// so the list below can filter as the user types.
class LibraryHeader extends StatelessWidget {
  const LibraryHeader({
    super.key,
    required this.controller,
    required this.onChanged,
    required this.onClear,
  });

  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

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
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Species Library',
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
                          'Documented seagrasses of Mati City',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: text.bodySmall?.copyWith(
                            color: SkyPalette.onHeader.withValues(alpha: 0.72),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _LibrarySearch(
                controller: controller,
                onChanged: onChanged,
                onClear: onClear,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Frosted search field that sits on the blue header.
class _LibrarySearch extends StatelessWidget {
  const _LibrarySearch({
    required this.controller,
    required this.onChanged,
    required this.onClear,
  });

  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final hasText = controller.text.isNotEmpty;

    return Material(
      color: SkyPalette.foam.withValues(alpha: 0.14),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.pill),
        side: BorderSide(color: SkyPalette.foam.withValues(alpha: 0.26)),
      ),
      child: TextField(
        controller: controller,
        onChanged: onChanged,
        textInputAction: TextInputAction.search,
        style: const TextStyle(
          color: SkyPalette.onHeader,
          fontSize: 15,
          height: 1.3,
        ),
        cursorColor: SkyPalette.goldBright,
        decoration: InputDecoration(
          isDense: true,
          filled: false,
          hintText: 'Search by scientific or common name',
          hintStyle: TextStyle(
            color: SkyPalette.onHeader.withValues(alpha: 0.62),
            fontSize: 14,
          ),
          prefixIcon: Icon(
            Icons.search,
            size: 20,
            color: SkyPalette.onHeader.withValues(alpha: 0.8),
          ),
          suffixIcon: hasText
              ? IconButton(
                  tooltip: 'Clear search',
                  onPressed: onClear,
                  icon: Icon(
                    Icons.close_rounded,
                    size: 18,
                    color: SkyPalette.onHeader.withValues(alpha: 0.85),
                  ),
                )
              : null,
          contentPadding: const EdgeInsets.symmetric(vertical: 14),
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
        ),
      ),
    );
  }
}
