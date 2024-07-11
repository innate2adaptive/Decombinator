from decombinator import pipeline, io
import pytest
import pathlib
import os
import subprocess

pytestmark = pytest.mark.usefixtures("resource_location", "chain_name")


@pytest.fixture(params=["a", "b"], scope="module")
def chain_type(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(scope="module")
def output_dir(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    # Create a temporary output directory
    output_dir = tmp_path_factory.mktemp("output")
    return output_dir


@pytest.fixture(scope="module")
def cli_decombine(
    output_dir: pathlib.Path, resource_location: pathlib.Path, chain_type: str
) -> None:
    filename: str = "TINY_1.fq.gz"
    process = subprocess.run(
        [
            "./decombinator-runner.py",
            "decombine",
            "-in",
            str((resource_location / filename).resolve()),
            "-br",
            "R2",
            "-bl",
            "42",
            "-c",
            chain_type,
            "-op",
            f"{output_dir}{os.sep}",
            "-tfdir",
            "tests/resources/Decombinator-Tags-FASTAs",
            "-dz",
        ]
    )
    print(f"running with {chain_type} chain")
    print(process.stdout)


@pytest.fixture(scope="module")
def cli_collapse(
    output_dir: pathlib.Path,
    resource_location: pathlib.Path,
    chain_name: dict,
    chain_type: str,
) -> None:
    filename: str = "dcr_TINY_1_" + chain_name[chain_type] + ".n12"
    process = subprocess.run(
        [
            "./decombinator-runner.py",
            "collapse",
            "-in",
            str((resource_location / filename).resolve()),
            "-ol",
            "M13",
            "-c",
            chain_type,
            "-op",
            f"{output_dir}{os.sep}",
            "-dz",
        ]
    )
    print(f"running with {chain_type} chain")
    print(process.stdout)


@pytest.fixture(scope="module")
def cli_translate(
    output_dir: pathlib.Path,
    resource_location: pathlib.Path,
    chain_name: dict,
    chain_type: str,
) -> None:
    filename: str = "dcr_TINY_1_" + chain_name[chain_type] + ".freq"
    process = subprocess.run(
        [
            "./decombinator-runner.py",
            "translate",
            "-in",
            str((resource_location / filename).resolve()),
            "-c",
            chain_type,
            "-op",
            f"{output_dir}{os.sep}",
            "-dz",
            "-tfdir",
            "tests/resources/Decombinator-Tags-FASTAs",
        ]
    )
    print(f"running with {chain_type} chain")
    print(process.stdout)


def test_n12_output(
    cli_decombine: None,
    output_dir: pathlib.Path,
    resource_location: pathlib.Path,
    chain_type: str,
    chain_name: dict,
) -> None:

    # Load reference n12
    reference_file = f"dcr_TINY_1_{chain_name[chain_type]}.n12"
    reference_path = resource_location / reference_file
    with open(reference_path, "r") as f:
        reference_data = f.read()

    # Load output file generated by pipeline.run
    output_file = f"dcr_TINY_1_{chain_name[chain_type]}.n12"
    output_path = output_dir / output_file
    with open(output_path, "r") as f:
        output_data = f.read()

    # Perform comparison
    assert output_data == reference_data, "Output does not match reference data"


def test_freq_output(
    cli_collapse: None,
    output_dir: pathlib.Path,
    resource_location: pathlib.Path,
    chain_type: str,
    chain_name: dict,
) -> None:

    # Load reference freq
    reference_file = f"dcr_TINY_1_{chain_name[chain_type]}.freq"
    reference_path = resource_location / reference_file
    with open(reference_path, "r") as f:
        reference_data = f.read()

    # Load output file generated by pipeline.run
    output_file = f"dcr_TINY_1_{chain_name[chain_type]}.freq"
    output_path = output_dir / output_file
    with open(output_path, "r") as f:
        output_data = f.read()

    # Perform comparison
    assert output_data == reference_data, "Output does not match reference data"


# @pytest.mark.filterwarnings("ignore::Bio.BiopythonWarning")
def test_tsv_output(
    cli_translate: None,
    output_dir: pathlib.Path,
    resource_location: pathlib.Path,
    chain_type: str,
    chain_name: dict,
) -> None:

    # Load reference tsv
    reference_file = f"dcr_TINY_1_{chain_name[chain_type]}.tsv"
    reference_path = resource_location / reference_file
    with open(reference_path, "r") as f:
        reference_data = f.read()

    # Load output file generated by pipeline.run
    output_file = f"dcr_TINY_1_{chain_name[chain_type]}.tsv"
    output_path = output_dir / output_file
    with open(output_path, "r") as f:
        output_data = f.read()

    # Perform comparison
    print(output_data)
    print(reference_data)
    assert output_data == reference_data, "Output does not match reference data"


def test_log_output(
    output_dir: pathlib.Path,
    resource_location: pathlib.Path,
    chain_type: str,
    chain_name: dict,
) -> None:

    # Load reference logs
    reference_log_paths = [file for file in resource_location.glob("*")]

    reference_logs = [
        file
        for file in reference_log_paths
        if (chain_name[chain_type] in file.name)
    ]

    # Load output logs
    output_log_paths = [file for file in output_dir.glob("**/*.csv")]

    output_logs = [
        file
        for file in output_log_paths
        if (chain_name[chain_type] in file.name)
    ]

    # Perform comparison
    comparison_start = {
        "Decombinator_Summary.csv": 8,
        "Collapsing_Summary.csv": 9,
        "Translation_Summary.csv": 7,
    }
    for reference_log, output_log in zip(
        sorted(reference_logs), sorted(output_logs)
    ):

        with open(reference_log, "r") as f:
            comparison_label = "_".join(reference_log.name.split("_")[-2:])
            print(comparison_label)
            reference_log_lines = f.readlines()[
                comparison_start[comparison_label]
            ]

        with open(output_log, "r") as f:
            comparison_label = "_".join(output_log.name.split("_")[-2:])
            print(comparison_label)
            output_log_lines = f.readlines()[comparison_start[comparison_label]]

        assert output_log_lines == reference_log_lines
