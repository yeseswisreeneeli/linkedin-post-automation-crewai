################ Project Setup on Google Cloud Console ##################################

Step 1: Set Up Google Cloud Project
Go to the Google Cloud Console.

Click on the project drop-down and select "New Project."

Enter a project name and (optionally) organization, then create the project.

Step 2: Enable the Gmail API
With your project selected, go to APIs & Services > Library.

Search for "Gmail API" and click on it.

Click the Enable button.

Step 3: Configure OAuth Consent Screen
Navigate to APIs & Services > OAuth consent screen.

Choose the User type:

Select External (for consumer Gmail accounts) or Internal (for G Suite domains).

Fill in the required app information (App name, User support email, Developer email address, etc.).

If user type is External, proceed to testing (app is unverified initially).

Step 4: Add Test Users (If Required)
On the OAuth consent screen setup, scroll to Test users section.

Click Add users and enter the email addresses of anyone who will test the app (including your own Gmail).

Click Save and continue.

Step 5: Create OAuth 2.0 Client ID Credentials
Navigate to APIs & Services > Credentials.

Click + Create credentials > OAuth client ID.

Choose "Desktop app" (or the appropriate application type).

Name the client (e.g., "Gmail Client Dev").

Click Create and download the credentials.json file.

Step 6: Set Authorized Redirect URIs
When prompted during credential creation, ensure you add the correct redirect URIs.

For Python scripts using run_local_server, use http://localhost:XXXX/ (replace XXXX with the actual port if specified).

Save your settings.

Step 7: Set Up Your Python Script
Place your credentials.json in your project directory.

Update your script to use the correct SCOPES and file paths as shown earlier.

Ensure you have the required packages installed:

google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client.

Step 8: Run the Script and Complete OAuth
Run your Python script.

The script will open a browser to allow you to sign in and consent.

Sign in with the test user email you added.

Review and accept the requested permissions.

On success, a token.json file will be created locally for future use.

#############################################################################################
