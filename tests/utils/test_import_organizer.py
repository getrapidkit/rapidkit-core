"""
Comprehensive tests for Import Organizer
=======================================

This module provides comprehensive test coverage for the import organizer service,
ensuring proper import sorting, deduplication, and file safety.
"""

import tempfile
import unittest
from pathlib import Path

from core.services.import_organizer import organize_imports


class TestImportOrganizer(unittest.TestCase):
    """Test cases for import organizer functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temp files
        for file in self.temp_dir.glob("*"):
            file.unlink()
        self.temp_dir.rmdir()

    def create_test_file(self, content: str, filename: str = "test.py") -> Path:
        """Create a test file with given content"""
        file_path = self.temp_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_organize_simple_imports(self):
        """Test organizing simple import statements"""
        content = """import os
import sys
import json
import os
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """import json
import os
import sys

"""
        self.assertEqual(result, expected)

    def test_organize_from_imports(self):
        """Test organizing from import statements"""
        content = """from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from typing import Optional
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

"""
        self.assertEqual(result, expected)

    def test_merge_duplicate_from_imports(self):
        """Test merging duplicate from imports"""
        content = """from typing import Dict
from typing import List
from typing import Dict
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """from typing import Dict, List

"""
        self.assertEqual(result, expected)

    def test_preserve_shebang(self):
        """Test preserving shebang lines"""
        content = """#!/usr/bin/env python3
import os
import sys
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """#!/usr/bin/env python3

import os
import sys

"""
        self.assertEqual(result, expected)

    def test_preserve_encoding_declaration(self):
        """Test preserving encoding declarations"""
        content = """# -*- coding: utf-8 -*-
import json
import os
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """# -*- coding: utf-8 -*-

import json
import os

"""
        self.assertEqual(result, expected)

    def test_skip_multiline_imports(self):
        """Test skipping files with multiline imports"""
        content = """import os
from typing import (
    Dict,
    List,
    Optional
)
import sys
"""
        file_path = self.create_test_file(content)

        original_content = content
        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        # Should remain unchanged due to multiline import
        self.assertEqual(result, original_content)

    def test_skip_line_continuation(self):
        """Test skipping files with line continuation"""
        content = """import os
import sys \\
    as system
import json
"""
        file_path = self.create_test_file(content)

        original_content = content
        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        # Should remain unchanged due to line continuation
        self.assertEqual(result, original_content)

    def test_skip_indented_imports(self):
        """Test skipping files with indented imports"""
        content = """def function():
    import os
    import sys
"""
        file_path = self.create_test_file(content)

        original_content = content
        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        # Should remain unchanged due to indented imports
        self.assertEqual(result, original_content)

    def test_mixed_imports_with_code(self):
        """Test organizing mixed imports with code"""
        content = """import os
import sys

def main():
    print("Hello world")

from pathlib import Path
import json
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """from pathlib import Path
import json
import os
import sys

def main():
    print("Hello world")

"""
        self.assertEqual(result, expected)

    def test_empty_file(self):
        """Test handling empty files"""
        content = ""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        self.assertEqual(result, content)

    def test_no_imports(self):
        """Test files with no imports"""
        content = """def function():
    pass

class MyClass:
    pass
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        self.assertEqual(result, content)

    def test_only_imports_no_blank_lines(self):
        """Test file with only imports and no blank lines"""
        content = """import os
import sys
import json"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """import json
import os
import sys

"""
        self.assertEqual(result, expected)

    def test_remove_leading_blank_lines(self):
        """Test removing leading blank lines after imports"""
        content = """

import os
import sys

def function():
    pass
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """import os
import sys

def function():
    pass
"""
        self.assertEqual(result, expected)

    def test_complex_from_import_with_parentheses(self):
        """Test skipping complex from imports with parentheses"""
        content = """from typing import(Dict, List)
import os
"""
        file_path = self.create_test_file(content)

        original_content = content
        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        # Should remain unchanged due to complex import
        self.assertEqual(result, original_content)

    def test_preserve_import_aliases(self):
        """Test preserving import aliases in plain imports"""
        content = """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""
        self.assertEqual(result, expected)

    def test_mixed_standard_library_and_third_party(self):
        """Test organizing mixed standard library and third-party imports"""
        content = """from mypackage import func
import os
from typing import List
import requests
import sys
"""
        file_path = self.create_test_file(content)

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        expected = """from mypackage import func
from typing import List
import os
import requests
import sys

"""
        self.assertEqual(result, expected)

    def test_organize_imports_complex_parentheses_import(self) -> None:
        """Test that complex imports with parentheses are left unchanged"""
        content = """from pathlib import Path
import os
from collections import (defaultdict, namedtuple)
import sys

def main():
    print("Hello world")
"""

        file_path = self.create_test_file(content, "complex_test.py")

        organize_imports(file_path)

        result = file_path.read_text(encoding="utf-8")
        # Complex import with parentheses should be left unchanged
        self.assertEqual(result, content)


if __name__ == "__main__":
    unittest.main()
