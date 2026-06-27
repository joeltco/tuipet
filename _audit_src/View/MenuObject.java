/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.Utility;
import View.SpriteObj;

public class MenuObject {
    private SpriteObj _object;
    private String _image;

    public SpriteObj getSpriteObj() {
        return this._object;
    }

    public MenuObject(SpriteObj object, String image) {
        this._object = object;
        this._image = image;
    }

    public void draw() {
        if (!Utility.isBlank(this._image)) {
            this._object.setAltIcon(this._image);
        }
        this._object.setVisible(true);
    }

    public void setVisible(boolean v) {
        this._object.setVisible(v);
    }
}

