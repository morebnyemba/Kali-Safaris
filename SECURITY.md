# Security Guidelines

## ⚠️ CRITICAL SECURITY NOTICE

**IMPORTANT**: This repository previously contained `.env` files with actual credentials in git history (commit aeb1da1). 

### Immediate Actions Required:

1. **Rotate All Credentials**: All passwords, API keys, and secrets that were committed must be rotated immediately:
   - Django SECRET_KEY
   - MAILU_IMAP_PASS (PfungwaHanna2024 was exposed)
   - WHATSAPP_APP_SECRET (c189bbdaac02442a28216debfed60a8b was exposed)
   - Database passwords
   - Meta/WhatsApp API tokens
   - Email passwords
   - Any other sensitive credentials

2. **Review Git History**: Consider using tools like `git-filter-repo` or `BFG Repo-Cleaner` to remove sensitive data from git history if this is a public repository.

3. **Monitor for Unauthorized Access**: Check logs for any unauthorized access using the exposed credentials.

## Environment Variable Management

### Never Commit Sensitive Data

- **NEVER** commit `.env` files containing actual credentials
- **NEVER** hardcode secrets in source code
- **ALWAYS** use `.env.example` files as templates (without real values)
- **ALWAYS** add all `.env*` files to `.gitignore` (except `.env.example`)

### Setting Up Environment Variables

1. Copy the appropriate `.env.example` file:
   ```bash
   # For backend
   cp whatsappcrm_backend/.env.example whatsappcrm_backend/.env
   
   # For frontend
   cp whatsapp-crm-frontend/.env.example whatsapp-crm-frontend/.env
   
   # For docker-compose
   cp .env.example .env
   ```

2. Fill in your actual values in the `.env` files

3. **Double-check** that your `.env` files are listed in `.gitignore`

4. **Verify** before committing:
   ```bash
   git status
   # Ensure no .env files (except .env.example) are staged
   ```

## Secret Key Generation

### Django SECRET_KEY

Generate a secure secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Database Passwords

Use strong, randomly generated passwords:
```bash
# On Linux/Mac
openssl rand -base64 32

# Or use a password manager
```

## Production Security Checklist

- [ ] All credentials rotated after being exposed
- [ ] `DEBUG=False` in production
- [ ] Strong, unique `SECRET_KEY` set
- [ ] HTTPS enabled for all domains
- [ ] CSRF and CORS properly configured
- [ ] Database uses strong password
- [ ] Redis password protected (if exposed to network)
- [ ] Firewall rules restrict access to internal services
- [ ] Regular security updates applied
- [ ] Monitoring and logging enabled
- [ ] Backup strategy in place
- [ ] `.env` files never committed

## API Keys and Tokens

### WhatsApp/Meta Integration

- Store Meta API credentials in environment variables only
- Use long-lived system user tokens with appropriate permissions
- Rotate tokens periodically
- Never log or display tokens in responses

### Google Cloud API Keys

- Use service account keys instead of API keys when possible
- Store in `.env` files, never in code
- Limit key permissions to minimum required
- Enable key restrictions in GCP Console

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. **DO NOT** disclose publicly until fixed
3. Contact the repository owner privately
4. Provide detailed information about the vulnerability

## Additional Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [React Security Best Practices](https://reactjs.org/docs/security.html)

## Security Updates

- Review dependencies regularly for vulnerabilities
- Use `pip-audit` for Python dependencies
- Use `npm audit` for Node.js dependencies
- Apply security patches promptly

---

**Last Updated**: December 2025  
**Next Review**: Quarterly or after any security incident
