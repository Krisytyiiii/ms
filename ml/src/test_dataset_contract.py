from dataset_contract import TRAINABLE_SPECIES, classify_folder


def test_study_all_and_research_grade():
    assert classify_folder("Enhalus acoroides dataset (all)") == (
        "enhalus_acoroides",
        "study",
        "all",
    )
    assert classify_folder("Enhalus acoroides dataset (research-grade)") == (
        "enhalus_acoroides",
        "study",
        "research-grade",
    )


def test_rotundata_without_all_suffix():
    assert classify_folder("Cymodocea rotundata dataset") == (
        "cymodocea_rotundata",
        "study",
        "all",
    )


def test_copy_and_extra_taxon():
    assert classify_folder("Halophila ovalis dataset (research-grade) - Copy") == (
        "halophila_ovalis",
        "study",
        "copy",
    )
    assert classify_folder("Halophila spinulosa dataset (all)")[1] == "extra"


def test_nine_classes_are_trainable():
    # The 16 Nov 2026 audit returned `clean`, so the held-out class is trainable
    # again. The locked v1/v2 artifacts stay eight-class and are not rebuilt.
    assert "thalassia_hemprichii" in TRAINABLE_SPECIES
    assert len(TRAINABLE_SPECIES) == 9


if __name__ == "__main__":
    test_study_all_and_research_grade()
    test_rotundata_without_all_suffix()
    test_copy_and_extra_taxon()
    test_nine_classes_are_trainable()
    print("ok")
