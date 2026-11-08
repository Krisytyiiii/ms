"""Spoken lesson for Syringodium isoetifolium. Same words as the transcript."""

TIMINGS = r"C:\Users\reaga\AppData\Local\Temp\si_isoetifolium_speech\timings.json"
WAV = r"C:\Users\reaga\AppData\Local\Temp\si_isoetifolium_speech\lesson.wav"

PARAGRAPHS = (
    "This is noodle seagrass, Syringodium isoetifolium. A display, not a scan of a meadow in Mati.",
    "Turn the plant. The leaf stays round. It is not a flat strap. The tip tapers to a point, the way a piece of spaghetti does.",
    "The leaves are about 7 to 30 centimetres long. The patch spreads when the buried stem grows through the sand and sends up new shoots. Roots grow down at each node. It can also flower and set seed.",
)

# text, SAPI rate (-10..10), pause after (seconds), subtitle (None = this text)
# A blank subtitle continues the previous line. "round" is its own beat so it can slow down.
BEATS = (
    ("This is noodle seagrass, Syringodium isoetifolium.", 2, 0.28, None),
    ("A display, not a scan of a meadow in Mati.", 2, 0.50, None),
    ("Turn the plant.", 1, 0.26, None),
    ("The leaf stays", 1, 0.04, "The leaf stays round."),
    ("round.", -4, 0.32, ""),
    ("It is not a flat strap.", 1, 0.20, None),
    ("The tip tapers to a point, the way a piece of spaghetti does.", 2, 0.36, None),
    ("The leaves are about 7 to 30 centimetres long.", 2, 0.18, None),
    ("The patch spreads when the buried stem grows through the sand and sends up new shoots.", 3, 0.16, None),
    ("Roots grow down at each node.", 2, 0.16, None),
    ("It can also flower and set seed.", 2, 0.24, None),
)


def transcript():
    return "\n\n".join(PARAGRAPHS)


def _norm(text):
    return " ".join(text.replace("\n", " ").split())


def assert_words():
    spoken = _norm(" ".join(beat[0] for beat in BEATS))
    source = _norm(" ".join(PARAGRAPHS))
    if spoken != source:
        raise SystemExit("spoken beats do not match the script")
