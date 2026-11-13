$ErrorActionPreference = 'Stop'
if (Test-Path '.env') { throw '.env already exists; refusing to overwrite it.' }
function New-HexSecret([int]$Bytes) {
    $data = [byte[]]::new($Bytes)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($data)
    return [Convert]::ToHexString($data).ToLowerInvariant()
}
$password = New-HexSecret 24
$token = New-HexSecret 32
@"
POSTGRES_DB=freelance_hunter
POSTGRES_USER=hunter_app
POSTGRES_PASSWORD=$password
DATABASE_URL=postgresql+asyncpg://hunter_app:${password}@db:5432/freelance_hunter
ADMIN_API_TOKEN=$token
LOG_LEVEL=INFO
"@ | Set-Content -Path '.env' -Encoding utf8NoBOM
Write-Host '.env created with random secrets. Do not commit it.'
