# Authentication Guide

ZERO-COMP API supports two authentication methods:

## 1. JWT Tokens (Dashboard Users)

JWT tokens are obtained through the web dashboard login process:

1. Sign up/login at [https://dashboard.zero-comp.com](https://dashboard.zero-comp.com)
2. The dashboard automatically handles JWT token management
3. Tokens are valid for 24 hours and automatically refreshed

### Using JWT Tokens

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     https://api.zero-comp.com/api/v1/alerts/current
```

## 2. API Keys (Programmatic Access)

API keys provide programmatic access for Pro and Enterprise subscribers:

### Generating API Keys

1. Login to the dashboard
2. Navigate to Account Settings → API Keys
3. Click "Generate New API Key"
4. **Important**: Copy the key immediately - it won't be shown again

### Using API Keys

```bash
curl -H "Authorization: Bearer zc_your-api-key-here" \
     https://api.zero-comp.com/api/v1/alerts/current
```

### API Key Format

API keys follow the format: `zc_` followed by 32 random characters.

Example: `zc_abc123def456ghi789jkl012mno345pqr678`

## Security Best Practices

1. **Never expose API keys in client-side code**
2. **Store API keys securely** (environment variables, secure vaults)
3. **Rotate API keys regularly** (every 90 days recommended)
4. **Use HTTPS only** - never send credentials over HTTP
5. **Monitor API usage** for suspicious activity

## Rate Limiting

Authentication affects rate limits:

| Tier | Rate Limit |
|------|------------|
| Free | 10 requests/hour |
| Pro | 1,000 requests/hour |
| Enterprise | 10,000 requests/hour |

## Troubleshooting

### Common Authentication Errors

**401 Unauthorized**
- Invalid or expired token
- Missing Authorization header
- Malformed token format

**403 Forbidden**  
- Valid token but insufficient permissions
- Feature requires higher subscription tier

**429 Rate Limit Exceeded**
- Too many requests for your tier
- Check `X-RateLimit-Reset` header for retry time
