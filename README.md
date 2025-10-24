# Main Runner - Python Script Runner

A Python desktop application built with PySide6/Qt for running scripts with a dynamic GUI.

## Features

### Core Functionality
- **Dynamic Form Builder**: Automatically generates input forms based on script metadata
- **Drag & Drop Support**: Drop files directly into the app
- **Theme Toggle**: Dark and light theme support
- **Progress Tracking**: Visual progress bars with PROGRESS markers from scripts
- **Error Highlighting**: Automatic highlighting of errors in output
- **Recent Runs History**: Quick access to recently executed scripts with saved parameters

### New: Notifications and Alerts ✨
- **Desktop Notifications**: Get notified when scripts finish running
- **System Tray Integration**: Minimizes to system tray with context menu
- **Success/Failure Alerts**: Different notifications for successful and failed script executions
- **Error Notifications**: Immediate alerts for process errors
- **Toggle On/Off**: Easy notification control with toolbar button (🔔/🔕)
- **Persistent Settings**: Your notification preference is saved across sessions

## Installation

### Requirements
- Python 3.8+
- PySide6 6.5.0+

### Setup
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Application
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the application
python Main_Runner_Balmas.py
```

### Using Notifications
1. **Enable/Disable**: Click the bell icon (🔔/🔕) in the toolbar
2. **System Tray**: Right-click the tray icon for quick actions
3. **Notifications**: Automatically appear when scripts finish

### Adding Scripts
Edit the `SCRIPTS` list in `Main_Runner_Balmas.py`:

```python
{
    "name": "My Script",
    "path": "my_script.py",
    "clue": "Description of what this script does",
    "args_schema": [
        {"key": "--arg", "label": "Argument", "type": "text", "required": True}
    ],
    "log_arg_style": "--log"
}
```

## Script Integration

Scripts can emit special markers for GUI integration:

### Progress Updates
```python
print("PROGRESS 50")  # Shows 50% in progress bar
```

### Error Highlighting
```python
print("ERROR: Something went wrong")  # Highlighted in red
print("Traceback: ...")  # Highlighted in red
```

## Testing

### Test Scripts Included
1. **Example.py**: Basic test script
2. **test_parser_output.py**: Tests progress markers and error highlighting
3. **test_notifications.py**: Tests notification system (NEW)

### Testing Notifications
```bash
python test_notifications.py --scenario success --steps 5
python test_notifications.py --scenario failure --steps 3
python test_notifications.py --scenario error --steps 2
```

## Documentation

- **NOTIFICATIONS.md**: Detailed notification feature documentation
- **CHANGELOG.md**: Complete changelog of recent updates
- **improvement_checklist.md**: Future enhancement roadmap

## Features Checklist

- [x] Script Output Logging (to GUI)
- [x] Recent Files/History
- [ ] Custom Script Arguments
- [ ] Script Templates
- [ ] Parallel Execution
- [x] Error Highlighting
- [x] Drag & Drop
- [x] **Notifications** ✨ NEW
- [ ] Command Preview
- [ ] Stop/Restart Script
- [ ] Output Filtering

## Architecture

### Main Components

1. **DynamicForm**: Builds input forms from schema definitions
2. **FilePicker**: File selection widget with drag & drop
3. **MainWindow**: Main application window with:
   - Script selector
   - Dynamic parameter form
   - Progress tracking
   - Log viewer with error highlighting
   - Recent runs history
   - **Notification system** ✨

### Notification System (NEW)
- **QSystemTrayIcon**: System tray integration
- **QSettings**: Persistent preference storage
- **Notification Types**:
  - Success (exit code 0)
  - Failure (non-zero exit code)
  - Error (process errors)

## Platform Support

- **Windows**: Full support including system tray
- **Linux**: Full support (requires system tray support in DE)
- **macOS**: Full support

## License

This project is provided as-is for use and modification.

## Contributing

To add features:
1. Follow existing code style and patterns
2. Update relevant documentation
3. Add test cases if applicable
4. Update the improvement checklist

## Troubleshooting

### Notifications Not Working
1. Check if notifications are enabled (🔔 icon)
2. Verify system tray support on your platform
3. Check system notification permissions

### GUI Not Starting
1. Ensure PySide6 is installed: `pip install PySide6`
2. Verify OpenGL libraries are available
3. Check virtual environment is activated

### Scripts Not Running
1. Verify script paths in SCRIPTS list
2. Check script has proper permissions
3. Ensure required arguments are provided

## Development

### Code Style
- Follow PESide6/Qt conventions
- Use type hints where appropriate
- Document complex logic
- Keep UI and business logic separate

### Adding New Features
See `improvement_checklist.md` for planned enhancements.

---

**Latest Update**: Added comprehensive notification and alert system with system tray integration and persistent settings. 🎉
