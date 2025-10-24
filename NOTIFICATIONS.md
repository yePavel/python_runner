# Notifications and Alerts

The Main Runner application now includes desktop notification support to alert users when scripts finish running.

## Features

### 1. Desktop Notifications
- **Success Notifications**: Receive a notification when a script completes successfully (exit code 0)
- **Failure Notifications**: Receive a notification when a script fails (non-zero exit code)
- **Error Notifications**: Receive a notification when a process error occurs

### 2. System Tray Integration
- System tray icon appears when the application is running (on supported platforms)
- Right-click the tray icon to show/hide the window or quit the application
- Notifications appear as system tray messages with appropriate icons:
  - ✅ Information icon for successful completions
  - ❌ Critical icon for failures and errors

### 3. Notification Toggle
- Click the bell icon (🔔/🔕) in the toolbar to enable/disable notifications
- Setting is persisted across application restarts
- When enabled, you'll see a confirmation notification
- When disabled, no notifications will be shown

### 4. Fallback Support
- On systems without system tray support, notifications appear as message dialogs
- Ensures users are always notified regardless of platform capabilities

## Usage

### Enabling/Disabling Notifications

1. Click the bell icon in the toolbar
   - 🔔 = Notifications enabled
   - 🔕 = Notifications disabled

2. The setting is automatically saved and will be remembered next time you launch the app

### Notification Types

#### Success Notification
```
Title: Script Completed Successfully
Message: [Script Name] finished successfully!
Icon: Information (ℹ️)
```

#### Failure Notification
```
Title: Script Failed
Message: [Script Name] failed with exit code [code]
Icon: Critical (❌)
```

#### Error Notification
```
Title: Script Error
Message: [Script Name] encountered an error: [error details]
Icon: Critical (❌)
```

## Implementation Details

### Technologies Used
- **QSystemTrayIcon**: Provides system tray integration and native notifications
- **QSettings**: Persists user preferences across sessions
- **Qt Signals/Slots**: Handles process completion and error events

### Settings Storage
- Organization: "MainRunner"
- Application: "ScriptRunner"
- Setting Key: "notifications_enabled"
- Default: `True` (enabled by default)

### Notification Duration
- Notifications are displayed for 5 seconds (5000ms)
- Can be clicked to dismiss earlier on some platforms

## Platform Support

### Fully Supported
- **Windows**: System tray icon and native notifications
- **Linux**: System tray icon and native notifications (requires system tray support)
- **macOS**: System tray icon and native notifications

### Limited Support
- Systems without system tray will fall back to message dialogs
- Headless environments (no GUI) will skip notifications gracefully

## Code Integration

The notification system is fully integrated with the existing process execution flow:

1. **Process Completion** (`on_proc_finished`):
   - Checks exit code
   - Sends appropriate notification based on success/failure

2. **Process Errors** (`on_proc_error`):
   - Catches process-level errors
   - Sends error notification with details

3. **Settings Persistence**:
   - User preference saved on toggle
   - Loaded on application startup

## Future Enhancements

Potential improvements for the notification system:

- [ ] Custom notification sounds
- [ ] Notification history/log
- [ ] Configurable notification duration
- [ ] Rich notifications with action buttons (e.g., "View Log", "Re-run")
- [ ] Summary notifications for batch operations
- [ ] Notification categories/filtering
- [ ] Desktop notification badges (e.g., show number of completed scripts)

## Troubleshooting

### Notifications Not Appearing

1. **Check if notifications are enabled**:
   - Look for 🔔 icon in the toolbar
   - If showing 🔕, click to enable

2. **System tray not available**:
   - On Linux, ensure your desktop environment supports system tray
   - Install system tray extensions if needed

3. **Permissions**:
   - Some systems require notification permissions
   - Check system settings to ensure the application can send notifications

### System Tray Icon Not Appearing

- The application checks for system tray availability before creating the icon
- On systems without tray support, notifications will use message dialogs instead
- This is expected behavior and doesn't affect functionality

## Technical Notes

### QSystemTrayIcon Availability
The application checks `QSystemTrayIcon.isSystemTrayAvailable()` before creating the tray icon. This ensures compatibility across different environments.

### Notification Fallback Logic
```python
if self.tray_icon and self.tray_icon.isVisible():
    # Use system tray notification
    self.tray_icon.showMessage(title, message, icon, 5000)
else:
    # Fall back to message dialog
    msg = QMessageBox()
    # ... show dialog
```

This ensures users always receive notifications regardless of system capabilities.
