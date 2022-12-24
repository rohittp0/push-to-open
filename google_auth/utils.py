import os
from dotenv import load_dotenv


def set_up():
    """Sets up configuration for the app"""

    load_dotenv()

    config = {
        "login_url": f"{os.getenv('LOGIN_URL')}&return_url={os.getenv('LOGIN_REDIRECT')}",
        "google": {
            "id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET")
        },
        "secret": os.getenv("APP_SECRET_KEY"),
        "domain": os.getenv("DOMAIN"),
        "protocol": os.getenv("PROTOCOL", "https://"),
        "port": os.getenv("PORT", 443),
        "db": os.getenv("DATABASE", "sqlite:///./test.db"),
        "form": os.getenv("REQUEST_FORM", "https://ugcsct.cusat.ac.in/")
    }

    return config


def get_login_js(client_id, api_location, swap_token_endpoint, success_route):
    google_login_javascript_client = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Google Login</title>
    </head>
        <body>
        <script src="https://accounts.google.com/gsi/client" async defer></script>
      <script>
        function onSignIn(id_token) {{
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '{api_location}{swap_token_endpoint}');
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.setRequestHeader('X-Google-OAuth2-Type', 'client');
                xhr.onload = () => location.href="{success_route}";
                xhr.send(id_token);
            }}
            
        function handleCredentialResponse(response) {{
          onSignIn(response.credential);
        }}
        
        window.onload = function () {{
          google.accounts.id.initialize({{
            client_id: "{client_id}",
            callback: handleCredentialResponse
          }});
          google.accounts.id.renderButton(
            document.getElementById("buttonDiv"),
            {{ theme: "outline", size: "large" }}  // customization attributes
          );
          google.accounts.id.prompt(); // also display the One Tap dialog
        }}
      </script>
    <div id="buttonDiv"></div> 
    </body>
    </html>"""

    return google_login_javascript_client
