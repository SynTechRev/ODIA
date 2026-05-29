# v3.2.4 smoke test against real TCSO Drupal pages.
# Validates: semantic-container extraction yields non-empty text + nonzero findings.
$ErrorActionPreference = 'Stop'
$token = (Get-Content "$env:APPDATA\ODIA\webhook_token" -Raw).Trim()
$hdr = @{ "x-odia-webhook-token" = $token; "Content-Type" = "application/json" }
$base = "http://127.0.0.1:8000/api/v1/webhook"

$urls = @(
    "https://tularecounty.ca.gov/sheriff/media/news-releases/32-year-old-man-shoots-kills-father-leads-deputies-on-a-chase-then-shoots-himself",
    "https://tularecounty.ca.gov/sheriff/media/news-releases/heartbreak-decoy-detail-nets-eight-felony-arrests",
    "https://tularecounty.ca.gov/sheriff/media/news-releases/shooting-in-cutler-sends-one-to-the-hospital",
    "https://tularecounty.ca.gov/sheriff/media/news-releases/taco-truck-robbed-at-gunpoint",
    "https://tularecounty.ca.gov/sheriff/media/news-releases/tcso-detectives-investigating-early-morning-gas-station-robbery"
)

$jobs = @()
foreach ($u in $urls) {
    $body = @{ url = $u; jurisdiction_id = "tulare-county" } | ConvertTo-Json -Compress
    try {
        $r = Invoke-RestMethod -Uri "$base/scrape-and-ingest-async" -Method Post -Headers $hdr -Body $body
        $jobs += [pscustomobject]@{ url = ($u -split '/')[ -1 ]; job_id = $r.job_id; status = $r.status }
        Write-Output "POSTED $($r.job_id) <- $(($u -split '/')[ -1 ])"
    } catch {
        Write-Output "POST FAIL: $u -- $($_.Exception.Message)"
    }
}

Write-Output "`n--- polling ---"
$pending = $jobs | Where-Object { $_.status -ne 'completed' -and $_.status -ne 'failed' }
$start = Get-Date
$timeoutSec = 600
while ($pending.Count -gt 0 -and ((Get-Date) - $start).TotalSeconds -lt $timeoutSec) {
    Start-Sleep -Seconds 8
    foreach ($j in $pending) {
        try {
            $s = Invoke-RestMethod -Uri "$base/status/$($j.job_id)" -Headers $hdr -Method Get
            $j.status = $s.status
        } catch {
            $j.status = "poll-err"
        }
    }
    $done = ($jobs | Where-Object { $_.status -eq 'completed' -or $_.status -eq 'failed' }).Count
    Write-Output ("  elapsed={0:N0}s  done={1}/{2}" -f ((Get-Date) - $start).TotalSeconds, $done, $jobs.Count)
    $pending = $jobs | Where-Object { $_.status -ne 'completed' -and $_.status -ne 'failed' -and $_.status -ne 'poll-err' }
}

Write-Output "`n--- final ---"
foreach ($j in $jobs) {
    try {
        $s = Invoke-RestMethod -Uri "$base/status/$($j.job_id)" -Headers $hdr -Method Get
        $findings = if ($s.result.findings_count -ne $null) { $s.result.findings_count } else { $s.result.anomalies_count }
        $bytes = $s.result.byte_length
        $textChars = if ($s.result.text_length) { $s.result.text_length } else { 'n/a' }
        Write-Output ("  {0,-60} status={1,-10} bytes={2,-8} text_chars={3,-8} findings={4}" -f $j.url, $s.status, $bytes, $textChars, $findings)
    } catch {
        Write-Output "  $($j.url) ERR $($_.Exception.Message)"
    }
}
