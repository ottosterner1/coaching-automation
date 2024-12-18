from authlib.integrations.flask_client import OAuth
from authlib.jose import jwk
from flask import current_app
import boto3
import requests
from botocore.exceptions import NoCredentialsError

oauth = OAuth()

def fetch_jwks(jwks_uri):
    """Fetch and parse JWKS from the provided URI"""
    try:
        response = requests.get(jwks_uri)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        return None

def init_oauth(app):
    oauth.init_app(app)

    try:
        # Construct base URLs
        region = app.config['AWS_COGNITO_REGION']
        user_pool_id = app.config['AWS_COGNITO_USER_POOL_ID']
        cognito_domain = app.config['COGNITO_DOMAIN']
        
        # Construct all required URIs
        base_url = f"https://{cognito_domain}"
        jwks_uri = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        
        # Fetch JWKS
        jwks = fetch_jwks(jwks_uri)
        if not jwks:
            raise Exception("Failed to fetch JWKS")

        print(f"Initializing OAuth with:")
        print(f"Base URL: {base_url}")
        print(f"JWKS URI: {jwks_uri}")

        oauth.register(
            name='cognito',
            client_id=app.config['AWS_COGNITO_CLIENT_ID'],
            client_secret=app.config['AWS_COGNITO_CLIENT_SECRET'],
            access_token_url=f"{base_url}/oauth2/token",
            access_token_params=None,
            authorize_url=f"{base_url}/oauth2/authorize",
            authorize_params=None,
            api_base_url=base_url,
            client_kwargs={
                'scope': 'email openid profile',
                'token_endpoint_auth_method': 'client_secret_post',
            },
            jwks=jwks,
            # Add server metadata URL for OpenID configuration
            server_metadata_url=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
        )
        
        print("OAuth client registered successfully")
        print(f"JWKS configured with {len(jwks.get('keys', [])) if jwks else 0} keys")
        
    except NoCredentialsError:
        print("AWS credentials not found. Please check your configuration.")
        raise
    except Exception as e:
        print(f"Error during OAuth initialization: {str(e)}")
        raise

    return oauth

def get_jwks():
    """Helper function to get JWKS for token validation"""
    cognito = oauth.create_client('cognito')
    if not cognito:
        raise Exception("Cognito client not initialized")
    return cognito.jwks