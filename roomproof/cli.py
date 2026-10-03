"""Content-addressed capture import and audited command execution."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid

from . import __version__


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    temporary.replace(path)


def git_revision():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def git_dirty():
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        check=False,
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def new_run(command, args):
    run_id = "run-" + uuid.uuid4().hex
    run_dir = Path(args.runs_dir).resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir, {
        "manifest_version": "0.1.0",
        "run_id": run_id,
        "command": command,
        "config": {key: str(value) for key, value in vars(args).items() if key != "func"},
        "argv": sys.argv[1:],
        "started_at_utc": utc_now(),
        "code_revision": git_revision(),
        "code_dirty": git_dirty(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "data_revision": None,
        "model_or_api": None,
        "seed": None,
        "stage_seconds": {},
        "status": "running",
        "warnings": [],
        "metrics": {},
        "artifacts": [],
    }


def execute(command, args, action):
    run_dir, run = new_run(command, args)
    started = time.monotonic()
    try:
        action(args, run_dir, run)
        run["status"] = "complete"
        code = 0
    except Exception as error:
        run["status"] = "failed"
        run["error"] = {"type": type(error).__name__, "message": str(error)}
        print(f"{command} failed: {error}", file=sys.stderr)
        code = 1
    finally:
        run["stage_seconds"][command] = round(time.monotonic() - started, 6)
        run["finished_at_utc"] = utc_now()
        write_json(run_dir / "run.json", run)
        print(f"run manifest: {run_dir / 'run.json'}")
    return code


def valid_id(value, prefix):
    if not value.startswith(prefix + "-") or len(value) <= len(prefix) + 1:
        raise ValueError(f"{prefix} ID must start with '{prefix}-'")
    if not all(character.isascii() and (character.islower() or character.isdigit() or character == "-") for character in value):
        raise ValueError(f"{prefix} ID must use lowercase ASCII letters, digits, or hyphens")
    return value


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def score_benchmark(args, run_dir, run):
    from .benchmark import evaluate, SCORER_VERSION
    report = evaluate(args.manifest)
    output = run_dir / "benchmark.json"
    write_json(output, report)
    run["data_revision"] = sha256(Path(args.manifest).resolve(strict=True))
    run["metrics"] = {"capture_count": len(report["captures"]), "scorer_version": SCORER_VERSION}
    run["artifacts"] = [{"path": str(output), "sha256": sha256(output)}]
    print(f"benchmark report: {output}")


def probe_vision(args, run_dir, run):
    from .cloud_vision import probe
    result = probe(args.image)
    output = run_dir / "vision_probe.json"
    write_json(output, result)
    run["model_or_api"] = result["model"]
    run["data_revision"] = sha256(Path(args.image).resolve(strict=True))
    run["metrics"] = {"latency_seconds": result["latency_seconds"], "image_bytes": result["image_bytes"]}
    run["artifacts"] = [{"path": str(output), "sha256": sha256(output)}]
    print(f"vision probe: {output}")


def link_capture_runs(args, run_dir, run):
    from .cross_capture import link_captures
    report, artifacts = link_captures(
        args.photo_run, args.video_run, args.lidar_run,
        args.photo_source, args.lidar_source, run_dir,
        max_views=args.max_views, lidar_rgb_rotation=args.lidar_rgb_rotation,
        match_backend=args.match_backend, model_root=args.model_root,
        calibration_path=args.calibration)
    source_revisions = []
    for path in (args.photo_run, args.video_run, args.lidar_run):
        source_run = json.loads((Path(path).resolve(strict=True)/'run.json').read_text())
        source_revisions.append(source_run['data_revision'])
    if args.calibration:
        source_revisions.append(sha256(Path(args.calibration).resolve(strict=True)))
    run['data_revision'] = hashlib.sha256(
        json.dumps(source_revisions, separators=(',', ':')).encode()).hexdigest()
    run['artifacts'] = artifacts
    registration = json.loads((run_dir/'cross_capture_registration.json').read_text())
    opening_links = json.loads((run_dir/'opening_correspondences.json').read_text())
    plan = json.loads((run_dir/'property_plan.json').read_text())
    run['metrics'] = {'pair_count': report['pair_count'],
                      'supported_2d_overlap_count': report['supported_2d_overlap_count'],
                      'plausible_assumed_pose_count': registration.get('plausible_assumed_pose_count', 0),
                      'cross_view_consistent_pose_count': len(registration.get('cross_view_consistent_hypotheses', [])),
                      'opening_region_link_count': opening_links['link_count'],
                      'fused_plan_status': plan['plan']['status'],
                      'status': report['status'], 'fused_plan_path': 'property_plan.json'}
    run['warnings'].extend(report['warnings'])
    print(f"cross-capture links: {run_dir/'cross_capture_links.json'}")


def summarize_dimensions_run(args, run_dir, run):
    from .dimension_summary import generate_dimension_summary
    source = Path(args.source_run).resolve(strict=True)
    report, artifact = generate_dimension_summary(source, run_dir)
    run['data_revision'] = sha256(source / 'property_plan.json')
    run['artifacts'] = [artifact]
    run['metrics'] = {'source_run_id': report['source_run_id'],
                      'room_count': len(report['rooms']),
                      'plan_opening_count': len(report['openings']),
                      'provisional_opening_hypothesis_count': len(report['opening_hypotheses'])}
    print(f"dimension summary: {artifact['path']}")


def assemble_property_runs(args, run_dir, run):
    from .property_assembly import assemble_property
    report, artifacts = assemble_property(args.linked_runs, run_dir)
    revisions = [json.loads((Path(path).resolve(strict=True)/'run.json').read_text())['data_revision']
                 for path in args.linked_runs]
    run['data_revision'] = hashlib.sha256(
        json.dumps(revisions, separators=(',', ':')).encode()).hexdigest()
    run['artifacts'] = artifacts
    run['metrics'] = {'linked_room_runs': len(args.linked_runs),
                      'verified_connections': len(report['verified_connections']),
                      'unplaced_rooms': len(report['placement']['unplaced_room_ids']),
                      'status': report['status']}
    print(f"property assembly: {run_dir/'property_assembly.json'}")


def object_path(bundle, digest):
    return bundle / "objects" / "sha256" / digest[:2] / digest


def import_capture(args, run_dir, run):
    source = Path(args.source).resolve(strict=True)
    bundle = Path(args.bundle).resolve()
    if not source.is_dir() and not source.is_file():
        raise ValueError("capture source must be a file or directory")
    if bundle == source or source in bundle.parents or bundle in source.parents:
        raise ValueError("source and bundle must be separate directory trees")
    property_id = valid_id(args.property_id, "prop")
    capture_id = valid_id(args.capture_id or "cap-" + uuid.uuid4().hex, "cap")
    manifest_path = bundle / "captures" / (capture_id + ".json")
    if manifest_path.exists():
        raise FileExistsError(f"capture ID already imported: {capture_id}")
    files = []
    paths = sorted(source.rglob("*")) if source.is_dir() else [source]
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"symlink in raw capture: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix() if source.is_dir() else path.name
        digest = sha256(path)
        size = path.stat().st_size
        object_file = object_path(bundle, digest)
        if not object_file.exists():
            object_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = object_file.with_name(object_file.name + ".tmp-" + uuid.uuid4().hex)
            shutil.copyfile(path, temporary)
            if sha256(temporary) != digest:
                temporary.unlink(missing_ok=True)
                raise OSError(f"copy changed while importing: {path}")
            temporary.chmod(0o444)
            temporary.replace(object_file)
        elif object_file.stat().st_size != size or sha256(object_file) != digest:
            raise OSError(f"stored object differs from expected content: {object_file}")
        files.append({"path": relative, "size_bytes": size, "sha256": digest})
    if not files:
        raise ValueError("capture source contains no files")
    manifest = {
        "manifest_version": "0.1.0",
        "property_id": property_id,
        "capture_id": capture_id,
        "tier": args.tier,
        "source_label": args.source_label,
        "source_path_at_import": str(source),
        "imported_at_utc": utc_now(),
        "device_model": args.device_model,
        "ios_version": args.ios_version,
        "capture_app": args.capture_app,
        "capture_app_version": args.capture_app_version,
        "capture_notes": args.notes,
        "files": files,
    }
    write_json(manifest_path, manifest)
    manifest_digest = sha256(manifest_path)
    run["data_revision"] = manifest_digest
    run["metrics"] = {"file_count": len(files), "total_bytes": sum(item["size_bytes"] for item in files)}
    run["artifacts"] = [{"path": str(manifest_path), "sha256": manifest_digest}]
    print(f"capture manifest: {manifest_path}")


def verify_capture(args, run_dir, run):
    bundle = Path(args.bundle).resolve(strict=True)
    manifest_path = Path(args.manifest).resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = []
    for item in manifest["files"]:
        path = object_path(bundle, item["sha256"])
        if not path.is_file() or path.stat().st_size != item["size_bytes"] or sha256(path) != item["sha256"]:
            failures.append(item["path"])
    digest = sha256(manifest_path)
    run["data_revision"] = digest
    run["metrics"] = {"file_count": len(manifest["files"]), "invalid_files": len(failures)}
    run["artifacts"] = [{"path": str(manifest_path), "sha256": digest}]
    if failures:
        raise ValueError(f"{len(failures)} raw objects missing or corrupt; first: {failures[0]}")
    print(f"verified {len(manifest['files'])} files for {manifest['capture_id']}")


def verify_bundle(args, run_dir, run):
    bundle = Path(args.bundle).resolve(strict=True)
    index_path = Path(args.index).resolve(strict=True)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    failures = []
    checked_files = 0
    seen_captures = set()
    for entry in index["capture_manifests"]:
        capture_id = valid_id(entry["capture_id"], "cap")
        if capture_id in seen_captures:
            failures.append(f"duplicate capture ID {capture_id}")
            continue
        seen_captures.add(capture_id)
        expected_path = f"captures/{capture_id}.json"
        if entry["path"] != expected_path:
            failures.append(f"invalid manifest path for {capture_id}")
            continue
        manifest_path = bundle / expected_path
        if not manifest_path.is_file() or sha256(manifest_path) != entry["sha256"]:
            failures.append(f"manifest missing or changed: {expected_path}")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["capture_id"] != capture_id or len(manifest["files"]) != entry["file_count"]:
            failures.append(f"manifest ID or file count differs: {capture_id}")
            continue
        for item in manifest["files"]:
            object_file = object_path(bundle, item["sha256"])
            if not object_file.is_file() or object_file.stat().st_size != item["size_bytes"] or sha256(object_file) != item["sha256"]:
                failures.append(f"object missing or corrupt: {capture_id}/{item['path']}")
            checked_files += 1
    run["data_revision"] = sha256(index_path)
    run["metrics"] = {"capture_count": len(seen_captures), "file_count": checked_files, "invalid_items": len(failures)}
    run["artifacts"] = [{"path": str(index_path), "sha256": run["data_revision"]}]
    if failures:
        raise ValueError(f"{len(failures)} bundle issues; first: {failures[0]}")
    print(f"verified {len(seen_captures)} captures and {checked_files} files")


def index_bundle(args, run_dir, run):
    bundle = Path(args.bundle).resolve(strict=True)
    index_path = Path(args.index).resolve()
    entries = []
    for manifest_path in sorted((bundle / "captures").glob("*.json")):
        capture_id = valid_id(manifest_path.stem, "cap")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["capture_id"] != capture_id:
            raise ValueError(f"capture ID differs from filename: {manifest_path}")
        entries.append({
            "capture_id": capture_id,
            "path": f"captures/{manifest_path.name}",
            "sha256": sha256(manifest_path),
            "file_count": len(manifest["files"]),
        })
    if not entries:
        raise ValueError("bundle has no capture manifests")
    write_json(index_path, {
        "manifest_version": "0.1.0",
        "bundle_kind": "content-addressed-local",
        "capture_manifests": entries,
    })
    run["data_revision"] = sha256(index_path)
    run["metrics"] = {"capture_count": len(entries)}
    run["artifacts"] = [{"path": str(index_path), "sha256": run["data_revision"]}]
    print(f"bundle index: {index_path}")


def main():
    parser = argparse.ArgumentParser(prog="roomproof", description="RoomProof reproducibility foundation")
    parser.add_argument("--version", action="version", version=f"RoomProof {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)
    importer = subcommands.add_parser("import-capture", help="copy a raw file or folder into a content-addressed bundle")
    importer.add_argument("source")
    importer.add_argument("--bundle", required=True)
    importer.add_argument("--property-id", required=True)
    importer.add_argument("--capture-id")
    importer.add_argument("--tier", choices=("photo", "video", "lidar"), required=True)
    importer.add_argument("--source-label", required=True)
    importer.add_argument("--device-model")
    importer.add_argument("--ios-version")
    importer.add_argument("--capture-app")
    importer.add_argument("--capture-app-version")
    importer.add_argument("--notes")
    importer.add_argument("--runs-dir", default="runs")
    importer.set_defaults(func=import_capture)
    verifier = subcommands.add_parser("verify-capture", help="verify all files named by a capture manifest")
    verifier.add_argument("--bundle", required=True)
    verifier.add_argument("--manifest", required=True)
    verifier.add_argument("--runs-dir", default="runs")
    verifier.set_defaults(func=verify_capture)
    bundle_verifier = subcommands.add_parser("verify-bundle", help="verify capture manifests and all raw objects against a tracked index")
    bundle_verifier.add_argument("--bundle", required=True)
    bundle_verifier.add_argument("--index", default="repro/manifest.json")
    bundle_verifier.add_argument("--runs-dir", default="runs")
    bundle_verifier.set_defaults(func=verify_bundle)
    indexer = subcommands.add_parser("index-bundle", help="write a versioned index of all capture manifests")
    indexer.add_argument("--bundle", required=True)
    indexer.add_argument("--index", default="repro/manifest.json")
    indexer.add_argument("--runs-dir", default="runs")
    indexer.set_defaults(func=index_bundle)
    auditor = subcommands.add_parser("audit-stray", help="inspect a Stray Scanner export and write a format report")
    auditor.add_argument("scan")
    auditor.add_argument("--report", required=True)
    auditor.add_argument("--capture-manifest")
    auditor.add_argument("--archive")
    auditor.add_argument("--device-model")
    auditor.add_argument("--ios-version")
    auditor.add_argument("--app-version")
    auditor.add_argument("--runs-dir", default="runs")
    from .stray_audit import audit_stray
    auditor.set_defaults(func=audit_stray)
    processor = subcommands.add_parser("process-capture", help="validate a capture, index photo/video frames, and create a run report")
    processor.add_argument("capture", help="photo room folders, one video file or property folder with one top-level video, or extracted Stray Scanner folder")
    processor.add_argument("--tier", choices=("photo", "video", "lidar"), required=True)
    processor.add_argument("--property-id", required=True)
    processor.add_argument("--capture-id", required=True)
    processor.add_argument("--room-id", help="optional known room label for a single-room video or LiDAR capture")
    processor.add_argument("--room-kind", choices=("room", "connector", "stairs", "other"), default="room")
    processor.add_argument("--device-model")
    processor.add_argument("--ios-version")
    processor.add_argument("--capture-app")
    processor.add_argument("--capture-app-version")
    processor.add_argument("--device-has-lidar", choices=("true", "false", "unknown"), default="unknown")
    processor.add_argument("--max-video-frames", type=positive_int, default=24, help="maximum evenly spaced frames to decode for an ordinary video")
    processor.add_argument("--max-lidar-frames", type=positive_int, default=32, help="maximum evenly spaced depth frames for diagnostic geometry")
    processor.add_argument("--lidar-drift", choices=("on", "off"), default="on", help="apply only geometrically verified LiDAR revisit correction")
    processor.add_argument("--visual-model", choices=("on", "off"), default="off", help="run the local experimental semantic candidate stage")
    processor.add_argument("--visual-backend", choices=("segformer", "owlv2", "florence2", "esanet", "grounding-dino"), default="segformer", help="local visual candidate backend; ESANet requires LiDAR RGB/depth")
    processor.add_argument("--visual-model-path", help="local SegFormer ONNX checkpoint or OWLv2/Florence-2/ESANet/Grounding DINO directory")
    processor.add_argument("--lidar-rgb-rotation", type=int, choices=(0, 90, 180, 270), default=0,
                           help="clockwise display rotation for OWLv2, Florence-2, ESANet, or Grounding DINO on LiDAR RGB; boxes map back to raw pixels")
    processor.add_argument("--max-model-frames", type=positive_int, default=24, help="maximum selected RGB frames passed to the visual model")
    processor.add_argument("--runs-dir", default="runs")
    from .capture import process_capture
    processor.set_defaults(func=process_capture)
    linker = subcommands.add_parser('link-captures',
        help='compare independent photo, video, and LiDAR RGB runs in image space')
    linker.add_argument('--photo-run', required=True)
    linker.add_argument('--video-run', required=True)
    linker.add_argument('--lidar-run', required=True)
    linker.add_argument('--photo-source', required=True)
    linker.add_argument('--lidar-source', required=True)
    linker.add_argument('--max-views', type=positive_int, default=12)
    linker.add_argument('--lidar-rgb-rotation', type=int, choices=(0, 90, 180, 270), default=0)
    linker.add_argument('--match-backend', choices=('patch', 'aliked-lightglue'), default='patch')
    linker.add_argument('--model-root', default='.room-proof/models')
    linker.add_argument('--calibration', help='optional calibrated photo/video intrinsics and scan RGB-to-depth pixel map JSON')
    linker.add_argument('--runs-dir', default='runs')
    linker.set_defaults(func=link_capture_runs)
    summary = subcommands.add_parser('summarize-dimensions',
        help='create one consolidated dimension report from a completed run without rerunning models')
    summary.add_argument('--source-run', required=True)
    summary.add_argument('--runs-dir', default='runs')
    summary.set_defaults(func=summarize_dimensions_run)
    opening_review = subcommands.add_parser('review-dino-openings',
        help='reuse a linked Grounding DINO run to find photo-to-scan passage correspondences')
    opening_review.add_argument('--linked-run', required=True)
    opening_review.add_argument('--photo-name', help='optional source photo filename to inspect')
    opening_review.add_argument('--runs-dir', default='runs')
    from .photo_guided_openings import review_existing_dino_openings
    opening_review.set_defaults(func=review_existing_dino_openings)
    assembler = subcommands.add_parser('assemble-property',
        help='combine separately linked metric room runs using shared calibrated openings')
    assembler.add_argument('--linked-run', action='append', dest='linked_runs', required=True)
    assembler.add_argument('--runs-dir', default='runs')
    assembler.set_defaults(func=assemble_property_runs)
    benchmark = subcommands.add_parser("score-benchmark", help="score frozen plans against separate reference truth")
    benchmark.add_argument("manifest")
    benchmark.add_argument("--runs-dir", default="runs")
    benchmark.set_defaults(func=score_benchmark)
    vision = subcommands.add_parser("probe-vision", help="optional disclosed single-image Gemini vision pilot")
    vision.add_argument("image")
    vision.add_argument("--runs-dir", default="runs")
    vision.set_defaults(func=probe_vision)
    args = parser.parse_args()
    return execute(args.command, args, args.func)
