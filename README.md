# 26fit-monitor

Monitor da ocupação (API 26fit) com notificação no Discord via [GitHub Actions](.github/workflows/monitor.yml).

Configure o secret `DISCORD_WEBHOOK_URL` no repositório (Settings → Secrets → Actions).

Localmente:

```powershell
$env:DISCORD_WEBHOOK_URL="<seu-webhook>"
python monitor.py
```

Variável opcional: `OCCUPANCY_BRANCH_ID` (padrão `4` = Sapiranga).
