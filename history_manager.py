#!/usr/bin/env python3
"""
History Manager - Undo/Redo Stack Management
Manages command history for undo/redo operations
"""


class HistoryManager:
    """Manages undo/redo history"""
    def __init__(self, max_history=50):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history

    def execute_command(self, command):
        """Execute command and add to history"""
        command.execute()
        self.undo_stack.append(command)

        # Clear redo stack when new command is executed
        self.redo_stack.clear()

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self):
        """Undo the last command"""
        if not self.undo_stack:
            return False

        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self):
        """Redo the last undone command"""
        if not self.redo_stack:
            return False

        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0
