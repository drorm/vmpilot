# VMPilot Code Review Plugin

This plugin provides guidelines for conducting code reviews within the VMPilot project, primarily utilizing LLM assistance to ensure code quality, consistency, and maintainability before merging feature branches into the development branch.

## Purpose

The primary goal of this code review process is to:
- Maintain a high standard of code quality across the project.
- Ensure consistency in coding style and practices.
- Improve code readability and maintainability.
- Catch potential bugs, logic errors, or design issues early.
- Verify adherence to project standards and requirements (as outlined in relevant issues like #6).

## Scope

This review process applies mainly to Python code within the VMPilot source (`/home/dror/vmpilot/src/vmpilot`). The review combines automated checks with LLM-assisted analysis based on the guidelines below.

## Code Review Process

1.  **Automated Checks (Developer Responsibility):**
    *   Before requesting a review, developers should ensure their code passes the configured pre-commit hooks.
    *   Currently, `black` (formatting) and `isort` (import sorting) are enforced via pre-commit.
    *   Additional linting tools like `flake8` or `ruff` will be integrated in the future.
    *   Passing these checks is a prerequisite for an effective LLM review.
    *   Note: `mypy` (type checking) is targeted for integration in Q2 2025 but is not yet part of the automated pre-commit checks. Developers should still strive for type correctness.

2.  **Review Initiation (User Driven):**
    *   A code review is initiated manually by the user (developer or maintainer) by prompting the LLM.
    *   The user must provide sufficient context for the review (see "How to Request a Review" below).

3.  **LLM Review Role:**
    *   The LLM analyzes the specified code based on the "Key Review Areas" outlined in this document.
    *   The review focuses on identifying deviations from standards, potential issues, and areas for improvement.
    *   The LLM provides feedback based *only* on the provided code and context.

## Key Review Areas

When requested to perform a code review, the LLM should focus on the following aspects:

1.  **Style Guide Adherence & Linting:**
    *   Verify code formatting generally aligns with `black`.
    *   Check that imports are sorted according to `isort` with the Black profile.
    *   Assess adherence to Google Python Style Guide principles, even though automated linting with `ruff` or `flake8` is not yet fully implemented.
2.  **Type Checking:**
    *   Assess the presence and correctness of type annotations (`mypy`).
    *   Identify missing annotations or potential type mismatches, even if `mypy` checks are not fully automated in CI yet.
3.  **Functionality & Logic:**
    *   Does the code seem to logically implement the intended feature or fix, based on the provided context (e.g., associated issue description)?
    *   Are there any obvious logic errors, off-by-one errors, or incorrect assumptions?
4.  **Readability & Maintainability:**
    *   Is the code clear, well-structured, and easy to understand?
    *   Are variable and function names descriptive?
    *   Is the code overly complex? Could it be simplified?
5.  **Documentation:**
    *   Are there adequate docstrings for modules, classes, functions, and methods?
    *   Are comments used effectively to explain complex or non-obvious code sections?
6.  **Testing:**
    *   Does the submitted code include corresponding unit or end-to-end tests? (Refer to the Testing Plugin guidelines).
    *   Do the tests seem adequate for the changes introduced?
7.  **Error Handling:**
    *   Does the code handle potential errors and exceptions gracefully?
    *   Are `try...except` blocks used appropriately?
8.  **Efficiency & Security:**
    *   Are there any *obvious* performance bottlenecks (e.g., loops performing expensive operations unnecessarily)?
    *   Are there any *obvious* security concerns (e.g., hardcoded secrets, potential injection points - context permitting)? (Note: This is not a full security audit).

## Tools and Standards

-   **Formatter:** `black`
-   **Formatters/Linters:** `black`, `isort`, and planned integration of `flake8` or `ruff`
-   **Type Checker:** `mypy` (planned for future integration)
-   **Style Guide:** Google Python Style Guide (target, to be enforced via linting rules)
-   **Configuration:** Managed via `pyproject.toml` and pre-commit hooks (`.pre-commit-config.yaml`).

## How to Request a Review

Provide the LLM with clear context. Examples:

*   "Look at Issue #<ISSUE_NUMBER> and do a diff dev. Look at the code review plugin and perform a code review."
*   "Review the file `/path/to/changed/file.py` according to the Code Review plugin README. Focus on readability and type checking."

**Essential Context:**
-   Issue number.
-   Any particular areas of concern.

## Best Practices for Code Submission

To facilitate effective reviews:

-   Run pre-commit hooks locally (`pre-commit run --all-files`) and fix issues before pushing.
-   Keep review focused on a single issue or feature.
-   Reference the relevant GitHub issue(s)
-   Ensure adequate tests are included for the changes.
-   Add comments for complex logic.
