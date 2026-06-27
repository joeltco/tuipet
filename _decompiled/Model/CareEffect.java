/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;

public class CareEffect {
    private int _id;
    private int _spriteNum;
    private int _spriteSet;
    private String _name;
    private String _description;
    private int _minDuration;
    private int _maxDuration;
    private int _lapse;
    private boolean _canReapply;
    private boolean _endOnSleepChange;
    private boolean _pauseHunger;
    private boolean _pauseStrength;
    private boolean _pauseTemp;
    private boolean _pauseCall;
    private int[] _moodChange;
    private int[] _energyChange;
    private int[] _hungerChange;
    private int[] _strengthChange;
    private int[] _sleepLapseChange;
    private int[] _awakeLapseChange;

    public int getID() {
        return this._id;
    }

    public int getSpriteNum() {
        return this._spriteNum;
    }

    public int getSpriteSet() {
        return this._spriteSet;
    }

    public String getName() {
        return this._name;
    }

    public String getDescription() {
        return this._description;
    }

    public int getMinDuration() {
        return this._minDuration;
    }

    public int getMaxDuration() {
        return this._maxDuration;
    }

    public boolean isActive() {
        return this._lapse > 0;
    }

    public int getLapse() {
        return this._lapse;
    }

    public void setLapse(int l) {
        this._lapse = l < 0 ? 0 : l;
    }

    public void decLapse() {
        this.setLapse(this._lapse - 1);
    }

    public boolean endOnSleepChange() {
        return this._endOnSleepChange;
    }

    public boolean pauseHunger() {
        return this._pauseHunger;
    }

    public boolean pauseStrength() {
        return this._pauseStrength;
    }

    public boolean pauseTemp() {
        return this._pauseTemp;
    }

    public boolean pauseCall() {
        return this._pauseCall;
    }

    public int[] getMoodChange() {
        return this._moodChange;
    }

    public int[] getEnergyChange() {
        return this._energyChange;
    }

    public int[] getHungerChange() {
        return this._hungerChange;
    }

    public int[] getStrengthChange() {
        return this._strengthChange;
    }

    public int[] getSleepLapseChange() {
        return this._sleepLapseChange;
    }

    public int[] getAwakeLapseChange() {
        return this._awakeLapseChange;
    }

    public CareEffect(String[] info) {
        this._id = Integer.parseInt(info[0]);
        this._spriteNum = Integer.parseInt(info[1]);
        this._spriteSet = Integer.parseInt(info[2]);
        this._name = info[3];
        this._description = info[4];
        this._minDuration = Integer.parseInt(info[5]);
        this._maxDuration = Integer.parseInt(info[6]);
        this._endOnSleepChange = Boolean.parseBoolean(info[7]);
        this._pauseHunger = Boolean.parseBoolean(info[8]);
        this._pauseStrength = Boolean.parseBoolean(info[9]);
        this._pauseTemp = Boolean.parseBoolean(info[10]);
        this._pauseCall = Boolean.parseBoolean(info[11]);
        String[] s = info[12].split(";");
        this._moodChange = new int[]{Integer.parseInt(s[0]), Integer.parseInt(s[1])};
        s = info[13].split(";");
        this._energyChange = new int[]{Integer.parseInt(s[0]), Integer.parseInt(s[1])};
        s = info[14].split(";");
        this._hungerChange = new int[]{Integer.parseInt(s[0]), Integer.parseInt(s[1])};
        s = info[15].split(";");
        this._strengthChange = new int[]{Integer.parseInt(s[0]), Integer.parseInt(s[1])};
        s = info[16].split(";");
        this._sleepLapseChange = new int[]{Integer.parseInt(s[0]), Integer.parseInt(s[1])};
        s = info[17].split(";");
        this._awakeLapseChange = new int[]{Integer.parseInt(s[0]), Integer.parseInt(s[1])};
        this._canReapply = Boolean.parseBoolean(info[18]);
    }

    public void startEffect() {
        if (this.canApply()) {
            this._lapse = Utility.randomBetween(this._minDuration, this._maxDuration);
        }
    }

    public boolean canApply() {
        return !this.isActive() || this._canReapply && this.isActive();
    }
}

