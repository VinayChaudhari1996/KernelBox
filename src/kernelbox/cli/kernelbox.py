"""Human-facing CLI for kernelbox."""

from __future__ import annotations

import argparse
import json
from typing import Any

from kernelbox.config.defaults import KernelBoxConfig
from kernelbox.core.executor import KernelExecutor
from kernelbox.core.manager import KernelManagerService
from kernelbox.store.registry import create_registry


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = KernelBoxConfig.from_env()
    registry = create_registry(config)
    manager = KernelManagerService(config=config, registry=registry)
    executor = KernelExecutor(config=config, registry=registry)

    if args.command == "create":
        record = manager.create(name=args.name)
        _print_json(record.to_dict())
        return 0

    if args.command == "list":
        records = [record.to_dict() for record in manager.list(refresh=args.refresh)]
        _print_json({"kernels": records})
        return 0

    if args.command == "exec":
        record = _resolve(manager, args)
        language = "bash" if args.bash else "python"
        result = executor.execute(record, args.code, language=language, timeout=args.timeout)
        _print_json(result.to_dict())
        return 0 if result.ok else 1

    if args.command == "restart":
        record = manager.restart(_identifier(args))
        _print_json(record.to_dict())
        return 0

    if args.command == "destroy":
        destroyed = manager.destroy(_identifier(args))
        _print_json({"destroyed": destroyed})
        return 0 if destroyed else 1

    if args.command == "wipe":
        destroyed = manager.wipe_all()
        _print_json({"destroyed": destroyed})
        return 0

    if args.command == "status":
        record = _resolve(manager, args)
        alive = manager.ping(record)
        refreshed = manager.get(record.kernel_id) or record
        _print_json({"alive": alive, "kernel": refreshed.to_dict()})
        return 0 if alive else 1

    if args.command == "serve":
        import uvicorn
        from kernelbox.server.app import app
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kernelbox")
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser("create", help="create a new kernel")
    create.add_argument("--name", required=True)

    list_parser = subparsers.add_parser("list", help="list registered kernels")
    list_parser.add_argument("--refresh", action="store_true")

    exec_parser = subparsers.add_parser("exec", help="execute code in a kernel")
    _add_identifier_args(exec_parser)
    exec_parser.add_argument("code")
    exec_parser.add_argument("--bash", action="store_true")
    exec_parser.add_argument("--timeout", type=float)

    restart = subparsers.add_parser("restart", help="restart a kernel")
    _add_identifier_args(restart)

    destroy = subparsers.add_parser("destroy", help="destroy a kernel")
    _add_identifier_args(destroy)

    subparsers.add_parser("wipe", help="destroy all registered kernels")

    status = subparsers.add_parser("status", help="check kernel health")
    _add_identifier_args(status)

    serve = subparsers.add_parser("serve", help="start the FastAPI server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)

    return parser


def _add_identifier_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name")
    group.add_argument("--id")


def _resolve(manager: KernelManagerService, args: argparse.Namespace):
    record = manager.get(_identifier(args))
    if record is None:
        raise SystemExit(f"Unknown kernel: {_identifier(args)}")
    return record


def _identifier(args: argparse.Namespace) -> str:
    return args.name or args.id


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())

