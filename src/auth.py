import os
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_access_token():
    """
    This script handles the 2-step OAuth2 process for Fyers V3.
    Step 1: Generate Auth URL
    Step 2: User logs in and provides the 'auth_code' from the redirect URL
    """
    client_id = os.getenv("FYERS_CLIENT_ID")
    secret_key = os.getenv("FYERS_SECRET_KEY")
    redirect_uri = os.getenv("FYERS_REDIRECT_URL")
    
    
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )

    # Step 1: Generate the auth URL
    auth_url = session.generate_authcode()
    print(f"\n1. Please login via this URL:\n{auth_url}\n")
    
    # Step 2: User provides the code from the browser
    auth_code = input("2. Paste the 'auth_code' from the URL here: ")
    
    session.set_token(auth_code)
    response = session.generate_token()
    
    if "access_token" in response:
        token = response["access_token"]
        # Save token to a file so we don't have to login again today
        with open("access_token.txt", "w") as f:
            f.write(token)
        print("\n✅ Access Token generated and saved to access_token.txt")
        return token
    else:
        print(f"❌ Error generating token: {response}")
        return None

if __name__ == "__main__":
    get_access_token()