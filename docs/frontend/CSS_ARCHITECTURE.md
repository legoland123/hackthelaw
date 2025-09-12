# CSS Architecture

This directory contains the modular CSS structure for the LIT Version Control application.

## Structure

```
src/styles/
├── main.css              # Main entry point that imports all modules
├── variables.css         # CSS custom properties (design tokens)
├── base.css             # Reset, typography, and global styles
├── header.css           # App header styles
├── sidebar.css          # Sidebar navigation styles
├── timeline.css         # Version timeline styles
├── upload.css           # Document upload styles
├── viewer.css           # Document viewer styles
├── conflict-resolver.css # Conflict resolution styles
├── overview.css         # Overview page styles
├── breadcrumb.css       # Breadcrumb navigation styles
└── README.md           # This file
```

## Benefits of Modular CSS

1. **Maintainability**: Each component's styles are isolated and easier to maintain
2. **Scalability**: New components can have their own CSS files
3. **Performance**: Only load the styles you need
4. **Team Collaboration**: Multiple developers can work on different CSS files without conflicts
5. **Debugging**: Easier to locate and fix styling issues

## Usage

### Adding New Styles

1. Create a new CSS file in the `src/styles/` directory
2. Import it in `main.css`
3. Use descriptive class names that follow the existing naming convention

### Naming Convention

- Use kebab-case for class names
- Prefix component-specific classes with the component name (e.g., `.timeline-card`, `.conflict-item`)
- Use semantic class names that describe the purpose, not the appearance

### CSS Variables

All design tokens are defined in `variables.css`. Use these variables instead of hardcoded values:

```css
/* Good */
color: var(--primary-color);
background: var(--surface-color);

/* Bad */
color: #2c3e50;
background: #ffffff;
```

### Responsive Design

Include responsive styles at the bottom of each component's CSS file:

```css
@media (max-width: 768px) {
  /* Mobile-specific styles */
}
```

## File Organization

- **variables.css**: Colors, spacing, shadows, and other design tokens
- **base.css**: Global styles, resets, buttons, and utility classes
- **Component files**: Styles specific to individual components or pages

## Import Order

The import order in `main.css` is important:

1. Variables (must be first)
2. Base styles
3. Component styles (order doesn't matter for components)

This ensures that CSS custom properties are available to all other stylesheets. 