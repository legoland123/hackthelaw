# AI Chat CSS Modules

This directory contains modular CSS files for the AI Chat component, organized by functionality for better maintainability.

## File Structure

```
ai-chat/
├── index.css          # Main entry point that imports all modules
├── layout.css         # Grid layout and container styles
├── header.css         # Chat header and connection status
├── messages.css       # Message bubbles, avatars, and typing indicators
├── input.css          # Chat input form and send button
├── sidebar.css        # Sidebar sections, quick actions, and statistics
└── README.md          # This documentation file
```

## Module Descriptions

### `layout.css`
- Main grid layout for the AI chat page
- Chat container and messages container
- Responsive grid adjustments
- Chat sidebar positioning

### `header.css`
- Chat header styling
- Connection status indicators (online/offline)
- Header actions and buttons
- Responsive header behavior

### `messages.css`
- Message bubble styling for user, AI, and error messages
- Message avatars and content layout
- Typing indicator animation
- Message timestamps and sender information

### `input.css`
- Chat input form styling
- Textarea and send button
- Focus states and disabled states
- Input container layout

### `sidebar.css`
- Sidebar section containers
- Quick action buttons
- Chat statistics display
- AI capabilities information

## Usage

The main `ai-chat.css` file in the parent directory now imports all these modules, so no changes are needed in your components. The modular structure is transparent to the rest of the application.

## Benefits

1. **Maintainability**: Each file focuses on a specific aspect of the UI
2. **Reusability**: Individual modules can be reused or modified independently
3. **Organization**: Easier to find and modify specific styles
4. **Collaboration**: Multiple developers can work on different modules simultaneously
5. **Testing**: Individual modules can be tested in isolation

## Adding New Styles

When adding new styles to the AI chat component:

1. Identify which module the new styles belong to
2. Add the styles to the appropriate module file
3. If the styles don't fit existing modules, consider creating a new module file
4. Update this README if you add new modules

## Responsive Design

Each module includes its own responsive design rules where appropriate. This ensures that related styles and their responsive variants are kept together. 