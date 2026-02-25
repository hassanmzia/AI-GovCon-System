# Admin Setup and User Management Guide

This guide explains how to create admin accounts, manage users, and understand the role-based access control system.

## User Roles

The system supports 9 different user roles:

1. **Admin** - Full system access, can manage all users and settings
2. **Executive** - Executive-level access to reports and strategic data
3. **Capture Manager** - Manages opportunity capture process
4. **Proposal Manager** - Manages proposal creation and review
5. **Pricing Manager** - Manages pricing scenarios and cost models
6. **Writer** - Can create and edit proposals and documents
7. **Reviewer** - Can review and provide feedback on documents
8. **Contracts Manager** - Manages contract creation and tracking
9. **Viewer** (Default) - Read-only access to most data

## Creating an Admin User

### Method 1: Using Django Management Command (Recommended)

```bash
cd backend
python manage.py create_user admin_username \
  --email admin@example.com \
  --password "secure_password_here" \
  --first-name "Admin" \
  --last-name "User" \
  --role admin
```

### Method 2: Using Django Shell

```bash
cd backend
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.create_user(
    username='admin_username',
    email='admin@example.com',
    password='secure_password_here',
    first_name='Admin',
    last_name='User',
    role='admin'
)
print(f"Created user: {user}")
```

### Method 3: Using Django Admin Interface

If you have Django admin set up:

```bash
python manage.py createsuperuser
```

Then log in to `/admin` and edit the user's role field.

## Creating Other User Types

### Create an Executive User

```bash
python manage.py create_user executive_username \
  --email executive@example.com \
  --password "password" \
  --first-name "Executive" \
  --last-name "User" \
  --role executive
```

### Create a Proposal Manager

```bash
python manage.py create_user proposal_mgr \
  --email proposal@example.com \
  --password "password" \
  --role proposal_manager
```

### Create a Viewer (Read-only User)

```bash
python manage.py create_user viewer_user \
  --email viewer@example.com \
  --password "password" \
  --role viewer
```

## Making a User a Django Admin (Superuser)

To grant a user full Django admin access:

```bash
python manage.py create_user admin_name \
  --email admin@example.com \
  --password "password" \
  --role admin \
  --is-staff \
  --is-superuser
```

## Authenticating via API

### 1. Get Authentication Token

Make a POST request to `/api/auth/token/`:

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_username",
    "password": "secure_password_here"
  }'
```

Response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Use Access Token in Requests

Include the access token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### 3. Refresh Token (When Access Token Expires)

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

## Role-Based Permissions

### Permission Classes Used

- **IsAdmin**: Only Admin users
- **IsExecutiveOrAbove**: Admin or Executive
- **IsCaptureManager**: Admin, Executive, or Capture Manager
- **IsProposalManager**: Admin, Executive, or Proposal Manager
- **IsViewerReadOnly**: All authenticated users; viewers can only read

### Typical Permission Setup

Most endpoints use:
- `[IsAuthenticated]` - Any authenticated user can access
- `[IsAuthenticated, IsAdmin]` - Only admins
- `[IsAuthenticated, IsViewerReadOnly]` - Non-viewers can create/edit, viewers can only read

## Troubleshooting

### Getting 401 Unauthorized Error

**Problem**: "401 (Unauthorized)" responses when trying to access endpoints

**Solutions**:
1. Ensure you have obtained a valid access token
2. Verify the token is included in the `Authorization: Bearer <token>` header
3. Check if the token has expired (access tokens last 60 minutes by default)
4. Use the refresh token to get a new access token

### User Can't Access Pages

**Problem**: Authenticated user getting access denied

**Possible Causes**:
1. User role doesn't have permissions for that endpoint
2. User is a "viewer" - viewers have read-only access only
3. Endpoint requires a specific role (admin, proposal_manager, etc.)

**Solution**:
- Check the user's role: `python manage.py shell` then `User.objects.get(username='username').role`
- Update the role: `user.role = 'admin'` then `user.save()`

### Changing a User's Role

```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='username')
user.role = 'admin'  # or 'executive', 'proposal_manager', etc.
user.save()
print(f"Updated {user.username} to {user.get_role_display()}")
```

## API Endpoints for User Management

- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/token/` - Get authentication tokens
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/me/` - Get current user info
- `PUT /api/auth/me/` - Update current user
- `GET /api/accounts/users/` - List all users (admin only)
- `POST /api/accounts/change-password/` - Change password
- `POST /api/accounts/mfa/setup/` - Setup MFA
- `POST /api/accounts/mfa/disable/` - Disable MFA

## Default Settings

- Access Token Lifetime: 60 minutes
- Refresh Token Lifetime: 7 days
- New user default role: VIEWER (read-only)
- Password requirements: Django defaults (minimum length, complexity if configured)

## Security Best Practices

1. **Never commit passwords** to version control
2. **Use strong passwords** with mixed case, numbers, and special characters
3. **Change default admin password** immediately in production
4. **Enable MFA** for admin accounts
5. **Rotate refresh tokens** regularly
6. **Restrict API access** using role-based permissions
7. **Monitor user activity** and audit logs

## Environment Variables

Set these in your `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```
