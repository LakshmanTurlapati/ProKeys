#!/usr/bin/env python3
"""
ProKeys - Clipboard Content Keystroke Emulator

This script reads content from the clipboard and emulates keystrokes to paste it
with accurate indentation and formatting. Useful for situations where standard
Ctrl+V doesn't work properly or when you need precise character-by-character pasting.

Usage:
    python prokeys.py [--delay DELAY] [--trigger-key KEY]

Options:
    --delay DELAY        Delay between keystrokes in seconds (default: 0.01)
    --trigger-key KEY    Key combination to trigger pasting (default: cmd+shift+v)
    --help              Show this help message
"""

import argparse
import time
import sys
import threading
import json
import os
from typing import Optional

try:
    import pyperclip
    import pynput
    from pynput import keyboard
    from pynput.keyboard import Key, Listener, KeyCode
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install them using: pip install pyperclip pynput")
    sys.exit(1)


CONFIG_FILE = "prokeys_config.json"

def wpm_to_delay(wpm: int) -> float:
    """Convert WPM to delay between keystrokes in seconds.
    
    More realistic calculation accounting for:
    - Natural typing rhythm
    - Application processing time  
    - Keystroke simulation overhead
    """
    # Base calculation: 60 / (WPM * 5) but adjusted for realism
    base_delay = 60.0 / (wpm * 5)
    
    # Add realistic overhead (20-50% depending on speed)
    if wpm < 60:
        # Slower speeds: minimal overhead
        return base_delay * 1.2
    elif wpm < 120:
        # Moderate speeds: some overhead
        return base_delay * 1.3
    elif wpm < 200:
        # Fast speeds: more overhead needed
        return base_delay * 1.4
    else:
        # Very fast speeds: significant overhead
        return base_delay * 1.5

def delay_to_wpm(delay: float) -> int:
    """Convert delay to WPM (approximate reverse calculation)."""
    if delay <= 0:
        return 9999
    
    # Reverse calculation accounting for overhead
    # This is approximate since the original calculation has variable overhead
    base_wpm = 60.0 / (delay * 5)
    
    # Estimate overhead and adjust
    if delay > 0.3:  # Corresponds to ~40 WPM
        return int(base_wpm / 1.2)
    elif delay > 0.15:  # Corresponds to ~80 WPM  
        return int(base_wpm / 1.3)
    elif delay > 0.08:  # Corresponds to ~150 WPM
        return int(base_wpm / 1.4)
    else:
        return int(base_wpm / 1.5)

def load_config() -> dict:
    """Load configuration from config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Default configuration
    return {
        "typing_speed_wpm": 250,
        "delay": wpm_to_delay(250),
        "trigger_key": "cmd+shift+v",
        "windows_mode": False
    }

def save_config(config: dict) -> bool:
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def validate_wpm(wpm: int) -> bool:
    """Validate WPM is in acceptable range."""
    return 99 <= wpm <= 5000

def set_typing_speed(wpm: int) -> bool:
    """Set typing speed in WPM."""
    if not validate_wpm(wpm):
        print(f"❌ Error: WPM must be between 99 and 5000. Got: {wpm}")
        return False
    
    config = load_config()
    config["typing_speed_wpm"] = wpm
    config["delay"] = wpm_to_delay(wpm)
    
    if save_config(config):
        print(f"✅ Typing speed set to {wpm} WPM")
        print(f"   Delay between keystrokes: {config['delay']:.4f} seconds")
        
        # Speed category
        if wpm < 30:
            category = "🐌 Very Slow"
        elif wpm < 60:
            category = "🚶 Slow"
        elif wpm < 120:
            category = "🚴 Moderate"
        elif wpm < 200:
            category = "🏃 Fast"
        elif wpm < 400:
            category = "🚀 Very Fast"
        else:
            category = "⚡ Lightning"
        
        print(f"   Speed category: {category}")
        return True
    else:
        return False

def show_config():
    """Display current configuration."""
    config = load_config()
    
    print("🎯 ProKeys Configuration")
    print("=" * 30)
    print(f"Typing Speed: {config['typing_speed_wpm']} WPM")
    print(f"Keystroke Delay: {config['delay']:.4f} seconds")
    print(f"Trigger Key: {config['trigger_key']}")
    
    # Speed reference
    print("\n📊 Speed Reference:")
    print("  99-149 WPM:   🚴 Moderate (recommended)")
    print(" 150-249 WPM:   🏃 Fast (may skip in some apps)")
    print(" 250-499 WPM:   🚀 Very Fast (for simple text)")
    print(" 500-999 WPM:   ⚡ Lightning (extreme speed)")
    print("1000-5000 WPM:  🚀💥 Ludicrous Speed (instant)")

def interactive_config():
    """Interactive configuration mode."""
    print("🎯 ProKeys Configuration")
    print("=" * 40)
    
    config = load_config()
    current_wpm = config["typing_speed_wpm"]
    
    print(f"Current typing speed: {current_wpm} WPM")
    print("\nSpeed recommendations:")
    print("  • 100-250 WPM: Best for most applications")
    print("  • 250-500 WPM: Faster but may skip in some apps")
    print("  • 500+ WPM: Very fast, simple text only")
    print("  • 1000+ WPM: Extreme speed")
    
    # Speed presets
    print("\n🚀 Quick Presets:")
    print("  [1] 100 WPM  - 🚴 Moderate")
    print("  [2] 250 WPM  - 🏃 Fast")
    print("  [3] 500 WPM  - 🚀 Very Fast")
    print("  [4] 1000 WPM - ⚡ Lightning")
    print("  [5] 2000 WPM - 🚀💥 Ludicrous")
    print("  [0] Custom WPM")
    
    while True:
        try:
            choice = input(f"\nSelect option (1-5 for presets, 0 for custom, Enter to cancel): ").strip()
            
            if not choice:
                print("No changes made.")
                return
            
            if choice == "1":
                wpm = 100
            elif choice == "2":
                wpm = 250
            elif choice == "3":
                wpm = 500
            elif choice == "4":
                wpm = 1000
            elif choice == "5":
                wpm = 2000
            elif choice == "0":
                custom_input = input("Enter custom WPM (99-5000): ").strip()
                if not custom_input:
                    print("No changes made.")
                    return
                wpm = int(custom_input)
            else:
                print("❌ Please enter a number between 0-5.")
                continue
            
            if validate_wpm(wpm):
                if set_typing_speed(wpm):
                    print("\n✅ Configuration updated successfully!")
                    return
                else:
                    print("\n❌ Failed to save configuration.")
                    return
            else:
                print(f"❌ Please enter a WPM between 99 and 5000.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nConfiguration cancelled.")
            return


class ProKeys:
    def __init__(self, delay: float = 0.01, trigger_key: str = "cmd+shift+v", windows_mode: bool = False, debug: bool = False):
        self.delay = delay
        self.trigger_key = trigger_key
        self.windows_mode = windows_mode
        self.debug = debug
        self.keyboard_controller = pynput.keyboard.Controller()
        self.listener = None
        self.running = False
        self.trigger_keys = self._parse_trigger_key(trigger_key)
        self.pressed_keys = set()
        
        
    def _parse_trigger_key(self, trigger_key: str) -> set:
        """Parse trigger key combination string into a set of keys."""
        key_mapping = {
            'ctrl': Key.ctrl_l,
            'shift': Key.shift_l,
            'alt': Key.alt_l,
            'cmd': Key.cmd,  # Use Key.cmd (not cmd_l)
            'super': Key.cmd,
            'win': Key.cmd,
        }
        
        keys = trigger_key.lower().split('+')
        parsed_keys = set()
        
        for key in keys:
            key = key.strip()
            if key in key_mapping:
                parsed_keys.add(key_mapping[key])
            elif len(key) == 1 and key.isalpha():
                # For letter keys, store as lowercase character
                parsed_keys.add(key.lower())
            elif len(key) == 1:
                # For other single characters (numbers, symbols)
                parsed_keys.add(key)
            else:
                # Handle special keys like 'space', 'enter', etc.
                try:
                    parsed_keys.add(getattr(Key, key))
                except AttributeError:
                    print(f"Warning: Unknown key '{key}' in trigger combination")
        
        return parsed_keys
    
    def get_clipboard_content(self) -> str:
        """Get content from clipboard."""
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return ""
    
    def type_content(self, content: str) -> None:
        """Type content using the most reliable method for the current platform."""
        if not content:
            print("Clipboard is empty or could not be read.")
            return
        
        print(f"Starting to type {len(content)} characters...")
        print("Press Ctrl+C to stop typing.")
        
        # Small delay before starting to type
        time.sleep(0.5)
        
        try:
            if self.windows_mode:
                # Use clipboard-based approach for Windows mode (most reliable)
                self._type_content_clipboard(content)
            else:
                # Use traditional character-by-character typing for Mac mode
                self._type_content_traditional(content)
                
        except KeyboardInterrupt:
            print("\n✗ Typing interrupted by user.")
        except Exception as e:
            print(f"\n✗ Error during typing: {e}")
            # Fallback to Unicode typing if primary method fails
            try:
                print("Trying fallback method...")
                self._type_content_unicode_fallback(content)
            except Exception as fallback_error:
                print(f"✗ Fallback method also failed: {fallback_error}")
    
    def _type_content_clipboard(self, content: str) -> None:
        """Type content using clipboard + Ctrl+V method (most reliable for Windows virtual desktop)."""
        if self.debug:
            print("[DEBUG] Using clipboard-based input method")
        
        try:
            # Store original clipboard content
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass  # Ignore if clipboard is empty or inaccessible
            
            # Set our content to clipboard
            pyperclip.copy(content)
            
            # Short delay to ensure clipboard is set
            time.sleep(0.1)
            
            # Send Ctrl+V to paste
            if self.debug:
                print("[DEBUG] Sending Ctrl+V to paste content")
            
            self.keyboard_controller.press(Key.ctrl_l)
            time.sleep(0.05)
            self.keyboard_controller.press(KeyCode.from_char('v'))
            time.sleep(0.05)
            self.keyboard_controller.release(KeyCode.from_char('v'))
            time.sleep(0.05)
            self.keyboard_controller.release(Key.ctrl_l)
            
            # Wait for paste to complete
            time.sleep(0.2)
            
            # Restore original clipboard content
            try:
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            except:
                pass  # Ignore if restoration fails
            
            print(f"✓ Successfully pasted {len(content)} characters using clipboard method!")
            
        except Exception as e:
            print(f"✗ Clipboard method failed: {e}")
            raise  # Re-raise to trigger fallback
    
    def _type_content_unicode_fallback(self, content: str) -> None:
        """Fallback method using pure Unicode typing (no virtual key codes)."""
        if self.debug:
            print("[DEBUG] Using Unicode fallback input method")
        
        try:
            # Use pure Unicode typing - let pynput handle all character translation
            self.keyboard_controller.type(content)
            
            print(f"✓ Successfully typed {len(content)} characters using Unicode method!")
            
        except Exception as e:
            print(f"✗ Unicode fallback method failed: {e}")
            raise
    
    def _type_content_traditional(self, content: str) -> None:
        """Traditional character-by-character typing for Mac mode."""
        lines = content.split('\n')
        total_chars = 0
        
        for line_num, line in enumerate(lines):
            if line_num > 0:
                # Press Enter to go to new line
                self.keyboard_controller.press(Key.enter)
                self.keyboard_controller.release(Key.enter)
                total_chars += 1
                
                if self.delay > 0:
                    time.sleep(self.delay)
                
                # Handle indentation smartly
                leading_whitespace = len(line) - len(line.lstrip())
                if leading_whitespace > 0:
                    # Clear any auto-indentation first by going to beginning of line
                    self.keyboard_controller.press(Key.home)
                    self.keyboard_controller.release(Key.home)
                    
                    if self.delay > 0:
                        time.sleep(self.delay * 2)  # Slightly longer delay
                    
                    # Type the exact indentation
                    for i in range(leading_whitespace):
                        if i < len(line) and line[i] == '\t':
                            self.keyboard_controller.press(Key.tab)
                            self.keyboard_controller.release(Key.tab)
                        else:
                            self.keyboard_controller.type(' ')
                        
                        if self.delay > 0:
                            time.sleep(self.delay)
                    
                    total_chars += leading_whitespace
                
                # Type the rest of the line (non-whitespace content)
                line_content = line.lstrip()
            else:
                # First line - type as-is
                line_content = line
            
            # Type the actual content of the line
            for char in line_content:
                if char == '\t':
                    self.keyboard_controller.press(Key.tab)
                    self.keyboard_controller.release(Key.tab)
                else:
                    try:
                        # Use normal typing for Mac mode
                        self.keyboard_controller.type(char)
                    except Exception as e:
                        print(f"Warning: Could not type character '{char}': {e}")
                        continue
                
                # Add delay between keystrokes
                if self.delay > 0:
                    time.sleep(self.delay)
                
                total_chars += 1
                
                # Print progress every 100 characters
                if total_chars % 100 == 0:
                    print(f"Progress: {total_chars}/{len(content)} characters typed")
        
        print(f"✓ Successfully typed {len(content)} characters!")
    
    def on_key_press(self, key):
        """Handle key press events."""
        try:
            # Convert character keys to lowercase for consistent matching
            if hasattr(key, 'char') and key.char:
                processed_key = key.char.lower()
            else:
                processed_key = key
                
            self.pressed_keys.add(processed_key)
            
            # Debug: Print key press (uncomment for debugging)
            # print(f"Key pressed: {processed_key} | Currently pressed: {self.pressed_keys}")
            
            # Check if trigger combination is pressed
            if self.trigger_keys.issubset(self.pressed_keys):
                print(f"\n🚀 Trigger activated! Reading clipboard and typing content...")
                # Run typing in a separate thread to avoid blocking the listener
                threading.Thread(target=self._handle_trigger, daemon=True).start()
                
        except UnicodeDecodeError:
            # Handle macOS pynput Unicode decode issues for special characters
            # This is common on macOS and shouldn't cause the app to exit
            pass
        except AttributeError:
            # Handle cases where key might not have expected attributes
            # This can happen with certain special keys on macOS
            pass
    
    def on_key_release(self, key):
        """Handle key release events."""
        try:
            # Convert character keys to lowercase for consistent matching
            if hasattr(key, 'char') and key.char:
                processed_key = key.char.lower()
            else:
                processed_key = key
                
            # Remove key from pressed keys set
            self.pressed_keys.discard(processed_key)
            
            # Debug: Print key release (uncomment for debugging)
            # print(f"Key released: {processed_key} | Currently pressed: {self.pressed_keys}")
            
            # Exit ONLY on actual Escape key - be very specific
            if key == Key.esc:
                print("\n👋 Exiting ProKeys...")
                return False
                
        except UnicodeDecodeError:
            # Handle macOS pynput Unicode decode issues for special characters
            # Only check for Escape if we can actually identify the key
            try:
                if key == Key.esc:
                    print("\n👋 Exiting ProKeys...")
                    return False
            except:
                # If we can't even check for Escape, just continue
                pass
        except AttributeError:
            # Handle cases where key might not have expected attributes
            # This can happen with certain special keys on macOS
            pass
    
    def _handle_trigger(self):
        """Handle the trigger key combination."""
        content = self.get_clipboard_content()
        if content:
            # Clear pressed keys to avoid interference
            self.pressed_keys.clear()
            self.type_content(content)
        else:
            print("No content found in clipboard.")
    
    def start_listening(self):
        """Start listening for key combinations."""
        print("🎯 ProKeys is now running in background!")
        print(f"📋 Trigger: {self.trigger_key}")
        print(f"⏱️  Delay: {self.delay}s between keystrokes")
        print("🔥 Copy anything, then press the trigger combination to paste with formatting")
        print("🚪 Press Escape to exit")
        print("-" * 50)
        
        self.running = True
        
        with Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        ) as listener:
            self.listener = listener
            listener.join()
    
    def paste_once(self):
        """Paste clipboard content once and exit."""
        print("🎯 ProKeys - One-time paste mode")
        content = self.get_clipboard_content()
        self.type_content(content)


def main():
    # Check if config subcommand is used
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        interactive_config()
        return
    
    # Load configuration
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description="ProKeys - Clipboard Content Keystroke Emulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python prokeys.py                          # Start with config settings ({config['typing_speed_wpm']} WPM)
    python prokeys.py config                   # Configure typing speed (9-999 WPM)
    python prokeys.py --delay 0.02             # Override delay (slower typing)
    python prokeys.py --trigger-key "ctrl+alt+v"  # Custom trigger key
    python prokeys.py --once                    # Paste once and exit

Configuration:
    Current: {config['typing_speed_wpm']} WPM, Delay: {config['delay']:.4f}s
    Use 'python prokeys.py config' to change typing speed
        """
    )
    
    parser.add_argument(
        '--delay', 
        type=float, 
        default=config['delay'],
        help=f'Delay between keystrokes in seconds (config: {config["delay"]:.4f}s)'
    )
    
    parser.add_argument(
        '--trigger-key',
        type=str,
        default=config['trigger_key'],
        help=f'Key combination to trigger pasting (config: {config["trigger_key"]})'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Paste clipboard content once and exit (no hotkey listening)'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current configuration and exit'
    )
    
    parser.add_argument(
        '--windows-mode',
        action='store_true',
        default=config.get('windows_mode', False),
        help=f'Use Windows keyboard layout mode (config: {config.get("windows_mode", False)})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode to see what keys are being sent'
    )
    
    
    args = parser.parse_args()
    
    # Show config if requested
    if args.show_config:
        show_config()
        return
    
    # Validate delay
    if args.delay < 0:
        print("Error: Delay cannot be negative")
        sys.exit(1)
    
    # Show current settings
    delay_to_wpm = 12.0 / args.delay if args.delay > 0 else 999
    print(f"⚡ ProKeys starting with {delay_to_wpm:.0f} WPM (delay: {args.delay:.4f}s)")
    if args.windows_mode:
        print(f"🪟 Windows mode enabled - using clipboard-based input for maximum compatibility")
    if args.debug:
        print("🐛 Debug mode enabled - will show input method details")
    
    try:
        prokeys = ProKeys(delay=args.delay, trigger_key=args.trigger_key, windows_mode=args.windows_mode, debug=args.debug)
        
        if args.once:
            prokeys.paste_once()
        else:
            prokeys.start_listening()
            
    except KeyboardInterrupt:
        print("\n👋 ProKeys terminated by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 