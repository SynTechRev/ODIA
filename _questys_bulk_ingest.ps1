# Bulk-ingest Questys File.ashx?id=N URLs from harvested manifest.
# Reads _questys_harvested_ids.json, POSTs each to /scrape-and-ingest-async,
# polls until complete, persists per-ID outcome to _questys_ingest_log.json.
#
# Concurrency: the backend already has a Semaphore(4) cap on _DOWNLOAD,
# so this script just keeps the queue topped up by submitting in waves.
# Designed to be RESUMABLE — re-runs skip IDs already in the log.

param(
    [int] $MaxToIngest = 0,       # 0 = all
    [int] $WaveSize = 6,           # submit this many at a time, poll, then more
    [int] $PollIntervalSec = 5,
    [int] $JobTimeoutSec = 600,
    [string[]] $ExtFilter = @('.pdf', '.doc', '.docx', '.html', '.htm', '.tif', '.tiff')
)

$ErrorActionPreference = 'Stop'
$token = (Get-Content "$env:APPDATA\ODIA\webhook_token" -Raw).Trim()
$hdr = @{ "x-odia-webhook-token" = $token; "Content-Type" = "application/json" }
$base = "http://127.0.0.1:8000/api/v1/webhook"
$file_base = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/File.ashx?id="

# --- Load manifest ---
$manifest = Get-Content "_questys_harvested_ids.json" -Raw | ConvertFrom-Json
$ids = @($manifest.ids.PSObject.Properties)
Write-Output "Loaded $($ids.Count) IDs from manifest"

# --- Load resume log ---
$logPath = "_questys_ingest_log.json"
$log = @{}
if (Test-Path $logPath) {
    $existing = Get-Content $logPath -Raw | ConvertFrom-Json
    foreach ($p in $existing.PSObject.Properties) {
        # NB: keep keys as STRINGS — ConvertTo-Json refuses int-keyed hashtables
        $log[$p.Name] = $p.Value
    }
    Write-Output "Resuming: $($log.Count) IDs already ingested"
}

# --- Filter ---
$todo = @()
foreach ($p in $ids) {
    $idStr = $p.Name  # keep as string
    if ($log.ContainsKey($idStr)) { continue }
    $meta = $p.Value
    $ext = ".$($meta.ext)"
    if ($ExtFilter -notcontains $ext) { continue }
    $todo += [pscustomobject]@{ id = $idStr; filename = $meta.filename; ext = $meta.ext }
}
if ($MaxToIngest -gt 0 -and $todo.Count -gt $MaxToIngest) {
    $todo = $todo | Select-Object -First $MaxToIngest
}
Write-Output "To ingest: $($todo.Count) IDs (after ext filter + resume skip)"

if ($todo.Count -eq 0) {
    Write-Output "Nothing to do. Exiting."
    return
}

# --- Wave loop ---
$start = Get-Date
$completed = 0
$failed = 0
$findings_total = 0

for ($i = 0; $i -lt $todo.Count; $i += $WaveSize) {
    $wave = $todo[$i..([Math]::Min($i + $WaveSize - 1, $todo.Count - 1))]
    $waveJobs = @()
    foreach ($item in $wave) {
        $url = "$file_base$($item.id)&v=1"
        $body = @{ url = $url; jurisdiction_id = "tulare-county" } | ConvertTo-Json -Compress
        try {
            $r = Invoke-RestMethod -Uri "$base/scrape-and-ingest-async" -Method Post -Headers $hdr -Body $body
            $waveJobs += [pscustomobject]@{ item = $item; job_id = $r.job_id; status = "submitted" }
        } catch {
            $log[$item.id] = @{ status = "submit_failed"; error = $_.Exception.Message; ts = (Get-Date).ToString("o") }
            $failed += 1
        }
    }

    # Poll wave
    $deadline = (Get-Date).AddSeconds($JobTimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $pending = $waveJobs | Where-Object { $_.status -ne "completed" -and $_.status -ne "failed" }
        if ($pending.Count -eq 0) { break }
        Start-Sleep -Seconds $PollIntervalSec
        foreach ($j in $pending) {
            try {
                $s = Invoke-RestMethod -Uri "$base/status/$($j.job_id)" -Headers $hdr -Method Get
                $j.status = $s.status
                if ($s.status -eq "completed" -or $s.status -eq "failed") {
                    $log[$j.item.id] = @{
                        status   = $s.status
                        sha256   = $s.sha256
                        filename = $j.item.filename
                        ext      = $j.item.ext
                        findings = if ($s.result.findings.count) { $s.result.findings.count } else { 0 }
                        bytes    = if ($s.result.document.byte_length) { $s.result.document.byte_length } else { 0 }
                        error    = $s.error
                        ts       = (Get-Date).ToString("o")
                    }
                    if ($s.status -eq "completed") {
                        $completed += 1
                        $findings_total += $log[$j.item.id].findings
                    } else {
                        $failed += 1
                    }
                }
            } catch {
                # transient poll error — try next loop
            }
        }
    }

    # Persist log every wave
    $log | ConvertTo-Json -Depth 4 | Set-Content -Path $logPath -Encoding utf8

    $elapsed = ((Get-Date) - $start).TotalSeconds
    $rate = if ($elapsed -gt 0) { ($completed + $failed) / $elapsed * 60 } else { 0 }
    Write-Output ("  wave {0:N0}/{1:N0}  completed={2}  failed={3}  findings_so_far={4}  rate={5:N1}/min  elapsed={6:N0}s" -f `
        ([Math]::Floor($i / $WaveSize) + 1), [Math]::Ceiling($todo.Count / $WaveSize), $completed, $failed, $findings_total, $rate, $elapsed)
}

Write-Output ""
Write-Output "=== BULK INGEST COMPLETE ==="
Write-Output ("  completed: {0}" -f $completed)
Write-Output ("  failed:    {0}" -f $failed)
Write-Output ("  total findings: {0}" -f $findings_total)
Write-Output ("  elapsed: {0:N0}s" -f ((Get-Date) - $start).TotalSeconds)
Write-Output ("  log saved: {0}" -f $logPath)
