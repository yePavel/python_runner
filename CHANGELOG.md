# Changelog

## [Latest] - Notifications and Alerts Implementation

### Added

#### Notification System
- **Desktop Notifications**: System tray notifications for script completion, failure, and errors
- **System Tray Integration**: Persistent system tray icon with context menu
- **Notification Toggle**: Easy on/off toggle with visual indicator (🔔/🔕) in toolbar
- **Persistent Settings**: User preferences saved across sessions using QSettings
- **Fallback Support**: Message dialogs on systems without system tray support

#### New Features
1. **Success Notifications**
   - Triggered when scripts complete with exit code 0
   - Shows informational icon
   - Includes script name in message

2. **Failure Notifications**
   - Triggered when scripts fail with non-zero exit code
   - Shows critical icon
   - Includes exit code in message

3. **Error Notifications**
   - Triggered on process errors
   - Shows critical icon
   - Includes error details in message

4. **System Tray Icon**
   - Context menu with "Show Window" and "Quit" options
   - Displays notification messages
   - Available on supported platforms

5. **Notification Toggle Button**
   - Bell icon in toolbar (🔔 = enabled, 🔕 = disabled)
   - Instant feedback on toggle
   - Preference persisted using QSettings

#### Test Scripts
- **test_notifications.py**: New test script for notification system
  - Supports success, failure, and error scenarios
  - Configurable progress steps
  - Integrated into Main Runner UI

#### Documentation
- **NOTIFICATIONS.md**: Comprehensive guide to notification features
  - Usage instructions
  - Implementation details
  - Platform support information
  - Troubleshooting guide

### Modified

#### Main_Runner_Balmas.py
- Added `QSettings` import for persistent preferences
- Added `QSystemTrayIcon` and `QMenu` imports for system tray
- Enhanced `MainWindow.__init__()`:
  - Initialize QSettings
  - Create system tray icon (when available)
  - Add notification toggle button to toolbar
- New method `toggle_notifications()`: Toggle and persist notification preference
- New method `show_notification()`: Display notifications via tray or dialog
- Updated `on_proc_finished()`: Send notifications on script completion
- Updated `on_proc_error()`: Send notifications on process errors

#### improvement_checklist.md
- Marked "Notifications" item as complete [x]

### Technical Details

#### Dependencies
- PySide6 >= 6.5.0 (already installed)
- QSystemTrayIcon for native notifications
- QSettings for preference persistence

#### Settings Storage
- Organization: "MainRunner"
- Application: "ScriptRunner"
- Key: "notifications_enabled"
- Default: True

#### Notification Display Duration
- 5000ms (5 seconds) for system tray notifications
- User-dismissible message dialogs as fallback

### Backward Compatibility
- All existing functionality preserved
- Notifications enabled by default (can be disabled)
- Graceful degradation on systems without system tray
- No breaking changes to existing API

### Testing
- Syntax validation: Passed
- Python compilation: Passed
- Test script execution: Passed (success, failure, error scenarios)
- Code style: Consistent with existing codebase

### Known Limitations
- System tray not available in headless environments (fallback to dialogs)
- Notification permissions may need to be granted on some systems
- OpenGL libraries required for GUI execution (standard for PySide6)

### Future Enhancements
See NOTIFICATIONS.md for planned improvements:
- Custom notification sounds
- Notification history/log
- Rich notifications with action buttons
- Configurable notification duration
- Batch operation summaries
