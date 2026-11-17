
# Test suite

Run:

```powershell
py -m pytest -q
```

Coverage summary:

- Authentication success, logout, and invalid credentials
- Role authorization for student, staff, and admin
- Catalog and checkout return-date validation
- Double-submission prevention
- Approval, checkout status, return logging, and return condition
- Denial behavior and audit logging
- Concurrent-style submission test ensuring only one active request is created

Test data is isolated in temporary SQLite databases created per pytest fixture.
