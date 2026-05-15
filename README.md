# Fantasy Football Schedule Generator

A Python script that generates a complete 14-week regular season schedule for a 12-team dynasty fantasy football league with fixed rivalries. Designed to be run once per year; the output is copy-pasted into the league platform.

## Overview

The league has fixed membership (12 teams) and fixed rivalry pairings that do not change year to year. Each year, the same constraints apply but the non-rival matchups should vary, and certain matchups that occurred in prior years' weeks 2-3 (which become the repeat weeks in weeks 12-13) should be avoided when possible — so the same opponents don't end up playing each other twice in consecutive years.

## Schedule Structure

| Week  | Type                              |
|-------|-----------------------------------|
| 1     | Rivalry week                      |
| 2–11  | Non-rival round robin (10 weeks)  |
| 12    | Repeat of week 2                  |
| 13    | Repeat of week 3                  |
| 14    | Rivalry week (identical to week 1)|

## Scheduling Rules

1. **Rivalry weeks (1 and 14)** — Every team plays their designated permanent rival. These two weeks are identical to each other.

2. **Round-robin block (weeks 2–11)** — Every team plays every non-rival opponent exactly once across these 10 weeks. Each week has exactly 6 matchups covering all 12 teams. No rival pair appears in this block. With 12 teams and 6 rival pairs, there are exactly 60 non-rival pairs (`C(12,2) − 6 = 60`), which slots perfectly into 10 weeks × 6 matchups = 60.

3. **Repeat weeks (12 and 13)** — Week 12 reproduces week 2's matchups; week 13 reproduces week 3's matchups. This means the pairings in weeks 2 and 3 are the only non-rival pairings that occur twice in the regular season.

4. **Cross-year repeat avoidance (soft constraint)** — A `repeats` dictionary tracks which pairs were used in weeks 2-3 in prior years. When generating a new schedule, the script tries to choose pairs not in the dictionary for the new weeks 2-3, so the same opponents don't end up as repeat opponents in consecutive years. This is a soft constraint: the script minimizes overlap with the dictionary and warns if it can't fully avoid it, rather than failing.

## Methodology

### Combinatorial framing

The round-robin block is equivalent to a **1-factorization of K₁₂ minus a perfect matching**: decomposing the 60 non-rival edges of the complete graph on 12 vertices into 10 edge-disjoint perfect matchings, one per week. This decomposition is mathematically guaranteed to exist (K₂ₙ has chromatic index 2n − 1, and removing one color class leaves a graph with chromatic index 2n − 2 that decomposes into 2n − 2 perfect matchings).

### Construction via the circle method

The script uses the classical circle method for K₂ₙ 1-factorization:

- Label the 12 teams with indices 0–11.
- Fix team 11. The other 11 teams (0–10) rotate.
- For round `r` (`r = 0..10`): team 11 plays team `r`, and each remaining team `i` pairs with team `(2r − i) mod 11`.

This produces 11 perfect matchings that partition all 66 edges of K₁₂. By construction, round 0 produces the pairs `(11,0), (1,10), (2,9), (3,8), (4,7), (5,6)` — six pairs whose indices sum to 11 (treating the `(11,0)` slot as the special one).

The key trick: **map the 6 rival pairs onto those 6 index slots**, and round 0 becomes exactly the rival matching. Discarding round 0 leaves rounds 1–10 — exactly the 10 perfect matchings of non-rival pairs needed for weeks 2–11.

### Choosing weeks 2 and 3

After constructing the 10 round-robin rounds, the script enumerates all `C(10,2) = 45` ways to pick 2 of them for weeks 2-3 and scores each pick by counting how many of its 12 pairs appear in the `repeats` dictionary. The lowest-scoring pick (ideally zero) becomes weeks 2 and 3; the other 8 rounds are shuffled and assigned to weeks 4-11.

### Randomization for year-to-year variety

The circle method is deterministic, so randomization is introduced at two points:

1. **Rival-to-index assignment** — The 6 rival pairs are randomly mapped to the 6 index slots (`6!` orderings), and within each rival pair the two teams are randomly assigned to the two indices (`2⁶` swaps). This yields up to `6! × 2⁶ ≈ 46,000` distinct round-robin structures.

2. **Week ordering** — Once weeks 2-3 are chosen, the remaining 8 rounds are shuffled and assigned to weeks 4-11 in random order.

The script repeats step 1 up to 2000 times, keeping the best result seen so far, and short-circuits as soon as it finds a structure where the chosen weeks 2-3 have zero overlap with the `repeats` dictionary. In practice it almost always succeeds within the first handful of trials.

### Why this is reliable

Earlier implementations treated the `repeats` dictionary as a hard constraint on all 10 round-robin rounds, which conflicts with the rule that every non-rival pair plays exactly once in weeks 2-11. Blocking pairs entirely from a structure that requires all 60 non-rival pairs is overconstrained by design, which is why those versions kept hitting fallback paths.

The current approach instead:

- Always produces a valid 10-round round-robin, guaranteed by the 1-factorization theorem.
- Treats `repeats` as a soft scoring constraint applied only when choosing which 2 rounds become weeks 2-3 — which is where the rule actually applies.
- Cannot dead-end on a "no valid round exists" state.

## Usage

Requirements: Python 3.

```bash
python3 schedule.py
```

The script prompts for the year being generated, prints the full 14-week schedule, runs validation, and prints the pairs from weeks 2-3 formatted as Python dict entries to paste into the `repeats` dictionary for next year's run.

## Configuration

All configuration lives at the top of the script:

- `members` — list of 12 team names.
- `rivals` — symmetric dictionary mapping each team to its permanent rival.
- `repeats` — dictionary of pairs played as weeks 2-3 matchups in prior years. Keys are sorted-name tuples, values are the year (informational; only the keys are used by the algorithm).

After running, copy the printed dict-entry block into the `repeats` dictionary for the next year's run. The dictionary grows over time as a record of which pairings have been "double-played" in recent seasons.

## Validation

A built-in validator runs after every generation and checks:

- Each week has exactly 6 matchups covering all 12 teams once.
- Rival pairs appear only in weeks 1 and 14.
- Weeks 1 and 14 are identical.
- Weeks 12 and 13 match weeks 2 and 3 respectively.
- Every non-rival pair plays exactly once across weeks 2-11.
- No rival pair appears in weeks 2-11.

Any failure prints a detailed error report; success prints a confirmation.

## Output

The schedule prints week-by-week with annotations marking rivalry weeks and repeat weeks. The final block is the `repeats` dictionary update for next year, formatted ready to paste.

## Key Numbers

| Metric                                          | Value   |
|-------------------------------------------------|---------|
| Teams                                           | 12      |
| Rival pairs                                     | 6       |
| Total possible pairs (`C(12,2)`)                | 66      |
| Non-rival pairs                                 | 60      |
| Pairs needed for round robin (10 × 6)           | 60      |
| Distinct round-robin structures sampled         | ~46,000 |
| Round-robin attempts per run (max)              | 2,000   |
