# ProcBench

Process Benchmarking Tool.

## Prerequisites

- Python 3.12+
- `uv`, the Python package manager.

## Setup

```sh
cd <project_root>
uv venv
uv sync
```

## Usage

### Prepare your Test Cases

Make a copy of `sample-test-case.json`, e.g.
`tc01.json`. Change the parameters as needed.

You can make several test cases, e.g. `tc02.json`, `tc03.json`.
Suppose we have those three test cases.

### Run the Test Cases

Suppose you want to dump the output to `result.json`, run:

```sh
uv run -m procbench -o result.json tc01.json tc02.json tc03.json
```

For verbose debug output, add `-v` flag:

```sh
uv run -m procbench -v -o result.json tc01.json tc02.json tc03.json
```
