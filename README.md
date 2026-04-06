# Deployed App Link - https://aventisia.onrender.com/docs

# Instructions to use the deployed app - 
Click on the link to go to the app's OpenAPI documentation.
Instructions are well provided in the WebPage itself for authentication.
After authentication, you can go on further to check for :
  1. List Repos
  2. List Issues
  3. Create Issues

# In case you want to set things up on your personal computer(advised to use the Deployed app) -
If you prefer to run the application locally rather than using the deployed app, follow these steps:

1. Clone and Extract: Download and extract the repository zip file.

2. Environment Configuration: 

    a. In the extracted folder - Create a file named .env
  
    b. Add the following variables (obtained from your GitHub Developer Settings):

  
        GITHUB_CLIENT_ID=your_client_id
      
        GITHUB_CLIENT_SECRET=your_client_secret
      
        GITHUB_REDIRECT_URI=http://127.0.0.1:8000/auth/callback
      
        SESSION_SECRET=your_random_session_secret

    
3. Install Dependencies:
   
    In terminal run

          python -m venv venv
       
          source venv/bin/activate  # On Windows use: venv\Scripts\activate
       
          pip install -r requirements.txt
  
5. Running the app :
    
        python -m uvicorn main:app --reload --port 8000


# The Endpoints - 
1. The Endpoints of Authentications are - /auth/login & /auth/callback 
2. The Endpoints of getting repositories list is - /repos
3. The Endpoints of creating issues and getting issues list is - /create-issues & /list-issues
4. Every request is a GET request except for creating issues which is a POST request.
