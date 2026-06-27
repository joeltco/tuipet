/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.FoodType;

public class MinLapsePacket {
    private boolean _cleaned;
    private FoodType _food;
    private boolean _lightSwitch;

    public boolean isCleaned() {
        return this._cleaned;
    }

    public FoodType getFood() {
        return this._food;
    }

    public boolean isLightSwitch() {
        return this._lightSwitch;
    }

    public MinLapsePacket(boolean c, FoodType f, boolean l) {
        this._cleaned = c;
        this._food = f;
        this._lightSwitch = l;
    }
}

