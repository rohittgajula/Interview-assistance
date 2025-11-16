# Auth Service Logging Configuration

## Overview
Comprehensive logging has been added to the auth_service, similar to the bloom_filter_service setup.

## Log Files

All logs are stored in `/app/logs/` directory:

1. **`auth_service.log`**
   - General application logs (INFO and above)
   - User registration, login, logout events
   - API requests and responses
   - Max size: 10 MB, rotating backups: 5 files

2. **`errors.log`**
   - Error-level logs only (ERROR and above)
   - Django request errors
   - Database errors
   - Critical failures
   - Max size: 10 MB, rotating backups: 5 files

3. **`signals.log`**
   - Dedicated log for Django signals (DEBUG level)
   - User creation/update/deletion signals
   - Webhook calls to bloom_filter_service
   - Signal processing success/failures
   - Max size: 10 MB, rotating backups: 5 files

## Log Formatters

### Verbose Format (for files)
```
{levelname} {asctime} {module} {process:d} {thread:d} {message}
```
Example:
```
INFO 2025-11-15 08:45:23,123 signals 1234 5678 User create signal processed for: testuser
```

### Simple Format (for console)
```
{levelname} {asctime} {message}
```
Example:
```
INFO 2025-11-15 08:45:23,123 User create signal processed for: testuser
```

## Loggers Available

### 1. General Django Logger
```python
logger = logging.getLogger('django')
```
- Use for: General Django framework logs
- Level: INFO
- Handlers: console, file

### 2. Auth Service Logger
```python
logger = logging.getLogger('auth_service')
```
- Use for: General auth_service application logs
- Level: DEBUG (dev) / INFO (prod)
- Handlers: console, file

### 3. Users App Logger
```python
logger = logging.getLogger('users')
```
- Use for: Users app specific logs (views, models, etc.)
- Level: DEBUG (dev) / INFO (prod)
- Handlers: console, file, signals_file

### 4. Signals Logger (Currently Used)
```python
logger = logging.getLogger('users.signals')
```
- Use for: Signal handlers only
- Level: DEBUG
- Handlers: console, signals_file

## Usage Examples

### In Views (users/views.py)
```python
import logging

logger = logging.getLogger('users')

def register_user(request):
    logger.info(f"User registration attempt: {request.data.get('username')}")
    try:
        # ... registration logic
        logger.info(f"User registered successfully: {user.username}")
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
```

### In Models (users/models.py)
```python
import logging

logger = logging.getLogger('users')

class User(AbstractBaseUser):
    def save(self, *args, **kwargs):
        logger.debug(f"Saving user: {self.username}")
        super().save(*args, **kwargs)
        logger.info(f"User saved: {self.username}")
```

### In Signals (users/signals.py) - Already Implemented
```python
import logging

logger = logging.getLogger('users.signals')

@receiver(post_save, sender=User)
def user_saved_handler(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    logger.info(f"User {action} signal processed for: {instance.username}")
```

## Viewing Logs

### In Docker Container
```bash
# View live logs
docker logs -f auth_service

# View specific log file
docker exec -it auth_service tail -f /app/logs/auth_service.log
docker exec -it auth_service tail -f /app/logs/signals.log
docker exec -it auth_service tail -f /app/logs/errors.log

# View last 100 lines
docker exec -it auth_service tail -n 100 /app/logs/auth_service.log
```

### On Host Machine
```bash
# Logs are mounted via volume in docker-compose
tail -f auth_service/logs/auth_service.log
tail -f auth_service/logs/signals.log
tail -f auth_service/logs/errors.log

# Search for specific user
grep "testuser" auth_service/logs/signals.log

# Search for errors
grep "ERROR" auth_service/logs/auth_service.log
```

## Log Levels

From most to least verbose:
- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Something unexpected happened, but still working
- **ERROR**: A serious problem has occurred
- **CRITICAL**: A very serious error, program may crash

## Current Signal Logging

When a user is created/updated/deleted, you'll see logs like:

```
DEBUG 2025-11-15 08:45:23,123 signals 1234 5678 User create signal processed for: testuser
INFO 2025-11-15 08:45:23,456 signals 1234 5678 Successfully sent create webhook for user testuser
```

Or on errors:
```
ERROR 2025-11-15 08:45:23,789 signals 1234 5678 Error sending webhook to bloom filter service: Connection refused
ERROR 2025-11-15 08:45:23,901 signals 1234 5678 Error in user_saved_handler: 'NoneType' object has no attribute 'username'
```

## Configuration Location

Logging is configured in: `auth_service/auth_service/settings.py` (lines 167-257)

## Docker Setup

The Dockerfile ensures logs directory exists:
```dockerfile
# Create logs directory
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Change ownership for non-root user
RUN adduser --disabled-password django && \
    chown -R django:django /app/logs
USER django
```

The docker-compose ensures directory on startup:
```yaml
command: >
  sh -c "mkdir -p /app/logs &&
          python manage.py makemigrations &&
          python manage.py migrate &&
          python manage.py runserver 0.0.0.0:8000"
```

## Monitoring Tips

1. **Watch for signal failures:**
   ```bash
   docker exec -it auth_service tail -f /app/logs/signals.log | grep ERROR
   ```

2. **Monitor user registrations:**
   ```bash
   docker exec -it auth_service tail -f /app/logs/auth_service.log | grep "registered"
   ```

3. **Track webhook calls:**
   ```bash
   docker exec -it auth_service tail -f /app/logs/signals.log | grep "webhook"
   ```

4. **Check all errors:**
   ```bash
   docker exec -it auth_service tail -f /app/logs/errors.log
   ```

## Best Practices

1. Use appropriate log levels
2. Include context (user IDs, action types)
3. Don't log sensitive data (passwords, tokens)
4. Use structured logging where possible
5. Monitor error logs regularly
6. Rotate logs to prevent disk space issues (automatically handled)

## Integration with Bloom Filter Service

The signals logger specifically tracks:
- User creation → Webhook sent to bloom filter
- User update → Webhook sent to bloom filter
- User deletion → Webhook sent to bloom filter
- Webhook success/failure responses
- Connection errors to bloom filter service

This makes debugging the auth ↔ bloom filter integration much easier!
