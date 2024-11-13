# Skript: Get-CustomTree.ps1

param (
    [string]$Path = "C:\Users\aulon\Documents\Projekte\MoneyMap",
    [int]$MaxDepth = 3,
    [string[]]$Exclude = @("node_modules", "dist", "build", ".git")
)

function Get-CustomTree {
    param (
        [string]$CurrentPath,
        [int]$CurrentDepth,
        [int]$MaxDepth,
        [string[]]$Exclude
    )

    if ($CurrentDepth -gt $MaxDepth) {
        return
    }

    $items = Get-ChildItem -Path $CurrentPath | Where-Object {
        -not ($_.PSIsContainer -and $Exclude -contains $_.Name)
    }

    foreach ($item in $items) {
        # Einrückung basierend auf der Tiefe
        $indent = ("    " * ($CurrentDepth - 1)) + "+-- "
        Write-Output "$indent$item"

        if ($item.PSIsContainer) {
            Get-CustomTree -CurrentPath $item.FullName -CurrentDepth ($CurrentDepth + 1) -MaxDepth $MaxDepth -Exclude $Exclude
        }
    }
}

# Start des Skripts
Write-Output (Split-Path $Path -Leaf)
Get-CustomTree -CurrentPath $Path -CurrentDepth 1 -MaxDepth $MaxDepth -Exclude $Exclude
