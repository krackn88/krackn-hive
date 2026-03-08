from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    stdout: str
    stderr: str = ""


class FakeSoftwareTools:
    def propose_patch(self, goal: str) -> ToolResult:
        return ToolResult(ok=True, stdout=f"patch-for:{goal}")

    def run_tests(self) -> ToolResult:
        return ToolResult(ok=True, stdout="tests: PASS")
