/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.ClockTic;
import Model.CrashEntry;
import Model.Enum;
import View.JTextFieldLimit;
import View.SoundConfig;
import View.SoundObj;
import View.ViewConfig;
import java.awt.Component;
import java.awt.KeyEventDispatcher;
import java.awt.KeyboardFocusManager;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyEvent;
import java.awt.event.MouseEvent;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.ConcurrentModificationException;
import java.util.List;
import javax.swing.JFrame;
import javax.swing.JTextField;
import javax.swing.text.BadLocationException;

public class KeyboardCursor {
    private ArrayList<Component> _interactiveButtons = new ArrayList();
    private SoundObj _sounds;
    private int _cursorPosition;
    private ClockTic _controller;
    private JFrame _frame;
    private final char[] _alphabet = " abcdefghijklmnopqrstuvwxyz.:/0123456789#".toCharArray();
    private int _charPosition = -1;
    private int _stringPosition = 0;
    private KeyEventDispatcher _dispatcher;
    private boolean _cPressed;

    public boolean getCPressed() {
        return this._cPressed;
    }

    private boolean isTextField() {
        JTextField f = new JTextField();
        boolean isTextField = false;
        if (this._cursorPosition < this._interactiveButtons.size() && this._cursorPosition >= 0) {
            try {
                isTextField = this._interactiveButtons.get(this._cursorPosition).getClass().isInstance(f);
            }
            catch (ArrayIndexOutOfBoundsException | NullPointerException runtimeException) {
                // empty catch block
            }
        }
        return isTextField;
    }

    private boolean isTextField(int position) {
        JTextField f = new JTextField();
        boolean isTextField = false;
        if (position < this._interactiveButtons.size() && position >= 0) {
            isTextField = this._interactiveButtons.get(position).getClass().isInstance(f);
        }
        return isTextField;
    }

    private boolean isTextField(Component obj) {
        JTextField f = new JTextField();
        if (obj != null) {
            return obj.getClass().isInstance(f);
        }
        return false;
    }

    public int getTextFieldPosition() {
        int p = -1;
        try {
            for (int i = 0; i < this._interactiveButtons.size(); ++i) {
                if (this._interactiveButtons.size() <= i || !this.isTextField(this._interactiveButtons.get(i))) continue;
                p = i;
                break;
            }
        }
        catch (ArrayIndexOutOfBoundsException arrayIndexOutOfBoundsException) {
            // empty catch block
        }
        return p;
    }

    public boolean textFieldHasFocus() {
        boolean focus = false;
        try {
            for (Component o : this._interactiveButtons) {
                if (!this.isTextField() || !(focus = o.hasFocus())) continue;
                break;
            }
        }
        catch (ConcurrentModificationException e) {
            e.printStackTrace();
        }
        return focus;
    }

    public void setCursorPosition(int p) {
        this._cursorPosition = p;
    }

    public int getCursorPosition() {
        return this._cursorPosition;
    }

    public List<Component> getInteractiveButtons() {
        return Collections.synchronizedList(this._interactiveButtons);
    }

    public void insertBefore(Component old, Component c) {
        int index = this.getComponentIndex(old);
        if (index != -1) {
            this._interactiveButtons.add(index, c);
        }
    }

    public void insertAfter(Component old, Component c) {
        int index = this.getComponentIndex(old) + 1;
        if (index != -1) {
            if (index < this._interactiveButtons.size()) {
                this._interactiveButtons.add(index, c);
            } else {
                this._interactiveButtons.add(c);
            }
        }
    }

    public void replace(Component old, Component c) {
        int index = this.getComponentIndex(old);
        if (index != -1) {
            this._interactiveButtons.set(index, c);
        }
    }

    public int getComponentIndex(Component c) {
        int index = -1;
        for (int i = 0; i < this._interactiveButtons.size(); ++i) {
            if (this._interactiveButtons.get(i) != c) continue;
            index = i;
            break;
        }
        return index;
    }

    public void addButton(Component c) {
        this._interactiveButtons.add(c);
    }

    public void addButton(Component c, int index) {
        this._interactiveButtons.add(index, c);
    }

    public void clearInteractiveButtons() {
        try {
            this._interactiveButtons.clear();
        }
        catch (ArrayIndexOutOfBoundsException arrayIndexOutOfBoundsException) {
            // empty catch block
        }
    }

    public KeyboardCursor(ClockTic controller, JFrame frame, SoundObj sounds) {
        this._controller = controller;
        this._frame = frame;
        this._sounds = sounds;
        this._dispatcher = new KeyEventDispatcher(){

            @Override
            public boolean dispatchKeyEvent(KeyEvent e) {
                KeyboardCursor.this._cPressed = false;
                if (ViewConfig._enableKeyboardCursor) {
                    int keyCode = e.getKeyCode();
                    int keyID = e.getID();
                    boolean textField = KeyboardCursor.this.isTextField();
                    if (!textField) {
                        switch (keyID) {
                            case 401: {
                                if (keyCode == ViewConfig._aButton) {
                                    KeyboardCursor.this.cycleCursor();
                                    return true;
                                }
                                if (keyCode == ViewConfig._bButton) {
                                    KeyboardCursor.this.reverseCursor();
                                    return true;
                                }
                                if (keyCode == ViewConfig._cButton) {
                                    KeyboardCursor.this._cPressed = true;
                                    KeyboardCursor.this.selectCursor();
                                    return true;
                                }
                                if (keyCode == ViewConfig._dButton) {
                                    KeyboardCursor.this.cancelCursor();
                                    return true;
                                }
                                return false;
                            }
                            case 402: {
                                if (keyCode == ViewConfig._cButton) {
                                    KeyboardCursor.this.releaseCursor();
                                    return true;
                                }
                                return false;
                            }
                        }
                        return false;
                    }
                    if (ViewConfig._enableTextFieldKeyboardCursor && keyID == 401) {
                        if (keyCode == ViewConfig._aButton) {
                            if (KeyboardCursor.this._cursorPosition >= 0) {
                                KeyboardCursor.this.cycleChar(true);
                            }
                            return true;
                        }
                        if (keyCode == ViewConfig._bButton) {
                            if (KeyboardCursor.this._cursorPosition >= 0) {
                                KeyboardCursor.this.cycleChar(false);
                            }
                            return true;
                        }
                        if (keyCode == ViewConfig._cButton) {
                            KeyboardCursor.this.selectChar();
                            return true;
                        }
                        if (keyCode == ViewConfig._dButton) {
                            KeyboardCursor.this.cancelChar();
                            return true;
                        }
                        if (keyCode == 8) {
                            KeyboardCursor.this._charPosition = 0;
                            KeyboardCursor.this._stringPosition--;
                            if (KeyboardCursor.this._stringPosition < 0) {
                                KeyboardCursor.this._stringPosition = 0;
                            }
                            return false;
                        }
                        return false;
                    }
                    return false;
                }
                return false;
            }
        };
        KeyboardFocusManager.getCurrentKeyboardFocusManager().addKeyEventDispatcher(this._dispatcher);
    }

    public void incCursor() {
        ++this._cursorPosition;
        if (this._cursorPosition >= this._interactiveButtons.size()) {
            this._cursorPosition = 0;
        }
    }

    public void decCursor() {
        --this._cursorPosition;
        if (this._cursorPosition < 0) {
            this._cursorPosition = this._interactiveButtons.size() - 1;
        }
    }

    private void nextChar() {
        this._sounds.playSound(SoundConfig._nextKeyboardCharacter);
        ++this._charPosition;
        if (this._charPosition >= this._alphabet.length) {
            this._charPosition = 0;
        }
    }

    private void previousChar() {
        this._sounds.playSound(SoundConfig._previousKeyboardCharacter);
        --this._charPosition;
        if (this._charPosition < 0) {
            this._charPosition = this._alphabet.length - 1;
        }
    }

    private void cycleChar(boolean forward) {
        JTextField stringPane = (JTextField)this._interactiveButtons.get(this._cursorPosition);
        if (forward) {
            this.nextChar();
        } else {
            this.previousChar();
        }
        char[] string = stringPane.getText().toCharArray();
        if (string.length == 0) {
            String s = "" + this._alphabet[this._charPosition];
            stringPane.setText(s);
        } else if (string.length > this._stringPosition) {
            string[this._stringPosition] = this._alphabet[this._charPosition];
            stringPane.setText(String.valueOf(string));
        }
        if (this._stringPosition >= 0 && this._stringPosition <= string.length) {
            stringPane.setCaretPosition(this._stringPosition + 1);
        }
    }

    public void addInteractiveButtons(Component[] objs) {
        this._charPosition = 0;
        this._stringPosition = 0;
        try {
            this._interactiveButtons.clear();
            if (this._interactiveButtons != null) {
                this._interactiveButtons.addAll(new ArrayList<Component>(Arrays.asList(objs)));
            }
        }
        catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Index out of bounds when clearing array list");
        }
    }

    private void cycleCursor() {
        int oldPosition = this._cursorPosition;
        this.incCursor();
        this.moveCursor(oldPosition);
    }

    private void reverseCursor() {
        int oldPosition = this._cursorPosition;
        this.decCursor();
        this.moveCursor(oldPosition);
    }

    public void moveCursor(int oldPosition) {
        try {
            if (this._cursorPosition < this._interactiveButtons.size() && this._cursorPosition >= 0) {
                Component obj;
                if (oldPosition >= 0 && oldPosition < this._interactiveButtons.size()) {
                    obj = this._interactiveButtons.get(oldPosition);
                    this.mouseExit(obj);
                }
                obj = this._interactiveButtons.get(this._cursorPosition);
                this.mouseEnter(obj);
            }
        }
        catch (ArrayIndexOutOfBoundsException e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void selectCursor() {
        try {
            if (this._cursorPosition < this._interactiveButtons.size() && this._cursorPosition >= 0) {
                Component obj = this._interactiveButtons.get(this._cursorPosition);
                this.mousePress(obj);
            }
        }
        catch (ArrayIndexOutOfBoundsException e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void selectChar() {
        if (this._cursorPosition >= 0) {
            JTextField stringPane = (JTextField)this._interactiveButtons.get(this._cursorPosition);
            JTextFieldLimit j = (JTextFieldLimit)stringPane.getDocument();
            char[] string = stringPane.getText().toCharArray();
            if (this._alphabet[this._charPosition] == '#') {
                try {
                    stringPane.setText(stringPane.getText(0, stringPane.getText().toCharArray().length - 1));
                }
                catch (BadLocationException badLocationException) {
                    // empty catch block
                }
                this.actionPerformed(stringPane);
            } else if (string.length != 0 && this._stringPosition < j.getLimit() - 1) {
                this._sounds.playSound(SoundConfig._selectKeyboardCharacter);
                ++this._stringPosition;
                stringPane.setCaretPosition(this._stringPosition);
                if (this._stringPosition > stringPane.getText().length() - 1) {
                    stringPane.setText(stringPane.getText() + " ");
                }
                this.setExistingCharPosition(string);
                this.previousChar();
                this.cycleChar(true);
            } else if (this._stringPosition >= j.getLimit() - 1) {
                int oldPosition = this._cursorPosition;
                this.incCursor();
                this._interactiveButtons.get(this._cursorPosition).requestFocus();
                this.moveCursor(oldPosition);
            }
        }
    }

    private void releaseCursor() {
        try {
            if (this._cursorPosition < this._interactiveButtons.size() && this._cursorPosition >= 0) {
                Component obj = this._interactiveButtons.get(this._cursorPosition);
                this.mouseRelease(obj);
            }
        }
        catch (ArrayIndexOutOfBoundsException e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void cancelCursor() {
        this._sounds.playSound(SoundConfig._cancel);
        if (this._controller.getCurrentMenu() != Enum.Menu.None) {
            this._controller.onBack();
        }
        if (this._cursorPosition < this._interactiveButtons.size() && this._cursorPosition >= 0) {
            Component obj = this._interactiveButtons.get(this._cursorPosition);
            this.mouseExit(obj);
        }
        this._cursorPosition = -1;
    }

    private void cancelChar() {
        if (this._cursorPosition >= 0) {
            JTextField stringPane = (JTextField)this._interactiveButtons.get(this._cursorPosition);
            char[] string = stringPane.getText().toCharArray();
            if (string.length > 0) {
                this._sounds.playSound(SoundConfig._selectKeyboardCharacter);
                string[this._stringPosition] = 32;
                stringPane.setText(String.valueOf(string));
                stringPane.setCaretPosition(this._stringPosition);
            } else {
                this._sounds.playSound(SoundConfig._cancelKeyboardCharacter);
            }
            --this._stringPosition;
            if (this._stringPosition < 0) {
                this._stringPosition = 0;
                int oldPosition = this._cursorPosition;
                this.incCursor();
                this._interactiveButtons.get(this._cursorPosition).requestFocus();
                this.moveCursor(oldPosition);
            } else {
                this.setExistingCharPosition(string);
            }
        }
    }

    private void actionPerformed(Component obj) {
        try {
            if (this.isTextField(obj)) {
                ((ActionListener[])obj.getListeners(ActionListener.class))[0].actionPerformed(new ActionEvent(obj, 1001, null));
            }
        }
        catch (ArrayIndexOutOfBoundsException | NullPointerException runtimeException) {
            // empty catch block
        }
    }

    private void mouseEnter(Component obj) {
        try {
            if (!this.isTextField(obj)) {
                obj.getMouseListeners()[0].mouseEntered(new MouseEvent(obj, 504, 1L, 0, 1, 1, 1, false));
            } else {
                this.mouseEnterStringPane(obj);
            }
        }
        catch (ArrayIndexOutOfBoundsException | NullPointerException runtimeException) {
            // empty catch block
        }
    }

    private void mousePress(Component obj) {
        try {
            if (!this.isTextField(obj)) {
                obj.getMouseListeners()[0].mousePressed(new MouseEvent(obj, 501, 1L, 0, 1, 1, 1, false));
            } else {
                this.mousePressStringPane(obj);
            }
        }
        catch (NullPointerException nullPointerException) {
            // empty catch block
        }
    }

    private void mouseExit(Component obj) {
        try {
            if (!this.isTextField(obj)) {
                obj.getMouseListeners()[0].mouseExited(new MouseEvent(obj, 505, 1L, 0, 1, 1, 1, false));
            } else {
                this.mouseExitStringPane(obj);
            }
        }
        catch (ArrayIndexOutOfBoundsException | NullPointerException runtimeException) {
            // empty catch block
        }
    }

    private void mouseRelease(Component obj) {
        try {
            if (!this.isTextField(obj)) {
                obj.getMouseListeners()[0].mouseReleased(new MouseEvent(obj, 502, 1L, 0, 1, 1, 1, false));
            }
        }
        catch (NullPointerException nullPointerException) {
            // empty catch block
        }
    }

    private void mouseEnterStringPane(Component stringPane) {
        this._sounds.playSound(SoundConfig._select);
        this.resetStringPane(stringPane);
        this._charPosition = 0;
    }

    private void mouseExitStringPane(Component stringPane) {
    }

    private void mousePressStringPane(Component stringPane) {
        this._sounds.playSound(SoundConfig._click);
    }

    public void resetStringPane(Component obj) {
        JTextField stringPane = (JTextField)obj;
        this._stringPosition = 0;
        stringPane.setText(ViewConfig._enableTextFieldKeyboardCursor ? " " : "");
        this.setExistingCharPosition(stringPane.getText().toCharArray());
        stringPane.requestFocus();
        stringPane.setCaretPosition(this._stringPosition);
    }

    private void setExistingCharPosition(char[] string) {
        if (string.length > this._stringPosition) {
            char c = string[this._stringPosition];
            for (int i = 0; i < this._alphabet.length; ++i) {
                if (this._alphabet[i] != c) continue;
                this._charPosition = i;
                break;
            }
        } else {
            this._charPosition = -1;
        }
    }

    public void dispose() {
        try {
            this._interactiveButtons.clear();
        }
        catch (ArrayIndexOutOfBoundsException arrayIndexOutOfBoundsException) {
            // empty catch block
        }
        KeyboardFocusManager.getCurrentKeyboardFocusManager().removeKeyEventDispatcher(this._dispatcher);
    }
}

