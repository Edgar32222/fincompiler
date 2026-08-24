from __future__ import annotations

import argparse
import json

from .mapping import MappingMemory
from .lineage_store import LineageStore
from .pipeline import compile_pack
from .scenario import SUPPORTED_ANOMALIES, generate_scenario
from .run_state import sign_off, verify_run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="fincompiler")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("input_dir")
    run.add_argument("--output", default="output")
    run.add_argument("--memory", default="mappings/memory.json")
    run.add_argument("--config")
    generate = sub.add_parser("generate-demo")
    generate.add_argument("output_dir")
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--invoices", type=int, default=50)
    generate.add_argument("--anomalies", nargs="*", choices=sorted(SUPPORTED_ANOMALIES), default=[])
    trace = sub.add_parser("trace")
    trace.add_argument("lineage_store")
    trace.add_argument("lineage_id")
    trace.add_argument("--limit", type=int, default=100)
    trace.add_argument("--offset", type=int, default=0)
    approval = sub.add_parser("sign-off")
    approval.add_argument("run_dir")
    approval.add_argument("--reviewer", required=True)
    approval.add_argument("--notes", default="")
    verify = sub.add_parser("verify-run")
    verify.add_argument("run_dir")
    confirm = sub.add_parser("confirm-mapping")
    confirm.add_argument("dataset", choices=["sales", "gl", "budget"])
    confirm.add_argument("source_field")
    confirm.add_argument("canonical_field")
    confirm.add_argument("--fields", nargs="+", required=True)
    confirm.add_argument("--memory", default="mappings/memory.json")
    args = parser.parse_args(argv)
    if args.command == "run":
        result = compile_pack(args.input_dir, args.output, args.memory, args.config)
        print(json.dumps({"output_readiness": result["output_readiness"], "variance": result["reconciliation"]["variance"], "output": f"{args.output}/management_pack.json"}, indent=2))
    elif args.command == "generate-demo":
        result = generate_scenario(args.output_dir, args.seed, args.invoices, args.anomalies)
        print(json.dumps(result, indent=2))
    elif args.command == "trace":
        with LineageStore(args.lineage_store) as lineage:
            print(json.dumps(lineage.trace(args.lineage_id, args.limit, args.offset), indent=2, ensure_ascii=False))
    elif args.command == "sign-off":
        print(json.dumps(sign_off(args.run_dir, args.reviewer, args.notes), indent=2, ensure_ascii=False))
    elif args.command == "verify-run":
        result = verify_run(args.run_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["valid"] else 2
    else:
        memory = MappingMemory(args.memory)
        memory.confirm(args.dataset, args.source_field, args.canonical_field, args.fields)
        print("Mapping confirmed and saved locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
