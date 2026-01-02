"""
Databricks Mocks
================

Comprehensive mock implementations for Databricks-specific components
that enable local testing without Databricks cluster access.

Components:
- MockDbutils: Full dbutils mock (widgets, notebook, fs, secrets)
- MockUnityCatalog: Unity Catalog namespace mocking
"""

import pytest
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import MagicMock


# =============================================================================
# MOCK DBUTILS COMPONENTS
# =============================================================================

class MockWidgets:
    """
    Mock implementation of dbutils.widgets.

    Provides:
    - Widget value get/set
    - Widget type definitions (text, dropdown, etc.)
    - Test helper methods for value manipulation
    """

    def __init__(self, defaults: Dict[str, str] = None):
        self._values: Dict[str, str] = defaults.copy() if defaults else {}
        self._definitions: Dict[str, Dict] = {}

    def get(self, name: str) -> str:
        """
        Get widget value.

        Args:
            name: Widget name

        Returns:
            Widget value

        Raises:
            ValueError: If widget not found
        """
        if name not in self._values:
            raise ValueError(
                f"InputWidget named '{name}' does not exist. "
                f"Available widgets: {list(self._values.keys())}"
            )
        return self._values[name]

    def text(self, name: str, defaultValue: str, label: str = "") -> None:
        """Create text widget with default value."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "text",
            "default": defaultValue,
            "label": label
        }

    def dropdown(
        self,
        name: str,
        defaultValue: str,
        choices: List[str],
        label: str = ""
    ) -> None:
        """Create dropdown widget."""
        if defaultValue not in choices:
            raise ValueError(f"Default value '{defaultValue}' not in choices")
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "dropdown",
            "default": defaultValue,
            "choices": choices,
            "label": label
        }

    def combobox(
        self,
        name: str,
        defaultValue: str,
        choices: List[str],
        label: str = ""
    ) -> None:
        """Create combobox widget."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "combobox",
            "default": defaultValue,
            "choices": choices,
            "label": label
        }

    def multiselect(
        self,
        name: str,
        defaultValue: str,
        choices: List[str],
        label: str = ""
    ) -> None:
        """Create multiselect widget."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "multiselect",
            "default": defaultValue,
            "choices": choices,
            "label": label
        }

    def remove(self, name: str) -> None:
        """Remove a widget."""
        self._values.pop(name, None)
        self._definitions.pop(name, None)

    def removeAll(self) -> None:
        """Remove all widgets."""
        self._values.clear()
        self._definitions.clear()

    # Test helper methods

    def set_value(self, name: str, value: str) -> None:
        """Test helper: Set widget value without creating definition."""
        self._values[name] = value

    def get_all_values(self) -> Dict[str, str]:
        """Test helper: Get all widget values."""
        return self._values.copy()

    def has_widget(self, name: str) -> bool:
        """Test helper: Check if widget exists."""
        return name in self._values


class MockNotebook:
    """
    Mock implementation of dbutils.notebook.

    Provides:
    - notebook.exit() for return values
    - notebook.run() for child notebook execution (stubbed)
    - notebook.getContext() for context info
    """

    def __init__(self):
        self._exit_value: Optional[str] = None
        self._run_results: Dict[str, str] = {}
        self._run_calls: List[Dict] = []

    def exit(self, value: str) -> None:
        """Exit notebook with return value."""
        self._exit_value = value

    def run(
        self,
        path: str,
        timeout_seconds: int = 0,
        arguments: Dict[str, str] = None
    ) -> str:
        """
        Run another notebook.

        In tests, returns pre-configured result or empty string.
        Records call for verification.
        """
        self._run_calls.append({
            "path": path,
            "timeout": timeout_seconds,
            "arguments": arguments or {},
        })
        return self._run_results.get(path, "")

    def getContext(self) -> MagicMock:
        """Get notebook context (mocked)."""
        context = MagicMock()
        context.notebookPath.return_value = "/Workspace/test_notebook"
        context.currentRunId.return_value = "run_12345"
        context.tags.return_value = {"user": "test_user@example.com"}
        return context

    # Test helper methods

    def set_run_result(self, path: str, result: str) -> None:
        """Test helper: Configure result for notebook.run()."""
        self._run_results[path] = result

    def get_exit_value(self) -> Optional[str]:
        """Test helper: Get the exit value."""
        return self._exit_value

    def get_run_calls(self) -> List[Dict]:
        """Test helper: Get list of notebook.run() calls."""
        return self._run_calls.copy()

    def clear(self) -> None:
        """Test helper: Clear all state."""
        self._exit_value = None
        self._run_results.clear()
        self._run_calls.clear()


@dataclass
class FileInfo:
    """Mock file info returned by dbutils.fs.ls()."""
    path: str
    name: str
    size: int
    modificationTime: int = 0
    isDir: bool = False
    isFile: bool = True


class MockFs:
    """
    Mock implementation of dbutils.fs.

    Provides:
    - ls, head for reading
    - cp, mv, rm for file operations
    - mkdirs, put for writing
    """

    def __init__(self):
        self._files: Dict[str, bytes] = {}
        self._directories: set = set()

    def ls(self, path: str) -> List[FileInfo]:
        """List files in directory."""
        results = []
        path = path.rstrip("/")

        for file_path in self._files:
            if file_path.startswith(path + "/"):
                # Get immediate child only
                remaining = file_path[len(path) + 1:]
                if "/" not in remaining:
                    results.append(FileInfo(
                        path=file_path,
                        name=remaining,
                        size=len(self._files[file_path])
                    ))

        for dir_path in self._directories:
            if dir_path.startswith(path + "/"):
                remaining = dir_path[len(path) + 1:]
                if "/" not in remaining:
                    results.append(FileInfo(
                        path=dir_path,
                        name=remaining,
                        size=0,
                        isDir=True,
                        isFile=False
                    ))

        return results

    def head(self, path: str, maxBytes: int = 65536) -> str:
        """Read first bytes of file."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path][:maxBytes].decode('utf-8')

    def cp(self, src: str, dst: str, recurse: bool = False) -> bool:
        """Copy file or directory."""
        if src in self._files:
            self._files[dst] = self._files[src]
        return True

    def mv(self, src: str, dst: str, recurse: bool = False) -> bool:
        """Move file or directory."""
        if src in self._files:
            self._files[dst] = self._files[src]
            del self._files[src]
        return True

    def rm(self, path: str, recurse: bool = False) -> bool:
        """Remove file or directory."""
        if path in self._files:
            del self._files[path]
        if path in self._directories:
            self._directories.remove(path)
        if recurse:
            # Remove all under path
            to_remove = [p for p in self._files if p.startswith(path + "/")]
            for p in to_remove:
                del self._files[p]
        return True

    def mkdirs(self, path: str) -> bool:
        """Create directory."""
        self._directories.add(path)
        return True

    def put(self, path: str, contents: str, overwrite: bool = False) -> bool:
        """Write contents to file."""
        if path in self._files and not overwrite:
            raise FileExistsError(f"File exists: {path}")
        self._files[path] = contents.encode('utf-8')
        return True

    # Test helper methods

    def add_file(self, path: str, contents: bytes) -> None:
        """Test helper: Add a mock file."""
        self._files[path] = contents

    def add_text_file(self, path: str, contents: str) -> None:
        """Test helper: Add a mock text file."""
        self._files[path] = contents.encode('utf-8')

    def clear(self) -> None:
        """Test helper: Clear all files."""
        self._files.clear()
        self._directories.clear()

    def file_exists(self, path: str) -> bool:
        """Test helper: Check if file exists."""
        return path in self._files


class MockSecrets:
    """
    Mock implementation of dbutils.secrets.

    Provides:
    - get/getBytes for secret retrieval
    - list/listScopes for discovery
    """

    def __init__(self):
        self._secrets: Dict[str, str] = {}

    def get(self, scope: str, key: str) -> str:
        """Get secret value."""
        full_key = f"{scope}/{key}"
        if full_key not in self._secrets:
            raise ValueError(f"Secret '{key}' not found in scope '{scope}'")
        return self._secrets[full_key]

    def getBytes(self, scope: str, key: str) -> bytes:
        """Get secret as bytes."""
        return self.get(scope, key).encode('utf-8')

    def list(self, scope: str) -> List[Dict]:
        """List secrets in scope."""
        results = []
        for key in self._secrets:
            if key.startswith(f"{scope}/"):
                secret_key = key.split("/", 1)[1]
                results.append({"key": secret_key})
        return results

    def listScopes(self) -> List[Dict]:
        """List all scopes."""
        scopes = set()
        for key in self._secrets:
            scope = key.split("/")[0]
            scopes.add(scope)
        return [{"name": s} for s in scopes]

    # Test helper methods

    def set_secret(self, scope: str, key: str, value: str) -> None:
        """Test helper: Set a secret value."""
        self._secrets[f"{scope}/{key}"] = value

    def clear(self) -> None:
        """Test helper: Clear all secrets."""
        self._secrets.clear()


class MockDbutils:
    """
    Complete mock implementation of Databricks dbutils.

    Provides mocked implementations of:
    - dbutils.widgets: Widget parameter handling
    - dbutils.notebook: Notebook execution and exit
    - dbutils.fs: File system operations
    - dbutils.secrets: Secret management

    Usage:
        @pytest.fixture
        def mock_dbutils():
            return MockDbutils(defaults={
                "catalog": "test_catalog",
                "schema": "test_schema",
            })

        def test_notebook(mock_dbutils, patch_dbutils):
            value = dbutils.widgets.get("catalog")
            assert value == "test_catalog"
    """

    def __init__(self, defaults: Dict[str, str] = None):
        """
        Initialize MockDbutils.

        Args:
            defaults: Default widget values to set up
        """
        self._widget_defaults = defaults or {}
        self._widgets = MockWidgets(defaults)
        self._notebook = MockNotebook()
        self._fs = MockFs()
        self._secrets = MockSecrets()

    @property
    def widgets(self) -> MockWidgets:
        """Access widgets mock."""
        return self._widgets

    @property
    def notebook(self) -> MockNotebook:
        """Access notebook mock."""
        return self._notebook

    @property
    def fs(self) -> MockFs:
        """Access fs mock."""
        return self._fs

    @property
    def secrets(self) -> MockSecrets:
        """Access secrets mock."""
        return self._secrets

    def reset(self) -> None:
        """Reset all mock state to initial values."""
        self._widgets = MockWidgets(self._widget_defaults)
        self._notebook = MockNotebook()
        self._fs = MockFs()
        self._secrets = MockSecrets()


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_dbutils():
    """
    Provide a mock dbutils instance with default widget values.

    Default widgets:
    - catalog: "test_catalog"
    - gold_schema: "system_gold"
    - bronze_schema: "system_bronze"
    - feature_schema: "system_gold_features"

    Returns:
        MockDbutils instance
    """
    return MockDbutils(defaults={
        "catalog": "test_catalog",
        "gold_schema": "system_gold",
        "bronze_schema": "system_bronze",
        "feature_schema": "system_gold_features",
    })


@pytest.fixture
def patch_dbutils(mock_dbutils):
    """
    Patch dbutils into builtins for notebook execution.

    This allows notebooks to use `dbutils.widgets.get()` without modification.
    The mock is injected as a builtin global variable.

    Usage:
        def test_with_dbutils(mock_dbutils, patch_dbutils):
            # Now dbutils is available globally
            catalog = dbutils.widgets.get("catalog")
            assert catalog == "test_catalog"
    """
    import builtins
    original = getattr(builtins, 'dbutils', None)
    builtins.dbutils = mock_dbutils
    yield mock_dbutils
    if original is not None:
        builtins.dbutils = original
    else:
        try:
            delattr(builtins, 'dbutils')
        except AttributeError:
            pass


@pytest.fixture
def custom_dbutils():
    """
    Factory fixture for creating custom MockDbutils instances.

    Usage:
        def test_custom_widgets(custom_dbutils):
            my_dbutils = custom_dbutils(
                catalog="my_catalog",
                custom_param="custom_value",
            )
            assert my_dbutils.widgets.get("catalog") == "my_catalog"
    """
    def factory(**widget_values):
        return MockDbutils(defaults=widget_values)
    return factory
