"""CLI tool to generate secure secrets for .env file."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.secrets import generate_env_template, SecretsValidator


def main():
    """Generate secure .env file with random secrets."""
    print("=" * 70)
    print("News Tunneler - Secure Secrets Generator")
    print("=" * 70)
    print()
    print("This tool generates a .env file with cryptographically secure secrets.")
    print()
    
    # Check if .env already exists
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    if os.path.exists(env_path):
        print(f"⚠️  Warning: .env file already exists at {env_path}")
        response = input("Do you want to overwrite it? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Aborted. No changes made.")
            return
    
    # Generate template
    template = generate_env_template()
    
    # Write to file
    with open(env_path, 'w') as f:
        f.write(template)
    
    print()
    print(f"✅ Secure .env file generated at: {env_path}")
    print()
    print("IMPORTANT:")
    print("  1. Review the generated file and update API keys as needed")
    print("  2. Never commit this file to version control")
    print("  3. Store secrets securely (use a password manager)")
    print("  4. Rotate secrets regularly in production")
    print()
    print("Generated secrets:")
    print("  - JWT_SECRET_KEY: 64 characters")
    print("  - POSTGRES_PASSWORD: 32 characters")
    print("  - ADMIN_TOKEN: 32 characters")
    print()


if __name__ == "__main__":
    main()

