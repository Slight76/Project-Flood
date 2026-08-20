---
description: C# and .NET implementation guidance for source and project files.
applyTo: "**/*.cs,**/*.csproj,**/*.sln,**/*.slnx,**/Directory.Build.*"
---

# C# and .NET

- Match the repository's target framework, language version, analyzers, formatting, and nullable-reference policy.
- Prefer clear framework-native solutions over new abstractions or packages.
- Preserve dependency direction and use dependency injection only where it improves testability or established composition.
- Use async APIs end-to-end for I/O. Propagate `CancellationToken` across applicable public and internal boundaries.
- Validate at trust boundaries and return errors using the repository's established problem/error contract.
- Do not catch `Exception` unless adding context, translating at a boundary, or ensuring required cleanup; preserve stack traces.
- Use structured logging without secrets, tokens, credentials, or unnecessary personal data.
- Add focused tests for changed behavior and failure paths using the repository's existing test framework.
- Run the solution/project restore, format/analyzer, build, and relevant test commands documented in the project profile.
