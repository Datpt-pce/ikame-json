[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$fileKey = "mmMqlJ5drO1IhYTaHDCm7f"
$rootNodeId = "6726:55902"
$projectDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sourceDirectory = Join-Path $projectDirectory "source"
$planPath = Join-Path $sourceDirectory "figma-layer-plan.json"
$sourcePath = Join-Path $sourceDirectory "figma-node-6726-55902.json"
$assetDirectory = [System.IO.Path]::GetFullPath((Join-Path $sourceDirectory "figma-assets"))

foreach ($requiredPath in @($planPath, $sourcePath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required scoped Figma file is missing: $requiredPath"
    }
}

$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$source = Get-Content -LiteralPath $sourcePath -Raw | ConvertFrom-Json
if ($plan.file_key -ne $fileKey -or $source.file_key -ne $fileKey) {
    throw "Figma file key differs from the project allowlist."
}
if ($plan.root_node_id -ne $rootNodeId -or $source.root_node_id -ne $rootNodeId) {
    throw "Figma root node differs from the project allowlist."
}

$allowedNodeIds = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::Ordinal
)
function Add-SourceNodeIds {
    param([Parameter(Mandatory = $true)]$Node)
    [void]$allowedNodeIds.Add([string]$Node.id)
    foreach ($child in @($Node.children)) {
        if ($null -ne $child) {
            Add-SourceNodeIds -Node $child
        }
    }
}
Add-SourceNodeIds -Node $source.document

$exportNodeIds = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::Ordinal
)
foreach ($output in @($plan.outputs)) {
    foreach ($scene in @($output.scenes)) {
        foreach ($layer in @($scene.layers)) {
            if ($layer.kind -eq "image") {
                $nodeId = [string]$layer.node_id
                if ($nodeId -notmatch "^[A-Za-z0-9:;_-]+$") {
                    throw "Layer plan contains an invalid node id."
                }
                if (-not $allowedNodeIds.Contains($nodeId)) {
                    throw "Layer $nodeId is outside the fetched root subtree."
                }
                [void]$exportNodeIds.Add($nodeId)
            }
        }
    }
}

if ($exportNodeIds.Count -eq 0) {
    throw "Layer plan has no Figma nodes to export."
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
        throw "Decrypted Figma token contains unsupported characters."
    }
    $headers = @{ "X-Figma-Token" = $plainToken }
    $encodedIds = [System.Uri]::EscapeDataString(
        (($exportNodeIds | Sort-Object) -join ",")
    )
    $uri = "https://api.figma.com/v1/images/${fileKey}?ids=$encodedIds&format=png&scale=1&use_absolute_bounds=true"
    $response = Invoke-RestMethod `
        -Method Get `
        -Uri $uri `
        -Headers $headers `
        -TimeoutSec 120
}
finally {
    $headers = $null
    $plainToken = $null
    if ($tokenPointer -ne [System.IntPtr]::Zero) {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    }
}

if ($response.err) {
    throw "Figma layer export failed: $($response.err)"
}

[System.IO.Directory]::CreateDirectory($assetDirectory) | Out-Null
$downloaded = 0
foreach ($nodeId in ($exportNodeIds | Sort-Object)) {
    $imageUrl = [string]$response.images.$nodeId
    if ([string]::IsNullOrWhiteSpace($imageUrl)) {
        throw "Figma did not return an export URL for node $nodeId."
    }
    $parsedUrl = [System.Uri]$imageUrl
    if ($parsedUrl.Scheme -ne "https") {
        throw "Figma returned a non-HTTPS export URL."
    }
    $filename = $nodeId.Replace(":", "_").Replace(";", "_") + ".png"
    $destination = [System.IO.Path]::GetFullPath((Join-Path $assetDirectory $filename))
    $allowedPrefix = $assetDirectory.TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
        [System.IO.Path]::DirectorySeparatorChar
    if (-not $destination.StartsWith(
            $allowedPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        throw "Resolved asset path escaped the project asset directory."
    }
    Invoke-WebRequest -Uri $parsedUrl -OutFile $destination -TimeoutSec 120
    $downloaded += 1
}

Write-Output "Exported $downloaded direct Figma node assets into $assetDirectory"
