# Copyright (c) Alibaba, Inc. and its affiliates.
import importlib.util
import os
import subprocess
import sys
from typing import Dict, List, Optional

ROUTE_MAPPING: Dict[str, str] = {
    'pt': 'swift.cli.sft',
    'sft': 'swift.cli.sft',
    'infer': 'swift.cli.infer',
    'app-ui': 'swift.cli.app_ui',
    'merge-lora': 'swift.cli.merge_lora',
    'web-ui': 'swift.cli.web_ui',
    'deploy': 'swift.cli.deploy',
    'dpo': 'swift.cli.rlhf',
    'orpo': 'swift.cli.rlhf',
    'simpo': 'swift.cli.rlhf',
    'rlhf': 'swift.cli.rlhf',
    'export': 'swift.cli.export',
    'eval': 'swift.cli.eval'
}

ROUTE_MAPPING.update({k.replace('-', '_'): v for k, v in ROUTE_MAPPING.items()})


def use_torchrun() -> bool:
    nproc_per_node = os.getenv('NPROC_PER_NODE')
    nnodes = os.getenv('NNODES')
    if nproc_per_node is None and nnodes is None:
        return False
    return True


def get_torchrun_args() -> Optional[List[str]]:
    if not use_torchrun():
        return
    torchrun_args = []
    for env_key in ['NPROC_PER_NODE', 'MASTER_PORT', 'NNODES', 'NODE_RANK', 'MASTER_ADDR']:
        env_val = os.getenv(env_key)
        if env_val is None:
            continue
        torchrun_args += [f'--{env_key.lower()}', env_val]
    return torchrun_args


def cli_main() -> None:
    argv = sys.argv[1:]
    method_name = argv[0]
    argv = argv[1:]
    # rlhf compatibility
    if method_name in ['dpo', 'simpo', 'orpo']:
        argv = ['--rlhf_type', method_name] + argv
    file_path = importlib.util.find_spec(ROUTE_MAPPING[method_name]).origin
    torchrun_args = get_torchrun_args()
    if torchrun_args is None or method_name not in ('sft', 'dpo', 'orpo', 'simpo', 'rlhf', 'pt'):
        # try:
        #     python_cmd = 'python'
        #     subprocess.run(
        #         [python_cmd, '--version'],
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #     )
        # except FileNotFoundError:
        python_cmd = 'python3'
        args = [python_cmd, file_path, *argv]
    else:
        args = ['torchrun', *torchrun_args, file_path, *argv]
    print(f"run sh: `{' '.join(args)}`", flush=True)
    result = subprocess.run(args)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == '__main__':
    cli_main()
