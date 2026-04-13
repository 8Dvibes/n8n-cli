"""Shell completion script generation for n8n-cli.

Generates bash and zsh completion scripts by introspecting the argparse
parser tree. No external dependencies required.

Usage:
    n8n-cli completion bash >> ~/.bashrc
    n8n-cli completion zsh > ~/.zsh/completions/_n8n-cli
    eval "$(n8n-cli completion bash)"
"""

from __future__ import annotations

import argparse


def _collect_commands(parser: argparse.ArgumentParser, prefix: str = "") -> dict:
    """Walk the parser tree and collect every leaf command with its flags."""
    result = {}

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in (action.choices or {}).items():
                path = f"{prefix} {name}".strip()

                # Check if this subparser has its own subparsers
                has_children = any(
                    isinstance(a, argparse._SubParsersAction)
                    for a in sub._actions
                )

                if has_children:
                    # Recurse into nested subparsers
                    result.update(_collect_commands(sub, path))
                else:
                    # Leaf command — collect its flags
                    flags = []
                    for sub_action in sub._actions:
                        if isinstance(sub_action, argparse._SubParsersAction):
                            continue
                        for opt in sub_action.option_strings:
                            if opt not in ("-h", "--help"):
                                flags.append(opt)
                    # Collect choices for flags that have them
                    choices_map = {}
                    for sa in sub._actions:
                        if isinstance(sa, argparse._SubParsersAction):
                            continue
                        if sa.choices and sa.option_strings:
                            for opt in sa.option_strings:
                                choices_map[opt] = list(sa.choices)
                    result[path] = {
                        "flags": flags,
                        "choices": choices_map,
                    }

    return result


def _get_top_commands(parser: argparse.ArgumentParser) -> list:
    """Get the list of top-level command names."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return sorted(action.choices.keys())
    return []


def _get_global_flags(parser: argparse.ArgumentParser) -> list:
    """Get global flags (before any subcommand)."""
    flags = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        for opt in action.option_strings:
            if opt not in ("-h", "--help"):
                flags.append(opt)
    return flags


def generate_bash(parser: argparse.ArgumentParser) -> str:
    """Generate a bash completion script from the parser."""
    prog = parser.prog
    fn = f"_{prog.replace('-', '_')}"
    top_cmds = _get_top_commands(parser)
    global_flags = _get_global_flags(parser)
    commands = _collect_commands(parser)

    # Build per-subcommand completions
    subcmd_cases = []
    for cmd_name in top_cmds:
        # Find all leaf commands under this top-level command
        sub_words = set()
        for path, info in commands.items():
            parts = path.split()
            if parts[0] == cmd_name:
                if len(parts) > 1:
                    sub_words.add(parts[1])
                sub_words.update(info["flags"])

        if sub_words:
            words = " ".join(sorted(sub_words))
            subcmd_cases.append(
                f"        {cmd_name})\n"
                f'            COMPREPLY=($(compgen -W "{words}" -- "$cur"))\n'
                f"            return 0\n"
                f"            ;;"
            )

    all_words = " ".join(sorted(top_cmds + global_flags))
    cases_block = "\n".join(subcmd_cases) if subcmd_cases else "        *) ;;"

    return f"""\
# Bash completion for {prog}
# Auto-generated from argparse parser
# Install: eval "$({prog} completion bash)"
#      or: {prog} completion bash >> ~/.bashrc

{fn}() {{
    local cur prev
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Subcommand dispatch
    if [[ $COMP_CWORD -ge 2 ]]; then
        local subcmd="${{COMP_WORDS[1]}}"
        case "$subcmd" in
{cases_block}
        esac
    fi

    # Top-level completions
    COMPREPLY=($(compgen -W "{all_words}" -- "$cur"))
}}

complete -o default -F {fn} {prog}
"""


def generate_zsh(parser: argparse.ArgumentParser) -> str:
    """Generate a zsh completion script from the parser."""
    prog = parser.prog
    fn = f"_{prog.replace('-', '_')}"
    top_cmds = _get_top_commands(parser)
    commands = _collect_commands(parser)

    # Build subcommand completions
    subcmd_funcs = []
    case_lines = []

    for cmd_name in top_cmds:
        sub_fn = f"{fn}_{cmd_name.replace('-', '_')}"
        sub_words = set()
        for path, info in commands.items():
            parts = path.split()
            if parts[0] == cmd_name:
                if len(parts) > 1:
                    sub_words.add(parts[1])
                sub_words.update(info["flags"])

        if sub_words:
            words = " ".join(sorted(sub_words))
            subcmd_funcs.append(
                f'{sub_fn}() {{\n'
                f'    _arguments -s \\\n'
                f"        '*::{cmd_name} commands:(({words}))'\n"
                f'}}'
            )
            case_lines.append(f"        {cmd_name}) {sub_fn} ;;")

    funcs_block = "\n\n".join(subcmd_funcs)
    cases_block = "\n".join(case_lines)
    cmds = " ".join(sorted(top_cmds))

    return f"""\
#compdef {prog}
# Zsh completion for {prog}
# Auto-generated from argparse parser
# Install: {prog} completion zsh > ~/.zsh/completions/_{prog}

{funcs_block}

{fn}() {{
    _arguments -s \\
        '1:command:(({cmds}))' \\
        '*::arg:->args'

    case $state in
        args)
            case ${{words[1]}} in
{cases_block}
            esac
            ;;
    esac
}}

{fn} "$@"
"""
