# Frontend Guide 02: Authentication

> **Purpose**: Secure authentication patterns for the Health Monitor Agent
> 
> **Audience**: Frontend developers implementing user authentication
> 
> **Time to Implement**: 30 minutes - 2 hours (depending on architecture)

---

## Authentication Overview

The Health Monitor Agent uses **On-Behalf-Of-User (OBO) authentication**, meaning:

- ✅ Queries execute with **the end user's permissions**
- ✅ Each user sees only data they have access to
- ✅ Unity Catalog permissions are enforced
- ✅ Actions are audited under the user's identity

**Critical Requirement**: Frontend must provide the **user's Databricks personal access token (PAT)**.

---

## Authentication Patterns

### Pattern 1: Backend Proxy (Recommended for Production)

**Architecture**:
```
User Browser → Your Backend → Databricks Agent
            (Your auth)    (User's Databricks token)
```

**Benefits**:
- ✅ User's Databricks token never exposed to client
- ✅ Backend can refresh tokens automatically
- ✅ Centralized security controls
- ✅ Additional logging and validation
- ✅ No CORS configuration needed

**Implementation**:

```typescript
// Frontend: Call your backend
async function sendAgentQuery(query: string): Promise<AgentResponse> {
  const response = await fetch('/api/agent/query', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${yourAppToken}`,  // Your app's auth
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  
  return await response.json();
}
```

```python
# Backend (Python/Flask example)
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/agent/query', methods=['POST'])
def proxy_agent_query():
    # 1. Verify user is authenticated with YOUR app
    user_token = request.headers.get('Authorization')
    user = verify_user_token(user_token)  # Your auth logic
    
    # 2. Get user's Databricks token (from secure storage)
    databricks_token = get_user_databricks_token(user.id)
    
    # 3. Forward to Databricks agent
    query = request.json.get('query')
    agent_response = requests.post(
        'https://workspace.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations',
        headers={
            'Authorization': f'Bearer {databricks_token}',
            'Content-Type': 'application/json'
        },
        json={
            'input': [{'role': 'user', 'content': query}],
            'custom_inputs': {
                'user_id': user.email,
                'session_id': request.json.get('session_id')
            }
        }
    )
    
    return jsonify(agent_response.json())
```

---

### Pattern 2: Direct Client Call (Simple, Development Only)

**Architecture**:
```
User Browser → Databricks Agent
            (User's Databricks token)
```

**Benefits**:
- ✅ Simpler architecture (no backend proxy)
- ✅ Faster development iteration

**Drawbacks**:
- ⚠️ User's token exposed to browser (less secure)
- ⚠️ Requires CORS configuration on Databricks side
- ⚠️ No centralized logging
- ⚠️ Can't refresh tokens automatically

**Implementation**:

```typescript
async function sendAgentQuery(
  query: string,
  userDatabricksToken: string
): Promise<AgentResponse> {
  const response = await fetch(
    'https://workspace.cloud.databricks.com/serving-endpoints/health_monitor_agent_dev/invocations',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userDatabricksToken}`,  // User's Databricks PAT
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        input: [{ role: 'user', content: query }],
        custom_inputs: {
          user_id: getUserEmail(),
          session_id: generateSessionId()
        }
      })
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return await response.json();
}
```

---

## Token Management

### Getting User's Databricks Token

**Option 1: OAuth 2.0 Flow (Recommended)**

```typescript
// Redirect user to Databricks OAuth
const OAUTH_URL = `${workspaceUrl}/oidc/oauth2/v1/authorize`;
const params = new URLSearchParams({
  client_id: 'your-app-client-id',
  redirect_uri: 'https://your-app.com/callback',
  response_type: 'code',
  scope: 'all-apis'  // Or specific scopes
});

window.location.href = `${OAUTH_URL}?${params}`;

// Handle callback
async function handleOAuthCallback(code: string) {
  // Exchange code for token
  const response = await fetch(`${workspaceUrl}/oidc/oauth2/v1/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: 'https://your-app.com/callback',
      client_id: 'your-app-client-id',
      client_secret: 'your-app-client-secret'  // Backend only!
    })
  });
  
  const { access_token } = await response.json();
  return access_token;  // This is the user's Databricks token
}
```

**Option 2: User Provides PAT (Development)**

```typescript
// Simple form for user to paste their PAT
function TokenSetup() {
  const [token, setToken] = useState('');
  
  return (
    <div>
      <h3>Enter Your Databricks Token</h3>
      <input
        type="password"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="dapi..."
      />
      <button onClick={() => saveToken(token)}>
        Save Token
      </button>
      <p className="text-sm text-gray-600">
        Get your PAT from: Settings → Developer → Access Tokens
      </p>
    </div>
  );
}
```

---

### Storing Tokens Securely

#### ❌ NEVER Do This

```typescript
// DON'T store in localStorage (exposed to XSS attacks!)
localStorage.setItem('databricks_token', userToken);  // ❌ INSECURE

// DON'T store in plain text cookies
document.cookie = `token=${userToken}`;  // ❌ INSECURE

// DON'T expose in URL parameters
window.location.href = `/chat?token=${userToken}`;  // ❌ INSECURE
```

#### ✅ DO This Instead

**Option 1: httpOnly Cookies (Best)**
```typescript
// Backend sets secure httpOnly cookie
// Token is never accessible to JavaScript
// Automatically sent with requests

// Backend (Express.js example)
res.cookie('databricks_token', userToken, {
  httpOnly: true,     // Not accessible via JavaScript
  secure: true,       // HTTPS only
  sameSite: 'strict', // CSRF protection
  maxAge: 3600000     // 1 hour
});
```

**Option 2: Session Storage (Acceptable)**
```typescript
// Better than localStorage (cleared on tab close)
sessionStorage.setItem('databricks_token_hash', hashToken(userToken));

// Retrieve
const tokenHash = sessionStorage.getItem('databricks_token_hash');
const token = await retrieveTokenFromBackend(tokenHash);
```

**Option 3: Memory Only (Most Secure)**
```typescript
// Store in React state only, never persisted
const [userToken, setUserToken] = useState<string | null>(null);

// Lost on page refresh (user must re-authenticate)
```

---

### Token Expiration Handling

```typescript
async function sendWithTokenRefresh(
  query: string,
  userToken: string
): Promise<AgentResponse> {
  try {
    return await sendAgentQuery(query, userToken);
    
  } catch (error) {
    // Check if token expired
    if (error.message.includes('401') || error.message.includes('Invalid access token')) {
      console.log('Token expired, refreshing...');
      
      // Refresh token (via your backend or OAuth)
      const newToken = await refreshUserToken();
      setUserToken(newToken);
      
      // Retry with new token
      return await sendAgentQuery(query, newToken);
    }
    
    throw error;  // Other errors
  }
}
```

---

## User Permissions Required

For OBO to work, the **end user** must have these permissions:

### Required Permissions

| Resource | Permission | How to Grant |
|---|---|---|
| **SQL Warehouse** | `CAN USE` | SQL Warehouses → Permissions → Add user with CAN USE |
| **Genie Space** | `CAN RUN` | Genie Space → Permissions → Share with user |
| **Unity Catalog Tables** | `SELECT` | `GRANT SELECT ON TABLE ... TO user@company.com` |

### Permission Check UI (Optional)

```typescript
export function PermissionCheck({ onSuccess, onError }: Props) {
  const [checking, setChecking] = useState(false);
  
  const checkPermissions = async () => {
    setChecking(true);
    try {
      // Send a simple test query
      const response = await sendAgentQuery(
        "Hello",  // Simple query that shouldn't fail if permissions are correct
        userToken
      );
      
      if (response.custom_outputs.source === 'error' && 
          response.custom_outputs.error?.includes('permission')) {
        onError('Missing permissions. Please contact your admin.');
      } else {
        onSuccess('Permissions verified!');
      }
    } catch (error) {
      onError(`Permission check failed: ${error.message}`);
    } finally {
      setChecking(false);
    }
  };
  
  return (
    <div className="permission-check p-4 bg-gray-50 rounded">
      <h3 className="font-semibold mb-2">🔒 Permission Check</h3>
      <p className="text-sm text-gray-600 mb-3">
        Verify you have access to Genie Spaces and SQL Warehouse
      </p>
      <button
        onClick={checkPermissions}
        disabled={checking}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {checking ? 'Checking...' : 'Check Permissions'}
      </button>
    </div>
  );
}
```

---

## Error Handling: Permission Errors

### Detecting Permission Errors

```typescript
function handleAgentResponse(response: AgentResponse) {
  const { source, error } = response.custom_outputs;
  
  if (source === 'error') {
    // Check if it's a permission error
    const isPermissionError = 
      error?.toLowerCase().includes('permission') ||
      error?.toLowerCase().includes('authorized') ||
      error?.toLowerCase().includes('can use');
    
    if (isPermissionError) {
      return {
        type: 'permission_error',
        message: 'You need CAN USE permission on the SQL warehouse.',
        action: 'Contact your Databricks administrator'
      };
    }
    
    // Other errors
    return {
      type: 'query_error',
      message: error || 'Unknown error occurred'
    };
  }
  
  return { type: 'success' };
}
```

### Permission Error Display

```typescript
export function PermissionError({ domain }: { domain: string }) {
  return (
    <div className="permission-error bg-red-50 border border-red-200 rounded p-4">
      <div className="flex items-start gap-3">
        <span className="text-2xl">🔒</span>
        <div>
          <h3 className="font-semibold text-red-800 mb-1">Permission Required</h3>
          <p className="text-sm text-red-700 mb-3">
            You need the following permissions to query {domain} data:
          </p>
          <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
            <li><strong>CAN USE</strong> on the SQL Warehouse</li>
            <li><strong>CAN RUN</strong> on the {domain} Genie Space</li>
            <li><strong>SELECT</strong> on Unity Catalog tables</li>
          </ul>
          <div className="mt-3">
            <a
              href="https://docs.databricks.com/security/auth-authz/access-control/index.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 underline"
            >
              View Setup Guide →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Security Best Practices

### 1. Token Transmission

```typescript
// ✅ GOOD: HTTPS only
const ENDPOINT_URL = 'https://workspace.cloud.databricks.com/...';

// ❌ BAD: Never use HTTP
const ENDPOINT_URL = 'http://workspace.cloud.databricks.com/...';  // ❌
```

### 2. Token Storage

```typescript
// ✅ GOOD: In-memory only (most secure)
const [token, setToken] = useState<string | null>(null);

// ⚠️ ACCEPTABLE: sessionStorage (cleared on tab close)
sessionStorage.setItem('token_ref', tokenReference);

// ❌ BAD: localStorage (persists forever, exposed to XSS)
localStorage.setItem('token', userToken);  // ❌
```

### 3. Token Validation

```typescript
function isValidDatabricksToken(token: string): boolean {
  // Databricks PATs start with 'dapi'
  if (!token.startsWith('dapi')) {
    return false;
  }
  
  // Reasonable length (typically 40-50 chars)
  if (token.length < 20 || token.length > 100) {
    return false;
  }
  
  return true;
}
```

### 4. Input Sanitization

```typescript
import DOMPurify from 'isomorphic-dompurify';

function sanitizeQuery(query: string): string {
  // Remove any HTML/script tags
  const clean = DOMPurify.sanitize(query, {
    ALLOWED_TAGS: [],  // No HTML allowed
    ALLOWED_ATTR: []
  });
  
  // Limit length
  return clean.slice(0, 5000);
}

// Use before sending
const request = {
  input: [{ role: 'user', content: sanitizeQuery(userInput) }]
};
```

---

## Environment Configuration

### Development

```typescript
// .env.development
NEXT_PUBLIC_DATABRICKS_WORKSPACE_URL=https://e2-demo-field-eng.cloud.databricks.com
NEXT_PUBLIC_AGENT_ENDPOINT_NAME=health_monitor_agent_dev

# Backend-only (never expose to frontend)
DATABRICKS_SERVICE_ACCOUNT_TOKEN=dapi...
```

### Production

```typescript
// .env.production
NEXT_PUBLIC_DATABRICKS_WORKSPACE_URL=https://prod-workspace.cloud.databricks.com
NEXT_PUBLIC_AGENT_ENDPOINT_NAME=health_monitor_agent

# Backend-only
DATABRICKS_SERVICE_ACCOUNT_TOKEN=dapi...
```

### Usage

```typescript
const AGENT_CONFIG = {
  workspaceUrl: process.env.NEXT_PUBLIC_DATABRICKS_WORKSPACE_URL!,
  endpointName: process.env.NEXT_PUBLIC_AGENT_ENDPOINT_NAME!,
  get endpointUrl() {
    return `${this.workspaceUrl}/serving-endpoints/${this.endpointName}/invocations`;
  }
};
```

---

## CORS Configuration (For Direct Client Calls)

If using Pattern 2 (direct client calls), your Databricks administrator must configure CORS:

```python
# Databricks Model Serving CORS configuration
# Done via API (not available in UI)

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.serving_endpoints.update_config(
    name="health_monitor_agent_dev",
    cors={
        "allowed_origins": [
            "https://your-app.com",
            "http://localhost:3000"  # For development
        ],
        "allowed_methods": ["POST", "OPTIONS"],
        "allowed_headers": ["Authorization", "Content-Type"],
        "allow_credentials": True
    }
)
```

**Frontend verification**:
```typescript
// Test if CORS is configured correctly
async function testCORS(): Promise<boolean> {
  try {
    const response = await fetch(AGENT_CONFIG.endpointUrl, {
      method: 'OPTIONS',
      headers: {
        'Origin': window.location.origin,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Authorization, Content-Type'
      }
    });
    return response.ok;
  } catch (error) {
    console.error('CORS not configured:', error);
    return false;
  }
}
```

---

## Authentication Context (React)

### Create Auth Provider

```typescript
// contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextType {
  userToken: string | null;
  userEmail: string | null;
  isAuthenticated: boolean;
  login: (token: string, email: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userToken, setUserToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  
  // Try to restore session
  useEffect(() => {
    const savedEmail = sessionStorage.getItem('user_email');
    // Note: Token should come from secure storage, not sessionStorage
    if (savedEmail) {
      setUserEmail(savedEmail);
      // Fetch token from backend
      fetchUserToken().then(setUserToken);
    }
  }, []);
  
  const login = (token: string, email: string) => {
    setUserToken(token);
    setUserEmail(email);
    sessionStorage.setItem('user_email', email);
  };
  
  const logout = () => {
    setUserToken(null);
    setUserEmail(null);
    sessionStorage.removeItem('user_email');
  };
  
  return (
    <AuthContext.Provider
      value={{
        userToken,
        userEmail,
        isAuthenticated: !!userToken,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### Use in Components

```typescript
import { useAuth } from './contexts/AuthContext';

export function AgentChat() {
  const { userToken, userEmail, isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <LoginPrompt />;
  }
  
  const sendMessage = async (query: string) => {
    const response = await sendAgentQuery(query, userToken!);
    // ... handle response
  };
  
  return <ChatInterface />;
}
```

---

## Testing Authentication

### Manual Tests

1. **Valid Token Test**:
   ```
   Query: "Hello"
   Expected: Response with domain="unified", source="genie"
   ```

2. **Invalid Token Test**:
   ```
   Token: "invalid_token"
   Expected: HTTP 401 error
   ```

3. **Expired Token Test**:
   ```
   Token: <expired PAT>
   Expected: HTTP 401 error, should trigger refresh
   ```

4. **Permission Test**:
   ```
   Query: "What are top jobs?"
   User with no SQL warehouse access
   Expected: source="error", error includes "permission"
   ```

### Automated Tests

```typescript
describe('Authentication', () => {
  it('should reject invalid tokens', async () => {
    await expect(
      sendAgentQuery('test', 'invalid_token')
    ).rejects.toThrow('401');
  });
  
  it('should handle token expiration', async () => {
    const expiredToken = 'dapi_expired_token';
    
    // Mock token refresh
    const refreshSpy = jest.spyOn(auth, 'refreshToken');
    
    await sendWithTokenRefresh('test', expiredToken);
    
    expect(refreshSpy).toHaveBeenCalled();
  });
  
  it('should handle permission errors gracefully', async () => {
    // User with no warehouse access
    const response = await sendAgentQuery('test query', noPermissionToken);
    
    expect(response.custom_outputs.source).toBe('error');
    expect(response.custom_outputs.error).toContain('permission');
  });
});
```

---

## Common Issues

### Issue: "401 Unauthorized"
**Cause**: Invalid or expired token
**Solution**:
1. Verify token is valid Databricks PAT (starts with `dapi`)
2. Check token hasn't expired
3. Implement token refresh logic

### Issue: "403 Forbidden" or "Permission denied"
**Cause**: User lacks necessary permissions
**Solution**:
1. Verify user has `CAN USE` on SQL warehouse
2. Verify user has `CAN RUN` on Genie Spaces
3. Check Unity Catalog table permissions
4. Display helpful error message with setup guide link

### Issue: "CORS error"
**Cause**: CORS not configured on serving endpoint
**Solution**:
1. Use backend proxy (Pattern 1)
2. OR contact Databricks admin to configure CORS
3. Verify origin is whitelisted

### Issue: "Token exposed in browser DevTools"
**Cause**: Token sent in headers (visible in Network tab)
**Solution**: This is expected behavior. Use HTTPS + httpOnly cookies to minimize risk.

---

## Security Checklist

Before production deployment:

### Token Security
- [ ] Tokens transmitted over HTTPS only
- [ ] Tokens not stored in localStorage
- [ ] Tokens not logged to console
- [ ] Token refresh implemented
- [ ] Token expiry handling implemented

### User Permissions
- [ ] Permission errors handled gracefully
- [ ] Clear error messages for missing permissions
- [ ] Setup guide linked from error messages
- [ ] Permission check available (optional)

### Network Security
- [ ] CORS configured (if using direct calls)
- [ ] Content Security Policy set
- [ ] No sensitive data in URL parameters
- [ ] All requests use HTTPS

### Code Security
- [ ] User input sanitized before sending
- [ ] Response data validated before rendering
- [ ] XSS protection implemented (React/DOMPurify)
- [ ] Error messages don't expose system internals

---

## Reference: OBO Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBO Authentication Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. User logs into your app                                       │
│     → Your app authenticates user                                 │
│     → Your app gets/stores user's Databricks token                │
│                                                                   │
│  2. User sends query via your frontend                            │
│     → Frontend includes user's Databricks token in request        │
│                                                                   │
│  3. Databricks Model Serving receives request                     │
│     → Validates token                                             │
│     → Extracts user identity from token                           │
│                                                                   │
│  4. Agent executes with user's permissions                        │
│     → Genie queries run as the user                               │
│     → Unity Catalog enforces user's table permissions             │
│     → SQL warehouse checks user's access                          │
│                                                                   │
│  5. Response returned                                             │
│     → Contains only data user has access to                       │
│     → Audit logs show user's actions, not deployer's              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

### Essential Headers
```typescript
{
  'Authorization': `Bearer ${userDatabricksToken}`,  // User's PAT
  'Content-Type': 'application/json'
}
```

### Essential Request Fields
```typescript
{
  input: [{ role: 'user', content: 'query' }],
  custom_inputs: {
    user_id: 'user@company.com'  // For personalization
  }
}
```

### Permission Requirements
- `CAN USE` on SQL Warehouse ✅
- `CAN RUN` on Genie Space ✅  
- `SELECT` on Unity Catalog tables ✅

---

**Next Guide**: [03 - API Reference](03-api-reference.md) (Request/response formats, error codes, rate limiting)

**Related**: 
- [Backend Auth Details](../obo-authentication-guide.md) (for backend developers)
- [Databricks OBO Docs](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication)
