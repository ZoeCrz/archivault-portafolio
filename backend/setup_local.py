"""Create local development secrets once; refuses to overwrite existing settings."""
from pathlib import Path
import secrets


def main():
    root = Path(__file__).resolve().parent
    template = (root / '.env.example').read_text()
    replacements = {
        'replace-with-a-long-random-secret': secrets.token_urlsafe(64),
        'replace-with-an-independent-webhook-secret': secrets.token_urlsafe(64),
        'YOUR_DB_PASSWORD': secrets.token_hex(24),
        'YOUR_ROOT_PASSWORD': secrets.token_hex(24),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    with (root / '.env').open('x') as output:
        output.write(template)
    frontend = root.parent / 'frontend' / '.env'
    if not frontend.exists():
        with frontend.open('x') as output:
            output.write('VITE_API_URL=http://localhost:8000\n')
    print('Configuración local creada. No publiques los archivos .env.')


if __name__ == '__main__':
    main()
