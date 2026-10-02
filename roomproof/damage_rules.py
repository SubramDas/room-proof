"""Versioned, evidence-gated recommendations for already identified damage.

This module does not detect damage. Callers must supply a source-linked region
on a known surface; no rule should be fired from an unclassified image edge.
"""

RULESET_VERSION = "0.1.0"
VISIBLE_CLASSES = (
    "discoloration_or_water_stain", "crack", "coating_failure",
    "surface_breakage", "floor_finish_damage",
)


def derive(damage_regions, surface_kinds, context=None):
    """Return schema-ready flags and scope for validated visible regions.

    context maps damage IDs to independently observed positional tags. Accepted
    tags are ceiling_junction, opening_edge, floor_edge, and corner. A caller
    must not manufacture those tags from the damage class alone.
    """
    context = context or {}
    flags, scope = [], []
    for damage in damage_regions:
        damage_id = damage["id"]
        cls = damage["class"]
        if cls not in VISIBLE_CLASSES:
            raise ValueError(f"unsupported damage class: {cls}")
        refs = damage["source_refs"]
        if not refs:
            raise ValueError(f"damage region {damage_id} requires source evidence")
        surface_id = damage["surface_id"]
        kind = surface_kinds[surface_id]
        tags = set(context.get(damage_id, ()))
        allowed = {"ceiling_junction", "opening_edge", "floor_edge", "corner"}
        if tags - allowed:
            raise ValueError(f"unsupported positional tag for {damage_id}")
        rule = None
        reason = None
        if cls in {"discoloration_or_water_stain", "coating_failure"}:
            if kind == "ceiling" or "ceiling_junction" in tags:
                rule, reason = "R-WATER-CEILING-01", "Possible moisture above or behind the finish; inspect the source."
            elif "opening_edge" in tags:
                rule, reason = "R-WATER-OPENING-02", "Possible moisture intrusion near the opening; inspect seal and substrate."
            elif "floor_edge" in tags:
                rule, reason = "R-WATER-FLOOR-03", "Possible moisture behind or below the finish; inspect before repair."
        elif cls == "crack" and tags & {"corner", "opening_edge", "ceiling_junction"}:
            rule, reason = "R-CRACK-REVIEW-01", "Possible joint failure or movement; obtain qualified inspection before cosmetic repair."
        if rule:
            flags.append({"id": f"flag-{damage_id}", "room_id": damage["room_id"],
                          "surface_id": surface_id, "rule_id": rule,
                          "reason": reason, "evidence_refs": refs, "status": "inferred"})
        work = "inspect" if cls in {"crack", "discoloration_or_water_stain"} else "prepare_surface"
        quantity = damage["length"] if cls == "crack" and "length" in damage else damage["area"]
        scope.append({"id": f"scope-{damage_id}", "room_id": damage["room_id"],
                      "surface_id": surface_id, "damage_region_id": damage_id,
                      "work_type": work,
                      "description": "Inspect visible damage and confirm cause before repair." if work == "inspect" else "Assess substrate and prepare affected finish; repair depends on inspection.",
                      "quantity": quantity, "source_refs": refs})
    return flags, scope
