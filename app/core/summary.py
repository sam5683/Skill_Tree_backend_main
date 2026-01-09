from datetime import datetime

def generate_summary(text: str) -> str:
    return f"REGENERATED @ {datetime.utcnow().isoformat()} | {text[:80]}"
