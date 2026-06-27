/*
 * Decompiled with CFR 0.152.
 */
package Model;

public class BackgroundRange {
    private int[] _range;
    private int _backgroundID;

    public int[] getRange() {
        return this._range;
    }

    public int getBackgroundID() {
        return this._backgroundID;
    }

    public BackgroundRange(int id, int[] range) {
        this._backgroundID = id;
        this._range = range;
    }

    public BackgroundRange(String data) {
        String[] backRange = data.split(":");
        this._backgroundID = Integer.parseInt(backRange[1]);
        String[] range = backRange[0].split("t");
        this._range = new int[]{Integer.parseInt(range[0]), Integer.parseInt(range[1])};
    }

    public BackgroundRange(String[] data) {
        this._backgroundID = Integer.parseInt(data[1]);
        String[] range = data[0].split("t");
        this._range = new int[]{Integer.parseInt(range[0]), Integer.parseInt(range[1])};
    }
}

