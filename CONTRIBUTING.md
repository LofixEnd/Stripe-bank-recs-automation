# Stripe Reconciliation Accelerator - Contributing Guide

## Development Setup

### Clone & Install
```bash
git clone <repository>
cd stripe-reconciliation-accelerator
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run Tests
```bash
python -m unittest test_logic.py -v
```

### Code Style
- Follow PEP 8
- Use descriptive variable names
- Add docstrings to functions
- Keep functions under 50 lines when possible

## File Organization

```
stripe-reconciliation-accelerator/
├── app.py                    # Main Flask application (now with auth)
├── models.py                 # SQLAlchemy models (User table)
├── auth.py                   # Authentication blueprint/routes
├── forms.py                  # WTForms definitions for login/register
├── logic.py                  # Core reconciliation engine
├── test_logic.py            # Unit tests
├── startup.py               # Quick start helper
├── create_user.py           # Script to bootstrap users
├── requirements.txt         # Dependencies
├── Procfile                 # Deployment config
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── README.md                # User documentation
├── DEPLOYMENT.md            # Deployment guide
├── CONTRIBUTING.md          # This file
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Home page
│   └── portal.html         # Main interface
├── static/                 # CSS, JS, images
├── uploads/                # Temporary uploads
└── sample_data/            # Test data
```

## Adding Features

### New Reconciliation Logic
1. Add method to `StripeReconciliator` class
2. Use existing helper methods (`_find_amount_column`, etc.)
3. Add unit test in `test_logic.py`
4. Document in docstring

Example:
```python
def new_feature(self):
    """
    Description of what this does.
    
    Returns:
        dict: Results of the operation
    """
    # Implementation here
    pass
```

### New API Endpoint
1. Add route in `app.py` or a blueprint
2. Use `@login_required` and `@validate_client` (or custom access decorators)
3. Verify `current_user.client_slug` if the route sinks a slug parameter
4. Log significant operations
5. Return JSON responses

Example:
```python
@app.route('/api/portal/<client_slug>/new-endpoint', methods=['POST'])
@validate_client
def new_endpoint(client_slug):
    """Description of endpoint."""
    try:
        # Your code here
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

### New UI Component
1. Update HTML template
2. Add CSS to `<style>` block
3. Add JavaScript interactivity
4. Test on mobile and desktop

## Performance Optimization

### For Large Files (>10MB)
- Consider streaming CSV processing
- Implement chunked reading
- Add progress indicators

### For Multiple Concurrent Users
- Add Redis caching
- Implement request queuing
- Use async processing with Celery

## Security Improvements

### To Add
- [ ] Rate limiting on uploads
- [ ] File virus scanning
- [ ] SQL injection prevention (if using DB)
- [ ] CORS configuration
- [ ] Two-factor authentication

## Testing

### Unit Tests
```bash
python -m unittest test_logic.py -v
```

### Integration Tests
```bash
python -m unittest discover -s tests/ -p "test_*.py"
```

### Manual Testing
1. Use sample files in `sample_data/`
2. Test with different CSV formats
3. Try edge cases (empty files, wrong data types)

## Documentation Updates

When adding features:
1. Update README.md with new functionality
2. Add docstrings to code
3. Update DEPLOYMENT.md if needed
4. Include usage examples

## Commit Guidelines

```
Format: <type>(<scope>): <subject>

Types: feat, fix, refactor, docs, test

Example:
feat(reconciliation): add multi-currency support
fix(api): correct payout matching logic
docs(readme): update installation steps
```

## Reporting Issues

Include:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version
- Sample CSV (if applicable)
- Error log/traceback

## Roadmap

### Q1 2026
- [ ] Database integration
- [ ] User authentication
- [ ] Scheduled reconciliation

### Q2 2026
- [ ] Multi-currency support
- [ ] Shopify integration
- [ ] Advanced analytics

### Q3 2026
- [ ] Mobile application
- [ ] API for third-party integration
- [ ] Automated report delivery

## Getting Help

- Check existing issues/discussions
- Review documentation in README.md
- Check code comments
- Ask in discussions tab

---

Thank you for contributing! 🙏
