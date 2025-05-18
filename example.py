import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import processing.music as music

progression = "F#m/C#, C#m, D, Fdim7/D, A/C#, Bbdim7"
bass2 = "C#, C#, D, D, C#, Bb"


result = music.export_to_midi(progression, "meteor.mid", bass2, 4, 2, 2) 
print(result)
