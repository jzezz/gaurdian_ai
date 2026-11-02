# Guardian AI - CONTRIBUTING Guidelines

Thank you for your interest in contributing to Guardian AI! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome feedback and differing opinions
- Focus on constructive criticism
- Report inappropriate behavior to maintainers

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/guardian-ai.git
   cd guardian-ai
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b codex/your-feature-name
   ```
4. **Set up development environment**:
   ```bash
   # Run setup script
   bash setup.sh
   ```

## Development Workflow

### Backend Development

1. **Create or modify** Python files in `backend/app/`
2. **Add or update tests** in `backend/tests/` for changed behavior
3. **Run tests**:
   ```bash
   python -m pytest -q
   ```

### Frontend Development

1. **Create or modify** TypeScript/React files in `frontend/src/`
2. **Start dev server**:
   ```bash
   cd frontend
   npm ci
   npm run dev
   ```
3. **Build for production**:
   ```bash
   npm run build
   ```

## Commit Guidelines

- Write clear, descriptive commit messages
- Use imperative mood: "Add feature" not "Added feature"
- Keep commits focused on a single change
- Reference issues: "Fix #123" or "Closes #456"

Example:
```
Add video frame sampling rate configuration

- Allow users to customize frame sampling interval
- Add tests for new configuration option
- Update API documentation

Fixes #123
```

## Pull Request Process

1. **Before submitting**, ensure:
   - All tests pass: `pytest tests/`
   - New features have tests
   - Documentation is updated
   - Commit messages are clear

2. **Submit a pull request** with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to related issues
   - Screenshots for UI changes

3. **Respond to feedback**:
   - Maintain professional tone
   - Make requested changes promptly
   - Push updates to the same branch

## Testing Standards

### Backend Tests
- Aim for >80% code coverage
- Test both success and failure cases
- Use descriptive test names

Example:
```python
def test_fusion_rejects_explicit_content():
    """Fusion engine should reject high NSFW scores"""
    result = fusion.fuse(
        make_image_result(nsfw=0.95),
        make_text_result(),
        ""
    )
    assert result["safe"] is False
```

## Code Style

### Python
- Follow PEP 8 guidelines
- Use type hints where possible
- Keep functions focused

### TypeScript/React
- Use functional components with hooks
- Add prop types/interfaces
- Keep components focused

## Issues & Bug Reports

### Filing an Issue
- Check for existing similar issues first
- Use clear, descriptive title
- Provide reproduction steps for bugs
- Include environment info (OS, versions, etc.)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Guardian AI! 🛡️
