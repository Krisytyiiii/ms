# Halodule pinifolia

One species only. Out of scope: the other eight species, a trident tip, flowers, a photo scan, and any change to the Flutter viewer.

## The model is solid geometry

A leaf is a closed strap with a thin edge and a flat face. The tip is rounded. One central vein runs the face and divides into two at that tip. The outline does not grow teeth. The sand is a solid cutaway bed. One pale rhizome runs the front of the bed, with clean black leaf-scar bands at the nodes. Roots are solid tubes that go down into the sand at those nodes.

## Close to the real plant

Sources: the `halodule_pinifolia` record in `app/assets/data/species.json`, `docs/11-species.md`, and Seagrass-Watch.

The record says fine leaves up to about 20 cm, one central vein that splits in two at a rounded leaf tip, and a usually pale rhizome with clean black leaf scars. It lives on intertidal sand banks. The patch spreads when the buried rhizome grows, and the plant can also flower and set seed.

*Halodule uninervis* is the wrong species. It has a trident tip. A three-toothed tip fails this model.

## Layout numbers are display choices

These live in `CONFIG` in `halodule_pinifolia_build/config.py`. They are not Mati measurements.

| Choice | Value | Note |
| --- | --- | --- |
| Leaf width | 2.4 mm | OPEN. The record says fine and gives no number. |
| Leaf thickness | 0.28 mm | Display choice, so the edge stays thin. |
| Leaf length | 8–20 cm | The top is the record's "up to about 20 cm". The short end is a display choice. |
| Vein | 1 | The record states one central vein. |
| Meadow | one rhizome, roots at nodes | Same cutaway bed as the rotundata meadow. How far it sits behind the cut is a display choice. |

## Replace or build

Nothing of this species was built before. The phone file is `halodule_pinifolia.blend` and `halodule_pinifolia.glb`. The lesson is `halodule_pinifolia_lesson.blend` and `halodule_pinifolia_lesson.mp4`. The 900-frame lesson is not the phone file.

## What a person can still edit

`Authoring` holds `HP_Rhizome`, `HP_Leaf_ii_j`, `HP_Root_ii_r`, and `HP_Shoot_ii`. `Meadow` holds the solid meshes. `HP_Controls` stores `leaf_width_m`, `leaf_thickness_m`, `vein_count`, and `shoot_count`. `HP_HOW_TO_EDIT` in the blend has the five edit steps. `cr_width_m`, `cr_thickness_m`, and `cr_hand_edited` keep the shared property names.

## Growth

30 fps. The phone action `Grow` runs frames 1–330. Frame 316 holds. Frame 330 matches frame 1. Sand is complete from frame 1. Each part lengthens from its base. The lesson uses the same plant on a 900-frame clock: bud, rhizome, roots, shoots, then the full patch.

## Phone file

`app/assets/models-3d/halodule_pinifolia.glb`, also copied into this folder. Meadow and `HP_Armature` only. One clip, `Grow`. No camera. Under 40,000 triangles.

## Presentation and pitch

The lesson film is 30 seconds, 1920×1080, five spoken lines, no music. The phone viewer is what a person rotates.

This is needle seagrass, a display, not a scan of a Mati meadow. The buried stem grows through the sand, roots go down at the nodes, and new shoots rise until it is a patch. Turn it to see the fine strap, the vein that splits at a rounded tip, and the black scars on the pale rhizome. Leaf width is a display choice.

## Done when

`checks.validate` reports no problems. A close view shows one dark vein dividing on a rounded tip, not a trident. The rhizome reads pale, with clean black bands. Frame 1 and frame 330 of the phone file are the same bud.
