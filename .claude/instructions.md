# AI model guidelines

1. Document architecture decisions in README.md. Write down the most important patterns and decisions.
2. Use always TDD when developing
    1. Write tests first.
    2. Run them to verify they fail.
    3. Write the code to make them pass.
2. Make the smallest changes possible.
3. Have fast feedback loops. Always use text boxes for approval or rejection so I can give feedback.
4. Focus on the most essential parts. Do not give verbose feedback if not asked.
5. Only stage commits, do not commit on your own. Do not push to the repository.
6. Always use a docker environment to execute or test the code.

## Project-specific

1. This project contains documentation only with security relevant information.
2. Documentation is in latex format.
3. Use the `Makefile` to build the documents.