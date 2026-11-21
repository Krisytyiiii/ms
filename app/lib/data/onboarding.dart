import 'package:flutter/material.dart';

class OnboardingSlide {
  const OnboardingSlide({
    required this.icon,
    required this.eyebrow,
    required this.title,
    required this.body,
    required this.imageAsset,
  });

  final IconData icon;

  /// Small label above the title. Rendered uppercase.
  final String eyebrow;
  final String title;
  final String body;
  final String imageAsset;
}

// Hero photos sourced from Unsplash (license: unsplash.com/license).
const onboardingSlides = [
  OnboardingSlide(
    icon: Icons.photo_camera_outlined,
    eyebrow: 'Identify',
    title: 'Identify seagrass',
    body:
        'Take a photo or choose one from your gallery. An on-device SVM names '
        'the species in seconds, even without a signal.',
    imageAsset: 'assets/images/onboarding/identify.jpg',
  ),
  OnboardingSlide(
    icon: Icons.menu_book_outlined,
    eyebrow: 'Library',
    title: 'Browse the library',
    body:
        'Nine documented seagrass species from Mati City, Davao Oriental, with '
        'study fields for each one.',
    imageAsset: 'assets/images/onboarding/library.jpg',
  ),
  OnboardingSlide(
    icon: Icons.waves_outlined,
    eyebrow: 'Learn',
    title: 'Learn as you go',
    body:
        'Open a species profile for its study fields, then rotate the growth '
        'model and play the lesson clip.',
    imageAsset: 'assets/images/onboarding/learn.jpg',
  ),
];
