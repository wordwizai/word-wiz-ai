// Hand-drawn strokes for the teacher's-pen marks (see TeacherPen.tsx).

/** Hand-drawn paths, each in the viewBox noted beside it. */
export const PEN_PATHS = {
  // 160 x 140: a loop that overshoots where it started
  loop: "M 94 9 C 50 3, 12 26, 10 68 C 8 110, 52 134, 92 131 C 136 127, 155 97, 151 62 C 147 27, 117 6, 76 11 C 62 13, 50 19, 41 27",
  // 108 x 64: the same loop, flatter, for a word chip
  loopFlat:
    "M 62 4 C 30 2, 6 14, 5 33 C 4 52, 32 61, 58 60 C 86 59, 104 48, 103 30 C 102 13, 82 4, 52 6 C 42 7, 34 10, 28 14",
  // 200 x 56: a long loop around a short phrase
  loopWide:
    "M 116 5 C 62 2, 8 12, 6 29 C 4 46, 60 54, 104 53 C 150 52, 196 44, 195 27 C 194 11, 150 4, 96 6 C 80 7, 64 9, 52 12",
  // 100 x 12
  underline: "M2 7 C 18 3, 34 10, 50 6 S 82 3, 98 7",
  underlineAlt: "M2 6 C 20 9, 36 3, 54 6 S 84 9, 98 5",
  // 100 x 14, a bolder underline for a headline word
  underlineBold: "M3 9 C 22 4, 46 12, 66 7 S 90 5, 97 9",
  // 30 x 24, three slightly different ticks so a list doesn't look stamped
  ticks: [
    "M3 13 C 6 15, 8 18, 10 21 C 14 12, 20 6, 27 2",
    "M3 12 C 6 15, 9 18, 11 21 C 15 11, 21 6, 28 3",
    "M2 14 C 5 16, 8 18, 10 21 C 13 13, 19 6, 27 2",
  ],
} as const;
