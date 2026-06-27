/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;
import Model.Enum;

public class WeatherRecord {
    private boolean _isHome;
    private int[] _mapZone = new int[]{-1, -1};
    private int[] _stepsRange = new int[]{-1, -1};
    private Enum.Weather _weather = Enum.Weather.Clear;
    private byte _temp = (byte)-1;
    private byte _dayTemp = (byte)-1;
    private int _habitat = -1;

    public boolean getIsHome() {
        return this._isHome;
    }

    public void setIsHome(boolean h) {
        this._isHome = h;
    }

    public int[] getMapZone() {
        return this._mapZone;
    }

    public void setMapZone(int[] mz) {
        this._mapZone = mz;
    }

    public int[] getStepsRange() {
        return this._stepsRange;
    }

    public void setStepsRange(int[] s) {
        this._stepsRange = s;
    }

    public Enum.Weather getWeather() {
        return this._weather;
    }

    public void setWeather(Enum.Weather w) {
        this._weather = w;
    }

    public byte getTemp() {
        return this._temp;
    }

    public void setTemp(int t) {
        if (t <= Config._maxTemp && t >= 0) {
            this._temp = (byte)t;
        }
    }

    public byte getDayTemp() {
        return this._dayTemp;
    }

    public void setDayTemp(int t) {
        if (t <= Config._maxTemp && t >= 0) {
            this._dayTemp = (byte)t;
        }
    }

    public int getHabitat() {
        return this._habitat;
    }

    public WeatherRecord(String[] info) {
        this.readInfo(info);
    }

    public WeatherRecord(boolean isHome, int habitat, Enum.Weather weather, int temp, int dayTemp) {
        this._habitat = habitat;
        this._isHome = isHome;
        this._weather = weather;
        this._temp = (byte)temp;
        this._dayTemp = (byte)dayTemp;
    }

    public WeatherRecord(int[] mapZone, int[] steps, Enum.Weather weather, int temp, int dayTemp, int habitat) {
        this._habitat = habitat;
        this._mapZone = mapZone;
        this._stepsRange = steps;
        this._weather = weather;
        this._temp = (byte)temp;
        this._dayTemp = (byte)dayTemp;
    }

    public String writeInfo() {
        return this._isHome + ";" + this._mapZone[0] + ";" + this._mapZone[1] + ";" + this._stepsRange[0] + "t" + this._stepsRange[1] + ";" + (Object)((Object)this._weather) + ";" + this._temp + ";" + this._dayTemp + ";" + this._habitat;
    }

    public void readInfo(String[] info) {
        this._isHome = Boolean.parseBoolean(info[0]);
        this._mapZone[0] = Integer.parseInt(info[1]);
        this._mapZone[1] = Integer.parseInt(info[2]);
        String[] steps = info[3].split("t");
        this._stepsRange[0] = Integer.parseInt(steps[0]);
        this._stepsRange[1] = Integer.parseInt(steps[1]);
        this._weather = Enum.Weather.valueOf(info[4]);
        this._temp = Byte.parseByte(info[5]);
        this._dayTemp = Byte.parseByte(info[6]);
        if (info.length > 7) {
            this._habitat = Integer.parseInt(info[7]);
        }
    }
}

