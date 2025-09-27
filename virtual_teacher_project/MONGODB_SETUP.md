# MongoDB Atlas Setup Instructions for GnyanSetu

## Quick Setup (5 minutes):

1. Go to: https://cloud.mongodb.com/
2. Click "Try Free" and create an account
3. Create a new project called "GnyanSetu"
4. Create a free cluster (M0 Sandbox)
5. Choose AWS, region closest to you
6. Name your cluster "gnyansetu-cluster"

## Security Setup:

1. **Database Access:**

   - Click "Database Access" in left sidebar
   - Click "+ Add New Database User"
   - Username: gnyansetu_user
   - Password: (generate a secure password)
   - Database User Privileges: Read and write to any database
   - Click "Add User"

2. **Network Access:**

   - Click "Network Access" in left sidebar
   - Click "+ Add IP Address"
   - Click "Allow Access from Anywhere" (for development)
   - Click "Confirm"

3. **Get Connection String:**
   - Go back to "Clusters"
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Select "Python" and version "3.6 or later"
   - Copy the connection string

## After you get the connection string, I'll update the project configuration.

The connection string will look like:
mongodb+srv://gnyansetu_user:<password>@gnyansetu-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority

Replace <password> with your actual password.
