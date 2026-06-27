/*
 * Decompiled with CFR 0.152.
 */
package View;

import Model.ViewSettings;

public class SpriteDetail {
    private String _location;
    private float _opacity;
    private double _spriteRescale;
    private boolean _isMirror;
    private int _width;
    private int _height;
    private ViewSettings _view;

    public String getLocation() {
        return this._location;
    }

    public float getOpacity() {
        return this._opacity;
    }

    public double getSpriteRescale() {
        return this._spriteRescale * this._view.getGameScale();
    }

    public boolean isMirror() {
        return this._isMirror;
    }

    public int getWidth() {
        return this._width;
    }

    public int getHeight() {
        return this._height;
    }

    public SpriteDetail(String location, float opacity, double scale, boolean isMirror, int width, int height, ViewSettings view) {
        this._location = location;
        this._opacity = opacity;
        this._spriteRescale = scale;
        this._isMirror = isMirror;
        this._width = width;
        this._height = height;
        this._view = view;
    }
}

