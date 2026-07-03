# 🖱️ Mouse Jiggler

A cross-platform mouse jiggler that simulates natural mouse movements to prevent inactivity status in Microsoft Teams, Slack, Zoom, Discord, and other applications.

Built with system-level APIs:
- Windows: SendInput API (user32.dll)
- macOS: CoreGraphics (Quartz) Events

## Features

- Cross-platform (Windows 7/8/10/11 & macOS 10.15+)
- System-level APIs for reliable input simulation
- Time window control (schedule active hours)
- Multiple movement patterns (random, circle, zigzag)
- Smooth multi-step movements
- Zero dependencies on Windows
- Minimal resource usage (CPU < 0.1%, RAM ~15-20 MB)
- Real-time status feedback

## Requirements

- Python 3.8 or higher
- Windows: No additional dependencies
- macOS: pyobjc-framework-Quartz package
- macOS: Accessibility permissions for Terminal/IDE

## Quick Start

### Windows Setup

    # Install UV package manager
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Create and activate virtual environment
    uv venv
    .venv\Scripts\activate
    
    # Test and run (no dependencies needed!)
    python mouse_jiggler.py --test
    python mouse_jiggler.py

### macOS Setup

    # Install UV package manager
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Create and activate virtual environment
    uv venv
    source .venv/bin/activate
    
    # Install Quartz dependency
    uv pip install pyobjc-framework-Quartz
    
    # Test and run
    python mouse_jiggler.py --test
    python mouse_jiggler.py

### Alternative: Using pip

    # Install UV
    pip install uv
    
    # Create and activate virtual environment
    uv venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    
    # macOS: Install dependency
    uv pip install pyobjc-framework-Quartz
    
    # Test and run
    python mouse_jiggler.py --test
    python mouse_jiggler.py

## Usage Guide

### Basic Commands

    # Default settings (60 min, 30s interval, ±3px, random, 9AM-5PM)
    python mouse_jiggler.py
    
    # Run for specific duration
    python mouse_jiggler.py -d 120    # 2 hours
    python mouse_jiggler.py -d 30     # 30 minutes
    python mouse_jiggler.py -d 0      # Run indefinitely
    
    # Adjust interval
    python mouse_jiggler.py -i 15     # Every 15 seconds
    python mouse_jiggler.py -i 45     # Every 45 seconds
    python mouse_jiggler.py -i 60     # Every 60 seconds

### Movement Patterns

    # Random movement (default)
    python mouse_jiggler.py --pattern random
    python mouse_jiggler.py -r 5 --pattern random     # ±5 pixels
    
    # Circular movement
    python mouse_jiggler.py --pattern circle
    python mouse_jiggler.py --pattern circle -r 5 -s 8 -i 20  # Slow circles
    
    # Zigzag movement
    python mouse_jiggler.py --pattern zigzag
    python mouse_jiggler.py --pattern zigzag -r 5      # Wide zigzag

### Time Window Control

    # Custom working hours
    python mouse_jiggler.py --time-start 08:00 --time-end 18:00
    
    # Night shift (10 PM to 6 AM)
    python mouse_jiggler.py --time-start 22:00 --time-end 06:00
    
    # 24/7 operation (no time restrictions)
    python mouse_jiggler.py --no-time-window
    
    # Check current time window status
    python mouse_jiggler.py --status

### Complete Examples

    # Office worker (conservative)
    python mouse_jiggler.py -d 0 -i 45 -r 2 -s 6 --time-start 08:30 --time-end 17:30 --pattern random
    
    # Meeting mode (active)
    python mouse_jiggler.py -d 120 -i 20 -r 3 -s 4 --pattern circle --no-time-window
    
    # Stealth mode (minimal)
    python mouse_jiggler.py -d 0 -i 60 -r 1 -s 10 --time-start 09:00 --time-end 17:00
    
    # Night owl setup
    python mouse_jiggler.py -d 0 -i 30 -r 3 --time-start 20:00 --time-end 04:00 --pattern zigzag
    
    # Weekend mode
    python mouse_jiggler.py -d 0 -i 45 --no-time-window -r 2 -s 5

## Configuration Reference

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| --duration | -d | 60 | Duration in minutes (0 = infinite) |
| --interval | -i | 30 | Seconds between movements |
| --range | -r | 3 | Maximum pixel movement per axis |
| --smooth | -s | 4 | Number of steps for smooth movement |
| --pattern | -p | random | Movement pattern: random, circle, zigzag |
| --time-start | | 09:00 | Active window start time (HH:MM) |
| --time-end | | 17:00 | Active window end time (HH:MM) |
| --no-time-window | | flag | Disable time restrictions (24/7) |
| --test | | flag | Test mouse API and exit |
| --status | | flag | Show time window status |

### Movement Pattern Details

- random: Random direction and distance within range. Best for general use.
- circle: Continuous circular motion. Best for long meetings and presentations.
- zigzag: Left-right zigzag pattern. Simulates reading/scanning behavior.

### Time Window Logic

Standard working hours (9-5):
    Active: 9:00 AM to 5:00 PM
    Inactive: 5:00 PM to 9:00 AM next day

Overnight shift (10-6):
    Active: 10:00 PM to 6:00 AM next day
    Inactive: 6:00 AM to 10:00 PM

Split shifts require two instances:
    # Morning session
    python mouse_jiggler.py -d 240 --time-start 09:00 --time-end 13:00
    # Afternoon session
    python mouse_jiggler.py -d 240 --time-start 14:00 --time-end 18:00

## macOS Setup

### Granting Accessibility Permissions

1. Open System Settings > Privacy & Security > Accessibility
2. Click the + button or toggle the switch for your application:
   - Terminal.app (/Applications/Utilities/Terminal.app)
   - iTerm2.app (/Applications/iTerm.app)
   - Your IDE (VS Code, PyCharm, etc.)
3. Enable the permission (toggle to ON/blue)
4. Restart the application

### Testing Permissions

    python mouse_jiggler.py --test
    
    # Success:
    # ✅ Mausbewegung erfolgreich!
    
    # Failure:
    # ❌ Fehler: Mouse control not authorized

### Resetting Permissions

    sudo tccutil reset Accessibility
    # Then re-grant permission to your application

### macOS Version Notes

- macOS Ventura/Sonoma: May need to add both Terminal AND Python
- macOS Monterey and earlier: Adding Terminal is usually sufficient
- Apple Silicon (M1/M2/M3): May need --no-cache-dir for pip install

## Windows Notes

### Zero-Dependency Operation

The Windows version works out of the box:
- No pip packages required
- No system modifications
- No administrator privileges
- Portable: can run from USB drive

### Compatibility

- Windows 11: All editions
- Windows 10: All editions
- Windows 8/8.1: Fully supported
- Windows 7: SP1 or later required
- Windows XP/Vista: Not supported (Python 3.8+ requirement)

### Running on Windows

As a regular user:
    python mouse_jiggler.py

With Python launcher:
    py mouse_jiggler.py

As a background process:
    Start-Process python -ArgumentList "mouse_jiggler.py -d 0" -WindowStyle Hidden

Create a shortcut:
    1. Right-click > New > Shortcut
    2. Location: pythonw.exe C:\path\to\mouse_jiggler.py -d 0
    3. Set to run minimized
    4. Optional: Add to startup folder

## Technical Details

### Windows: SendInput API

The script uses the SendInput function from user32.dll with MOUSEINPUT structures.
Movement flags used:
- MOUSEEVENTF_MOVE (0x0001): Movement occurred
- MOUSEEVENTF_ABSOLUTE (0x8000): Absolute coordinates (0-65535 range)

Why SendInput instead of SetCursorPos?
- SendInput injects at hardware input level
- SetCursorPos only moves cursor visually
- Applications can detect SetCursorPos but not SendInput
- Teams/Slack look for hardware-level events

### macOS: CoreGraphics Events

The script creates mouse events using CGEventCreateMouseEvent and posts them
via CGEventPost to the kCGHIDEventTap (hardware input level).

Delta values for relative movement are set using:
- kCGMouseEventDeltaX
- kCGMouseEventDeltaY

### Smooth Movement Algorithm

Movements are divided into micro-steps:
1. Calculate total delta (dx, dy)
2. Divide into N steps
3. Send each micro-step individually
4. Small delay (0.003s) between steps
5. Result: Fluid, natural-looking movement

## Use Cases

1. Preventing screen lock during presentations
2. Long-running processes (downloads, computations)
3. Monitoring dashboards during shifts
4. Testing and development
5. Virtual machine management
6. Remote desktop sessions

## Development

### Project Structure

    mouse-jiggler/
    ├── mouse_jiggler.py    # Main script
    ├── pyproject.toml      # Project configuration
    └── README.md          # Documentation

### Using as a Python Module

    from mouse_jiggler import MouseJiggler, TimeWindow
    
    # Basic usage
    jiggler = MouseJiggler()
    jiggler.jiggle(duration_minutes=5, interval_seconds=10)
    
    # Custom time window
    time_window = TimeWindow("09:00", "17:00")
    jiggler = MouseJiggler(time_window)
    jiggler.jiggle(
        duration_minutes=None,
        interval_seconds=30,
        movement_range=3,
        smooth_steps=4,
        pattern="random"
    )

### Creating Executables

Windows (.exe):
    pip install pyinstaller
    pyinstaller --onefile --console mouse_jiggler.py
    pyinstaller --onefile --noconsole mouse_jiggler.py  # No console window

macOS (.app):
    pip install py2app
    python setup.py py2app

## Troubleshooting

### Mouse not moving (Windows)
- Run: python mouse_jiggler.py --test
- Check antivirus isn't blocking SendInput
- Try running as administrator
- Update Windows if using Windows 7

### Mouse not moving (macOS)
- Run: python mouse_jiggler.py --test
- Check System Settings > Privacy > Accessibility
- Toggle permission off and on again
- Restart Terminal/IDE
- Reset permissions: sudo tccutil reset Accessibility

### Module not found (macOS)
    uv pip install pyobjc-framework-Quartz
    # If on Apple Silicon:
    pip install --no-cache-dir pyobjc-framework-Quartz

### Time window issues
- Check system time is correct
- Use --status to verify configuration
- Try --no-time-window to test without restrictions
- Ensure 24-hour format for times

### High CPU usage
- Increase interval: -i 60
- Reduce smoothness: -s 2
- Use simpler pattern

## FAQ

Q: Will this get me in trouble at work?
A: Check your company's IT policies. Some organizations consider automatic
   mouse movement a violation of acceptable use policies.

Q: Can IT detect this?
A: Movements are at hardware input level, indistinguishable from real mouse
   movements. However, consistent patterns could theoretically be detected.

Q: Does this work with Teams/Slack/Zoom?
A: Yes, works with any application that tracks mouse movement.

Q: Will it prevent screen saver/sleep?
A: Yes, mouse movement resets the system idle timer.

Q: Do I need admin rights?
A: No, standard user permissions are sufficient.

Q: Can I run multiple instances?
A: Yes, each instance operates independently.

Q: What settings are least detectable?
A: Random pattern, 1-2px range, 8-10 smooth steps, 45-60s interval.

Q: How long can it run continuously?
A: Indefinitely with minimal resources and no known memory leaks.

Q: Does it work with multiple monitors?
A: Yes, moves mouse on whatever screen the cursor is currently on.

Q: Can I change settings while running?
A: No, stop with Ctrl+C and restart with new parameters.

## Best Practices

1. Check company policies before using
2. Use conservative settings (small movements, longer intervals)
3. Enable time windows to save resources
4. Test with --test before long runs
5. Create aliases for common configurations:

    # Linux/macOS aliases
    alias jiggle-meeting='python mouse_jiggler.py -d 60 -i 20 -r 2 -s 6'
    alias jiggle-day='python mouse_jiggler.py -d 0 -i 45 -r 1 -s 10'

## Performance

- CPU Usage: Less than 0.1%
- Memory Usage: 15-20 MB
- Network Activity: None
- Disk Activity: None during operation
- Battery Impact: Negligible

## Contributing

Contributions welcome! Ideas for improvement:
- Linux/X11 support (using Xlib/XTest)
- GUI interface
- System tray integration
- Additional movement patterns
- Configuration file support
- Activity logging

## Changelog

v2.0.0 (Current):
- Added SendInput API for Windows
- Added CGEvent for macOS
- Multiple movement patterns
- Time window control
- Smooth multi-step movements
- Complete rewrite for system-level APIs

v1.0.0:
- Initial release with basic jiggling
- Cross-platform via pyautogui
- Basic configuration options

## License

MIT License - See LICENSE file for details.

## Disclaimer

This tool is intended for legitimate use cases such as:
- Preventing screen locks during presentations
- Maintaining presence during long-running processes
- Testing and development purposes

Please use responsibly and in accordance with your organization's policies.
The authors are not responsible for any consequences from using this software.