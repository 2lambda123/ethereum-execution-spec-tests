"""
Fixture collector class used to collect, sort and combine the different types of generated
fixtures.
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple

from evm_transition_tool import FixtureFormats, TransitionTool

from ..common.json import to_json
from .base.base_test import BaseFixture


def strip_test_prefix(name: str) -> str:
    """
    Removes the test prefix from a test case name.
    """
    TEST_PREFIX = "test_"
    if name.startswith(TEST_PREFIX):
        return name[len(TEST_PREFIX) :]
    return name


def get_module_relative_output_dir(test_module: Path, filler_path: Path) -> Path:
    """
    Return a directory name for the provided test_module (relative to the
    base ./tests directory) that can be used for output (within the
    configured fixtures output path or the base_dump_dir directory).

    Example:
    tests/shanghai/eip3855_push0/test_push0.py -> shanghai/eip3855_push0/test_push0
    """
    basename = test_module.with_suffix("").absolute()
    basename_relative = basename.relative_to(filler_path.absolute())
    module_path = basename_relative.parent / basename_relative.stem
    return module_path


@dataclass(kw_only=True)
class TestInfo:
    """
    Contains test information from the current node.
    """

    name: str  # pytest: Item.name
    id: str  # pytest: Item.nodeid
    original_name: str  # pytest: Item.originalname
    path: Path  # pytest: Item.path

    def get_name_and_parameters(self) -> Tuple[str, str]:
        """
        Converts a test name to a tuple containing the test name and test parameters.

        Example:
        test_push0_key_sstore[fork_Shanghai] -> test_push0_key_sstore, fork_Shanghai
        """
        test_name, parameters = self.name.split("[")
        return test_name, re.sub(r"[\[\-]", "_", parameters).replace("]", "")

    def get_single_test_name(self) -> str:
        """
        Converts a test name to a single test name.
        """
        test_name, test_parameters = self.get_name_and_parameters()
        return f"{test_name}__{test_parameters}"

    def get_dump_dir_path(
        self,
        base_dump_dir: Optional[Path],
        filler_path: Path,
        level: Literal["test_module", "test_function", "test_parameter"] = "test_parameter",
    ) -> Optional[Path]:
        """
        The path to dump the debug output as defined by the level to dump at.
        """
        if not base_dump_dir:
            return None
        test_module_relative_dir = get_module_relative_output_dir(self.path, filler_path)
        if level == "test_module":
            return Path(base_dump_dir) / Path(str(test_module_relative_dir).replace(os.sep, "__"))
        test_name, test_parameter_string = self.get_name_and_parameters()
        flat_path = f"{str(test_module_relative_dir).replace(os.sep, '__')}__{test_name}"
        if level == "test_function":
            return Path(base_dump_dir) / flat_path
        elif level == "test_parameter":
            return Path(base_dump_dir) / flat_path / test_parameter_string
        raise Exception("Unexpected level.")


@dataclass(kw_only=True)
class FixtureCollector:
    """
    Collects all fixtures generated by the test cases.
    """

    output_dir: str
    flat_output: bool
    single_fixture_per_file: bool
    filler_path: Path
    base_dump_dir: Optional[Path] = None

    # Internal state
    all_fixtures: Dict[Path, Dict[str, BaseFixture]] = field(default_factory=dict)
    json_path_to_fixture_type: Dict[Path, FixtureFormats] = field(default_factory=dict)
    json_path_to_test_item: Dict[Path, TestInfo] = field(default_factory=dict)

    def get_fixture_basename(self, info: TestInfo) -> Path:
        """
        Returns the basename of the fixture file for a given test case.
        """
        if self.flat_output:
            if self.single_fixture_per_file:
                return Path(strip_test_prefix(info.get_single_test_name()))
            return Path(strip_test_prefix(info.original_name))
        else:
            relative_fixture_output_dir = Path(info.path).parent / strip_test_prefix(
                Path(info.path).stem
            )
            module_relative_output_dir = get_module_relative_output_dir(
                relative_fixture_output_dir, self.filler_path
            )

            if self.single_fixture_per_file:
                return module_relative_output_dir / strip_test_prefix(info.get_single_test_name())
            return module_relative_output_dir / strip_test_prefix(info.original_name)

    def add_fixture(self, info: TestInfo, fixture: BaseFixture) -> None:
        """
        Adds a fixture to the list of fixtures of a given test case.
        """
        fixture_basename = self.get_fixture_basename(info)

        fixture_path = (
            self.output_dir
            / fixture.format.output_base_dir_name
            / fixture_basename.with_suffix(fixture.format.output_file_extension)
        )
        if fixture_path not in self.all_fixtures:  # relevant when we group by test function
            self.all_fixtures[fixture_path] = {}
            if fixture_path in self.json_path_to_fixture_type:
                if self.json_path_to_fixture_type[fixture_path] != fixture.format:
                    raise Exception(
                        f"Fixture {fixture_path} has two different types: "
                        f"{self.json_path_to_fixture_type[fixture_path]} "
                        f"and {fixture.format}"
                    )
            else:
                self.json_path_to_fixture_type[fixture_path] = fixture.format
            self.json_path_to_test_item[fixture_path] = info

        self.all_fixtures[fixture_path][info.id] = fixture

    def dump_fixtures(self) -> None:
        """
        Dumps all collected fixtures to their respective files.
        """
        if self.output_dir == "stdout":
            combined_fixtures = {
                k: to_json(v) for fixture in self.all_fixtures.values() for k, v in fixture.items()
            }
            json.dump(combined_fixtures, sys.stdout, indent=4)
            return
        os.makedirs(self.output_dir, exist_ok=True)
        for fixture_path, fixtures in self.all_fixtures.items():
            os.makedirs(fixture_path.parent, exist_ok=True)

            # Get the first fixture to dump to get its type
            fixture = next(iter(fixtures.values()))
            # Call class method to dump all the fixtures
            with open(fixture_path, "w") as fd:
                fixture.collect_into_file(fd, fixtures)

    def verify_fixture_files(self, evm_fixture_verification: TransitionTool) -> None:
        """
        Runs `evm [state|block]test` on each fixture.
        """
        for fixture_path, fixture_format in self.json_path_to_fixture_type.items():
            if FixtureFormats.is_verifiable(fixture_format):
                info = self.json_path_to_test_item[fixture_path]
                verify_fixtures_dump_dir = self._get_verify_fixtures_dump_dir(info)
                use_single_test = False
                fixture_name = ""
                evm_fixture_verification.verify_fixture(
                    fixture_format,
                    fixture_path,
                    use_single_test,
                    fixture_name,
                    verify_fixtures_dump_dir,
                )

    def _get_verify_fixtures_dump_dir(
        self,
        info: TestInfo,
    ):
        """
        The directory to dump the current test function's fixture.json and fixture
        verification debug output.
        """
        if not self.base_dump_dir:
            return None
        if self.single_fixture_per_file:
            return info.get_dump_dir_path(
                self.base_dump_dir, self.filler_path, level="test_parameter"
            )
        else:
            return info.get_dump_dir_path(
                self.base_dump_dir, self.filler_path, level="test_function"
            )
