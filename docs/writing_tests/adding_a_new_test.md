# Adding a New Test

All test cases are located underneath the `tests` directory, which are then organized by fork. Each fork contains sub-directories containing test sub-categories.

```text
📁 execution-test-specs/
├─╴📁 tests/
|   ├── 📄 __init__.py
│   ├── 📁 cancun/
|   |    ├── 📄 __init__.py
│   |    └── 📁 eip4844_blobs/
|   |        ├── 📄 __init__.py
|   |        ├── 📄 test_blobhash_opcode.py
|   |        ├── 📄 test_excess_blob_gas.py
|   |        └── 📄 ...
|   ├── 📁 shanghai
|   |    ├── 📄 __init__.py
|   |    ├── 📁 eip3651_warm_coinbase
|   |    |   ├── 📄 __init__.py
|   |    |   └── 📄 test_warm_coinbase.py
|   |    ├── 📁 eip3855_push0
|   |    |   ├── 📄 __init__.py
|   |    |   └── 📄 test_push0.py
|   |    ├── 📁...
|   |    ...
|   ├── 📁 frontier
|   |    ├── 📄 __init__.py
|   |    ├── 📁 opcodes
|   |    |   ├── 📄 __init__.py
|   |    |   └── 📄 test_dup.py
|   |    |   └── 📄 test_call.py
|   |    |   └── 📄 ...
|   |    ├── 📁...
│   └── 📁 ...
```

Each fork/sub-directory may have multiple Python test modules (`*.py`) which in turn may contain many test functions. The test functions themselves are always parametrized by fork (by the framework). In general, sub-directories can be feature categories such as opcodes or eips.

A new test can be added by either:

- Adding a new `test_` python function to an existing file in any of the existing category subdirectories within `tests`.
- Creating a new source file in an existing category, and populating it with the new test function(s).
- Creating an entirely new category by adding a subdirectory in `tests` with the appropriate source files and test functions.

!!! note "Which fork does my test belong?"
    Tests should be added to the fork folder where the feature or EIP was introduced. For example, if the callcode opcode is being tested it should be added to the
    Frontier fork folder as this opcode was first introduced in Frontier. This remains true for cases where the test is [valid from](../writing_a_new_test/#specifying-which-forks-tests-are-valid-for) a later fork, such as a callcode specific bug introduced in London.
