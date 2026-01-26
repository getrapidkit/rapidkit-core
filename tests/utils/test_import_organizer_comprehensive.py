# tests/test_import_organizer_comprehensive.py
"""Comprehensive tests for import organizer from end-user perspective."""

import tempfile
from pathlib import Path

from core.services.import_organizer import organize_imports


class TestImportOrganizerEndUser:
    """Test import organizer from end-user perspective."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_organize_simple_imports_end_user(self) -> None:
        """Test organizing simple import statements from end-user perspective."""
        # Create a Python file with disorganized imports
        content = """import os
import sys
from pathlib import Path
import json
from typing import List, Dict
import re

def main():
    print("Hello World")
"""

        test_file = self.project_root / "test_file.py"
        test_file.write_text(content)

        # Organize imports
        organize_imports(test_file)

        # Check that imports are organized
        result = test_file.read_text()
        lines = result.splitlines()

        # Should have imports first, then blank line, then code
        assert lines[0] == "from pathlib import Path"
        assert lines[1] == "from typing import Dict, List"
        assert lines[2] == "import json"
        assert lines[3] == "import os"
        assert lines[4] == "import re"
        assert lines[5] == "import sys"
        assert lines[6] == ""
        assert lines[7] == "def main():"

    def test_organize_imports_with_duplicates_end_user(self) -> None:
        """Test organizing imports with duplicates from end-user perspective."""
        content = """import os
from pathlib import Path
import os
from pathlib import Path
import json
from typing import List
from typing import Dict

print("Test")
"""

        test_file = self.project_root / "duplicate_imports.py"
        test_file.write_text(content)

        organize_imports(test_file)

        result = test_file.read_text()
        lines = result.splitlines()

        # Should merge duplicates and sort
        assert lines[0] == "from pathlib import Path"
        assert lines[1] == "from typing import Dict, List"
        assert lines[2] == "import json"
        assert lines[3] == "import os"
        assert lines[4] == ""
        assert lines[5] == 'print("Test")'

    def test_organize_imports_with_shebang_end_user(self) -> None:
        """Test organizing imports with shebang from end-user perspective."""
        content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import os

print("Script with shebang")
"""

        test_file = self.project_root / "script.py"
        test_file.write_text(content)

        organize_imports(test_file)

        result = test_file.read_text()
        lines = result.splitlines()

        # Should preserve shebang and encoding
        assert lines[0] == "#!/usr/bin/env python3"
        assert lines[1] == "# -*- coding: utf-8 -*-"
        assert lines[2] == ""
        assert lines[3] == "from pathlib import Path"
        assert lines[4] == "import os"
        assert lines[5] == "import sys"
        assert lines[6] == ""
        assert lines[7] == 'print("Script with shebang")'

    def test_organize_imports_skip_complex_end_user(self) -> None:
        """Test that complex imports are skipped from end-user perspective."""
        content = """import os
from typing import (
    List,
    Dict,
    Optional
)
import sys

print("Complex imports should be skipped")
"""

        test_file = self.project_root / "complex_imports.py"
        test_file.write_text(content)

        original_content = content
        organize_imports(test_file)

        # Should not modify file with complex imports
        result = test_file.read_text()
        assert result == original_content

    def test_organize_imports_skip_indented_end_user(self) -> None:
        """Test that indented imports are skipped from end-user perspective."""
        content = """import os
if True:
    import sys
    from pathlib import Path

print("Indented imports should be skipped")
"""

        test_file = self.project_root / "indented_imports.py"
        test_file.write_text(content)

        organize_imports(test_file)

        # Should organize top-level imports but leave indented ones alone
        expected = """import os

if True:
    import sys
    from pathlib import Path

print("Indented imports should be skipped")
"""

        result = test_file.read_text()
        assert result == expected

    def test_organize_imports_with_line_continuation_end_user(self) -> None:
        """Test that line continuation imports are skipped from end-user perspective."""
        content = """import os
import \\
    sys
from pathlib import Path

print("Line continuation should be skipped")
"""

        test_file = self.project_root / "line_continuation.py"
        test_file.write_text(content)

        original_content = content
        organize_imports(test_file)

        # Should not modify file with line continuation
        result = test_file.read_text()
        assert result == original_content

    def test_organize_imports_empty_file_end_user(self) -> None:
        """Test organizing imports in empty file from end-user perspective."""
        content = ""

        test_file = self.project_root / "empty.py"
        test_file.write_text(content)

        organize_imports(test_file)

        # Should remain unchanged
        result = test_file.read_text()
        assert result == content

    def test_organize_imports_no_imports_end_user(self) -> None:
        """Test organizing file with no imports from end-user perspective."""
        content = """def hello():
    print("Hello World")

class MyClass:
    pass
"""

        test_file = self.project_root / "no_imports.py"
        test_file.write_text(content)

        organize_imports(test_file)

        # Should remain unchanged
        result = test_file.read_text()
        assert result == content

    def test_organize_imports_mixed_content_end_user(self) -> None:
        """Test organizing imports with mixed content from end-user perspective."""
        content = '''"""Module docstring."""
import random
from collections import defaultdict
import json
from typing import Union, Optional

# Some comment
CONSTANT = "value"

def function():
    """Function docstring."""
    import os  # This should not be touched
    return "test"

class MyClass:
    """Class docstring."""
    def method(self):
        import sys  # This should not be touched
        pass
'''

        test_file = self.project_root / "mixed_content.py"
        test_file.write_text(content)

        organize_imports(test_file)

        result = test_file.read_text()
        lines = result.splitlines()

        # Should organize only top-level imports
        assert lines[0] == "from collections import defaultdict"
        assert lines[1] == "from typing import Optional, Union"
        assert lines[2] == "import json"
        assert lines[3] == "import random"
        assert lines[4] == ""
        assert lines[5] == '"""Module docstring."""'
        assert lines[6] == ""
        assert lines[7] == "# Some comment"

        # Should preserve indented imports
        assert "import os  # This should not be touched" in result
        assert "import sys  # This should not be touched" in result

    def test_organize_imports_with_aliases_end_user(self) -> None:
        """Test organizing imports with aliases from end-user perspective."""
        content = """import json as j
import os as o
from pathlib import Path as P
from typing import Dict as D

print("Imports with aliases")
"""

        test_file = self.project_root / "aliases.py"
        test_file.write_text(content)

        organize_imports(test_file)

        result = test_file.read_text()
        lines = result.splitlines()

        # Should preserve aliases
        assert lines[0] == "from pathlib import Path as P"
        assert lines[1] == "from typing import Dict as D"
        assert lines[2] == "import json as j"
        assert lines[3] == "import os as o"
        assert lines[4] == ""
        assert lines[5] == 'print("Imports with aliases")'

    def test_organize_imports_preserve_blank_lines_end_user(self) -> None:
        """Test that blank lines are handled properly from end-user perspective."""
        content = """import os


import sys
from pathlib import Path

def main():
    pass
"""

        test_file = self.project_root / "blank_lines.py"
        test_file.write_text(content)

        organize_imports(test_file)

        result = test_file.read_text()
        lines = result.splitlines()

        # Should organize imports and add proper spacing
        assert lines[0] == "from pathlib import Path"
        assert lines[1] == "import os"
        assert lines[2] == "import sys"
        assert lines[3] == ""
        assert lines[4] == "def main():"

    def test_organize_imports_real_world_example_end_user(self) -> None:
        """Test organizing imports in a real-world example from end-user perspective."""
        content = '''#!/usr/bin/env python3
"""
RapidKit CLI Tool
Main entry point for the rapidkit command-line interface.
"""
import argparse
import sys
from pathlib import Path
import json
from typing import Optional, List, Dict
import os

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="RapidKit CLI")
    parser.add_argument("--config", type=str, help="Configuration file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        print(f"Loading config from: {args.config}")

    # Load configuration
    config_path = Path(args.config) if args.config else Path("rapidkit.json")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}

    print("RapidKit CLI initialized")

if __name__ == "__main__":
    main()
'''

        test_file = self.project_root / "cli_tool.py"
        test_file.write_text(content)

        organize_imports(test_file)

        result = test_file.read_text()
        lines = result.splitlines()

        # Should have shebang first
        assert lines[0] == "#!/usr/bin/env python3"
        assert lines[1] == ""
        assert lines[2] == "from pathlib import Path"
        assert lines[3] == "from typing import Dict, List, Optional"
        assert lines[4] == "import argparse"
        assert lines[5] == "import json"
        assert lines[6] == "import os"
        assert lines[7] == "import sys"
        assert lines[8] == ""
        assert lines[9] == '"""'
        assert lines[10] == "RapidKit CLI Tool"
        assert lines[11] == "Main entry point for the rapidkit command-line interface."
        assert lines[12] == '"""'
