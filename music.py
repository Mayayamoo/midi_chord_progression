import os
import music21
from datetime import datetime
import traceback 

#------------------------------------------------------------------------------
# Notes and Chords
#------------------------------------------------------------------------------

notes = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

# Maps between sharps and flats - useful for music21 which sometimes prefers one form
accidental_map = {
    "C#": "Db", "Db": "C#",
    "D#": "Eb", "Eb": "D#",
    "F#": "Gb", "Gb": "F#",
    "G#": "Ab", "Ab": "G#",
    "A#": "Bb", "Bb": "A#"
}

# Dictionary of common chords - each one is just the major triad for that root
chord = {
    "A": ["A", "C#", "E"],
    "A#": ["A#", "D", "F"], 
    "Bb": ["Bb", "D", "F"],
    "B": ["B", "D#", "F#"],
    "C": ["C", "E", "G"],
    "C#": ["C#", "F", "G#"],
    "Db": ["Db", "F", "Ab"],
    "D": ["D", "F#", "A"],
    "D#": ["D#", "G", "A#"],
    "Eb": ["Eb", "G", "Bb"],
    "E": ["E", "G#", "B"],
    "F": ["F", "A", "C"],
    "F#": ["F#", "A#", "C#"],
    "Gb": ["Gb", "Bb", "Db"],
    "G": ["G", "B", "D"],
    "G#": ["G#", "C", "D#"],
    "Ab": ["Ab", "C", "Eb"],
}

# Same notes with different names
enharmonic = {
    "Bb": "A#", "A#": "Bb",
    "Db": "C#", "C#": "Db",
    "Eb": "D#", "D#": "Eb",
    "E#": "F",  "F": "E#",
    "Gb": "F#", "F#": "Gb",
    "Ab": "G#", "G#": "Ab"
}

#------------------------------------------------------------------------------
# CHORD FUNCTIONS
#------------------------------------------------------------------------------
def get_note_index(note):
    """Find where a note sits in the chromatic scale"""
    for i, note_options in enumerate(notes):
        if note in note_options.split('/'):
            return i
    raise ValueError(f"Note {note} not found in notes list")

def lower_note_by_semitone(note):
    # Go down one semitone
    try:
        idx = get_note_index(note)
        new_idx = (idx - 1) % len(notes)
        return notes[new_idx].split('/')[0]
    except Exception as e:
        print(f"Error lowering note {note}: {e}")
        return note

def raise_note_by_semitone(note):
    # Go up one semitone
    try:
        idx = get_note_index(note)
        new_idx = (idx + 1) % len(notes)
        return notes[new_idx].split('/')[0]
    except Exception as e:
        print(f"Error raising note {note}: {e}")
        return note  

def make_minor_chord(chord_notes):
    # Lower the third to make a minor chord
    minor = chord_notes.copy()
    minor[1] = lower_note_by_semitone(minor[1])
    return minor

def make_diminished_chord(chord_notes):
    # Lower both third and fifth
    dim = chord_notes.copy()
    dim[1] = lower_note_by_semitone(dim[1]) 
    dim[2] = lower_note_by_semitone(dim[2])  
    return dim

def make_seventh_chord(chord_notes, chord_type):
    # Add a seventh note based on chord type
    try:
        result = chord_notes.copy()
        root = chord_notes[0]
        
        # Number of semitones from root for different seventh types
        seventh_intervals = {
            'maj7': 11,  # Major 7th (11 semitones)
            '7': 10,     # Dominant 7th (10 semitones)
            'm7': 10,    # Minor 7th (10 semitones)
            'dim7': 9,   # Diminished 7th (9 semitones)
            'aug7': 10,  # Augmented 7th
        }
        
        interval = seventh_intervals.get(chord_type)
        if not interval:
            print(f"Unknown seventh type: {chord_type}")
            return chord_notes
        
        # Walk up the scale to find the seventh note
        current_note = root
        for _ in range(interval):
            current_note = raise_note_by_semitone(current_note)
        
        # For diminished 7ths, we need flat notation (like Bb instead of A#)
        if chord_type == 'dim7' and 'b' not in current_note and '#' in current_note:
            current_note = accidental_map.get(current_note, current_note)
        
        result.append(current_note)
        return result
    except:
        # If something goes wrong, just return the original chord
        print(f"Problem creating seventh chord")
        traceback.print_exc()
        return chord_notes  

def inversion_by_bass_note(chord_notes, bass_note):
    """Rearrange a chord to put the bass note at the bottom"""
    # Nothing to do if no bass note given
    if not bass_note:
        return chord_notes.copy()
    
    # Check enharmonic equivalents (e.g., C# = Db)
    if bass_note in enharmonic and enharmonic[bass_note] in chord_notes:
        bass_note = enharmonic[bass_note]
    elif bass_note not in chord_notes:
        print(f"Warning: Bass note {bass_note} not found in chord {chord_notes}")
        return chord_notes.copy()
    
    # Rotate the chord until bass note is first
    result = chord_notes.copy()
    while result[0] != bass_note:
        result.append(result.pop(0))
    
    return result

#------------------------------------------------------------------------------
# CHORD STRING PARSING
#------------------------------------------------------------------------------

def parse_chord_string(chord_string):
    """Figure out what notes make up a chord from text like 'Dm7/F'"""
    # Default values
    is_minor = False
    is_dim = False
    seventh = None
    bass = None
    
    # Handle slash notation (inversions)
    if '/' in chord_string:
        chord_part, bass = chord_string.split('/')
        chord_string = chord_part.strip()
        bass = bass.strip()
    
    # Get the root note
    root = chord_string
    
    # Check for diminished chords first
    if 'dim7' in chord_string:
        root = chord_string.replace('dim7', '')
        seventh = 'dim7'
        is_dim = True
    elif 'dim' in chord_string:
        root = chord_string.replace('dim', '')
        is_dim = True
    # Check for minor chords
    elif 'm' in chord_string and not chord_string.endswith('maj7'):
        is_minor = True
        if chord_string.endswith('m7'):
            root = chord_string[:-2]
            seventh = 'm7'
        elif chord_string.endswith('m'):
            root = chord_string[:-1]
    # Handle seventh chords
    elif chord_string.endswith('maj7'):
        root = chord_string[:-4]
        seventh = 'maj7'
    elif chord_string.endswith('7'):
        root = chord_string[:-1]
        seventh = '7'
    
    # Clean up the root note
    root = root.strip()
    
    # Handle bass note enharmonics - prefer flats for readability
    if bass and bass in enharmonic and '#' in bass:
        if 'b' in enharmonic[bass]:
            bass = enharmonic[bass]
    
    print(f"Parsed '{chord_string}': root={root}, minor={is_minor}, dim={is_dim}, 7th={seventh}, bass={bass}")
    return root, is_minor, is_dim, seventh, bass

def get_chord_from_string(chord_string):
    """Convert a chord name to actual notes"""
    try:
        # Parse the chord string
        root, is_minor, is_dim, seventh, bass = parse_chord_string(chord_string)
        
        # Check for valid root
        if root not in chord:
            print(f"Root '{root}' not found in chord dictionary")
            # Try the enharmonic equivalent
            if root in enharmonic and enharmonic[root] in chord:
                root = enharmonic[root]
                print(f"Using {root} instead")
            else:
                print(f"Can't find chord {chord_string}")
                return None
        
        # Get the basic triad
        notes = chord[root].copy()
        print(f"Base chord for {chord_string}: {notes}")
        
        # Apply modifications in order
        if is_dim:
            notes = make_diminished_chord(notes)
            print(f"After making diminished: {notes}")
        elif is_minor:
            notes = make_minor_chord(notes)
            print(f"After making minor: {notes}")
        
        # Add seventh if needed
        if seventh:
            notes = make_seventh_chord(notes, seventh)
            print(f"After adding {seventh}: {notes}")
        
        # Handle inversion if needed
        if bass:
            notes = inversion_by_bass_note(notes, bass)
            print(f"After inversion with {bass}: {notes}")
        
        print(f"Final chord: {notes}")
        return notes
    except Exception as e:
        print(f"Problem with chord '{chord_string}': {e}")
        traceback.print_exc()
        return None

#------------------------------------------------------------------------------
# MIDI creation
#------------------------------------------------------------------------------
def create_music21_chord(chord_notes, octave=4, duration=1.0):
    """Turn chord notes into a music21 chord object"""
    if not chord_notes:
        return None
    
    m21_notes = []
    for note in chord_notes:
        # Music21 prefers flats in some cases
        if note in accidental_map and 'b' in accidental_map[note]:
            note = accidental_map[note]
            
        m21_note = music21.note.Note(f"{note}{octave}")
        m21_note.quarterLength = duration
        m21_notes.append(m21_note)
    
    return music21.chord.Chord(m21_notes)

def create_music21_note(note_name, octave=2, duration=1.0):
    """Turn a single note into a music21 note object"""
    # Use flat notation for sharps in bass
    if '#' in note_name and note_name in accidental_map:
        note_name = accidental_map[note_name]
    
    note = music21.note.Note(f"{note_name}{octave}")
    note.quarterLength = duration
    return note

def create_chord_progression(progression, octave=4, duration=1.0):
    """Create a music21 stream from a chord progression"""
    if isinstance(progression, str):
        progression = [c.strip() for c in progression.split(',')]
    
    stream = music21.stream.Stream()
    
    for chord_name in progression:
        chord_notes = get_chord_from_string(chord_name)
        if chord_notes:
            chord_obj = create_music21_chord(chord_notes, octave, duration)
            if chord_obj:
                stream.append(chord_obj)
    
    return stream

def create_bass_line(bass_progression, octave=2, duration=1.0):
    """Create a music21 stream from a bass progression"""
    if isinstance(bass_progression, str):
        bass_notes = [n.strip() for n in bass_progression.split(',')]
    else:
        bass_notes = bass_progression
    
    stream = music21.stream.Stream()
    
    for note_name in bass_notes:
        note = create_music21_note(note_name, octave, duration)
        stream.append(note)
    
    return stream
#------------------------------------------------------------------------------
# EXPORT FUNCTIONS
#------------------------------------------------------------------------------
def get_output_path(filename):
    """Make sure we have a proper output path"""
    # Go up one directory level to get to main Music folder
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(parent_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    if os.path.sep not in filename:
        return os.path.join(output_dir, filename)
    return filename

def get_unique_filename(filename):
    """Create a unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(os.path.basename(filename))
    return f"{base}_{timestamp}{ext}"

def export_to_midi(chord_progression, filename, bass_progression=None, 
                   chord_octave=4, bass_octave=2, duration=1.0):
    """
    Export a chord progression (with optional bass) to a MIDI file
    
    Args:
        chord_progression: String like "C, F, G7" or a list of chord names
        filename: Where to save the MIDI file
        bass_progression: Optional bass notes like "C, F, G"
        chord_octave: Which octave for the chords (default=4)
        bass_octave: Which octave for the bass (default=2)
        duration: How many beats per chord (default=1.0)
    """
    filepath = get_output_path(filename)
    
    # If there's no bass line, just export the chords
    if not bass_progression:
        stream = create_chord_progression(chord_progression, chord_octave, duration)
        try:
            stream.write('midi', fp=filepath)
            return f"Saved chord progression to {filepath}"
        except PermissionError:
            # If the file is locked, use a different name
            new_path = os.path.join(os.path.dirname(filepath), get_unique_filename(filepath))
            stream.write('midi', fp=new_path)
            return f"File was in use. Saved to {new_path} instead."
    
    # Create the chord and bass streams
    chord_stream = create_chord_progression(chord_progression, chord_octave, duration)
    bass_stream = create_bass_line(bass_progression, bass_octave, duration)
    
    # Check if they match in length
    if len(chord_stream) != len(bass_stream):
        return f"Warning: Chord progression ({len(chord_stream)} chords) and bass line ({len(bass_stream)} notes) don't match"
    
    # Make a score with two parts
    score = music21.stream.Score()
    
    # Add chords as piano
    chord_part = music21.stream.Part()
    chord_part.insert(0, music21.instrument.Piano())
    for chord in chord_stream:
        chord_part.append(chord)
    
    # Add bass notes
    bass_part = music21.stream.Part()
    bass_part.insert(0, music21.instrument.AcousticBass())
    for note in bass_stream:
        bass_part.append(note)
    
    # Put it all together
    score.append(chord_part)
    score.append(bass_part)
    
    # Save the file
    try:
        score.write('midi', fp=filepath)
        return f"Saved chord progression with bass to {filepath}"
    except PermissionError:
        # Try again with a unique name
        new_path = os.path.join(os.path.dirname(filepath), get_unique_filename(filepath))
        score.write('midi', fp=new_path)
        return f"File was in use. Saved to {new_path} instead."




