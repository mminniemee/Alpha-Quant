import os
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv

load_dotenv()

def get_fyers_model(access_token=None):
    """
    Initializes the Fyers V3 Model.
    In V3, the client_id is your 'App ID'.
    """
    client_id = os.getenv("FYERS_CLIENT_ID") # This is your App ID
    
    if access_token:
        # Initializing the fyers model with the provided access_token
        return fyersModel.FyersModel(
            client_id=client_id, 
            token=access_token, 
            is_async=False, 
            log_path=os.getcwd()
        )
    return None

def generate_auth_url():
    """
    Generates the login URL for V3.
    """
    client_id = os.getenv("FYERS_CLIENT_ID")
    redirect_uri = os.getenv("FYERS_REDIRECT_URL")
    secret_key = os.getenv("FYERS_SECRET_KEY")
    
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )
    return session.generate_authcode()