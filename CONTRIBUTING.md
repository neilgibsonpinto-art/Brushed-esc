# Contributing to STMESC

Thank you for your interest in improving the **STMESC Dual-Motor Brushed ESC** project!

## How to Contribute

1. **Reporting Issues & Bugs**:
   - Open a detailed issue on GitHub describing the bug or electrical behavior.
   - Include battery voltage, motor specs, and steps to reproduce.
   - For hardware/PCB bugs, cite the specific net, schematic sheet, or component designator.

2. **Suggesting Improvements**:
   - Feature requests, firmware enhancements, or alternative component suggestions are welcome via GitHub Issues.

3. **Submitting Changes (Pull Requests)**:
   - Fork the repository and create a feature branch (`git checkout -b feature/awesome-feature`).
   - Use KiCad 9 or KiCad 10 for all schematic and PCB layout modifications.
   - Run the automated test script before committing:
     ```bash
     python scripts/run_all_tests_and_generate_report.py
     ```
   - Ensure KiCad ERC and DRC pass without introducing new violations.
   - Submit a pull request with a clear description of your changes.

## License

By contributing to this repository, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
