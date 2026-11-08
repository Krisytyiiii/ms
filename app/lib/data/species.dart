class Species {
  const Species({
    required this.slug,
    required this.scientificName,
    required this.commonName,
    required this.botanicalCharacteristics,
    required this.ecologicalRole,
    required this.conservationStatus,
    required this.habitat,
    required this.growthProcess,
    required this.sources,
    this.pitch,
    this.transcript,
  });

  final String slug;
  final String scientificName;
  final String commonName;
  final String botanicalCharacteristics;
  final String ecologicalRole;
  final String conservationStatus;
  final String habitat;
  final String growthProcess;
  final List<String> sources;

  /// Locked narration. The same words as the bundled recording, when one exists.
  final String? pitch;

  /// Spoken lines for the lesson clip, when that clip has a voice.
  final String? transcript;

  bool get dataComing => slug == 'thalassia_hemprichii';

  factory Species.fromJson(Map<String, dynamic> json) {
    return Species(
      slug: json['slug'] as String,
      scientificName: json['scientificName'] as String,
      commonName: json['commonName'] as String,
      botanicalCharacteristics: json['botanicalCharacteristics'] as String,
      ecologicalRole: json['ecologicalRole'] as String,
      conservationStatus: json['conservationStatus'] as String,
      habitat: json['habitat'] as String,
      growthProcess: json['growthProcess'] as String,
      sources: [
        for (final item in json['sources'] as List<dynamic>) item as String,
      ],
      pitch: json['pitch'] as String?,
      transcript: json['transcript'] as String?,
    );
  }
}
