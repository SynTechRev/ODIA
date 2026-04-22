"""Command-line interface for ODIA AI pipelines.

Usage:
    odia-ai init-config [--path config.json]
    odia-ai build-dataset --config config.json [--mas-dir DIR]
    odia-ai train --config config.json
    odia-ai evaluate --config config.json [--backend BACKEND]
    odia-ai extract --text "..." [--backend BACKEND]
    odia-ai extract-file FILE [--backend BACKEND]
    odia-ai registry list
    odia-ai registry promote VERSION_ID
    odia-ai feedback stats

Each command runs a stage of the pipeline. Stages are independent —
you can run build-dataset without ever training, evaluate against the
pattern backend without any fine-tuned model, and extract against any
available backend.

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ------------------------------------------------------------------
# init-config
# ------------------------------------------------------------------


def cmd_init_config(args: argparse.Namespace) -> int:
    from odia_ai.configs import ODIAAIConfig, write_config

    out_path = Path(args.path)
    cfg = ODIAAIConfig()
    write_config(cfg, out_path)
    print(f"Wrote default config to {out_path}")
    return 0


# ------------------------------------------------------------------
# build-dataset
# ------------------------------------------------------------------


def cmd_build_dataset(args: argparse.Namespace) -> int:
    from odia_ai.backref import compute_corpus_stats, extract_corpus, write_jsonl
    from odia_ai.configs import load_config
    from odia_ai.training import build_dataset, split_summary, write_dataset_splits

    cfg = load_config(args.config) if args.config else None
    mas_dir = Path(
        args.mas_dir or (cfg.dataset.mas_corpus_dir if cfg else "./data/mas_corpus")
    )
    output_dir = Path(
        args.output_dir or (cfg.dataset.output_dir if cfg else "./data/training_splits")
    )
    format_choice = args.format or (cfg.dataset.format if cfg else "alpaca")

    if not mas_dir.exists():
        print(f"ERROR: MAS corpus directory does not exist: {mas_dir}", file=sys.stderr)
        return 1

    # set-union dedupes hits on case-insensitive filesystems (Windows/macOS),
    # where *.md and *.MD match the same files.
    mas_files = sorted({*mas_dir.glob("*.md"), *mas_dir.glob("*.MD")})
    mas_files = [f for f in mas_files if f.is_file()]
    if not mas_files:
        print(f"ERROR: No .md files found in {mas_dir}", file=sys.stderr)
        return 1

    print(f"Scanning {len(mas_files)} MAS files in {mas_dir}...")
    alerts = extract_corpus(mas_files)
    print(f"Extracted {len(alerts)} alerts")

    stats = compute_corpus_stats(alerts)
    print("\nCorpus statistics:")
    print(f"  Total alerts:      {stats['total_alerts']}")
    print(f"  Average body size: {stats['avg_body_length']} chars")
    for j, n in sorted(stats["by_jurisdiction"].items()):
        print(f"    {j:20s} {n}")

    # Write raw alerts
    raw_path = output_dir / "_raw_alerts.jsonl"
    write_jsonl(alerts, raw_path)
    print(f"\nWrote raw alerts: {raw_path}")

    # Build training examples
    examples = build_dataset(
        alerts,
        enable_jurisdiction_transfer=args.enable_synthesis,
        enable_negatives=False,
        random_seed=42,
    )
    split_info = split_summary(examples)
    print(f"\nBuilt {split_info['total']} training examples:")
    for split_name, count in split_info["by_split"].items():
        print(f"  {split_name:12s} {count}")

    counts = write_dataset_splits(examples, output_dir, format=format_choice)
    print(f"\nWrote dataset splits to {output_dir}:")
    for split_name, count in counts.items():
        print(f"  {split_name}.jsonl: {count} examples")
    return 0


# ------------------------------------------------------------------
# train
# ------------------------------------------------------------------


def cmd_train(args: argparse.Namespace) -> int:
    from odia_ai.configs import load_config
    from odia_ai.registry import (
        ModelRegistry,
        ModelVersion,
        compute_dataset_hash,
        generate_version_id,
    )
    from odia_ai.training.lora_runner import (
        LoRAConfig,
        TrainingConfig,
        train_lora,
    )

    cfg = load_config(args.config)
    train_path = Path(args.train_path or f"{cfg.dataset.output_dir}/train.jsonl")
    val_path_raw = args.validation_path or f"{cfg.dataset.output_dir}/validation.jsonl"
    val_path = Path(val_path_raw) if val_path_raw else None

    if not train_path.exists():
        print(f"ERROR: Train file not found: {train_path}", file=sys.stderr)
        return 1

    lora_cfg = LoRAConfig(
        r=cfg.training.lora_r,
        alpha=cfg.training.lora_alpha,
        dropout=cfg.training.lora_dropout,
    )
    training_cfg = TrainingConfig(
        base_model=cfg.training.base_model,
        output_dir=cfg.training.output_dir,
        num_train_epochs=cfg.training.num_train_epochs,
        per_device_train_batch_size=cfg.training.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.training.gradient_accumulation_steps,
        learning_rate=cfg.training.learning_rate,
        max_seq_length=cfg.training.max_seq_length,
        load_in_4bit=cfg.training.load_in_4bit,
        bf16=cfg.training.bf16,
        seed=cfg.training.seed,
    )

    print("Starting LoRA fine-tuning...")
    print(f"  Base model: {training_cfg.base_model}")
    print(f"  Train file: {train_path} (hash: {compute_dataset_hash(train_path)[:12]})")
    if val_path and val_path.exists():
        print(f"  Validation: {val_path}")

    result = train_lora(train_path, val_path, lora_cfg, training_cfg)

    if result.success:
        print("\nTraining succeeded.")
        print(f"  Model path:      {result.model_path}")
        print(f"  Train loss:      {result.train_loss}")
        print(f"  Eval loss:       {result.eval_loss}")
        print(f"  Steps completed: {result.steps_completed}")

        # Register the new model version
        registry = ModelRegistry(Path(cfg.deployment.registry_root))
        version_id = generate_version_id()
        version = ModelVersion(
            version_id=version_id,
            base_model=training_cfg.base_model,
            model_path=result.model_path,
            training_config=result.config_snapshot.get("training", {}),
            lora_config=result.config_snapshot.get("lora", {}),
            training_data_hash=compute_dataset_hash(train_path),
            num_training_examples=result.num_train_examples,
            num_evaluation_examples=result.num_eval_examples,
            evaluation_metrics={
                "train_loss": result.train_loss,
                "eval_loss": result.eval_loss,
            },
        )
        registry.register(version)
        print(f"  Registered as:   {version_id}")
        return 0
    else:
        print("\nTraining FAILED.", file=sys.stderr)
        print(f"  Error: {result.error_message}", file=sys.stderr)
        return 1


# ------------------------------------------------------------------
# evaluate
# ------------------------------------------------------------------


def cmd_evaluate(args: argparse.Namespace) -> int:
    from odia_ai.configs import load_config
    from odia_ai.evaluation import (
        compare_backends,
        write_evaluation_report,
    )
    from odia_ai.extraction import (
        FinetunedExtractionBackend,
        PatternExtractionBackend,
        RAGExtractionBackend,
    )

    cfg = load_config(args.config) if args.config else None
    dataset_path = Path(
        args.dataset
        or (
            cfg.evaluation.test_dataset_path
            if cfg
            else "./data/training_splits/test.jsonl"
        )
    )
    report_dir = Path(
        args.report_dir or (cfg.evaluation.report_dir if cfg else "./reports/eval")
    )

    if not dataset_path.exists():
        print(f"ERROR: Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    # Build backend list
    backends = []
    if args.backend == "pattern" or args.backend is None:
        backends.append(PatternExtractionBackend())
    if args.backend == "rag_llm" or (args.backend is None and cfg):
        backends.append(
            RAGExtractionBackend(
                llm_provider=cfg.deployment.default_llm_provider if cfg else "ollama",
                llm_model=cfg.deployment.default_llm_model if cfg else None,
            )
        )
    if args.backend == "finetuned" and cfg and cfg.deployment.finetuned_model_path:
        backends.append(FinetunedExtractionBackend(cfg.deployment.finetuned_model_path))

    if not backends:
        # Default: just evaluate the pattern backend
        backends = [PatternExtractionBackend()]

    results = compare_backends(backends, dataset_path, max_examples=args.max_examples)
    report_dir.mkdir(parents=True, exist_ok=True)

    for backend_name, result in results.items():
        print(result.summary_report())
        print()
        out_path = report_dir / f"eval_{backend_name}.json"
        write_evaluation_report(result, out_path)
        print(f"Report written: {out_path}")
    return 0


# ------------------------------------------------------------------
# extract
# ------------------------------------------------------------------


def cmd_extract(args: argparse.Namespace) -> int:
    from odia_ai.configs import load_config
    from odia_ai.extraction import ExtractionService

    cfg = load_config(args.config) if args.config else None

    if args.text:
        text = args.text
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    svc = ExtractionService(
        finetuned_model_path=(cfg.deployment.finetuned_model_path if cfg else None),
        llm_provider=(cfg.deployment.default_llm_provider if cfg else "ollama"),
        llm_model=(cfg.deployment.default_llm_model if cfg else None),
        force_backend=args.backend,
    )
    output = svc.extract(text)
    print(json.dumps(output.to_dict(), indent=2, ensure_ascii=False))
    return 0


# ------------------------------------------------------------------
# registry
# ------------------------------------------------------------------


def cmd_registry(args: argparse.Namespace) -> int:
    from odia_ai.configs import load_config
    from odia_ai.registry import ModelRegistry

    cfg = load_config(args.config) if args.config else None
    root = Path(
        args.registry_root
        or (cfg.deployment.registry_root if cfg else "./models/registry")
    )
    registry = ModelRegistry(root)

    if args.action == "list":
        versions = registry.list_versions()
        if not versions:
            print("(registry is empty)")
            return 0
        for v in versions:
            prod_marker = (
                " [PROD]" if v.get("deployment_status") == "production" else ""
            )
            print(
                f"{v['version_id']:40s} "
                f"{v.get('deployment_status', '?'):12s} "
                f"{v.get('base_model', '?')}{prod_marker}"
            )
        return 0

    if args.action == "promote":
        if not args.version_id:
            print("ERROR: --version-id required for promote", file=sys.stderr)
            return 1
        ok = registry.set_deployment_status(args.version_id, "production")
        if ok:
            print(f"Promoted {args.version_id} to production")
            return 0
        print(f"ERROR: version not found: {args.version_id}", file=sys.stderr)
        return 1

    if args.action == "show":
        if not args.version_id:
            print("ERROR: --version-id required for show", file=sys.stderr)
            return 1
        v = registry.get(args.version_id)
        if v is None:
            print(f"ERROR: version not found: {args.version_id}", file=sys.stderr)
            return 1
        print(json.dumps(v.to_dict(), indent=2))
        return 0

    print(f"Unknown registry action: {args.action}", file=sys.stderr)
    return 1


# ------------------------------------------------------------------
# feedback
# ------------------------------------------------------------------


def cmd_feedback(args: argparse.Namespace) -> int:
    from odia_ai.configs import load_config
    from odia_ai.continual import (
        CorrectionStore,
        TriggerConfig,
        should_trigger_retraining,
    )

    cfg = load_config(args.config) if args.config else None
    db_path = Path(
        args.db_path
        or (cfg.continual.correction_store_path if cfg else "./data/corrections.db")
    )
    store = CorrectionStore(db_path)

    if args.action == "stats":
        total = store.count()
        reviewed = store.count(reviewed_only=True)
        pending = store.count(reviewed_only=True, unapplied_only=True)
        print(f"Corrections store: {db_path}")
        print(f"  Total corrections:          {total}")
        print(f"  Reviewed:                   {reviewed}")
        print(f"  Pending (reviewed+unapplied):{pending}")
        print("\n  By field:")
        for k, v in store.stats_by_field().items():
            print(f"    {k:30s} {v}")
        print("\n  By jurisdiction:")
        for k, v in store.stats_by_jurisdiction().items():
            print(f"    {k:30s} {v}")
        trig_cfg = TriggerConfig(
            min_new_corrections=cfg.continual.min_new_corrections if cfg else 50,
            min_days_since_last_training=(
                cfg.continual.min_days_since_last_training if cfg else 30
            ),
        )
        decision = should_trigger_retraining(store, trig_cfg)
        print(f"\n  Retrain trigger: {'YES' if decision.should_retrain else 'no'}")
        print(f"  Reason: {decision.reason}")
        return 0

    print(f"Unknown feedback action: {args.action}", file=sys.stderr)
    return 1


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odia-ai",
        description="O.D.I.A. AI — fine-tuning and continual learning for surveillance audit extraction",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to config YAML/JSON"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init-config
    p_init = sub.add_parser("init-config", help="Write default config to disk")
    p_init.add_argument("--path", default="./odia_ai_config.json")
    p_init.set_defaults(func=cmd_init_config)

    # build-dataset
    p_bd = sub.add_parser(
        "build-dataset", help="Build training dataset from MAS corpus"
    )
    p_bd.add_argument("--mas-dir", help="Directory with *.md MAS files")
    p_bd.add_argument("--output-dir", help="Where to write split JSONL files")
    p_bd.add_argument("--format", choices=["alpaca", "openai", "raw"], default=None)
    p_bd.add_argument(
        "--enable-synthesis",
        action="store_true",
        default=True,
        help="Produce synthetic jurisdiction-transfer variants",
    )
    p_bd.set_defaults(func=cmd_build_dataset)

    # train
    p_train = sub.add_parser("train", help="Run LoRA fine-tuning")
    p_train.add_argument("--train-path")
    p_train.add_argument("--validation-path")
    p_train.set_defaults(func=cmd_train)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Evaluate extraction backends")
    p_eval.add_argument("--dataset")
    p_eval.add_argument("--report-dir")
    p_eval.add_argument("--backend", choices=["pattern", "rag_llm", "finetuned"])
    p_eval.add_argument("--max-examples", type=int, default=None)
    p_eval.set_defaults(func=cmd_evaluate)

    # extract
    p_ext = sub.add_parser("extract", help="Run extraction on text or file")
    p_ext.add_argument("--text", help="Text to extract from")
    p_ext.add_argument("--file", help="Read text from file")
    p_ext.add_argument("--backend", choices=["pattern", "rag_llm", "finetuned"])
    p_ext.set_defaults(func=cmd_extract)

    # registry
    p_reg = sub.add_parser("registry", help="Model registry operations")
    p_reg.add_argument("action", choices=["list", "show", "promote"])
    p_reg.add_argument("--version-id")
    p_reg.add_argument("--registry-root")
    p_reg.set_defaults(func=cmd_registry)

    # feedback
    p_fb = sub.add_parser(
        "feedback", help="User feedback / correction store operations"
    )
    p_fb.add_argument("action", choices=["stats"])
    p_fb.add_argument("--db-path")
    p_fb.set_defaults(func=cmd_feedback)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
