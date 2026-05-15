# -*- coding: utf-8 -*-
"""
Created on Thu May 14 21:23:23 2026

@author: natha
"""

"""
Fantasy Football Schedule Generator — 12 team dynasty league.

Structure:
  Week 1:        rivalry week (every team plays their rival)
  Weeks 2-11:    full non-rival round robin (every non-rival pair plays once)
  Week 12:       repeat of week 2
  Week 13:       repeat of week 3
  Week 14:       rivalry week (same as week 1)

The `repeats` dict tracks pairs that were used as the weeks 2-3 repeat
matchups in PRIOR years. We try to avoid them when picking which two
rounds of the round robin become weeks 2-3. If we can't fully avoid them,
we minimize the count and warn rather than silently clearing history.
"""

import random
from collections import defaultdict

# --------------------------------------------------------------------------
# League configuration
# --------------------------------------------------------------------------

members = [
    "Nathan", "Nick", "Greg", "Ryan A", "Ryan C", "Aiden",
    "Colin", "Levi", "Tyler", "Brian", "Bradley", "Jayden"
]

rivals = {
    "Nathan": "Brian", "Brian": "Nathan",
    "Nick": "Greg", "Greg": "Nick",
    "Jayden": "Aiden", "Aiden": "Jayden",
    "Ryan A": "Tyler", "Tyler": "Ryan A",
    "Ryan C": "Colin", "Colin": "Ryan C",
    "Levi": "Bradley", "Bradley": "Levi",
}

# Pairs that were the weeks 2-3 matchups in prior years.
# Avoid these for the new weeks 2-3 if possible.
repeats = {
    tuple(sorted(("Nathan", "Aiden"))): 2025,
    tuple(sorted(("Levi", "Brian"))): 2025,
    tuple(sorted(("Bradley", "Greg"))): 2025,
    tuple(sorted(("Nick", "Jayden"))): 2025,
    tuple(sorted(("Ryan A", "Ryan C"))): 2025,
    tuple(sorted(("Colin", "Tyler"))): 2025,
    tuple(sorted(("Nathan", "Jayden"))): 2025,
    tuple(sorted(("Tyler", "Ryan C"))): 2025,
    tuple(sorted(("Levi", "Greg"))): 2025,
    tuple(sorted(("Colin", "Nick"))): 2025,
    tuple(sorted(("Brian", "Ryan A"))): 2025,
    tuple(sorted(("Bradley", "Aiden"))): 2025,
    tuple(sorted(("Aiden", "Brian"))): 2026,
    tuple(sorted(("Aiden", "Levi"))): 2026,
    tuple(sorted(("Bradley", "Colin"))): 2026,
    tuple(sorted(("Bradley", "Tyler"))): 2026,
    tuple(sorted(("Brian", "Greg"))): 2026,
    tuple(sorted(("Colin", "Jayden"))): 2026,
    tuple(sorted(("Greg", "Nathan"))): 2026,
    tuple(sorted(("Jayden", "Ryan A"))): 2026,
    tuple(sorted(("Levi", "Ryan C"))): 2026,
    tuple(sorted(("Nathan", "Tyler"))): 2026,
    tuple(sorted(("Nick", "Ryan A"))): 2026,
    tuple(sorted(("Nick", "Ryan C"))): 2026,
}

# --------------------------------------------------------------------------
# Sanity checks on configuration
# --------------------------------------------------------------------------

assert len(members) == 12, "League must have 12 members"
assert len(set(members)) == 12, "Member names must be unique"
assert all(rivals[m] in members for m in members), "Each rival must be a member"
assert all(rivals[rivals[m]] == m for m in members), "Rivalries must be symmetric"
assert all(rivals[m] != m for m in members), "A team can't be its own rival"

# Extract canonical list of 6 rival pairs
rival_pairs = []
_seen = set()
for t in members:
    if t not in _seen:
        rival_pairs.append((t, rivals[t]))
        _seen.add(t)
        _seen.add(rivals[t])
assert len(rival_pairs) == 6


# --------------------------------------------------------------------------
# Round-robin generation via the circle method
# --------------------------------------------------------------------------
"""
 Classical 1-factorization of K_12: label teams 0..11, fix team 11. For
 round r in 0..10, team 11 plays team r, and team i plays team (2r - i)
 mod 11 for each i in {0..10} with i != r.

 Round 0 produces the pairs: (11,0), (1,10), (2,9), (3,8), (4,7), (5,6) —
 a perfect matching. If we map our 6 rival pairs onto those 6 index pairs,
 then round 0 IS the rival matching, and rounds 1..10 are 10 perfect
 matchings of non-rival pairs that cover every non-rival pair exactly once.

 Randomizing which rival pair lands on which index slot (6! orderings) and
 which team in each rival pair gets which index (2^6 swaps) gives ~46,000
 distinct round-robin structures to draw from year to year.
"""

def generate_non_rival_rounds(rival_pairs):
    """Return 10 perfect matchings (rounds), each a list of 6 sorted pair
    tuples, covering all 60 non-rival pairs exactly once."""

    index_slot_pairs = [(11, 0), (1, 10), (2, 9), (3, 8), (4, 7), (5, 6)]

    rps = list(rival_pairs)
    random.shuffle(rps)
    random.shuffle(index_slot_pairs)

    team_to_idx = {}
    for (a, b), (ia, ib) in zip(rps, index_slot_pairs):
        if random.random() < 0.5:
            team_to_idx[a], team_to_idx[b] = ia, ib
        else:
            team_to_idx[a], team_to_idx[b] = ib, ia

    idx_to_team = {v: k for k, v in team_to_idx.items()}

    rounds = []
    for r in range(1, 11):  # skip round 0 — that's the rival matching
        pairs = [tuple(sorted((idx_to_team[11], idx_to_team[r])))]
        seen = {r}
        for i in range(11):
            if i in seen:
                continue
            j = (2 * r - i) % 11
            if j == i or j in seen:
                continue
            pairs.append(tuple(sorted((idx_to_team[i], idx_to_team[j]))))
            seen.update((i, j))
        assert len(pairs) == 6
        rounds.append(pairs)
    return rounds


def pick_weeks_2_and_3(rounds, repeat_set):
    """Choose which 2 of the 10 rounds minimize overlap with repeat_set.
    Returns (score, (i, j)) where score is the count of repeat pairs in
    those two rounds combined."""
    best = (float("inf"), None)
    for i in range(len(rounds)):
        for j in range(i + 1, len(rounds)):
            score = len((set(rounds[i]) | set(rounds[j])) & repeat_set)
            if score < best[0]:
                best = (score, (i, j))
                if score == 0:
                    return best
    return best


# --------------------------------------------------------------------------
# Search across many random round-robin structures for one with zero
# repeats in weeks 2-3
# --------------------------------------------------------------------------

repeat_set = set(repeats.keys())
best = (float("inf"), None, None)

for trial in range(2000):
    rounds = generate_non_rival_rounds(rival_pairs)
    score, choice = pick_weeks_2_and_3(rounds, repeat_set)
    if score < best[0]:
        best = (score, rounds, choice)
        if score == 0:
            break

best_score, rounds, (wk2_idx, wk3_idx) = best

if best_score == 0:
    print(f"✅ Found schedule with 0 repeat-pairs in weeks 2-3.")
else:
    print(f"⚠️  Best schedule has {best_score} repeat-pair(s) in weeks 2-3 "
          f"(could not fully avoid).")

# --------------------------------------------------------------------------
# Assemble the full 14-week schedule
# --------------------------------------------------------------------------

year = int(input("Enter the year being generated: "))

schedule = {}

# Weeks 1 and 14: rivalry weeks
rival_matchups = [tuple(sorted(p)) for p in rival_pairs]
schedule[1] = list(rival_matchups)
schedule[14] = list(rival_matchups)

# Weeks 2 and 3: best two non-rival rounds for avoiding repeats
schedule[2] = list(rounds[wk2_idx])
schedule[3] = list(rounds[wk3_idx])

# Weeks 4-11: the other 8 rounds in random order
other_rounds = [k for k in range(10) if k not in (wk2_idx, wk3_idx)]
random.shuffle(other_rounds)
for offset, idx in enumerate(other_rounds):
    schedule[4 + offset] = list(rounds[idx])

# Weeks 12 and 13: repeats of weeks 2 and 3
schedule[12] = list(schedule[2])
schedule[13] = list(schedule[3])

# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

print()
for wk in range(1, 15):
    label = ""
    if wk in (1, 14):
        label = "  (rivalry week)"
    elif wk == 12:
        label = "  (repeat of week 2)"
    elif wk == 13:
        label = "  (repeat of week 3)"
    print(f"Week {wk}:{label}")
    for m1, m2 in schedule[wk]:
        print(f"  {m1} vs {m2}")
    print()

# --------------------------------------------------------------------------
# Repeats dict snippet for next year
# --------------------------------------------------------------------------

print("📋 Add these to your repeats dictionary for next year's run:")
new_repeats = set(schedule[2]) | set(schedule[3])
for pair in sorted(new_repeats):
    print(f'    tuple(sorted(("{pair[0]}", "{pair[1]}"))): {year},')


# --------------------------------------------------------------------------
# Built-in sanity check — runs every time so you know it's correct
# --------------------------------------------------------------------------

def validate(schedule, members, rivals):
    errors = []

    non_rival = set()
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            a, b = members[i], members[j]
            if rivals[a] != b:
                non_rival.add(tuple(sorted((a, b))))

    # Each week: 6 matchups, all 12 teams, no duplicate
    for wk, ms in schedule.items():
        if len(ms) != 6:
            errors.append(f"Week {wk}: {len(ms)} matchups (need 6)")
        flat = [t for m in ms for t in m]
        if len(set(flat)) != 12:
            errors.append(f"Week {wk}: not all 12 teams appear exactly once")

    # Rivalry weeks only in 1 and 14
    for wk, ms in schedule.items():
        for a, b in ms:
            if rivals[a] == b and wk not in (1, 14):
                errors.append(f"Week {wk}: rival pair {a} vs {b} outside week 1/14")

    # Weeks 1 and 14 must be identical (as sets)
    if set(map(lambda m: tuple(sorted(m)), schedule[1])) != \
       set(map(lambda m: tuple(sorted(m)), schedule[14])):
        errors.append("Weeks 1 and 14 differ")

    # Weeks 12 and 13 must equal weeks 2 and 3
    if set(map(lambda m: tuple(sorted(m)), schedule[12])) != \
       set(map(lambda m: tuple(sorted(m)), schedule[2])):
        errors.append("Week 12 does not equal week 2")
    if set(map(lambda m: tuple(sorted(m)), schedule[13])) != \
       set(map(lambda m: tuple(sorted(m)), schedule[3])):
        errors.append("Week 13 does not equal week 3")

    # Weeks 2-11: every non-rival pair plays exactly once
    counts = defaultdict(int)
    for wk in range(2, 12):
        for a, b in schedule[wk]:
            counts[tuple(sorted((a, b)))] += 1
    for pair in non_rival:
        if counts[pair] != 1:
            errors.append(f"Pair {pair} plays {counts[pair]}x in weeks 2-11 "
                          "(should be exactly 1)")
    for pair, c in counts.items():
        if pair not in non_rival:
            errors.append(f"Rival pair {pair} appeared in weeks 2-11")

    return errors


errs = validate(schedule, members, rivals)
print()
if errs:
    print("❌ Validation errors:")
    for e in errs:
        print(f"   {e}")
else:
    print("✅ Schedule passes all validation checks.")