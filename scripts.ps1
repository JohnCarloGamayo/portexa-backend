param(
    [switch]$Migrate,
    [switch]$Run
)

if ($Migrate) {
    python -m alembic upgrade head
}

if ($Run) {
    python -m uvicorn app.main:app --reload
}
