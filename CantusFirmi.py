from music21 import *
import random

us = environment.UserSettings()
us['musicxmlPath'] = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'

def next_natural(note_str: str) -> str:
    letter = note_str[0].upper()
    octave = int(note_str[1:])
    naturals = ["A", "B", "C", "D", "E", "F", "G"]
    idx = naturals.index(letter)
    next_idx = (idx + 1) % len(naturals)
    next_letter = naturals[next_idx]
    if letter == "B":
        octave += 1
    return f"{next_letter}{octave}"

def duplicate_note(n: note.Note) -> note.Note:
    return note.Note(n.nameWithOctave, quarterLength=n.quarterLength)

def get_extrema(midis):
    local_max = []
    local_min = []
    for i in range(1, len(midis) - 1):
        if midis[i] > midis[i - 1] and midis[i] > midis[i + 1]:
            local_max.append((i, midis[i]))
        if midis[i] < midis[i - 1] and midis[i] < midis[i + 1]:
            local_min.append((i, midis[i]))
    return local_max, local_min

def has_repeated_pattern(lst, min_len=3):
    n = len(lst)
    for l in range(min_len, n // 2 + 1):
        for start in range(n - 2 * l + 1):
            if lst[start:start + l] == lst[start + l:start + 2 * l]:
                return True
    return False

def has_repeated_three_note_sequence(notes, to_add):
    if len(notes) < 2:
        return False
    midis = [n.pitch.midi for n in notes] + [to_add.pitch.midi]
    n = len(midis)
    if n < 3:
        return False
    current_three = midis[-3:]
    for i in range(n - 3):
        if midis[i:i+3] == current_three:
            return True
    return False

def can_add_note(notes, to_add, current_min, current_max, is_antepenultimate=False, penultimate_midi=None):
    last = notes[-1]
    m = to_add.pitch.midi
    new_min = min(current_min, m)
    new_max = max(current_max, m)
    if new_max - new_min > 12 or new_max - new_min in [6, 10, 11]:
        return False
    semi = abs(m - last.pitch.midi)
    if semi in [0, 6, 10, 11] or semi > 9:
        return False
    direction = 1 if m > last.pitch.midi else -1 if m < last.pitch.midi else 0
    is_skip = semi in [3, 4]
    is_jump = semi > 4
    prev_is_jump = False
    prev_direction = 0
    if len(notes) > 1:
        prev_semi = abs(notes[-1].pitch.midi - notes[-2].pitch.midi)
        prev_is_jump = prev_semi > 4
        prev_direction = 1 if notes[-1].pitch.midi > notes[-2].pitch.midi else -1
        if is_jump and prev_is_jump:
            return False
    if prev_is_jump and direction != -prev_direction:
        return False
    if len(notes) > 1:
        if len(notes) > 2:
            prev_prev_semi = abs(notes[-2].pitch.midi - notes[-3].pitch.midi)
            if is_skip and (prev_semi in [3, 4]) and (prev_prev_semi in [3, 4]):
                return False
    new_delta = m - last.pitch.midi
    if len(notes) >= 2:
        prev_delta = notes[-1].pitch.midi - notes[-2].pitch.midi
        if len(notes) >= 3:
            prev_prev_delta = notes[-2].pitch.midi - notes[-3].pitch.midi
            if new_delta == prev_delta == prev_prev_delta:
                return False
            if new_delta == prev_prev_delta and prev_delta == -new_delta:
                return False
    note_count = sum(1 for n in notes if n.nameWithOctave == to_add.nameWithOctave)
    if note_count >= 3:
        return False
    if has_repeated_three_note_sequence(notes, to_add):
        return False
    if is_antepenultimate and penultimate_midi is not None:
        if abs(m - penultimate_midi) not in [1, 2]:
            return False
    return True

def generate_cantus_firmus(tonic_str, max_attempts=10000):
    tonic_note = note.Note(tonic_str, quarterLength=4)
    penultimate_str = next_natural(tonic_str)
    pen_note = note.Note(penultimate_str, quarterLength=4)
    final_note = duplicate_note(tonic_note)
    possible_pitches = [note.Note(l + str(o), quarterLength=4) for o in range(2, 6) for l in 'ABCDEFG']
    for attempt in range(max_attempts):
        length = random.randint(9, 12)
        notes = [duplicate_note(tonic_note)]
        current_min = tonic_note.pitch.midi
        current_max = current_min
        while len(notes) < length - 3:
            possible = []
            weights = []
            last = notes[-1]
            prev_is_jump = False
            prev_direction = 0
            prev_semi = 0
            if len(notes) > 1:
                prev_semi = abs(notes[-1].pitch.midi - notes[-2].pitch.midi)
                prev_is_jump = prev_semi > 4
                prev_direction = 1 if notes[-1].pitch.midi > notes[-2].pitch.midi else -1
            for cand_note in possible_pitches:
                m = cand_note.pitch.midi
                new_min = min(current_min, m)
                new_max = max(current_max, m)
                if new_max - new_min > 12 or new_max - new_min in [6, 10, 11]:
                    continue
                semi = abs(m - last.pitch.midi)
                if semi in [0, 6, 10, 11] or semi > 9:
                    continue
                direction = 1 if m > last.pitch.midi else -1 if m < last.pitch.midi else 0
                is_skip = semi in [3, 4]
                is_jump = semi > 4
                if prev_is_jump and direction != -prev_direction:
                    continue
                if is_jump and prev_is_jump:
                    continue
                if len(notes) > 2:
                    prev_prev_semi = abs(notes[-2].pitch.midi - notes[-3].pitch.midi)
                    if is_skip and (prev_semi in [3, 4]) and (prev_prev_semi in [3, 4]):
                        continue
                new_delta = m - last.pitch.midi
                skip = False
                if len(notes) >= 2:
                    prev_delta = notes[-1].pitch.midi - notes[-2].pitch.midi
                    if len(notes) >= 3:
                        prev_prev_delta = notes[-2].pitch.midi - notes[-3].pitch.midi
                        if new_delta == prev_delta == prev_prev_delta:
                            skip = True
                        if new_delta == prev_prev_delta and prev_delta == -new_delta:
                            skip = True
                if skip:
                    continue
                note_count = sum(1 for n in notes if n.nameWithOctave == cand_note.nameWithOctave)
                if note_count >= 3:
                    continue
                if has_repeated_three_note_sequence(notes, cand_note):
                    continue
                possible.append(cand_note)
                weight = 10 if semi <= 2 else 3 if is_skip else 1
                if prev_is_jump and semi <= 2:
                    weight *= 2
                weights.append(weight)
            if not possible:
                break
            next_note = duplicate_note(random.choices(possible, weights=weights)[0])
            notes.append(next_note)
            current_min = min(current_min, next_note.pitch.midi)
            current_max = max(current_max, next_note.pitch.midi)
        if len(notes) < length - 3:
            continue
        possible = []
        weights = []
        for cand_note in possible_pitches:
            m = cand_note.pitch.midi
            if not can_add_note(notes, cand_note, current_min, current_max, is_antepenultimate=True, penultimate_midi=pen_note.pitch.midi):
                continue
            semi = abs(m - notes[-1].pitch.midi)
            possible.append(cand_note)
            is_skip = semi in [3, 4]
            is_jump = semi > 4
            weight = 10 if semi <= 2 else 3 if is_skip else 1
            prev_semi = abs(notes[-1].pitch.midi - notes[-2].pitch.midi) if len(notes) > 1 else 0
            prev_is_jump = prev_semi > 4
            if prev_is_jump and semi <= 2:
                weight *= 2
            weights.append(weight)
        if not possible:
            continue
        antepen_note = duplicate_note(random.choices(possible, weights=weights)[0])
        notes.append(antepen_note)
        current_min = min(current_min, antepen_note.pitch.midi)
        current_max = max(current_max, antepen_note.pitch.midi)
        # Add penultimate note
        pen_copy = duplicate_note(pen_note)
        if can_add_note(notes, pen_copy, current_min, current_max):
            notes.append(pen_copy)
            current_min = min(current_min, pen_note.pitch.midi)
            current_max = max(current_max, pen_note.pitch.midi)
        else:
            continue
        # Add final note
        final_copy = duplicate_note(final_note)
        if can_add_note(notes, final_copy, current_min, current_max):
            notes.append(final_copy)
            current_min = min(current_min, final_note.pitch.midi)
            current_max = max(current_max, final_note.pitch.midi)
        else:
            continue
        midis = [n.pitch.midi for n in notes]
        intervals_semi = [abs(midis[i + 1] - midis[i]) for i in range(length - 1)]
        num_jumps = sum(1 for s in intervals_semi if s > 4)
        if num_jumps < 1:
            continue
        max_midi = max(midis)
        if midis.count(max_midi) != 1:
            continue
        pos = midis.index(max_midi)
        if pos < length // 2:
            continue
        local_max, local_min = get_extrema(midis)
        extrema = sorted(local_max + local_min, key=lambda x: x[0])
        bad_outline = False
        for j in range(len(extrema) - 1):
            if abs(extrema[j][1] - extrema[j + 1][1]) in [6, 10, 11]:
                bad_outline = True
                break
        if bad_outline:
            continue
        deltas = [midis[i + 1] - midis[i] for i in range(length - 1)]
        if has_repeated_pattern(deltas):
            continue
        if has_repeated_pattern(midis, min_len=3):
            continue
        return notes
    return None

tonic = input("Enter a letter between A-G, which will be the starting and ending note: ")
if tonic in ["C", "D", "E", "F"]:
    tonic += "4"
else:
    tonic += "3"

notes = generate_cantus_firmus(tonic)
if notes:
    s = stream.Stream()
    s.insert(0, clef.AltoClef())
    s.metadata = metadata.Metadata()
    s.metadata.title = "Cantus Firmus"
    s.metadata.composer = "Bot"
    for n in notes:
        s.append(n)
    s.show()
else:
    print("Failed to generate a valid Cantus Firmus after maximum attempts.")