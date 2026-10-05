param(
    [Parameter(Mandatory = $true)][string]$Link,
    [Parameter(Mandatory = $true)][string]$Target
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Target -PathType Container)) {
    throw "Junction target is not a directory: $Target"
}
if (Test-Path -LiteralPath $Link) {
    throw "Junction path already exists: $Link"
}
New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null
