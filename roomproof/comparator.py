"""Predeclared two-room consumer-app comparison; values are independent inputs."""

WALL_LIMIT_M = 0.05  # Project rule frozen before the owner benchmark baseline.
LIMITS = {"wall_length": WALL_LIMIT_M, "opening_width": 0.02, "ceiling_height": 0.015}


def compare(rows, selected_rooms):
    if len(selected_rooms) != 2 or len(set(selected_rooms)) != 2:
        raise ValueError("exactly two distinct preselected rooms are required")
    if not rows or any(row["room_id"] not in selected_rooms for row in rows):
        raise ValueError("rows must cover only selected rooms")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate dimension ID")
    details = []
    shared_wins = shared_count = expanded_wins = 0
    for row in rows:
        kind = row["kind"]
        if kind not in LIMITS:
            raise ValueError(f"unsupported comparison kind: {kind}")
        truth = row["truth_m"]
        ours, app = row.get("ours_m"), row.get("app_m")
        if truth <= 0 or any(value is not None and value <= 0 for value in (ours, app)):
            raise ValueError(f"nonpositive dimension: {row['id']}")
        ours_error = abs(ours-truth) if ours is not None else None
        app_error = abs(app-truth) if app is not None else None
        shared = ours is not None and app is not None
        if shared:
            shared_count += 1
            shared_win = ours_error <= app_error
            shared_wins += int(shared_win)
            expanded_win = shared_win
        elif ours is not None:
            shared_win = None
            expanded_win = ours_error <= LIMITS[kind]
        else:
            shared_win = None
            expanded_win = False
        expanded_wins += int(expanded_win)
        details.append({"id": row["id"], "room_id": row["room_id"], "kind": kind,
                        "truth_m": truth, "ours_m": ours, "app_m": app,
                        "ours_error_m": ours_error, "app_error_m": app_error,
                        "shared": shared, "shared_win_or_tie": shared_win,
                        "expanded_win_or_tie": expanded_win,
                        "omission": "both" if ours is None and app is None else "ours" if ours is None else "app" if app is None else None})
    return {"selected_rooms": selected_rooms, "wall_ours_only_limit_m": WALL_LIMIT_M,
            "rows": details,
            "shared": {"wins_or_ties": shared_wins, "denominator": shared_count,
                       "rate": shared_wins/shared_count if shared_count else None,
                       "pass_70pct": shared_wins/shared_count >= .70 if shared_count else None},
            "expanded": {"wins_or_ties": expanded_wins, "denominator": len(rows),
                         "rate": expanded_wins/len(rows), "pass_70pct": expanded_wins/len(rows) >= .70}}
