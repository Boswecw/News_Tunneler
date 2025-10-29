# Contributing to News Tunneler

Thank you for your interest in contributing to News Tunneler! This document provides guidelines and instructions for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

### Suggesting Features

Feature requests are welcome! Please:
- Check existing issues first to avoid duplicates
- Clearly describe the feature and its benefits
- Provide use cases and examples
- Consider implementation complexity

### Submitting Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/Boswecw/News_Tunneler.git
   cd News_Tunneler
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines below
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Frontend tests (if applicable)
   cd frontend
   bun test
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template
   - Wait for review

## 📝 Code Style Guidelines

### Python (Backend)

- **PEP 8**: Follow Python style guide
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Use Google-style docstrings
- **Line Length**: Max 100 characters
- **Imports**: Group and sort imports (stdlib, third-party, local)

**Example:**
```python
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Article


def get_articles(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    min_score: Optional[float] = None
) -> List[Article]:
    """
    Fetch articles from database with optional filtering.
    
    Args:
        db: Database session
        limit: Maximum number of results
        offset: Pagination offset
        min_score: Minimum score threshold
        
    Returns:
        List of Article objects
        
    Raises:
        HTTPException: If database query fails
    """
    query = db.query(Article)
    
    if min_score is not None:
        query = query.filter(Article.score >= min_score)
    
    return query.limit(limit).offset(offset).all()
```

**Formatting:**
```bash
# Format with black
black app/

# Lint with ruff
ruff check app/

# Type check with mypy
mypy app/
```

### TypeScript (Frontend)

- **ESLint**: Follow ESLint rules
- **Types**: Use explicit types, avoid `any`
- **Components**: Use functional components with SolidJS
- **Naming**: PascalCase for components, camelCase for functions/variables
- **Line Length**: Max 100 characters

**Example:**
```typescript
import { createSignal, For, Show } from "solid-js";
import { Article } from "../lib/api";

interface ArticleListProps {
  articles: Article[];
  onArticleClick?: (article: Article) => void;
}

export default function ArticleList(props: ArticleListProps) {
  const [selectedId, setSelectedId] = createSignal<number | null>(null);

  const handleClick = (article: Article) => {
    setSelectedId(article.id);
    props.onArticleClick?.(article);
  };

  return (
    <div class="article-list">
      <Show when={props.articles.length > 0} fallback={<p>No articles</p>}>
        <For each={props.articles}>
          {(article) => (
            <div
              class="article-item"
              onClick={() => handleClick(article)}
            >
              <h3>{article.title}</h3>
              <p>{article.summary}</p>
            </div>
          )}
        </For>
      </Show>
    </div>
  );
}
```

**Formatting:**
```bash
# Format with prettier
bun run format

# Lint with eslint
bun run lint
```

## 🧪 Testing Guidelines

### Backend Tests

- **Location**: `backend/tests/`
- **Framework**: pytest
- **Coverage**: Aim for >80% coverage
- **Fixtures**: Use pytest fixtures for common setup

**Example:**
```python
import pytest
from app.core.scoring import calculate_score

def test_calculate_score_high_catalyst():
    """Test scoring with high catalyst value."""
    score = calculate_score(
        catalyst=5,
        novelty=3,
        credibility=4,
        sentiment=3,
        liquidity=2
    )
    assert score > 50
    assert isinstance(score, float)

def test_calculate_score_zero_values():
    """Test scoring with all zeros."""
    score = calculate_score(
        catalyst=0,
        novelty=0,
        credibility=0,
        sentiment=0,
        liquidity=0
    )
    assert score == 0
```

### Frontend Tests

- **Location**: `frontend/src/__tests__/`
- **Framework**: Vitest (if configured)
- **Components**: Test user interactions and state changes

## 🏗️ Architecture Guidelines

### Adding New Features

1. **Backend API Endpoint**
   - Create route in `backend/app/api/`
   - Add request/response models
   - Implement business logic in `backend/app/core/`
   - Add database models if needed in `backend/app/models/`
   - Create migration with Alembic
   - Add tests in `backend/tests/`

2. **Frontend Component**
   - Create component in `frontend/src/components/` or `frontend/src/pages/`
   - Add API client function in `frontend/src/lib/api.ts`
   - Update routing in `frontend/src/App.tsx` if needed
   - Add to navigation in `frontend/src/components/Navigation.tsx`
   - Style with Tailwind CSS classes

### Database Changes

Always use Alembic migrations:

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Add new table"

# Review generated migration
# Edit if needed

# Apply migration
alembic upgrade head
```

### Adding New RSS Sources

1. Add to `backend/app/seeds/seed_sources.py`
2. Run seed script or add via API/UI
3. Test feed parsing with `backend/test_poll.py`

## 📚 Documentation

- Update README.md for major features
- Add docstrings to all functions/classes
- Update API documentation (FastAPI auto-generates from docstrings)
- Add examples for complex features
- Update FAQ page for user-facing features

## 🔍 Code Review Process

All PRs will be reviewed for:
- **Functionality**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Code Quality**: Is it readable and maintainable?
- **Documentation**: Is it properly documented?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security issues?

## 🎯 Priority Areas

We're especially interested in contributions for:

- **ML Model Improvements**: Better prediction algorithms
- **Additional Data Sources**: New RSS feeds, APIs
- **Performance Optimization**: Faster data processing
- **UI/UX Enhancements**: Better visualizations, user experience
- **Testing**: Increased test coverage
- **Documentation**: Tutorials, guides, examples
- **Mobile Support**: Responsive design improvements

## 💬 Communication

- **GitHub Issues**: For bugs and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For questions and ideas

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make News Tunneler better for everyone. We appreciate your time and effort!

---

**Questions?** Feel free to open an issue or reach out to [@Boswecw](https://github.com/Boswecw)

