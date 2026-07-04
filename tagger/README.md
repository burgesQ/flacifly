# tagger

Task 2. Iterates downloaded FLAC files, identifies artist/track (heuristic + yt-dlp
embedded metadata), writes tags via `mutagen`, and queues low-confidence items in the
shared SQLite DB for interactive `--review`. CLI: `flacifly-tag`.
