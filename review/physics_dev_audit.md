# Physics dev audit, 2026-11-13

Reviewer 1 of the 28 public Class 9–10 physics items. Reviewer 2 is not filled
in. `verified` stays false. A score on this split is still a harness demo.

The sheet is `review/physics_dev_r1.csv`. `review-apply` will not mark any row
verified from that file, because the second reviewer is empty and no row is
`accept`.

## What was checked

Every stored calculation was recomputed from its `answer_check.expression`.
The arithmetic matches the key on all 28 items. The non-numeric keys were read
against the usual school rule.

| Item | Key | Verdict |
|---|---|---|
| bebench-phy-001 | Electric current is a base quantity. Force, velocity and pressure are derived. | key yes |
| bebench-phy-004 | 0.00450 has 3 significant figures. | key yes; confirm the 2026 section |
| bebench-phy-007 | In vacuum the feather and the iron ball land together. | key yes |
| bebench-phy-010 | F = ma = 10 N. | key yes |
| bebench-phy-013 | Rolling friction is the smallest of the three school cases. | key yes; confirm the book's wording |
| bebench-phy-016 | mgh = 98 J. | key yes |
| bebench-phy-019 | A solid floats when its density is less than water. | key yes |
| bebench-phy-022 | Specific heat of water taken as 4200 J kg⁻¹ K⁻¹. | key yes; confirm the printed value |
| bebench-phy-025 | Among the options, sound is fastest in steel and does not travel in vacuum. | key yes |
| bebench-phy-028 | An optical fibre carries light by total internal reflection. | key yes |
| bebench-phy-031 | Doubling the distance makes the Coulomb force one quarter. | key yes |
| bebench-phy-034 | The fuse is on the live wire. | key yes |
| bebench-phy-037 | Gamma is the most penetrating of the three. | key yes |
| bebench-phy-039 | Vernier constant 0.1 mm. | key yes |
| bebench-phy-042 | Retardation 5 m s⁻². | key yes |
| bebench-phy-045 | Recoil speed 1 m s⁻¹. | key yes |
| bebench-phy-048 | Efficiency 80%. | key yes |
| bebench-phy-051 | Pressure 20000 Pa. | key yes |
| bebench-phy-054 | Heat to melt the ice 168000 J, using L = 336000. | key yes; confirm L in the book |
| bebench-phy-057 | Refractive index 1.5. | key yes |
| bebench-phy-060 | Energy used 15 kWh. | key yes |
| bebench-phy-063 | 5 g left after four half-lives. | key yes; confirm the syllabus still has half-life |
| bebench-phy-066 | The instrument is a barometer. | key yes |
| bebench-phy-069 | The usual second law is i = r. | key yes; confirm the book numbers it second |
| bebench-phy-070 | Parts খ, গ and ঘ check out (total distance 550 m). Part ক does not. | key no |
| bebench-phy-073 | Density 600 kg m⁻³, it floats, submerged fraction 0.6. | key yes |
| bebench-phy-076 | v = 60 cm and the magnitude of m is 2. The key also accepts −2. | key yes; confirm the sign convention |
| bebench-phy-079 | Equivalent resistance 5 Ω, current in the 4 Ω resistor 1.8 A. | key yes |

## The one key to change

`bebench-phy-070` part ক says acceleration is the rate at which speed increases.
The definition to accept is the rate of change of velocity. That includes
slowing down and a change of direction. The correction belongs in
`data/private/source/`, then a rebuild. This audit does not edit the public
JSONL.

## Why nothing is verified

`syllabus_ok` is no on every row. The chapter titles match the items, and the
section numbers in `topic_id` were not checked against the 2026 book. Chapters
4–13 were mapped earlier without that check. A teacher with the book fills
reviewer 2. An item becomes verified only when both reviewers accept it, or an
adjudicator accepts it.
