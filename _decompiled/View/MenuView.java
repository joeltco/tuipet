/*
 * Decompiled with CFR 0.152.
 */
package View;

import View.SpriteObjWIP;
import View.ViewUtil;
import java.util.HashMap;
import java.util.Map;

public class MenuView {
    private HashMap<String, SpriteObjWIP> _objects = new HashMap();

    public SpriteObjWIP getSpriteObj(String name) {
        return this._objects.get(name);
    }

    public void addSpriteObj(String name, SpriteObjWIP obj) {
        this._objects.put(name, obj);
    }

    public void addSpriteObj(SpriteObjWIP obj) {
        String name = ViewUtil.trimDirectory(obj.getSpriteLoc());
        this._objects.put(name, obj);
    }

    public void drawMenu() {
        for (Map.Entry<String, SpriteObjWIP> entry : this._objects.entrySet()) {
            entry.getValue().draw();
        }
    }

    public void hideMenu() {
        for (Map.Entry<String, SpriteObjWIP> entry : this._objects.entrySet()) {
            entry.getValue().setVisible(false);
        }
    }

    public void dispose() {
        for (Map.Entry<String, SpriteObjWIP> entry : this._objects.entrySet()) {
            entry.getValue().dispose();
        }
        this._objects.clear();
        this._objects = null;
    }
}

