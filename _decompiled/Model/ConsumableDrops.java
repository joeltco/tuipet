/*
 * Decompiled with CFR 0.152.
 */
package Model;

public class ConsumableDrops {
    private int _id;
    private int _consumableID;
    private boolean _isFood;
    private int _rate;

    public int getID() {
        return this._id;
    }

    public int getConsumableID() {
        return this._consumableID;
    }

    public boolean isFood() {
        return this._isFood;
    }

    public int getRate() {
        return this._rate;
    }

    public ConsumableDrops(String[] info) {
        this._id = Integer.parseInt(info[0]);
        this._consumableID = Integer.parseInt(info[1]);
        this._isFood = Boolean.parseBoolean(info[2]);
        this._rate = Integer.parseInt(info[3]);
    }
}

