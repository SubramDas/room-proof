# Flat-805 benchmark handoff

Your current `Flat-805/` folder already has the original photo and video
captures. Keep those files unchanged. The following evidence is still needed
for the full benchmark; these are not inference inputs.

1. **LiDAR:** Make one Stray Scanner scan of the same flat, walking through all
   four spaces and revisiting a starting area. Export and transfer the complete
   original ZIP or export folder. Record phone model, iOS version, Stray version,
   scan date, and whether any room was inaccessible.
2. **Repeatability:** Independently scan one of the same rooms a second time at
   the same tier. Start a new session and keep both exports. Do not choose only
   the better recording.
3. **Room map:** Draw a rough list of rooms and which door connects each pair.
   Confirm whether `room-hall` is a connector. Record any stairs or other
   floors. This map is benchmark reference material and must stay outside the
   capture input folder.
4. **Reference measurements:** With tape or laser, record every wall length,
   each door/window width and its distance from a named wall corner, ceiling
   height in each room, and overall footprint dimensions. Record metres to at
   least centimetre precision, the instrument, how endpoints were chosen, and
   repeated readings where practical. Use stable IDs such as
   `surf-bed-wall-1` and `ref-bed-wall-1`; the exact wall numbering can be
   agreed from the room map before scoring. Do not place this sheet under
   `Flat-805/`.
5. **Damage:** Select two distinct visible classes from
   [damage_vocabulary.md](damage_vocabulary.md). Capture each in all three
   tiers, mark which room and wall/floor/ceiling it belongs to, and measure its
   visible extent. Record whether it was existing or safely staged. Do not
   damage the property just to create a sample.
6. **Comparator:** Check whether a free magicplan account exports dimensions.
   If it does, record app version and scan two distinct rooms during the same
   visit with no tape-based correction. Keep both original exports.

The first follow-up after LiDAR arrives is an input-format and alignment audit.
The benchmark cannot be called complete until the independent measurements,
repeat capture, damage labels, and comparator evidence arrive. The model pilot
also requires explicit approval for a specific private photo to be sent to
Google; it is separate from this local capture handoff.
