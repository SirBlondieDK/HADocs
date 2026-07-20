# HTML CSS patch

Add this to `src/hadocs/html/css.py` inside `dashboard_css()` if the Explain box is not styled:

```css
.explain {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(11, 16, 32, .42);
}
.explain summary {
  cursor: pointer;
  color: var(--blue);
  font-weight: 700;
}
.explain h4 { margin: 12px 0 8px; }
.explain p, .explain li {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}
```
