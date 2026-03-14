# Feature: User Login

> Example feature flow document. Copy this as a starting point.

**Status**: ✅ Documented and Tested
**Last Updated**: 2025-01-08

---

## Overview

Authenticates a user with email and password, returning a session token.

## User Story

As a registered user, I want to log in with my email and password so that I can access my account.

---

## Entry Points

- **UI**: `src/frontend/src/views/Login.vue` - Login form submission
- **API**: `POST /api/auth/login`

---

## Frontend Layer

### Components

**Login.vue:45** - Form component
```vue
<form @submit.prevent="handleLogin">
  <input v-model="email" type="email" />
  <input v-model="password" type="password" />
  <button type="submit">Login</button>
</form>
```

**Login.vue:78** - Submit handler
```javascript
async handleLogin() {
  try {
    await authStore.login(this.email, this.password);
    this.$router.push('/dashboard');
  } catch (error) {
    this.error = error.message;
  }
}
```

### State Management

**stores/auth.js:23** - Login action
```javascript
async login(email, password) {
  const response = await api.post('/api/auth/login', { email, password });
  this.user = response.data.user;
  this.token = response.data.token;
}
```

### API Calls

```javascript
await api.post('/api/auth/login', {
  email: 'user@example.com',
  password: '********'
});
```

**Response**:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  },
  "token": "jwt_token_here"
}
```

---

## Backend Layer

### Endpoint

**src/backend/routes/auth.py:45** - Login handler
```python
@router.post("/api/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return {"user": user, "token": token}
```

### Business Logic

1. **Validate input**: Email format, password not empty
2. **Find user**: Query database by email
3. **Verify password**: Compare hash with stored hash
4. **Generate token**: Create JWT with user ID
5. **Return response**: User data and token

### Database Operations

**Query**: Find user by email
```sql
SELECT id, email, name, password_hash
FROM users
WHERE email = $1
```

**Update**: Record last login (optional)
```sql
UPDATE users
SET last_login_at = NOW()
WHERE id = $1
```

---

## Side Effects

- **Session Created**: New JWT token issued
- **Audit Log**: `event_type="auth", action="login", user_id="uuid"`
- **Metrics**: Login counter incremented

---

## Error Handling

| Error Case | HTTP Status | Message |
|------------|-------------|---------|
| Invalid email format | 400 | "Invalid email format" |
| User not found | 401 | "Invalid credentials" |
| Wrong password | 401 | "Invalid credentials" |
| Account locked | 403 | "Account is locked" |
| Server error | 500 | "Authentication failed" |

**Note**: Same message for "not found" and "wrong password" to prevent user enumeration.

---

## Security Considerations

- Password hashed with bcrypt (cost factor 12)
- Rate limiting: 5 attempts per minute per IP
- HTTPS required for all auth endpoints
- Token expiry: 24 hours
- Credentials never logged

---

## Testing

**Prerequisites**:
- [ ] Application running
- [ ] Test user exists (test@example.com / password123)

**Test Steps**:

### 1. Successful Login
**Action**:
- Navigate to /login
- Enter valid credentials
- Click "Login"

**Expected**: Redirect to /dashboard

**Verify**:
- [ ] User object in state
- [ ] Token in storage
- [ ] Dashboard loads

### 2. Invalid Password
**Action**:
- Enter valid email, wrong password
- Click "Login"

**Expected**: Error message displayed

**Verify**:
- [ ] "Invalid credentials" shown
- [ ] No redirect
- [ ] No token stored

### 3. Invalid Email
**Action**:
- Enter malformed email
- Click "Login"

**Expected**: Validation error

**Verify**:
- [ ] "Invalid email format" shown
- [ ] Form not submitted

**Edge Cases**:
- [ ] SQL injection in email field
- [ ] Very long password (10000 chars)
- [ ] Empty form submission
- [ ] Rapid repeated attempts (rate limiting)

**Last Tested**: 2025-01-08
**Tested By**: Claude Code
**Status**: All tests passing
**Issues**: None

---

## Related Flows

- **Upstream**: User Registration (creates account to log into)
- **Downstream**:
  - Dashboard (redirect after login)
  - Password Reset (alternative flow)
  - Logout (ends session)
