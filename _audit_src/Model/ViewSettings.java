/*
 * Decompiled with CFR 0.152.
 */
package Model;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

public class ViewSettings {
    private double _gameScale;
    private boolean _isSound = true;
    private boolean _isFocus = true;
    private boolean _isOnTop;
    private int _shell;

    public double getGameScale() {
        return this._gameScale;
    }

    public void setGameScale(double s) {
        this._gameScale = s;
    }

    public boolean isSound() {
        return this._isSound;
    }

    public void setSound(boolean b) {
        this._isSound = b;
    }

    public boolean isFocus() {
        return this._isFocus;
    }

    public void setFocus(boolean b) {
        this._isFocus = b;
    }

    public boolean isOnTop() {
        return this._isOnTop;
    }

    public void setOnTop(boolean b) {
        this._isOnTop = b;
    }

    public int getShell() {
        return this._shell;
    }

    public void setShell(int i) {
        this._shell = i;
    }

    public ViewSettings(double scale, boolean isSound, boolean focus, boolean isOnTop, int shell) {
        this._gameScale = scale;
        this._isSound = isSound;
        this._isFocus = focus;
        this._isOnTop = isOnTop;
        this._shell = shell;
    }

    public ViewSettings() {
    }

    public void saveLastSettings() {
        try (FileOutputStream saveFile = new FileOutputStream("files" + File.separator + "saves" + File.separator + "Shared" + File.separator + "settings.txt");
             ObjectOutputStream save = new ObjectOutputStream(saveFile);){
            save.writeObject(this._gameScale);
            save.writeObject(this._isSound);
            save.writeObject(this._isFocus);
            save.writeObject(this._isOnTop);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void loadSettings() {
        String path = "files" + File.separator + "saves" + File.separator + "Shared" + File.separator;
        File f = new File(path + "settings.txt");
        if (!f.exists()) {
            f = new File(path + "settings.sav");
        }
        if (f.exists()) {
            try {
                FileInputStream saveFile = new FileInputStream(f);
                ObjectInputStream save = new ObjectInputStream(saveFile);
                this._gameScale = (Double)save.readObject();
                this._isSound = (Boolean)save.readObject();
                this._isFocus = (Boolean)save.readObject();
                this._isOnTop = (Boolean)save.readObject();
                save.close();
            }
            catch (Exception e) {
                this._gameScale = 1.0;
                this._isSound = true;
                e.printStackTrace();
            }
        } else {
            this._gameScale = 1.0;
            this._isSound = true;
        }
        if ((f = new File("files/saves/Shared/settings.sav")).exists()) {
            f.delete();
        }
    }
}

