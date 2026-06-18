# NIFTI Workflow & Rules

## Core Rules
1. **PowerShell Only:** All operations (Git, Python scripts, API testing, File manipulation) must be executed via PowerShell.
2. **Commit Policy:** Every milestone must be documented in this file before running `git commit`.
3. **API Integrity:** Any change to `api_gateway.py` or `db_manager.py` must be validated with a `curl` test immediately after.

## Open Tasks
- [x] Marketplace live with first transaction
- [x] Database backup created
- [x] Release notes documented
- [x] Git anchor point committed
- [x] Serve Mini App from FastAPI (static files)
- [ ] Implement BOC verification
- [ ] SIF Token integration
- [ ] Admin Dashboard
- [ ] Landing page
- [ ] Full i18n (9+ languages)
- [ ] NFT card generation
- [ ] Order book / Exchange
