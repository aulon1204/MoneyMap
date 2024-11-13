# Skript: ExportProjektDetails.ps1

param (
    [string]$ProjektPfad = "C:\Users\aulon\Documents\Projekte\MoneyMap",
    [string]$AusgabeDatei = "C:\Users\aulon\Documents\Projekte\MoneyMap\ProjektExport.txt",
    [string[]]$AusschlussVerzeichnisse = @("venv", ".git", "__pycache__", ".pytest_cache", "node_modules", "dist", "build")
)

function Export-Project {
    param (
        [string]$CurrentPath,
        [int]$Level = 0
    )

    # Einrückung basierend auf der Verzeichnistiefe
    $Indent = "    " * $Level

    # Listet alle Elemente im aktuellen Verzeichnis auf
    $Items = Get-ChildItem -Path $CurrentPath | Sort-Object -Property PSIsContainer -Descending

    foreach ($Item in $Items) {
        # Überspringen von ausgeschlossenen Verzeichnissen
        if ($Item.PSIsContainer -and $AusschlussVerzeichnisse -contains $Item.Name) {
            continue
        }

        if ($Item.PSIsContainer) {
            # Verzeichnis anzeigen
            Add-Content -Path $AusgabeDatei -Value "$Indent+-- $($Item.Name)/"
            # Rekursiver Aufruf für Unterverzeichnisse
            Export-Project -CurrentPath $Item.FullName -Level ($Level + 1)
        }
        else {
            # Datei anzeigen
            Add-Content -Path $AusgabeDatei -Value "$Indent+-- $($Item.Name)"
            
            # Nur bestimmte Dateitypen exportieren (z.B. .py, .html, .css, .js, .json, .md)
            if ($Item.Extension -in @(".py", ".html", ".css", ".js", ".json", ".md", ".txt")) {
                Add-Content -Path $AusgabeDatei -Value "$Indent    --- Inhalt von $($Item.Name):"
                try {
                    $Inhalt = Get-Content -Path $Item.FullName -ErrorAction Stop
                    foreach ($Zeile in $Inhalt) {
                        # Zeilenumbrüche und spezielle Zeichen handhaben
                        $CleanZeile = $Zeile -replace "`r`n", "`n" -replace "`n", "`n"
                        Add-Content -Path $AusgabeDatei -Value "$Indent    $Zeile"
                    }
                }
                catch {
                    Add-Content -Path $AusgabeDatei -Value "$Indent    [Fehler beim Lesen der Datei]"
                }
            }
        }
    }
}

# Initialisieren der Ausgabedatei
if (Test-Path $AusgabeDatei) {
    Remove-Item -Path $AusgabeDatei
}
New-Item -Path $AusgabeDatei -ItemType File -Force | Out-Null

# Start der Export-Funktion
Export-Project -CurrentPath $ProjektPfad

Write-Output "Export abgeschlossen. Überprüfen Sie die Datei: $AusgabeDatei"
