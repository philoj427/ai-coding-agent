$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$tasksPath = Join-Path $root "pressure_tasks.txt"
$workspaceDir = Join-Path $root "workspace"
$taskFile = Join-Path $workspaceDir "task.txt"
$resultsDir = Join-Path $workspaceDir "pressure_results"
$reportPath = Join-Path $workspaceDir "pressure_test_report.md"

New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null

$tasks = Get-Content -LiteralPath $tasksPath | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") }

$report = New-Object System.Collections.Generic.List[string]
$report.Add("# Pressure Test Report")
$report.Add("")
$report.Add("Total tasks: $($tasks.Count)")
$report.Add("")

$passCount = 0
$failCount = 0

for ($i = 0; $i -lt $tasks.Count; $i++) {
    $taskNumber = $i + 1
    $taskText = $tasks[$i]
    $taskDir = Join-Path $resultsDir ("task_{0:D2}" -f $taskNumber)
    New-Item -ItemType Directory -Force -Path $taskDir | Out-Null

    Set-Content -LiteralPath $taskFile -Value $taskText -NoNewline

    $output = & python .\agent.py --root . --task workspace\task.txt --model qwen2.5-coder:7b 2>&1
    $exitCode = $LASTEXITCODE

    $testResultPath = Join-Path $workspaceDir "test_result.txt"
    $gitDiffPath = Join-Path $workspaceDir "git_diff.txt"
    $patchPath = Join-Path $workspaceDir "search_replace.patch"

    if (Test-Path $testResultPath) {
        Copy-Item -LiteralPath $testResultPath -Destination (Join-Path $taskDir "test_result.txt") -Force
    }
    if (Test-Path $gitDiffPath) {
        Copy-Item -LiteralPath $gitDiffPath -Destination (Join-Path $taskDir "git_diff.txt") -Force
    }
    if (Test-Path $patchPath) {
        Copy-Item -LiteralPath $patchPath -Destination (Join-Path $taskDir "search_replace.patch") -Force
    }

    $stage = ""
    $reason = ""
    if (Test-Path $testResultPath) {
        $lines = Get-Content -LiteralPath $testResultPath
        foreach ($line in $lines) {
            if ($line -like "Stage:*") { $stage = $line.Substring(7).Trim() }
            elseif ($line -like "Reason:*") { $reason = $line.Substring(8).Trim() }
        }
    }

    if ($exitCode -eq 0) {
        $passCount++
        $status = "PASS"
    } else {
        $failCount++
        $status = "FAIL"
    }

    $report.Add("## Task $taskNumber")
    $report.Add("")
    $report.Add("- Status: $status")
    $report.Add("- Exit code: $exitCode")
    $report.Add("- Task: $taskText")
    if ($stage) { $report.Add("- Stage: $stage") }
    if ($reason) { $report.Add("- Reason: $reason") }
    if ($output) {
        $report.Add("- Agent output: $($output -join ' ')" )
    }
    $report.Add("")

    git reset --hard HEAD | Out-Null
    git clean -fd | Out-Null
}

$report.Add("## Summary")
$report.Add("")
$report.Add("- Passed: $passCount")
$report.Add("- Failed: $failCount")
$report.Add("")

Set-Content -LiteralPath $reportPath -Value $report
