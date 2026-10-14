# A few design decisions

## Use synthetic data first

I use synthetic events because this is a student project and I do not have a real pharmaceutical dataset or permission to use patient data. This also makes it easier to repeat the same test.

## Use rules that can be inspected

The current signals come from configured thresholds. I can look at the input and rule to understand why a signal was produced. I have not added machine learning where a straightforward rule is enough for the current example.

## Keep it local for now

SQLite, a CLI and a small API are enough to test the workflow. A distributed setup would add work without helping me answer a current project question.

## Keep limitations visible

A generated flag is not proof of a real-world problem, a clinical conclusion or misconduct. The project needs better fixtures and more testing before any stronger claim would be reasonable.
