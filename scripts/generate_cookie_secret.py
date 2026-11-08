"""Owner utility: generate a random OIDC cookie secret; run locally only."""
import secrets
if __name__ == '__main__':
    print(secrets.token_urlsafe(48))
