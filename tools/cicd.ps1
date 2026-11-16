param(
    [ValidateSet('status', 'start', 'stop', 'backup')]
    [string]$Action = 'status'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $repoRoot 'docker-compose.yml'
$composeArgs = @('compose', '-p', 'telecom-alert-correlation-n42', '-f', $composeFile)
$volumeNames = @(
    'n42-cicd_jenkins_data', 'n42-cicd_sonar_data',
    'n42-cicd_sonar_extensions', 'n42-cicd_sonar_logs',
    'telecom-alert-correlation-n42_n42-db-data'
)
foreach ($volumeName in $volumeNames) {
    docker volume inspect $volumeName --format '{{.Name}}'
    if ($LASTEXITCODE -ne 0) { throw "Missing existing volume: $volumeName. Stop and restore the backup first." }
}
switch ($Action) {
    'status' { docker @composeArgs ps }
    'start' { docker @composeArgs up -d db sonarqube jenkins }
    'stop' { docker @composeArgs stop jenkins sonarqube db }
    'backup' { python (Join-Path $PSScriptRoot 'backup_lab.py') }
}
if ($LASTEXITCODE -ne 0) { throw "CI/CD operation failed: $Action" }
