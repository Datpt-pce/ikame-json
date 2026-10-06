[CmdletBinding()]
param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$fileKey = "mmMqlJ5drO1IhYTaHDCm7f"
$rootNodeId = "6726:55902"
$projectDirectory = [System.IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot "..")
)
$sourceDirectory = Join-Path $projectDirectory "source"

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $sourceDirectory "figma-node-6726-55902.json"
}

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$allowedPrefix = $projectDirectory.TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
    [System.IO.Path]::DirectorySeparatorChar
if (-not $resolvedOutput.StartsWith(
        $allowedPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
    throw "Output path must remain inside $projectDirectory"
}

$tokenPath = Join-Path $env:LOCALAPPDATA "ikame-json\figma-token.dpapi"
if (-not (Test-Path -LiteralPath $tokenPath -PathType Leaf)) {
    throw "Encrypted Figma token was not found at the expected local path."
}

$encryptedToken = (Get-Content -LiteralPath $tokenPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($encryptedToken)) {
    throw "Encrypted Figma token file is empty."
}

$secureToken = ConvertTo-SecureString $encryptedToken
$tokenPointer = [System.IntPtr]::Zero
$plainToken = $null
$headers = $null

try {
    $tokenPointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR(
        $secureToken
    )
    $plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR(
        $tokenPointer
    ).Trim()
    if ($plainToken -notmatch "^[A-Za-z0-9_-]+$") {
        throw "Decrypted Figma token contains unsupported characters. Re-save the PAT without surrounding whitespace."
    }
    $headers = @{ "X-Figma-Token" = $plainToken }
    $encodedNodeId = [System.Uri]::EscapeDataString($rootNodeId)
    $uri = "https://api.figma.com/v1/files/$fileKey/nodes?ids=$encodedNodeId&geometry=paths"
    $response = Invoke-RestMethod `
        -Method Get `
        -Uri $uri `
        -Headers $headers `
        -TimeoutSec 60
}
finally {
    $headers = $null
    $plainToken = $null
    if ($tokenPointer -ne [System.IntPtr]::Zero) {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    }
}

$nodeRecord = $response.nodes.$rootNodeId
if ($null -eq $nodeRecord -or $null -eq $nodeRecord.document) {
    throw "Figma response did not include root node $rootNodeId."
}

[System.IO.Directory]::CreateDirectory(
    [System.IO.Path]::GetDirectoryName($resolvedOutput)
) | Out-Null

$payload = [ordered]@{
    file_key = $fileKey
    root_node_id = $rootNodeId
    name = $response.name
    version = $response.version
    last_modified = $response.lastModified
    document = $nodeRecord.document
    components = $nodeRecord.components
    component_sets = $nodeRecord.componentSets
    styles = $nodeRecord.styles
}

$json = $payload | ConvertTo-Json -Depth 100 -Compress
[System.IO.File]::WriteAllText(
    $resolvedOutput,
    $json,
    [System.Text.UTF8Encoding]::new($false)
)

$directChildren = @($nodeRecord.document.children).Count
Write-Output "Fetched Figma node $rootNodeId with $directChildren direct children."
Write-Output "Saved scoped source data to $resolvedOutput"
