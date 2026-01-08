# procmon/cli.py

import time
from pathlib import Path
from typing import List

import click

from .testcase import TestCase
from .runner import ProcessRunner
from .monitor import ProcessMonitor
from .summary import summarize_samples
from .output import OutputWriter
from .errors import ProcMonError


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "testcases",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    nargs=-1,
    required=True,
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output JSON file",
)
@click.option(
    "--continue-on-error/--stop-on-error",
    default=True,
    help="Continue running remaining test cases if one fails",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose logging to stdout",
)
def main(
    testcases: List[Path],
    output_path: Path,
    continue_on_error: bool,
    verbose: bool,
):
    """
    Run process monitoring test cases and write a single JSON output.
    """

    session_start = time.time()
    results = []

    writer = OutputWriter(schema_version="1.0")

    for tc_path in testcases:
        if verbose:
            click.echo(f"[+] Loading test case: {tc_path}")

        try:
            tc = TestCase.load_from_file(tc_path)

            if verbose:
                click.echo(f"[+] Running test case: {tc.id}")

            runner = ProcessRunner(
                command=tc.command,
                cwd=tc.cwd,
                env=tc.env,
            )
            runner.start()

            assert runner.pid is not None

            monitor = ProcessMonitor(
                pid=runner.pid,
                sampling_interval_ms=tc.sampling_interval_ms,
                timeout_sec=tc.timeout_sec,
                include_children=tc.include_children,
            )

            monitor.run()

            # If monitor timed out, ensure process is terminated
            if monitor.status == "timeout":
                if verbose:
                    click.echo(f"[!] Timeout reached, terminating pid {runner.pid}")
                runner.terminate()
            else:
                runner.wait(timeout=1)

            process_info = runner.info()

            summary = summarize_samples(
                samples=monitor.samples,
                start_time=monitor.start_time,
                end_time=monitor.end_time,
                exit_code=process_info.get("exit_code"),
                status=monitor.status,
            )

            result = writer.build_testcase_result(
                testcase_meta=tc.to_dict(),
                process_info=process_info,
                samples=monitor.samples,
                summary=summary,
            )

            results.append(result)

            if verbose:
                click.echo(f"[+] Test case {tc.id} completed with status={monitor.status}")

        except ProcMonError as e:
            click.echo(f"[ERROR] {e}", err=True)

            if not continue_on_error:
                break

        except Exception as e:
            click.echo(f"[FATAL] Unexpected error: {e}", err=True)
            if not continue_on_error:
                break

    session_end = time.time()

    writer.write(
        output_path=output_path,
        session_start=session_start,
        session_end=session_end,
        results=results,
    )

    if verbose:
        click.echo(f"[+] Results written to {output_path}")


if __name__ == "__main__":
    main()
