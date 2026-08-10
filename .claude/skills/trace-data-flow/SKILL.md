---
name: trace-data-flow
description: Trace the execution path of a request or data flow through the repository, ordered by runtime sequence and grounded in actual code. Use this skill when asked to follow what happens from input to output.
---

Steps:
1. Clarify the entry point for the request or data flow (e.g. HTTP request, user action, tool call).
2. Locate the starting file and function using Read, Grep, and Glob.
3. Follow the call chain through handlers, services, tools, and responses.
4. Present the trace in execution order, not by file order.
5. Cite exact file paths and line ranges for every major step in the trace.
6. Identify the boundary where the repository hands off to external APIs, frameworks, or the browser.
