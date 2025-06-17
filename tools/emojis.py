# Current emoji -> MinTTY compatible alternative
EMOJI_MAP = {
    "🚀": "↗",     # Rocket -> Up-right arrow
    "🤖": "⚙",     # Robot -> Gear symbol
    "📦": "■",     # Package -> Filled square
    "⏰": "⏲",     # Clock -> Timer clock (works in MinTTY)
    "🆔": "ID",    # ID badge -> Just text
    "💻": "⌨",     # Computer -> Keyboard
    "📂": "□",     # Folder -> Square
    "✅": "✓",     # Check mark -> Simple check
    "🔄": "⟲",     # Refresh -> Circular arrow
    "⚠️": "⚠",     # Warning -> Warning sign (remove emoji modifier)
    "❌": "✗",     # Cross -> Simple X
    "🔧": "⚙",     # Wrench -> Gear
    "📊": "▬",     # Chart -> Bar
    "🌐": "○",     # Globe -> Circle
    "🎯": "●",     # Target -> Filled circle
    "⭐": "★",     # Star -> Filled star
    "🔍": "◉",     # Magnifier -> Target circle
    "📁": "▶",     # Folder -> Right arrow
    "🛠️": "⚒",     # Tools -> Hammer and pick
    "📈": "↗",     # Chart up -> Up arrow
    "📉": "↘",     # Chart down -> Down arrow
    "🎉": "✦",     # Party -> Sparkle
    "🎊": "※",     # Confetti -> Reference mark
    "💡": "◐",     # Bulb -> Half circle
    "🔔": "♪",     # Bell -> Musical note
    "🔕": "♫",     # Bell slash -> Musical notes
    "📝": "✎",     # Memo -> Pencil
    "📄": "⎘",     # Document -> Page
    "🗂️": "≡",     # File dividers -> Three lines
    "🗃️": "▤",     # File cabinet -> Square with fill
    "📋": "☰",     # Clipboard -> Three horizontal lines
}

# Box drawing characters for UI elements
BOX_CHARS = {
    "top_left": "┌",
    "top_right": "┐", 
    "bottom_left": "└",
    "bottom_right": "┘",
    "horizontal": "─",
    "vertical": "│",
    "cross": "┼",
    "tee_down": "┬",
    "tee_up": "┴",
    "tee_right": "├",
    "tee_left": "┤"
}

# Status indicators
STATUS_CHARS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "question": "?",
    "running": "⟲", 
    "stopped": "■",
    "connected": "●",
    "disconnected": "○"
}